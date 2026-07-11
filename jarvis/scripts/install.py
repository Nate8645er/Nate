#!/usr/bin/env python3
"""JARVIS installer: dependency check, GPU/CUDA detection, guided setup.

Usage::

    python scripts/install.py            # interactive, installs recommended extras
    python scripts/install.py --all      # everything (voice, vision, desktop, browser, gui)
    python scripts/install.py --headless # API/core only
    python scripts/install.py --check    # environment report, no changes

Uses ``uv`` when available (much faster), otherwise falls back to pip.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIN_PYTHON = (3, 11)
RECOMMENDED_PYTHON = (3, 13)


def _run(cmd: list[str]) -> int:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.call(cmd)


def check_python() -> bool:
    version = sys.version_info[:2]
    print(f"Python: {platform.python_version()} ({sys.executable})")
    if version < MIN_PYTHON:
        print(f"  ERROR: Python >= {'.'.join(map(str, MIN_PYTHON))} required.")
        return False
    if version < RECOMMENDED_PYTHON:
        print(f"  Note: Python {'.'.join(map(str, RECOMMENDED_PYTHON))} is recommended.")
    return True


def detect_gpu() -> dict[str, object]:
    """Detect NVIDIA GPU and CUDA availability."""
    info: dict[str, object] = {"nvidia": False, "cuda_version": None, "gpus": []}
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            output = subprocess.check_output(
                [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader"],
                text=True,
                timeout=15,
            )
            info["nvidia"] = True
            info["gpus"] = [line.strip() for line in output.strip().splitlines()]
            version_out = subprocess.check_output([nvidia_smi], text=True, timeout=15)
            for token in version_out.split():
                if token.replace(".", "").isdigit() and "." in token:
                    prev = version_out.split()[version_out.split().index(token) - 2]
                    if prev == "CUDA":
                        info["cuda_version"] = token
                        break
        except (subprocess.SubprocessError, OSError):
            pass
    return info


def check_system_deps() -> None:
    print("\nSystem tools:")
    for binary, purpose in [
        ("git", "version control"),
        ("ffmpeg", "audio processing (voice pipeline)"),
        ("tesseract", "OCR (vision pipeline)"),
        ("docker", "container deployment"),
    ]:
        found = shutil.which(binary)
        print(f"  {'✓' if found else '✗'} {binary:<10} {purpose}{'' if found else '  (optional, not found)'}")


def installer_command() -> list[str]:
    if shutil.which("uv"):
        print("Using uv for installation.")
        return ["uv", "pip", "install", "--python", sys.executable]
    print("uv not found; using pip. (Tip: install uv for much faster installs: https://docs.astral.sh/uv/)")
    return [sys.executable, "-m", "pip", "install"]


def install(extras: list[str], gpu: dict[str, object]) -> int:
    base = installer_command()
    target = "." if not extras else f".[{','.join(extras)}]"
    print(f"\nInstalling jarvis-assistant with extras: {extras or 'none'}")
    code = _run([*base, "-e", target])
    if code != 0:
        return code
    if "voice" in extras and gpu.get("nvidia"):
        print("\nNVIDIA GPU detected — faster-whisper will use CUDA automatically "
              "(ensure cuBLAS/cuDNN are installed; CPU fallback is automatic).")
    if "browser" in extras:
        print("\nInstalling Playwright browser (chromium)...")
        _run([sys.executable, "-m", "playwright", "install", "chromium"])
    return 0


def write_env_template() -> None:
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        return
    template = PROJECT_ROOT / ".env.example"
    if template.exists():
        env_file.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"\nCreated {env_file} — add your API keys there.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install JARVIS")
    parser.add_argument("--all", action="store_true", help="install every optional subsystem")
    parser.add_argument("--headless", action="store_true", help="core + API only")
    parser.add_argument("--check", action="store_true", help="report environment, change nothing")
    parser.add_argument(
        "--extras",
        default="",
        help="comma-separated extras (gui,voice,vision,desktop,browser,vector,langchain,dev)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("JARVIS installer")
    print("=" * 60)
    if not check_python():
        return 1

    gpu = detect_gpu()
    print(f"\nGPU: {'NVIDIA ' + ', '.join(map(str, gpu['gpus'])) if gpu['nvidia'] else 'none detected (CPU mode)'}")
    if gpu["cuda_version"]:
        print(f"CUDA: {gpu['cuda_version']}")
    check_system_deps()

    if args.check:
        return 0

    if args.extras:
        extras = [e.strip() for e in args.extras.split(",") if e.strip()]
    elif args.all:
        extras = ["gui", "voice", "vision", "desktop", "browser", "vector"]
    elif args.headless:
        extras = []
    else:
        extras = ["gui", "vector"]  # sensible default: HUD + vector memory

    code = install(extras, gpu)
    if code == 0:
        write_env_template()
        print("\nDone. Next steps:")
        print("  1. Add API keys to .env (or start Ollama for local models)")
        print("  2. jarvis status   — verify providers")
        print("  3. jarvis chat     — terminal chat")
        print("  4. jarvis gui      — the HUD")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
