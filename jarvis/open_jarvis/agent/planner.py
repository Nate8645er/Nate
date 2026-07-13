"""Planer fuer den JARVIS-Agenten.

Ein Planer nimmt eine Aufgabe (natuerliche Sprache) und die Werkzeugliste und
liefert einen Plan: eine Liste von Schritten ``{tool, args, why}`` plus eine
Abschlussnachricht ``final``.

Zwei Planer:
- ``LocalPlanner``  — deterministisch, keyless, offline. Erkennt Absichten per
                      Schluesselwoertern (Shop bauen, Suche, Webseite, App,
                      Notiz, Datei, Plugins). Immer verfuegbar.
- ``ClaudePlanner`` — nutzt ein Claude-/Fable-Modell ueber ``ClaudeProvider``.
                      Faellt bei fehlendem Schluessel/Fehler auf ``LocalPlanner``
                      zurueck (kein Absturz).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from open_jarvis.agent.claude_provider import ClaudePlannerError, ClaudeProvider
from open_jarvis.agent.models import AgentModel
from open_jarvis.agent.tools import Tool, describe_tools


@dataclass
class Plan:
    steps: list[dict[str, Any]]
    final: str
    planner: str
    note: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


PLANNER_SYSTEM = (
    "Du bist der Planer von JARVIS. Zerlege die Aufgabe des Nutzers in konkrete "
    "Werkzeug-Schritte. Antworte AUSSCHLIESSLICH mit einem JSON-Objekt der Form "
    '{"steps": [{"tool": <name>, "args": {..}, "why": <kurz>}], "final": <abschluss auf deutsch>}. '
    "Verwende nur die aufgelisteten Werkzeuge. Halte args minimal und passend."
)


def build_planner_prompt(task: str, registry: dict[str, Tool]) -> str:
    return (
        f"AUFGABE: {task}\n\n"
        f"VERFUEGBARE WERKZEUGE:\n{describe_tools(registry)}\n\n"
        "Gib den Plan als JSON zurueck."
    )


class LocalPlanner:
    """Deterministischer, keyless Planer per Schluesselwort-Erkennung."""

    name = "local"

    def plan(self, task: str, registry: dict[str, Tool]) -> Plan:
        text = (task or "").strip()
        low = text.lower()
        steps: list[dict[str, Any]] = []

        mentions_shop = any(w in low for w in ("shop", "laden", "store", "unternehmen", "firma"))
        wants_live = any(w in low for w in ("shopify", " live", "veroeffentlich", "veröffentlich", "online stellen", "online-stellen", "online", "publiziere", "publizieren"))
        build_verb = any(w in low for w in ("bau", "erstell", "gründ", "gruend", "eröffne", "eroeffne", "stelle einen", "stell einen", "neuer shop", "neuen shop", "neues unternehmen", "leg mir einen", "mach mir einen"))
        if mentions_shop and (build_verb or wants_live):
            steps.append({
                "tool": "shop_veroeffentlichen" if wants_live else "shop_bauen",
                "args": self._shop_args(text),
                "why": "Shop live in Shopify anlegen." if wants_live else "Kompletter Shop-Bauplan aus der Aufgabe abgeleitet.",
            })
        # Shopify-Store-Abfragen/Aktionen (echte MCP-gespiegelte Faehigkeiten).
        if any(w in low for w in ("rabatt", "gutschein", "discount", "code")) and "shop" not in low[:5]:
            code = self._discount_code(text)
            if code:
                steps.append({"tool": "shop_rabatt", "args": {"code": code, "percentage": self._percentage(text)}, "why": "Rabattcode in Shopify anlegen."})
        if any(w in low for w in ("bestellung", "bestellungen", "orders", "verkauf", "umsatz")):
            steps.append({"tool": "shop_bestellungen", "args": {}, "why": "Bestellungen aus Shopify abrufen."})
        if any(w in low for w in ("meine produkte", "produkte im shop", "produkte anzeigen", "welche produkte", "katalog")):
            steps.append({"tool": "shop_produkte", "args": {}, "why": "Produkte aus Shopify abrufen."})
        if any(w in low for w in ("store info", "shop info", "welcher store", "welcher shop", "verbundener")):
            steps.append({"tool": "shop_info", "args": {}, "why": "Store-Info abrufen."})

        if any(w in low for w in ("plugin", "plugins", "faehigkeit", "fähigkeit")):
            steps.append({"tool": "plugins", "args": {}, "why": "Verfuegbare Plugins auflisten."})
        if any(w in low for w in ("such", "google", "finde ", "recherch")):
            steps.append({"tool": "web_suche", "args": {"query": self._strip_verb(text)}, "why": "Websuche vorbereiten."})
        url = self._find_url(text)
        if url:
            steps.append({"tool": "webseite", "args": {"url": url}, "why": "Genannte Webseite oeffnen."})
        if any(w in low for w in ("starte app", "oeffne app", "öffne app", "programm", "app ")):
            steps.append({"tool": "app_starten", "args": {"app": self._app_name(text)}, "why": "Genannte App starten."})
        if any(w in low for w in ("notiz", "merke", "erinner")):
            steps.append({"tool": "notiz", "args": {"note": text}, "why": "Notiz ablegen."})

        if not steps:
            # Fallback: als Notiz festhalten, damit nie ein leerer Plan entsteht.
            steps.append({
                "tool": "notiz",
                "args": {"note": text},
                "why": "Aufgabe nicht eindeutig — als Notiz festgehalten.",
            })
            final = ("Ich konnte keinen eindeutigen Befehl erkennen und habe die Aufgabe als "
                     "Notiz festgehalten. Formuliere z. B. 'baue einen Shop fuer ...' oder "
                     "'suche nach ...'.")
        else:
            final = "Plan erstellt. Ich fuehre die Schritte der Reihe nach aus."
        return Plan(steps=steps, final=final, planner=self.name)

    @staticmethod
    def _strip_verb(text: str) -> str:
        return re.sub(r"^(such[e]?|finde|google|recherchiere)\s+(nach\s+)?", "", text, flags=re.IGNORECASE).strip() or text

    @staticmethod
    def _discount_code(text: str) -> str | None:
        m = re.search(r"\bcode\s+([A-Za-z0-9]{3,})", text, flags=re.IGNORECASE)
        if m:
            return m.group(1).upper()
        m2 = re.search(r"\b([A-Z][A-Z0-9]{3,})\b", text)  # z. B. SOMMER10
        return m2.group(1) if m2 else None

    @staticmethod
    def _percentage(text: str) -> int:
        m = re.search(r"(\d{1,2})\s*%", text)
        return int(m.group(1)) if m else 10

    @staticmethod
    def _find_url(text: str) -> str | None:
        match = re.search(r"(https?://\S+|\b[\w-]+\.(?:de|com|ch|org|net|io)\b\S*)", text)
        return match.group(1) if match else None

    @staticmethod
    def _app_name(text: str) -> str:
        match = re.search(r"(?:app|programm)\s+([\w .-]+)", text, flags=re.IGNORECASE)
        return (match.group(1).strip() if match else text).split()[0] if text else "notepad"

    @staticmethod
    def _shop_args(text: str) -> dict[str, Any]:
        args: dict[str, Any] = {}
        # Stoppwoerter, an denen ein Name endet (Bindewoerter / Befehlsteile).
        stop = (r"live|auf|online|shopify|und|oder|mit|fuer|für|als|in|zum|zur|"
                r"veroeffentlich\w*|veröffentlich\w*|publizier\w*")
        # Name aus "namens X" / "heisst X" ziehen — hoert an einem Stoppwort auf.
        m2 = re.search(
            rf"(?:namens|heisst|heißt|name\s+ist)\s+((?:(?!\b(?:{stop})\b)[\wäöüÄÖÜ'-]+\s*){{1,4}})",
            text,
            flags=re.IGNORECASE,
        )
        if m2:
            args["name"] = m2.group(1).strip(" .")
        # "shop fuer X" / "shop für X" -> was verkauft wird
        m = re.search(r"(?:shop|laden|store|unternehmen|firma)\s+(?:fuer|für|mit|zum verkauf von)\s+(.+)", text, flags=re.IGNORECASE)
        if m:
            sells = m.group(1).strip(" .")
            # Ein evtl. angehaengtes "namens ..."/"heisst ..." aus dem Verkaufstext entfernen.
            sells = re.split(r"\s+(?:namens|heisst|heißt|name\s+ist)\s+", sells, flags=re.IGNORECASE)[0].strip(" .")
            args["sells"] = sells
        if "name" not in args and args.get("sells"):
            args["name"] = args["sells"].split(",")[0].strip().title() + " Shop"
        return args


class ClaudePlanner:
    """Planer auf Basis eines Claude-/Fable-Modells, mit lokalem Fallback."""

    def __init__(self, model: AgentModel, *, provider: ClaudeProvider | None = None, fallback: LocalPlanner | None = None) -> None:
        self.model = model
        self.name = model.key
        self.provider = provider if provider is not None else ClaudeProvider(model_id=model.model_id, env_key=model.env_key or "ANTHROPIC_API_KEY")
        self.fallback = fallback or LocalPlanner()

    def plan(self, task: str, registry: dict[str, Tool]) -> Plan:
        if not self.provider.available():
            plan = self.fallback.plan(task, registry)
            plan.note = (f"Modell '{self.model.label}' braucht {self.model.env_key}. "
                         "Kein Schluessel gesetzt — lokaler Planer verwendet.")
            plan.planner = f"{self.model.key}->local"
            return plan
        try:
            raw = self.provider.plan(PLANNER_SYSTEM, build_planner_prompt(task, registry))
        except (ClaudePlannerError, ValueError) as exc:
            plan = self.fallback.plan(task, registry)
            plan.note = f"Modell '{self.model.label}' nicht erreichbar ({exc}). Lokaler Planer verwendet."
            plan.planner = f"{self.model.key}->local"
            return plan
        steps = raw.get("steps") if isinstance(raw, dict) else None
        if not isinstance(steps, list) or not steps:
            plan = self.fallback.plan(task, registry)
            plan.note = f"Modell '{self.model.label}' lieferte keinen nutzbaren Plan. Lokaler Planer verwendet."
            plan.planner = f"{self.model.key}->local"
            return plan
        clean_steps = [s for s in steps if isinstance(s, dict) and s.get("tool") in registry]
        if not clean_steps:
            plan = self.fallback.plan(task, registry)
            plan.note = f"Modell '{self.model.label}' nannte nur unbekannte Werkzeuge. Lokaler Planer verwendet."
            plan.planner = f"{self.model.key}->local"
            return plan
        return Plan(steps=clean_steps, final=str(raw.get("final") or "Plan erstellt."), planner=self.model.key, raw=raw)


def build_planner(model: AgentModel) -> LocalPlanner | ClaudePlanner:
    """Passenden Planer fuer ein Modell erzeugen."""

    if model.provider == "local":
        return LocalPlanner()
    if model.provider == "claude":
        return ClaudePlanner(model)
    # Groq ist im Repo als Provider vorhanden; fuer den Agenten nutzen wir vorerst
    # den lokalen Planer, wenn kein Groq-Schluessel/Client vorliegt.
    return LocalPlanner()
