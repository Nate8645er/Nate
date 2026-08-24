"""Sandboxed file management for desktop tools.

Every path is resolved (symlinks and ``..`` included) and validated against a
set of allowed directory trees before any operation touches the filesystem.
Deletion is soft: files are moved into a ``.jarvis-trash`` directory under the
JARVIS data directory instead of being removed permanently.
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from jarvis.core.config import JarvisConfig
from jarvis.core.errors import DesktopError

T = TypeVar("T")

_MAX_READ_CHARS = 200_000


class FileManager:
    """File operations restricted to configured directory trees.

    Allowed roots come from ``config.desktop.allowed_directories``; when the
    list is empty the user's home directory is the only allowed root.
    Relative paths are resolved against the first allowed root.
    """

    def __init__(self, config: JarvisConfig) -> None:
        roots = [Path(d).expanduser().resolve() for d in config.desktop.allowed_directories]
        self._roots: list[Path] = roots or [Path.home().resolve()]
        self._trash_dir: Path = config.data_dir / ".jarvis-trash"

    @property
    def allowed_directories(self) -> tuple[Path, ...]:
        """The directory trees this manager may touch."""
        return tuple(self._roots)

    @property
    def trash_dir(self) -> Path:
        """Directory that receives soft-deleted files."""
        return self._trash_dir

    def resolve(self, path: str | Path) -> Path:
        """Resolve *path* and ensure it lies inside an allowed directory.

        Raises :class:`DesktopError` for paths escaping the sandbox (including
        ``..`` traversal and symlink tricks, thanks to ``Path.resolve``).
        """
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self._roots[0] / candidate
        resolved = candidate.resolve()
        if any(resolved == root or resolved.is_relative_to(root) for root in self._roots):
            return resolved
        raise DesktopError(f"Access denied: '{resolved}' is outside the allowed directories")

    @staticmethod
    async def _run(func: Callable[[], T]) -> T:
        """Run a blocking operation in a worker thread, mapping OS errors."""
        try:
            return await asyncio.to_thread(func)
        except DesktopError:
            raise
        except OSError as exc:
            raise DesktopError(str(exc), cause=exc) from exc

    # -- operations ----------------------------------------------------------

    async def read_text(self, path: str | Path, max_chars: int = _MAX_READ_CHARS) -> str:
        """Return the text content of a file (truncated to *max_chars*)."""
        target = self.resolve(path)

        def _read() -> str:
            if not target.is_file():
                raise DesktopError(f"Not a file: '{target}'")
            return target.read_text(encoding="utf-8", errors="replace")[:max_chars]

        return await self._run(_read)

    async def write_text(self, path: str | Path, content: str) -> str:
        """Write *content* to a file, creating parent directories as needed."""
        target = self.resolve(path)

        def _write() -> str:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return str(target)

        return await self._run(_write)

    async def append_text(self, path: str | Path, content: str) -> str:
        """Append *content* to a file, creating it if missing."""
        target = self.resolve(path)

        def _append() -> str:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(content)
            return str(target)

        return await self._run(_append)

    async def delete(self, path: str | Path) -> str:
        """Soft-delete: move the file or directory into the trash directory."""
        target = self.resolve(path)

        def _delete() -> str:
            if not target.exists():
                raise DesktopError(f"Path does not exist: '{target}'")
            self._trash_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            destination = self._trash_dir / f"{stamp}-{target.name}"
            counter = 1
            while destination.exists():
                destination = self._trash_dir / f"{stamp}-{counter}-{target.name}"
                counter += 1
            shutil.move(str(target), str(destination))
            return str(destination)

        return await self._run(_delete)

    async def move(self, source: str | Path, destination: str | Path) -> str:
        """Move a file or directory inside the sandbox."""
        src = self.resolve(source)
        dst = self.resolve(destination)

        def _move() -> str:
            if not src.exists():
                raise DesktopError(f"Source does not exist: '{src}'")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return str(dst)

        return await self._run(_move)

    async def copy(self, source: str | Path, destination: str | Path) -> str:
        """Copy a file or directory tree inside the sandbox."""
        src = self.resolve(source)
        dst = self.resolve(destination)

        def _copy() -> str:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            else:
                raise DesktopError(f"Source does not exist: '{src}'")
            return str(dst)

        return await self._run(_copy)

    async def mkdir(self, path: str | Path) -> str:
        """Create a directory (parents included, idempotent)."""
        target = self.resolve(path)

        def _mkdir() -> str:
            target.mkdir(parents=True, exist_ok=True)
            return str(target)

        return await self._run(_mkdir)

    async def list_dir(self, path: str | Path) -> list[dict[str, Any]]:
        """List directory entries with type, size and modification time."""
        target = self.resolve(path)

        def _list() -> list[dict[str, Any]]:
            if not target.is_dir():
                raise DesktopError(f"Not a directory: '{target}'")
            entries: list[dict[str, Any]] = []
            for entry in sorted(target.iterdir(), key=lambda p: p.name.lower()):
                try:
                    stat = entry.stat()
                except OSError:
                    continue
                entries.append(
                    {
                        "name": entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(
                            timespec="seconds"
                        ),
                    }
                )
            return entries

        return await self._run(_list)

    async def search(
        self,
        directory: str | Path,
        pattern: str = "**/*",
        content: str | None = None,
        max_results: int = 50,
    ) -> list[str]:
        """Find files below *directory* by glob *pattern*, optionally filtered
        by a plain-text *content* substring."""
        root = self.resolve(directory)

        def _search() -> list[str]:
            if not root.is_dir():
                raise DesktopError(f"Not a directory: '{root}'")
            matches: list[str] = []
            for candidate in sorted(root.glob(pattern)):
                if len(matches) >= max_results:
                    break
                if content is not None:
                    if not candidate.is_file():
                        continue
                    try:
                        text = candidate.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if content not in text:
                        continue
                matches.append(str(candidate))
            return matches

        return await self._run(_search)
