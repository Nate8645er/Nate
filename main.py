"""Jarvis - Einstiegspunkt.

Schritt 3: Plugins, Skills, Agenten und das virtuelle Unternehmen.

Befehle im Chat:
  /hilfe               - Alle Befehle anzeigen
  /plugins             - Geladene Plugins und ihre Befehle
  /skills              - Verfügbare Skills
  /skill <name> <text> - Skill ausführen (z.B. /skill uebersetzen Hallo Welt)
  /agenten             - Verfügbare Agenten des Unternehmens
  /agent <name> <frage>- Einen Agenten direkt fragen
  /firma <aufgabe>     - Aufgabe durch das komplette Unternehmen schicken
  /neu                 - Gesprächsverlauf zurücksetzen
  /exit                - Jarvis beenden
"""

import sys

from jarvis.core.agents import AgentRegistry
from jarvis.core.claude_client import ClaudeClient
from jarvis.core.company import Company
from jarvis.core.conversation import ConversationManager
from jarvis.core.errors import LLMError
from jarvis.core.ollama_client import OllamaClient
from jarvis.core.skills import SkillRegistry
from jarvis.memory.long_term import LongTermMemory
from jarvis.plugins.loader import PluginManager
from jarvis.speech.speech_to_text import SpeechToText
from jarvis.speech.text_to_speech import TextToSpeech
from jarvis.system.app_control import AppController
from jarvis.utils.config_loader import PROJECT_ROOT, load_config
from jarvis.utils.latency import TurnTimer
from jarvis.utils.logger import setup_logger

EXIT_COMMANDS = {"exit", "quit"}

HELP_TEXT = """Verfügbare Befehle:
  /hilfe                Diese Übersicht
  /plugins              Geladene Plugins und ihre Befehle
  /skills               Verfügbare Skills
  /skill <name> <text>  Skill ausführen, z.B. /skill uebersetzen Hallo Welt
  /agenten              Verfügbare Agenten des Unternehmens
  /agent <name> <frage> Einen Agenten direkt fragen
  /firma <aufgabe>      Aufgabe durchs komplette Unternehmen schicken
  /sprechen             Sprachmodus: mit Jarvis reden statt tippen
  /stimme an|aus        Gesprochene Antworten ein-/ausschalten
  /oeffne <programm>    Programm, Datei oder Webseite öffnen
  /schliesse <programm> Programm beenden
  /apps                 Alle bekannten Programme anzeigen
  /merken <fakt>        Fakt dauerhaft speichern (Langzeitgedächtnis)
  /gedaechtnis          Alle gespeicherten Fakten anzeigen
  /vergessen <nr>       Fakt Nummer <nr> löschen (/vergessen alles = alle)
  /neu                  Gesprächsverlauf (Kurzzeitgedächtnis) löschen
  /exit                 Jarvis beenden
Alles andere ist normales Gespräch mit Jarvis."""


