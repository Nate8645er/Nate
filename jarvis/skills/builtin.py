"""Built-in skills: the hands of JARVIS.

Everything here is registered at boot via register_builtin_skills(kernel).
Skills are grouped by category (matching the org chart's skill_categories)
and each declares an honest risk level — the ApprovalManager decides what
needs an explicit user "yes" before it runs.

Heavy desktop capabilities (OCR, PDF, Office, screen analysis, browser
automation) degrade gracefully: if the optional dependency is missing the
skill reports how to enable it instead of crashing.
"""

from __future__ import annotations

import asyncio
import html
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from jarvis.core.approvals import Risk
from jarvis.skills.base import Skill

if TYPE_CHECKING:
    from jarvis.kernel import Kernel


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def register_builtin_skills(kernel: "Kernel") -> None:  # noqa: C901 - registration list
    reg = kernel.skills

    def add(
        name: str,
        description: str,
        category: str,
        risk: Risk,
        func: Any,
        parameters: dict[str, Any],
    ) -> None:
        reg.register(
            Skill(
                name=name,
                description=description,
                category=category,
                risk=risk,
                func=func,
                parameters=parameters,
            )
        )

    # ------------------------------------------------------------------ files
    async def list_files(path: str = ".") -> list[dict[str, Any]]:
        p = _expand(path)
        return [
            {"name": c.name, "dir": c.is_dir(), "size": c.stat().st_size if c.is_file() else 0}
            for c in sorted(p.iterdir())
        ][:500]

    async def read_file(path: str, max_chars: int = 20000) -> str:
        return _expand(path).read_text(encoding="utf-8", errors="replace")[:max_chars]

    async def write_file(path: str, content: str) -> str:
        p = _expand(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"geschrieben: {p} ({len(content)} Zeichen)"

    async def move_file(source: str, destination: str) -> str:
        src, dst = _expand(source), _expand(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"verschoben: {src} -> {dst}"

    async def create_folder(path: str) -> str:
        p = _expand(path)
        p.mkdir(parents=True, exist_ok=True)
        return f"Ordner angelegt: {p}"

    async def delete_path(path: str) -> str:
        p = _expand(path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return f"gelöscht: {p}"

    add("list_files", "Listet Dateien und Ordner in einem Verzeichnis.", "files", Risk.READ,
        list_files, {"path": {"type": "string", "optional": True}})
    add("read_file", "Liest den Inhalt einer Textdatei.", "files", Risk.READ,
        read_file, {"path": {"type": "string"}, "max_chars": {"type": "integer", "optional": True}})
    add("write_file", "Schreibt Text in eine Datei (erstellt sie bei Bedarf).", "files", Risk.WRITE,
        write_file, {"path": {"type": "string"}, "content": {"type": "string"}})
    add("move_file", "Verschiebt oder benennt eine Datei/einen Ordner um.", "files", Risk.WRITE,
        move_file, {"source": {"type": "string"}, "destination": {"type": "string"}})
    add("create_folder", "Legt einen Ordner an (inkl. Elternordner).", "files", Risk.WRITE,
        create_folder, {"path": {"type": "string"}})
    add("delete_path", "Löscht eine Datei oder einen Ordner endgültig.", "files", Risk.CRITICAL,
        delete_path, {"path": {"type": "string"}})

    # ----------------------------------------------------------------- system
    async def run_command(command: str, cwd: str = ".", timeout: int = 60) -> dict[str, Any]:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(_expand(cwd)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return {"exit_code": -1, "stdout": "", "stderr": f"Timeout nach {timeout}s"}
        return {
            "exit_code": proc.returncode,
            "stdout": out.decode(errors="replace")[-8000:],
            "stderr": err.decode(errors="replace")[-8000:],
        }

    async def launch_app(command: str) -> str:
        subprocess.Popen(
            command, shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"gestartet: {command}"

    async def open_url(url: str) -> str:
        if not re.match(r"^https?://", url):
            url = "https://" + url
        opener = {"darwin": "open", "win32": "start"}.get(sys.platform, "xdg-open")
        subprocess.Popen(
            f'{opener} "{url}"', shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return f"Browser geöffnet: {url}"

    async def system_stats() -> dict[str, Any]:
        du = shutil.disk_usage("/")
        stats: dict[str, Any] = {
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "disk_free_gb": round(du.free / 1e9, 1),
            "disk_total_gb": round(du.total / 1e9, 1),
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if hasattr(os, "getloadavg"):
            stats["load_avg"] = os.getloadavg()
        return stats

    add("run_command", "Führt einen Shell-Befehl aus und liefert die Ausgabe.", "system",
        Risk.SYSTEM, run_command,
        {"command": {"type": "string"}, "cwd": {"type": "string", "optional": True},
         "timeout": {"type": "integer", "optional": True}})
    add("launch_app", "Startet ein Programm im Hintergrund.", "system", Risk.SYSTEM,
        launch_app, {"command": {"type": "string"}})
    add("open_url", "Öffnet eine URL im Standard-Browser.", "browser", Risk.SYSTEM,
        open_url, {"url": {"type": "string"}})
    add("system_stats", "Zeigt Systemstatus (Plattform, Speicher, Last, Zeit).", "system",
        Risk.READ, system_stats, {})

    # ----------------------------------------------------------------- coding
    async def git_command(args: str, repo: str = ".") -> dict[str, Any]:
        return await run_command(f"git {args}", cwd=repo)

    add("git_command", "Führt einen Git-Befehl im angegebenen Repository aus.", "coding",
        Risk.SYSTEM, git_command,
        {"args": {"type": "string"}, "repo": {"type": "string", "optional": True}})

    # -------------------------------------------------------------------- web
    async def fetch_url(url: str, max_chars: int = 8000) -> str:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "JARVIS-AI-OS/0.1"})
            resp.raise_for_status()
            text = resp.text
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        return html.unescape(re.sub(r"\s+", " ", text)).strip()[:max_chars]

    async def web_search(query: str, limit: int = 5) -> list[dict[str, str]]:
        """DuckDuckGo HTML search — no API key required."""
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (JARVIS-AI-OS)"},
            )
            resp.raise_for_status()
        results = []
        for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.S
        ):
            url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            results.append({"title": html.unescape(title), "url": html.unescape(url)})
            if len(results) >= limit:
                break
        return results

    add("fetch_url", "Lädt eine Webseite und liefert den Textinhalt.", "web", Risk.READ,
        fetch_url, {"url": {"type": "string"}, "max_chars": {"type": "integer", "optional": True}})
    add("web_search", "Sucht im Web (DuckDuckGo) und liefert Treffer mit URLs.", "web", Risk.READ,
        web_search, {"query": {"type": "string"}, "limit": {"type": "integer", "optional": True}})

    # ----------------------------------------------------------------- memory
    async def remember_fact(subject: str, content: str, kind: str = "fact") -> str:
        fact_id = await kernel.memory.remember(subject, content, kind)
        return f"gemerkt (#{fact_id}): {subject}"

    async def recall_facts(query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        return await kernel.memory.long_term.recall(query=query, limit=limit)

    async def search_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
        return await kernel.memory.search(query, limit=limit)

    add("remember_fact", "Speichert ein Faktum/eine Präferenz im Langzeitgedächtnis.", "memory",
        Risk.WRITE, remember_fact,
        {"subject": {"type": "string"}, "content": {"type": "string"},
         "kind": {"type": "string", "optional": True}})
    add("recall_facts", "Sucht Fakten im Langzeitgedächtnis (Volltext).", "memory", Risk.READ,
        recall_facts, {"query": {"type": "string", "optional": True},
                       "limit": {"type": "integer", "optional": True}})
    add("search_memory", "Semantische Suche über alle Erinnerungen.", "memory", Risk.READ,
        search_memory, {"query": {"type": "string"}, "limit": {"type": "integer", "optional": True}})

    # --------------------------------------------------------------- calendar
    async def create_reminder(message: str, in_minutes: float) -> dict[str, Any]:
        job = kernel.scheduler.add(in_minutes * 60, message, kind="reminder")
        return job.to_dict()

    async def create_appointment(message: str, in_minutes: float) -> dict[str, Any]:
        job = kernel.scheduler.add(in_minutes * 60, message, kind="appointment")
        return job.to_dict()

    async def list_schedule() -> list[dict[str, Any]]:
        return kernel.scheduler.upcoming()

    async def cancel_schedule(job_id: str) -> str:
        return "abgesagt" if kernel.scheduler.cancel(job_id) else "nicht gefunden"

    add("create_reminder", "Erstellt eine Erinnerung in N Minuten.", "calendar", Risk.WRITE,
        create_reminder, {"message": {"type": "string"}, "in_minutes": {"type": "number"}})
    add("create_appointment", "Legt einen Termin an (Benachrichtigung zur Startzeit).",
        "calendar", Risk.WRITE, create_appointment,
        {"message": {"type": "string"}, "in_minutes": {"type": "number"}})
    add("list_schedule", "Listet anstehende Erinnerungen und Termine.", "calendar", Risk.READ,
        list_schedule, {})
    add("cancel_schedule", "Sagt eine Erinnerung / einen Termin ab.", "calendar", Risk.WRITE,
        cancel_schedule, {"job_id": {"type": "string"}})

    # ------------------------------------------------------------------ email
    async def draft_email(to: str, subject: str, body: str) -> str:
        drafts = kernel.settings.data_dir / "drafts"
        drafts.mkdir(exist_ok=True)
        safe_to = re.sub(r"[^\w@.-]", "_", to)[:40]
        path = drafts / f"{int(time.time())}_{safe_to}.eml"
        path.write_text(
            f"To: {to}\nSubject: {subject}\n\n{body}\n", encoding="utf-8"
        )
        return f"E-Mail-Entwurf gespeichert: {path} (Senden erfordert separaten Schritt)"

    add("draft_email", "Bereitet einen E-Mail-Entwurf vor (sendet NICHT).", "email", Risk.WRITE,
        draft_email, {"to": {"type": "string"}, "subject": {"type": "string"},
                      "body": {"type": "string"}})

    # -------------------------------------------------------------- documents
    async def create_document(title: str, content: str, folder: str = "~/Documents") -> str:
        safe_title = re.sub(r"[^\w -]", "", title).strip() or "dokument"
        p = _expand(folder) / f"{safe_title}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
        return f"Dokument erstellt: {p}"

    async def read_pdf(path: str, max_chars: int = 12000) -> str:
        try:
            from pypdf import PdfReader  # optional dependency
        except ImportError:
            return "PDF-Unterstützung fehlt. Installiere sie mit: pip install 'jarvis-ai-os[desktop]'"
        reader = PdfReader(str(_expand(path)))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text[:max_chars]

    async def ocr_image(path: str) -> str:
        try:
            import pytesseract  # optional dependency
            from PIL import Image
        except ImportError:
            return "OCR fehlt. Installiere sie mit: pip install 'jarvis-ai-os[desktop]'"
        return pytesseract.image_to_string(Image.open(str(_expand(path))))

    add("create_document", "Erstellt ein Markdown-Dokument im Zielordner.", "files", Risk.WRITE,
        create_document, {"title": {"type": "string"}, "content": {"type": "string"},
                          "folder": {"type": "string", "optional": True}})
    add("read_pdf", "Extrahiert Text aus einer PDF-Datei.", "files", Risk.READ,
        read_pdf, {"path": {"type": "string"}, "max_chars": {"type": "integer", "optional": True}})
    add("ocr_image", "Liest Text aus einem Bild (OCR).", "media", Risk.READ,
        ocr_image, {"path": {"type": "string"}})

    # ------------------------------------------------------------------ media
    async def list_media(folder: str = "~", kinds: str = "jpg,png,mp4,mp3,wav") -> list[str]:
        exts = {e.strip().lower() for e in kinds.split(",")}
        base = _expand(folder)
        hits = [
            str(p) for p in base.rglob("*")
            if p.is_file() and p.suffix.lstrip(".").lower() in exts
        ]
        return hits[:200]

    add("list_media", "Findet Mediendateien (Bilder/Videos/Audio) in einem Ordner.", "media",
        Risk.READ, list_media,
        {"folder": {"type": "string", "optional": True}, "kinds": {"type": "string", "optional": True}})

    # -------------------------------------------------------------- workflows
    async def run_workflow(name: str) -> dict[str, Any]:
        return await kernel.workflows.run(name)

    async def list_workflows() -> list[dict[str, Any]]:
        return [w.to_dict() for w in kernel.workflows.workflows.values()]

    add("run_workflow", "Startet einen gespeicherten Workflow.", "workflows", Risk.WRITE,
        run_workflow, {"name": {"type": "string"}})
    add("list_workflows", "Listet alle verfügbaren Workflows.", "workflows", Risk.READ,
        list_workflows, {})

    # ------------------------------------------------------------- delegation
    async def delegate(agent: str, goal: str) -> str:
        """Fire-and-forget delegation to another agent (CEO's main tool)."""
        target = kernel.agents.get(agent)
        if target is None:
            available = ", ".join(a.spec.name for a in kernel.agents.all())
            return f"Unbekannter Agent '{agent}'. Verfügbar: {available}"
        task = await target.submit(goal)
        return f"delegiert an {agent} (Task {task.id})"

    async def list_agents() -> list[dict[str, Any]]:
        return kernel.agents.status()

    add("delegate", "Delegiert eine Aufgabe an einen anderen Agenten.", "general", Risk.READ,
        delegate, {"agent": {"type": "string"}, "goal": {"type": "string"}})
    add("list_agents", "Listet alle Agenten der virtuellen Firma mit Status.", "general",
        Risk.READ, list_agents, {})
