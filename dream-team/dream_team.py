#!/usr/bin/env python3
"""Dream Team — Claude Code (Fable 5) x ChatGPT (GPT Sol 5.6).

Zwei KI-Modelle verbinden sich zu einem Team:

  * Claude Fable 5   (Anthropic)  — der Builder/Architekt
  * GPT Sol 5.6      (OpenAI)     — der Reviewer/Sparringspartner

Modi:
  ask   <frage>     Beide diskutieren die Frage in Runden, Claude fasst zusammen.
  code  <aufgabe>   Claude schreibt Code, GPT reviewt, Claude verbessert.
  chat              Interaktiver Modus: du schreibst, beide antworten im Team.

Benoetigte Umgebungsvariablen:
  ANTHROPIC_API_KEY   API-Key fuer Claude
  OPENAI_API_KEY      API-Key fuer ChatGPT

Optionale Umgebungsvariablen:
  DREAMTEAM_CLAUDE_MODEL    (Default: claude-fable-5)
  DREAMTEAM_CLAUDE_FALLBACK (Default: claude-opus-4-8)
  DREAMTEAM_OPENAI_MODEL    (Default: gpt-5.6 — anpassen falls dein Modell
                             z.B. "gpt-sol-5.6" heisst)
  DREAMTEAM_MAX_TOKENS      (Default: 16000)
  DREAMTEAM_MOCK=1          Demo-Modus ohne API-Keys (canned responses)
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field

CLAUDE_MODEL = os.environ.get("DREAMTEAM_CLAUDE_MODEL", "claude-fable-5")
CLAUDE_FALLBACK = os.environ.get("DREAMTEAM_CLAUDE_FALLBACK", "claude-opus-4-8")
OPENAI_MODEL = os.environ.get("DREAMTEAM_OPENAI_MODEL", "gpt-5.6")
MAX_TOKENS = int(os.environ.get("DREAMTEAM_MAX_TOKENS", "16000"))

ORANGE = "\033[38;5;208m"
GREEN = "\033[38;5;114m"
GREY = "\033[38;5;245m"
BOLD = "\033[1m"
RESET = "\033[0m"

TEAM_RULES = (
    "Du bist Teil des 'AI Dream Team' aus zwei Modellen, die gemeinsam an einer "
    "Aufgabe arbeiten. Lies die bisherige Team-Diskussion aufmerksam. Baue auf den "
    "Beitraegen deines Partners auf, statt sie zu wiederholen: bestaetige was gut ist, "
    "korrigiere Fehler konkret, und bringe eigene neue Punkte ein. Antworte in der "
    "Sprache des Nutzers. Halte dich kurz und substanziell."
)

CLAUDE_PERSONA = (
    TEAM_RULES
    + " Deine Rolle im Team: Claude (Fable 5), der Builder und Architekt. Du "
    "entwirfst Loesungen, schreibst Code und triffst Entscheidungen. Am Ende einer "
    "Diskussion lieferst du das konsolidierte Endergebnis."
)

GPT_PERSONA = (
    TEAM_RULES
    + " Deine Rolle im Team: GPT Sol, der Reviewer und Sparringspartner. Du pruefst "
    "die Vorschlaege deines Partners kritisch, findest Luecken, Bugs und Risiken, "
    "und machst konkrete Verbesserungsvorschlaege."
)


@dataclass
class Turn:
    speaker: str  # "claude" | "gpt" | "user"
    text: str


@dataclass
class Transcript:
    turns: list[Turn] = field(default_factory=list)

    def add(self, speaker: str, text: str) -> None:
        self.turns.append(Turn(speaker, text))

    def as_messages(self, me: str) -> list[dict]:
        """Render the shared transcript from one agent's perspective.

        The agent's own turns become 'assistant' messages; everything else
        (user + the partner model) becomes 'user' messages with a speaker tag,
        so each model always sees who said what.
        """
        labels = {"claude": "Claude (Fable 5)", "gpt": "GPT Sol 5.6", "user": "Nutzer"}
        messages: list[dict] = []
        for turn in self.turns:
            if turn.speaker == me:
                messages.append({"role": "assistant", "content": turn.text})
            else:
                messages.append(
                    {"role": "user", "content": f"[{labels[turn.speaker]}]: {turn.text}"}
                )
        # APIs require the first message to be a user turn.
        if messages and messages[0]["role"] != "user":
            messages.insert(0, {"role": "user", "content": "(Team-Session gestartet)"})
        return messages


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


class ClaudeAgent:
    key = "claude"
    label = f"{ORANGE}{BOLD}Claude (Fable 5){RESET}"

    def __init__(self) -> None:
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()

    def reply(self, transcript: Transcript, system: str = CLAUDE_PERSONA) -> str:
        messages = transcript.as_messages(self.key)
        try:
            # Fable 5: Refusal-Fallback auf Opus 4.8, damit ein Safety-Decline
            # den Team-Loop nicht abbricht.
            response = self.client.beta.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                betas=["server-side-fallback-2026-06-01"],
                fallbacks=[{"model": CLAUDE_FALLBACK}],
                system=system,
                messages=messages,
            )
        except (TypeError, self._anthropic.BadRequestError):
            # SDK/Modell ohne Fallback-Support (z.B. aelteres SDK oder ein
            # Nicht-Fable-Modell via DREAMTEAM_CLAUDE_MODEL): plain retry.
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
            )
        if response.stop_reason == "refusal":
            return "(Claude hat diese Anfrage aus Sicherheitsgruenden abgelehnt.)"
        return "\n".join(
            block.text for block in response.content if block.type == "text"
        ).strip()


class GPTAgent:
    key = "gpt"
    label = f"{GREEN}{BOLD}GPT Sol 5.6{RESET}"

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI()

    def reply(self, transcript: Transcript, system: str = GPT_PERSONA) -> str:
        messages = [{"role": "system", "content": system}]
        messages += transcript.as_messages(self.key)
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        return (response.choices[0].message.content or "").strip()


class MockAgent:
    """Demo-Agent ohne API-Keys (DREAMTEAM_MOCK=1 oder --mock)."""

    def __init__(self, key: str, label: str) -> None:
        self.key = key
        self.label = label
        self._n = 0

    def reply(self, transcript: Transcript, system: str = "") -> str:
        self._n += 1
        who = "Claude" if self.key == "claude" else "GPT Sol"
        last = transcript.turns[-1].text if transcript.turns else ""
        return (
            f"[MOCK {who} #{self._n}] Antwort auf: {last[:80]!r} — "
            "setze echte API-Keys, um das Team live arbeiten zu lassen."
        )


# ---------------------------------------------------------------------------
# Team workflows
# ---------------------------------------------------------------------------


def say(label: str, text: str) -> None:
    print(f"\n{label}\n{GREY}{'─' * 60}{RESET}\n{text}\n")


def mode_ask(claude, gpt, question: str, rounds: int) -> None:
    transcript = Transcript()
    transcript.add("user", question)
    print(f"{GREY}Dream Team diskutiert ({rounds} Runde(n))…{RESET}")
    for _ in range(rounds):
        answer = claude.reply(transcript)
        transcript.add("claude", answer)
        say(claude.label, answer)

        review = gpt.reply(transcript)
        transcript.add("gpt", review)
        say(gpt.label, review)

    transcript.add(
        "user",
        "Fasse die Team-Diskussion jetzt zu einer finalen, konsolidierten Antwort "
        "zusammen. Uebernimm die berechtigten Punkte deines Partners.",
    )
    final = claude.reply(transcript)
    say(f"{BOLD}🏆 Team-Ergebnis{RESET}", final)


def mode_code(claude, gpt, task: str, rounds: int) -> None:
    transcript = Transcript()
    transcript.add(
        "user",
        f"Implementiere folgende Aufgabe vollstaendig mit Code:\n\n{task}",
    )
    print(f"{GREY}Dream Team baut ({rounds} Review-Runde(n))…{RESET}")
    code = claude.reply(transcript)
    transcript.add("claude", code)
    say(claude.label, code)

    for _ in range(rounds):
        transcript.add(
            "user",
            "Reviewe den Code deines Partners: Bugs, Sicherheitsluecken, Edge Cases, "
            "Verbesserungen. Sei konkret (Datei/Zeile/Fix).",
        )
        review = gpt.reply(transcript)
        transcript.add("gpt", review)
        say(gpt.label, review)

        transcript.add(
            "user",
            "Ueberarbeite deinen Code anhand des Reviews und liefere die "
            "vollstaendige, finale Version.",
        )
        code = claude.reply(transcript)
        transcript.add("claude", code)
        say(claude.label, code)

    say(f"{BOLD}🏆 Finaler Code des Teams{RESET}", code)


def mode_chat(claude, gpt) -> None:
    transcript = Transcript()
    print(
        f"{GREY}Interaktiver Team-Chat. Beide Modelle antworten dir. "
        f"'exit' zum Beenden.{RESET}"
    )
    while True:
        try:
            user_input = input(f"\n{BOLD}Du>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() in {"exit", "quit"}:
            break
        transcript.add("user", user_input)

        answer = claude.reply(transcript)
        transcript.add("claude", answer)
        say(claude.label, answer)

        second = gpt.reply(transcript)
        transcript.add("gpt", second)
        say(gpt.label, second)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_agents(mock: bool):
    if mock or os.environ.get("DREAMTEAM_MOCK") == "1":
        return (
            MockAgent("claude", ClaudeAgent.label),
            MockAgent("gpt", GPTAgent.label),
        )
    missing = [
        var
        for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")
        if not os.environ.get(var)
    ]
    if missing:
        sys.exit(
            f"Fehlende API-Keys: {', '.join(missing)}\n"
            "Setze sie als Umgebungsvariablen (siehe .env.example) oder starte "
            "mit --mock fuer eine Demo ohne Keys."
        )
    return ClaudeAgent(), GPTAgent()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dream-team",
        description="Das AI Dream Team: Claude Code (Fable 5) x ChatGPT (GPT Sol 5.6)",
    )
    parser.add_argument(
        "--mock", action="store_true", help="Demo-Modus ohne API-Keys"
    )
    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=1,
        help="Anzahl Diskussions-/Review-Runden (Default: 1)",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_ask = sub.add_parser("ask", help="Frage vom Team beantworten lassen")
    p_ask.add_argument("question", nargs="+", help="Die Frage")

    p_code = sub.add_parser("code", help="Claude baut, GPT reviewt, Claude verbessert")
    p_code.add_argument("task", nargs="+", help="Die Coding-Aufgabe")

    sub.add_parser("chat", help="Interaktiver Team-Chat")

    args = parser.parse_args(argv)
    claude, gpt = build_agents(args.mock)

    if args.mode == "ask":
        mode_ask(claude, gpt, " ".join(args.question), args.rounds)
    elif args.mode == "code":
        mode_code(claude, gpt, " ".join(args.task), args.rounds)
    elif args.mode == "chat":
        mode_chat(claude, gpt)


if __name__ == "__main__":
    main()