class Jarvis:
    """Bündelt alle Komponenten und verteilt eingehende Befehle."""

    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger

        self.provider = config.get("provider", "ollama")
        if self.provider == "claude":
            claude_cfg = config.get("claude", {})
            claude = ClaudeClient(
                model=claude_cfg.get("model", "claude-fable-5"),
                max_tokens=claude_cfg.get("max_tokens", 16000),
                fallback_model=claude_cfg.get("fallback_model", "claude-opus-4-8"),
            )
            if claude.is_available():
                self.client = claude
            else:
                logger.warning(
                    "provider ist 'claude', aber es wurde kein API-Schlüssel "
                    "gefunden (config/secrets.json) - nutze stattdessen Ollama."
                )
                self.provider = "ollama"
        if self.provider == "ollama":
            ollama_cfg = config["ollama"]
            self.client = OllamaClient(
                base_url=ollama_cfg["base_url"],
                model=ollama_cfg["model"],
                timeout=ollama_cfg.get("timeout_seconds", 120),
            )

        memory_file = PROJECT_ROOT / config.get("memory", {}).get(
            "file", "data/memory/long_term.json"
        )
        self.memory = LongTermMemory(memory_file)

        assistant_cfg = config.get("assistant", {})
        self.base_system_prompt = assistant_cfg.get(
            "system_prompt", "Du bist ein hilfsbereiter Assistent."
        )
        self.conversation = ConversationManager(
            client=self.client,
            system_prompt=self._full_system_prompt(),
            max_history_messages=assistant_cfg.get("max_history_messages", 20),
        )

        self.plugins = PluginManager()
        self.plugins.load_plugins()

        skills_path = PROJECT_ROOT / config.get("skills", {}).get("path", "skills")
        self.skills = SkillRegistry(skills_path)
        self.skills.load()

        agent_paths = [
            PROJECT_ROOT / p
            for p in config.get("agents", {}).get(
                "paths", ["ultra-enterprise-os/agents"]
            )
        ]
        self.agents = AgentRegistry(agent_paths)
        self.agents.load()

        apps_file = PROJECT_ROOT / config.get("apps", {}).get(
            "file", "config/apps.json"
        )
        self.app_control = AppController(apps_file)

        speech_cfg = config.get("speech", {})
        self.tts = TextToSpeech(
            rate=speech_cfg.get("rate", 180),
            language=speech_cfg.get("voice_language", "de"),
            enabled=speech_cfg.get("tts_enabled", True),
        )
        self.stt = SpeechToText(language=speech_cfg.get("stt_language", "de-DE"))
        # Latenz-Anzeige im Sprachmodus: zeigt pro Runde, wohin die Zeit geht
        self.show_timing = speech_cfg.get("show_timing", True)

        self.company = Company(
            client=self.client,
            agents=self.agents,
            pipeline=config.get("company", {}).get("pipeline"),
        )

    #: Antwort, die nach dem Anzeigen noch gesprochen werden soll
    pending_speech: str | None = None

    def flush_speech(self) -> None:
        """Spricht die zuletzt gemerkte Antwort aus (falls Stimme an)."""
        if self.pending_speech:
            self.tts.speak(self.pending_speech)
            self.pending_speech = None

    def _toggle_voice(self, args: str) -> str:
        args = args.strip().lower()
        if args == "an":
            self.tts.enabled = True
        elif args == "aus":
            self.tts.enabled = False
        elif args:
            return "Nutzung: /stimme an  oder  /stimme aus"
        return f"{self.tts.status()}\n{self.stt.status()}"

    def _voice_mode(self) -> str:
        if not self.stt.available:
            return self.stt.status()
        print("\n🎤 Sprachmodus! Enter drücken und lossprechen.")
        print("   (x + Enter beendet den Sprachmodus)\n")
        while True:
            choice = input("[Enter = sprechen | x = beenden] ").strip().lower()
            if choice in {"x", "exit", "beenden"}:
                return "Sprachmodus beendet - wir tippen wieder."
            timer = TurnTimer()
            text = self.stt.listen(timer)
            if not text:
                continue
            print(f"Du (verstanden): {text}")
            if text.lower().strip(".!?") in {"beenden", "stopp", "auf wiedersehen"}:
                return "Sprachmodus beendet - wir tippen wieder."

            # Antwort satzweise streamen: der erste Satz wird gesprochen,
            # während das Modell noch am Rest schreibt - keine lange Stille.
            print("\nJarvis: ", end="", flush=True)
            try:
                for sentence in self.conversation.ask_stream(text):
                    timer.mark("erster Satz")
                    print(sentence, end=" ", flush=True)
                    self.tts.speak_async(
                        sentence, on_start=lambda: timer.mark("Sprachbeginn")
                    )
            except LLMError as e:
                self.logger.error("%s", e)
                print("\n(Verbindungsproblem - versuch es gleich nochmal.)\n")
                self.tts.wait()
                continue
            timer.mark("Antwort komplett")
            self.tts.wait()
            timer.mark("Ausgesprochen")
            print("\n")
            timer.log()
            if self.show_timing:
                report = timer.report()
                if report:
                    print(f"   ⏱  {report}\n")

    def _full_system_prompt(self) -> str:
        """Basis-Prompt plus alle Fakten aus dem Langzeitgedächtnis."""
        return self.base_system_prompt + self.memory.as_prompt_context()

    def _refresh_memory_context(self) -> None:
        """Nach Gedächtnis-Änderungen den System-Prompt aktualisieren."""
        self.conversation.update_system_prompt(self._full_system_prompt())

    # ------------------------------------------------------------------
    # Befehlsverarbeitung
    # ------------------------------------------------------------------

    def handle(self, user_input: str) -> str | None:
        """Verarbeitet eine Eingabe. None = Jarvis beenden."""
        lowered = user_input.lower()

        if lowered in EXIT_COMMANDS or lowered in {"/exit", "/quit"}:
            return None
        if lowered in {"/hilfe", "/help"}:
            return HELP_TEXT
        if lowered == "/neu":
            self.conversation.reset()
            return "(Verlauf gelöscht - wir fangen von vorne an.)"
        if lowered == "/plugins":
            return self.plugins.overview()
        if lowered == "/skills":
            return self.skills.overview()
        if lowered in {"/agenten", "/agents"}:
            return self.agents.overview()
        if lowered == "/gedaechtnis":
            return self.memory.overview()
        if lowered == "/apps":
            return self.app_control.overview()

        if user_input.startswith("/"):
            command, _, args = user_input[1:].partition(" ")
            command = command.lower()
            args = args.strip()

            if command == "skill":
                return self._run_skill(args)
            if command == "agent":
                return self._run_agent(args)
            if command == "firma":
                return self._run_company(args)
            if command == "merken":
                return self._remember(args)
            if command == "vergessen":
                return self._forget(args)
            if command in {"oeffne", "öffne", "open"}:
                return self.app_control.open(args)
            if command in {"schliesse", "schließe", "close"}:
                return self.app_control.close(args)
            if command == "stimme":
                return self._toggle_voice(args)
            if command == "sprechen":
                return self._voice_mode()

            plugin_answer = self.plugins.handle(command, args)
            if plugin_answer is not None:
                return plugin_answer
            return f"Unbekannter Befehl: /{command} - /hilfe zeigt alle Befehle."

        # Kein Befehl: normales Gespräch mit Kurzzeitgedächtnis
        answer = self.conversation.ask(user_input)
        self.pending_speech = answer
        return answer

    def _run_skill(self, args: str) -> str:
        name, _, text = args.partition(" ")
        if not name:
            return "Nutzung: /skill <name> <text>\n" + self.skills.overview()
        if not text.strip():
            return f"Bitte Text angeben: /skill {name} <text>"
        return self.skills.run(self.client, name, text.strip())

    def _run_agent(self, args: str) -> str:
        name, _, question = args.partition(" ")
        if not name:
            return "Nutzung: /agent <name> <frage>\n" + self.agents.overview()
        if not question.strip():
            return f"Bitte eine Frage angeben: /agent {name} <frage>"
        return self.agents.ask(self.client, name, question.strip())

    def _remember(self, fact: str) -> str:
        if not fact.strip():
            return "Nutzung: /merken <fakt> - z.B. /merken Mein Name ist Nate"
        number = self.memory.remember(fact)
        self._refresh_memory_context()
        return f"Gemerkt (Fakt Nr. {number}): {fact.strip()}"

    def _forget(self, args: str) -> str:
        args = args.strip().lower()
        if args in {"alles", "alle"}:
            count = self.memory.forget_all()
            self._refresh_memory_context()
            return f"Langzeitgedächtnis gelöscht ({count} Fakten entfernt)."
        if not args.isdigit():
            return ("Nutzung: /vergessen <nummer> oder /vergessen alles\n"
                    + self.memory.overview())
        removed = self.memory.forget(int(args))
        if removed is None:
            return f"Fakt Nr. {args} gibt es nicht.\n" + self.memory.overview()
        self._refresh_memory_context()
        return f"Vergessen: {removed}"

    def _run_company(self, task: str) -> str:
        if not task.strip():
            return "Nutzung: /firma <aufgabe> - z.B. /firma Plane eine Todo-App"

        def on_step(role: str, step: int, total: int) -> None:
            print(f"  [{step}/{total}] {role} arbeitet ...")

        print("\nDas Unternehmen übernimmt die Aufgabe:")
        results = self.company.run(task.strip(), on_step=on_step)
        blocks = [
            f"{'=' * 60}\n{role.upper()}\n{'=' * 60}\n{answer}"
            for role, answer in results
        ]
        return "\n\n".join(blocks)


