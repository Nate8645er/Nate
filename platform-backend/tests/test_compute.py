"""Tests für das Compute-HAL — laufen OHNE GPU (gemockter nvidia-smi)."""

from app.compute.hal import (
    CpuBackend,
    detect_devices,
    detect_summary,
    parse_nvidia_smi,
)

# Beispiel-Ausgabe von `nvidia-smi --query-gpu=... --format=csv,noheader,nounits`
SMI_RTX = "0, NVIDIA GeForce RTX 4090, 24564, 8.9, 12, 2048, 55, 120.5\n"
SMI_SPARK = "0, NVIDIA GB10, 131072, 12.0, 3, 4096, 48, 90.0\n"


def test_cpu_immer_verfuegbar():
    dev = CpuBackend().device()
    assert dev.vendor == "cpu"
    assert CpuBackend().available() is True
    assert "cpu" in dev.backends
    assert dev.memory_model == "unified"  # CPU-RAM ist geteilt


def test_detect_ohne_gpu_liefert_nur_cpu():
    # runner=None + kein nvidia-smi -> nur CPU. Wir erzwingen den No-GPU-Pfad,
    # indem der Runner einen Fehler wirft (simuliert 'nvidia-smi' nicht nutzbar).
    def failing_runner(argv):
        raise FileNotFoundError("nvidia-smi")

    devices = detect_devices(runner=failing_runner)
    assert len(devices) == 1
    assert devices[0].vendor == "cpu"


def test_parse_rtx_dedicated():
    (dev, metrics), = parse_nvidia_smi(SMI_RTX)
    assert dev.vendor == "nvidia"
    assert dev.memory_model == "dedicated"       # klassische RTX: VRAM ≠ RAM
    assert dev.memory_total_mb == 24564
    assert dev.arch == "sm_89"
    assert "fp8" in dev.capabilities             # cc 8.9
    assert "flash_attn" in dev.capabilities
    assert metrics.temperature_c == 55.0
    assert metrics.utilization_pct == 12.0


def test_parse_dgx_spark_unified():
    (dev, _), = parse_nvidia_smi(SMI_SPARK)
    # DGX Spark (GB10): unified memory MUSS erkannt werden
    assert dev.memory_model == "unified"
    assert dev.memory_total_mb == 131072
    assert "fp4" in dev.capabilities             # cc 12.0


def test_detect_mit_gemocktem_gpu_runner():
    devices = detect_devices(runner=lambda argv: SMI_RTX)
    vendors = {d.vendor for d in devices}
    assert "nvidia" in vendors and "cpu" in vendors
    summary = detect_summary(runner=lambda argv: SMI_RTX)
    assert summary["gpu_available"] is True
    assert summary["device_count"] == 2


def test_detect_summary_ohne_gpu():
    summary = detect_summary(runner=lambda argv: (_ for _ in ()).throw(OSError()))
    assert summary["gpu_available"] is False
    assert summary["device_count"] == 1
