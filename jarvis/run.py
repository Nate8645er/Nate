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
    parser.add_argument("--autopilot", action="store_true",
                        help="24/7-Autopilot beim Start automatisch aktivieren")
    parser.add_argument("--no-workforce", action="store_true",
                        help="Belegschaft-Betrieb (Roll-Call der ganzen Organisation) NICHT starten")
    parser.add_argument("--lan", action="store_true",
                        help="Handy-Modus: im WLAN erreichbar machen (bindet an 0.0.0.0 "
                             "und erlaubt die eigene LAN-IP)")
    args = parser.parse_args()

    if args.demo:
        os.environ["JARVIS_DEMO"] = "1"
    if args.autopilot:
        os.environ["JARVIS_AUTOPILOT"] = "1"
    if args.no_workforce:
        os.environ["JARVIS_WORKFORCE"] = "0"

    # Handy-Modus: JARVIS im lokalen WLAN erreichbar machen. Der Host-Guard
    # (DNS-Rebinding-Schutz) bleibt aktiv — wir erlauben NUR die eigene LAN-IP.
    if args.lan:
        from jarvis.core.netinfo import lan_ip
        ip = lan_ip()
        if args.host == "127.0.0.1":
            args.host = "0.0.0.0"
        if ip:
            hosts = {h.strip() for h in os.environ.get("JARVIS_ALLOWED_HOSTS", "").split(",") if h.strip()}
            hosts.add(ip)
            os.environ["JARVIS_ALLOWED_HOSTS"] = ",".join(sorted(hosts))
            print("\n  📱  HANDY-MODUS AKTIV")
            print(f"      Auf dem Handy (gleiches WLAN) oeffnen:  http://{ip}:{args.port}/")
            print(f"      Oder am PC http://127.0.0.1:{args.port}/handy  fuer den QR-Code.\n")
        else:
            print("\n  ⚠  Handy-Modus: keine LAN-IP gefunden. Ist WLAN/LAN verbunden?\n")

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("\n  ⚠  WARNUNG: JARVIS wird an eine NICHT-lokale Adresse gebunden "
              f"({args.host}).\n     Damit ist die Steuer-API im Netzwerk erreichbar. "
              "Nur in vertrauenswürdigen\n     Netzen tun und JARVIS_ALLOWED_HOSTS setzen. "
              "Standard ist das sichere 127.0.0.1.\n")

    import uvicorn
    uvicorn.run("jarvis.dashboard.app:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
