"""JARVIS HyperScale starten.

Beispiele:
    python -m jarvis.run                 # Dashboard auf http://127.0.0.1:8787
    python -m jarvis.run --demo          # mit klar markierten Demo-Aufgaben
    python -m jarvis.run --port 9000
"""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS HyperScale")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--demo", action="store_true",
                        help="markierte Demo-Aufgaben erzeugen, damit der Ticker lebt")
    args = parser.parse_args()

    if args.demo:
        os.environ["JARVIS_DEMO"] = "1"

    import uvicorn
    uvicorn.run("jarvis.dashboard.app:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
