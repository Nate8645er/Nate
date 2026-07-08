"""Plugin: Informationen über das System, auf dem Jarvis läuft."""

import os
import platform
import shutil

from jarvis.plugins.base import JarvisPlugin


class SystemInfoPlugin(JarvisPlugin):
    name = "system"
    description = "Zeigt Informationen über deinen Rechner"
    commands = {"systeminfo": "Betriebssystem, Python-Version, CPU und Speicherplatz"}

    def execute(self, command: str, args: str) -> str:
        disk = shutil.disk_usage(os.path.expanduser("~"))
        gb = 1024 ** 3
        return (
            f"Betriebssystem: {platform.system()} {platform.release()}\n"
            f"Rechnername: {platform.node()}\n"
            f"Python: {platform.python_version()}\n"
            f"CPU-Kerne: {os.cpu_count()}\n"
            f"Speicherplatz: {disk.free / gb:.1f} GB frei von {disk.total / gb:.1f} GB"
        )