def chat_loop(jarvis: Jarvis) -> None:
    print("\nJarvis ist bereit. Schreib mir etwas! (/hilfe zeigt alle Befehle)\n")
    while True:
        try:
            user_input = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBis bald!")
            return

        if not user_input:
            continue

        try:
            answer = jarvis.handle(user_input)
        except LLMError as e:
            jarvis.logger.error("%s", e)
            print(f"(Problem mit dem Sprachmodell: {e})\n")
            continue

        if answer is None:
            print("Bis bald!")
            return
        print(f"\nJarvis: {answer}\n")
        jarvis.flush_speech()


def main() -> int:
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"FEHLER: {e}")
        return 1

    logger = setup_logger("jarvis", config)
    logger.info("Jarvis startet (Schritt 6: Sprachsteuerung) ...")

    jarvis = Jarvis(config, logger)

    if jarvis.provider == "claude":
        if not jarvis.client.is_available():
            logger.error(
                "Kein Anthropic-API-Schlüssel gefunden. Trage ihn in "
                "config/secrets.json ein (Vorlage: config/secrets.example.json) "
                "oder setze provider in config/config.json zurück auf \"ollama\"."
            )
            return 1
        logger.info("Cloud-Gehirn aktiv: Claude API (%s).", jarvis.client.model)
    else:
        if not jarvis.client.is_available():
            logger.error(
                "Ollama ist unter %s nicht erreichbar. "
                "Bitte Ollama starten (z.B. 'ollama serve' oder die Ollama-App öffnen).",
                config["ollama"]["base_url"],
            )
            return 1
        logger.info("Ollama-Server erreichbar.")
        try:
            models = jarvis.client.list_models()
            logger.info("Installierte Modelle: %s", ", ".join(models) or "keine")
            if not any(m.startswith(jarvis.client.model) for m in models):
                logger.warning(
                    "Modell '%s' scheint nicht installiert zu sein. "
                    "Installation mit: ollama pull %s",
                    jarvis.client.model, jarvis.client.model,
                )
        except LLMError as e:
            logger.error("%s", e)
            return 1

    chat_loop(jarvis)
    logger.info("Jarvis beendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
