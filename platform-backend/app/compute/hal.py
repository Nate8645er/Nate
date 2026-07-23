"""Hardware-Abstraktions-Schicht (HAL) — Erkennung, Geräte, Metriken.

Auftrag §5. Wichtige Design-Entscheidungen, die im Code stehen MÜSSEN:

* `memory_model` unterscheidet `dedicated` (klassische RTX: VRAM ≠ RAM) von
  `unified` (z. B. NVIDIA DGX Spark / GB10 / Apple Silicon: CPU & GPU teilen
  denselben Speicher). Budget-Strategien unterscheiden sich dadurch.
* Erkennung ist robust und ohne Hardware testbar: der Kommando-Runner ist
  injizierbar, sodass Tests eine gemockte `nvidia-smi`-Ausgabe einspeisen
  (kein NVML/keine GPU nötig).
* Reihenfolge mit Fallback: NVIDIA (nvidia-smi) → Plattform/CPU. Schlägt die
  GPU-Erkennung fehl, ist das kein Fehler, sondern der normale CPU-Pfad.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

MemoryModel = Literal["dedicated", "unified"]
Vendor = Literal["nvidia", "amd", "apple", "cpu"]

#: Injizierbarer Kommando-Runner: (argv) -> stdout. Default nutzt subprocess.
CommandRunner = Callable[[list[str]], str]


@dataclass(frozen=True)
class ComputeDevice:
    id: str
    vendor: Vendor
    name: str
    arch: str | None
    memory_total_mb: int
    memory_model: MemoryModel
    backends: frozenset[str] = field(default_factory=frozenset)
    capabilities: frozenset[str] = field(default_factory=frozenset)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["backends"] = sorted(self.backends)
        d["capabilities"] = sorted(self.capabilities)
        return d


@dataclass(frozen=True)
class DeviceMetrics:
    device_id: str
    utilization_pct: float | None
    memory_used_mb: int | None
    memory_total_mb: int | None
    temperature_c: float | None
    power_w: float | None
    throttle_reason: str | None = None


@runtime_checkable
class ComputeBackend(Protocol):
    """Ein ausführendes Backend für ein Gerät (CPU, CUDA/vLLM, llama.cpp, …)."""

    def available(self) -> bool: ...
    def device(self) -> ComputeDevice: ...
    def metrics(self) -> DeviceMetrics: ...


# --------------------------------------------------------------------------- #
# Standard-Kommando-Runner
# --------------------------------------------------------------------------- #
def default_runner(argv: list[str], timeout: float = 3.0) -> str:
    """Führt ein Kommando aus, gibt stdout zurück; wirft bei Fehler/Timeout."""
    proc = subprocess.run(
        argv, capture_output=True, text=True, timeout=timeout, check=True
    )
    return proc.stdout


# --------------------------------------------------------------------------- #
# CPU-Backend (immer verfügbar, vollwertiger Pfad)
# --------------------------------------------------------------------------- #
def _total_ram_mb() -> int:
    try:
        with open("/proc/meminfo", encoding="ascii") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 0


class CpuBackend:
    def available(self) -> bool:
        return True

    def device(self) -> ComputeDevice:
        return ComputeDevice(
            id="cpu:0",
            vendor="cpu",
            name=platform.processor() or platform.machine() or "cpu",
            arch=platform.machine() or None,
            memory_total_mb=_total_ram_mb(),
            memory_model="unified",  # CPU-RAM ist per Definition geteilt
            backends=frozenset({"cpu", "llama_cpp", "onnx"}),
            capabilities=frozenset({"fp32"}),
        )

    def metrics(self) -> DeviceMetrics:
        dev = self.device()
        return DeviceMetrics(
            device_id=dev.id,
            utilization_pct=None,
            memory_used_mb=None,
            memory_total_mb=dev.memory_total_mb,
            temperature_c=None,
            power_w=None,
        )


# --------------------------------------------------------------------------- #
# NVIDIA-Erkennung (nvidia-smi, injizierbar für Tests)
# --------------------------------------------------------------------------- #
#: unified-memory-Geräte (ARM SoC mit geteiltem Speicher). Namen-Muster.
_UNIFIED_HINTS = ("gb10", "grace", "spark", "orin", "thor", "agx")

_SMI_QUERY = (
    "--query-gpu=index,name,memory.total,compute_cap,"
    "utilization.gpu,memory.used,temperature.gpu,power.draw"
)


def parse_nvidia_smi(csv_out: str) -> list[tuple[ComputeDevice, DeviceMetrics]]:
    """Parst die CSV-Ausgabe von `nvidia-smi --query-gpu=… --format=csv,noheader,nounits`.

    Rein und ohne Hardware testbar.
    """
    results: list[tuple[ComputeDevice, DeviceMetrics]] = []
    for raw in csv_out.strip().splitlines():
        if not raw.strip():
            continue
        cols = [c.strip() for c in raw.split(",")]
        if len(cols) < 4:
            continue
        idx, name, mem_total = cols[0], cols[1], cols[2]
        compute_cap = cols[3] if len(cols) > 3 else ""

        def _num(i: int, cols: list = cols) -> float | None:
            # cols explizit gebunden (Default-Argument), damit die Closure die
            # Spalten DIESER Zeile nutzt — kein Late-Binding auf die Loop-Variable.
            if i < len(cols):
                try:
                    return float(cols[i])
                except ValueError:
                    return None
            return None

        low = name.lower()
        memory_model: MemoryModel = "unified" if any(h in low for h in _UNIFIED_HINTS) else "dedicated"
        try:
            mem_total_mb = int(float(mem_total))
        except ValueError:
            mem_total_mb = 0
        arch = f"sm_{compute_cap.replace('.', '')}" if compute_cap else None

        caps = {"fp16", "bf16"}
        # grobe Fähigkeits-Ableitung aus Compute-Capability
        try:
            cc = float(compute_cap) if compute_cap else 0.0
        except ValueError:
            cc = 0.0
        if cc >= 8.9:
            caps.add("fp8")
        if cc >= 10.0:
            caps.add("fp4")
        if cc >= 8.0:
            caps.add("flash_attn")

        dev = ComputeDevice(
            id=f"cuda:{idx}",
            vendor="nvidia",
            name=name,
            arch=arch,
            memory_total_mb=mem_total_mb,
            memory_model=memory_model,
            backends=frozenset({"cuda", "vllm", "llama_cpp", "onnx"}),
            capabilities=frozenset(caps),
        )
        metrics = DeviceMetrics(
            device_id=dev.id,
            utilization_pct=_num(4),
            memory_used_mb=int(_num(5)) if _num(5) is not None else None,
            memory_total_mb=mem_total_mb,
            temperature_c=_num(6),
            power_w=_num(7),
        )
        results.append((dev, metrics))
    return results


def detect_devices(runner: CommandRunner | None = None) -> list[ComputeDevice]:
    """Erkennt alle Geräte. CPU immer; NVIDIA falls `nvidia-smi` vorhanden/erfolgreich.

    `runner` ist injizierbar: Tests übergeben einen Fake, der eine CSV liefert —
    so wird der NVIDIA-Pfad ohne echte GPU getestet.
    """
    devices: list[ComputeDevice] = []

    smi_available = runner is not None or shutil.which("nvidia-smi") is not None
    if smi_available:
        run = runner or (lambda argv: default_runner(argv))
        try:
            out = run(["nvidia-smi", _SMI_QUERY, "--format=csv,noheader,nounits"])
            devices.extend(dev for dev, _ in parse_nvidia_smi(out))
        except (OSError, subprocess.SubprocessError, ValueError):
            pass  # ehrlicher Fallback: keine GPU-Geräte, CPU folgt

    devices.append(CpuBackend().device())
    return devices


def detect_summary(runner: CommandRunner | None = None) -> dict:
    """Kompakte Übersicht für /health/compute."""
    devices = detect_devices(runner)
    gpus = [d for d in devices if d.vendor != "cpu"]
    return {
        "gpu_available": bool(gpus),
        "device_count": len(devices),
        "devices": [d.to_dict() for d in devices],
    }
