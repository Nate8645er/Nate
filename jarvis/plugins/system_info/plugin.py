"""System information plugin: CPU, memory, disks, battery, uptime."""

from __future__ import annotations

import platform
import shutil
import time
from pathlib import Path

from jarvis.plugins.api import Plugin, PluginContext, PluginManifest


class SystemInfoPlugin(Plugin):
    manifest = PluginManifest(
        name="system_info",
        version="1.0.0",
        description="Reads CPU, RAM, disk, battery and OS information",
        author="JARVIS",
        tags=["system", "utility"],
    )

    async def setup(self, context: PluginContext) -> None:
        context.register_tool(
            "system_overview",
            "Get an overview of the machine: OS, CPU load, RAM, disk usage, uptime.",
            self.overview,
            tags={"system", "utility"},
        )
        context.register_tool(
            "system_disk_usage",
            "Get free/total disk space for a path (default: home directory).",
            self.disk_usage,
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Filesystem path"}},
            },
            tags={"system", "utility"},
        )

    def overview(self) -> str:
        lines = [
            f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
            f"Python: {platform.python_version()}",
        ]
        try:
            import psutil

            lines.append(f"CPU: {psutil.cpu_percent(interval=0.2)}% of {psutil.cpu_count()} cores")
            memory = psutil.virtual_memory()
            lines.append(
                f"RAM: {memory.used / 1e9:.1f} / {memory.total / 1e9:.1f} GB ({memory.percent}%)"
            )
            boot = time.time() - psutil.boot_time()
            lines.append(f"Uptime: {boot / 3600:.1f} hours")
            battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
            if battery is not None:
                state = "charging" if battery.power_plugged else "discharging"
                lines.append(f"Battery: {battery.percent:.0f}% ({state})")
        except ImportError:
            lines.append("(install psutil for CPU/RAM/battery details)")
        return "\n".join(lines)

    def disk_usage(self, path: str = "") -> str:
        target = Path(path).expanduser() if path else Path.home()
        usage = shutil.disk_usage(target)
        return (
            f"{target}: {usage.free / 1e9:.1f} GB free of {usage.total / 1e9:.1f} GB "
            f"({usage.used / usage.total * 100:.0f}% used)"
        )
