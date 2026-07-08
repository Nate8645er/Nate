"""Jarvis - Grafische Oberfläche im Sci-Fi-Stil.

Dunkles HUD mit pulsierendem Orb (wie im Film): links der leuchtende
Reaktor-Kern, rechts das Gespräch. Alle Chat-Befehle (/oeffne, /firma,
/merken, ...) funktionieren hier genauso wie in der Konsole.

Start:  python jarvis_gui.py     (Konsolen-Version weiterhin: python main.py)
"""

import math
import queue
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont

from jarvis.core.errors import LLMError
from jarvis.utils.config_loader import load_config
from jarvis.utils.logger import setup_logger
from main import Jarvis

# Farbschema (dunkles HUD mit rot-orangem Orb wie im Video)
BG = "#060a12"
PANEL = "#0b1220"
ORB_CORE = "#ff4a1f"
ORB_GLOW = ["#3a0f08", "#7a2410", "#c23a15", "#ff4a1f"]
TEXT_USER = "#7fd8ff"
TEXT_JARVIS = "#ffb38a"
TEXT_DIM = "#5a6b85"
ACCENT = "#ff5a2a"


class JarvisGUI:
    def __init__(self, jarvis: Jarvis):
        self.jarvis = jarvis
        self.busy = False
        self.recording = False
        self.ui_queue: queue.Queue = queue.Queue()

        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=BG)
        self.root.geometry("1000x640")
        self.root.minsize(820, 520)

        self._build_layout()
        self._tick = 0
        self._animate()
        self._poll_queue()

        self._append("jarvis", "Systeme online. Wie kann ich helfen?")
        if not jarvis.client.is_available():
            self._append(
                "info",
                "Achtung: Ollama ist nicht erreichbar - bitte Ollama starten "
                "und Jarvis neu öffnen.",
            )

    # ------------------------------------------------------------------
    # Aufbau der Oberfläche
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        mono = tkfont.Font(family="Consolas", size=11)
        title_font = tkfont.Font(family="Consolas", size=22, weight="bold")
        status_font = tkfont.Font(family="Consolas", size=10)

        left = tk.Frame(self.root, bg=BG)
        left.pack(side="left", fill="y", padx=(16, 8), pady=16)

        tk.Label(left, text="J.A.R.V.I.S.", fg=ACCENT, bg=BG,
                 font=title_font).pack(pady=(8, 0))
        tk.Label(left, text="Just A Rather Very Intelligent System",
                 fg=TEXT_DIM, bg=BG, font=status_font).pack()

        self.canvas = tk.Canvas(left, width=320, height=320, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(pady=12)

        self.status = tk.Label(left, text="● BEREIT", fg=ACCENT, bg=BG,
                               font=status_font)
        self.status.pack()

        self.mic_button = tk.Button(
            left, text="🎤  Sprechen", command=self.toggle_recording,
            bg=PANEL, fg=TEXT_USER, activebackground=ACCENT,
            activeforeground="white", relief="flat", font=mono,
            padx=18, pady=8, cursor="hand2",
        )
        self.mic_button.pack(pady=(14, 4), fill="x")
        if not self.jarvis.stt.available:
            self.mic_button.configure(state="disabled",
                                      text="🎤  (kein Mikrofon)")

        self.voice_out = tk.Button(
            left, text=self._voice_out_label(), command=self.toggle_voice_out,
            bg=PANEL, fg=TEXT_USER, activebackground=ACCENT,
            activeforeground="white", relief="flat", font=mono,
            padx=18, pady=8, cursor="hand2",
        )
        self.voice_out.pack(pady=4, fill="x")

        right = tk.Frame(self.root, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(8, 16), pady=16)

        self.chat = tk.Text(
            right, bg=PANEL, fg=TEXT_JARVIS, insertbackground=TEXT_JARVIS,
            relief="flat", wrap="word", font=mono, padx=14, pady=12,
            state="disabled",
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure("user", foreground=TEXT_USER)
        self.chat.tag_configure("jarvis", foreground=TEXT_JARVIS)
        self.chat.tag_configure("info", foreground=TEXT_DIM)

        entry_row = tk.Frame(right, bg=BG)
        entry_row.pack(fill="x", pady=(10, 0))

        self.entry = tk.Entry(
            entry_row, bg=PANEL, fg="white", insertbackground=ACCENT,
            relief="flat", font=mono,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self.entry.bind("<Return>", lambda _e: self.send())
        self.entry.focus_set()

        tk.Button(
            entry_row, text="Senden ➤", command=self.send,
            bg=ACCENT, fg="white", activebackground=ORB_CORE,
            activeforeground="white", relief="flat", font=mono,
            padx=16, cursor="hand2",
        ).pack(side="right", ipady=6)

    # ------------------------------------------------------------------
    # Orb-Animation
    # ------------------------------------------------------------------

    def _animate(self) -> None:
        self.canvas.delete("all")
        cx = cy = 160
        speed = 0.35 if self.busy or self.recording else 0.12
        self._tick += speed
        pulse = (math.sin(self._tick) + 1) / 2  # 0..1

        # Äußere Glut-Ringe
        for i, color in enumerate(ORB_GLOW):
            radius = 58 + i * 18 + pulse * 10
            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=color, width=2,
            )
        # Rotierende Segmente (HUD-Gefühl)
        for k in range(3):
            start = (self._tick * 40 + k * 120) % 360
            self.canvas.create_arc(
                cx - 120, cy - 120, cx + 120, cy + 120,
                start=start, extent=40, style="arc",
                outline=ACCENT, width=2,
            )
        # Kern
        core = 34 + pulse * 8
        self.canvas.create_oval(
            cx - core, cy - core, cx + core, cy + core,
            fill=ORB_CORE, outline="",
        )
        inner = 16 + pulse * 4
        self.canvas.create_oval(
            cx - inner, cy - inner, cx + inner, cy + inner,
            fill="#ffd9a0", outline="",
        )
        self.root.after(50, self._animate)

    # ------------------------------------------------------------------
    # Chat-Logik
    # ------------------------------------------------------------------

    def _append(self, tag: str, text: str) -> None:
        prefixes = {"user": "DU      ▸ ", "jarvis": "JARVIS  ▸ ", "info": "SYSTEM  ▸ "}
        self.chat.configure(state="normal")
        self.chat.insert("end", prefixes.get(tag, "") + text + "\n\n", tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def send(self, text: str | None = None) -> None:
        if self.busy:
            return
        user_input = (text if text is not None else self.entry.get()).strip()
        if not user_input:
            return
        self.entry.delete(0, "end")
        self._append("user", user_input)

        if user_input.lower() in {"/sprechen", "sprechen"}:
            self._append("info", "Nutze hier einfach den 🎤-Knopf links.")
            return

        self.busy = True
        self._set_status("● DENKE NACH ...")
        threading.Thread(target=self._worker, args=(user_input,),
                         daemon=True).start()

    def _worker(self, user_input: str) -> None:
        """Läuft im Hintergrund-Thread, damit die Oberfläche flüssig bleibt."""
        try:
            answer = self.jarvis.handle(user_input)
        except LLMError as e:
            self.ui_queue.put(("info", f"Problem mit dem Sprachmodell: {e}"))
            self.ui_queue.put(("done", ""))
            return
        except Exception as e:  # GUI darf nie abstürzen
            self.jarvis.logger.exception("Unerwarteter Fehler")
            self.ui_queue.put(("info", f"Unerwarteter Fehler: {e}"))
            self.ui_queue.put(("done", ""))
            return

        if answer is None:  # /exit
            self.ui_queue.put(("quit", ""))
            return

        self.ui_queue.put(("jarvis", answer))
        # Antwort aussprechen (nur normale Gespräche, wie in der Konsole)
        if self.jarvis.pending_speech:
            self.ui_queue.put(("status", "● SPRICHT ..."))
            self.jarvis.flush_speech()
        self.ui_queue.put(("done", ""))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "quit":
                    self.root.destroy()
                    return
                if kind == "done":
                    self.busy = False
                    self._set_status("● BEREIT")
                elif kind == "status":
                    self._set_status(payload)
                else:
                    self._append(kind, payload)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_queue)

    # ------------------------------------------------------------------
    # Sprache
    # ------------------------------------------------------------------

    def toggle_recording(self) -> None:
        if not self.jarvis.stt.available or self.busy:
            return
        if not self.recording:
            try:
                self.jarvis.stt.record_start()
            except Exception as e:
                self._append("info", f"Mikrofon-Problem: {e}")
                return
            self.recording = True
            self.mic_button.configure(text="⏹  Stopp (ich höre zu)", fg=ACCENT)
            self._set_status("● ICH HÖRE ZU ...")
        else:
            self.recording = False
            self.mic_button.configure(text="🎤  Sprechen", fg=TEXT_USER)
            self._set_status("● VERARBEITE ...")
            threading.Thread(target=self._transcribe_worker, daemon=True).start()

    def _transcribe_worker(self) -> None:
        try:
            raw = self.jarvis.stt.record_stop()
            text, message = self.jarvis.stt.transcribe(raw)
        except Exception as e:
            self.ui_queue.put(("info", f"Mikrofon-Problem: {e}"))
            self.ui_queue.put(("done", ""))
            return
        if text:
            self.ui_queue.put(("done", ""))
            self.root.after(0, lambda: self.send(text))
        else:
            self.ui_queue.put(("info", message))
            self.ui_queue.put(("done", ""))

    def _voice_out_label(self) -> str:
        if not self.jarvis.tts.available:
            return "🔇  (keine Sprachausgabe)"
        return "🔊  Stimme: AN" if self.jarvis.tts.enabled else "🔇  Stimme: AUS"

    def toggle_voice_out(self) -> None:
        if not self.jarvis.tts.available:
            return
        self.jarvis.tts.enabled = not self.jarvis.tts.enabled
        self.voice_out.configure(text=self._voice_out_label())

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"FEHLER: {e}")
        return 1

    logger = setup_logger("jarvis", config)
    logger.info("Jarvis startet (GUI-Modus) ...")
    jarvis = Jarvis(config, logger)
    JarvisGUI(jarvis).run()
    logger.info("Jarvis beendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
