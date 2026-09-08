# KRYPTO - Konfiguration.
#
# Eine einzige Stelle, an der die Zahlen stehen, die ueber Geld
# entscheiden. Alles ist per Umgebungsvariable ueberschreibbar, aber die
# Vorgaben sind bewusst die vorsichtigen.
#
# Grundsatz: In diesem System steht KEIN Zugangsdatum. Weder Schluessel
# noch Passwort noch Kontonummer. Was das System braucht, liest es aus
# der Umgebung - und gibt es nie aus.

import os

WURZEL = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(WURZEL, "logs")
ZUSTAND = os.path.join(WURZEL, "zustand")


def _zahl(name, vorgabe):
    roh = os.environ.get(name)
    if roh is None or roh.strip() == "":
        return vorgabe
    try:
        return float(roh)
    except ValueError:
        raise SystemExit(
            "Konfigurationsfehler: %s ist keine Zahl (%r)." % (name, roh))


def _ganz(name, vorgabe):
    return int(_zahl(name, vorgabe))


def _schalter(name, vorgabe=False):
    """Nur die woertliche Zeichenfolge 'true' schaltet ein.

    Absichtlich streng. '1', 'yes', 'True ' schalten NICHT ein. Wer
    echtes Geld freigeben will, soll genau tippen muessen.
    """
    roh = os.environ.get(name)
    if roh is None:
        return vorgabe
    return roh == "true"


# --- Der wichtigste Schalter des Systems ------------------------------
#
# Vorgabe false. Er wird nirgends im Code auf true gesetzt, von keinem
# Modul, unter keiner Bedingung. Nur ein Mensch in seiner Umgebung.
LIVE_TRADING_ENABLED = _schalter("LIVE_TRADING_ENABLED", False)

# Zweiter Riegel: auch mit LIVE_TRADING_ENABLED=true passiert nichts,
# solange nicht zusaetzlich hier die Freigabe steht. Zwei Schalter,
# damit ein versehentlich gesetzter nicht reicht.
LIVE_TRADING_CONFIRM = os.environ.get("LIVE_TRADING_CONFIRM", "")
LIVE_FREIGABE_WORT = "ICH-HANDLE-MIT-ECHTEM-GELD"

BETRIEBSART = os.environ.get("KRYPTO_MODUS", "paper")   # paper | backtest


# --- Risikogrenzen ----------------------------------------------------
#
# Das sind Obergrenzen, keine Ziele. Das System darf sie unterschreiten,
# nie ueberschreiten.
KAPITAL_START = _zahl("KRYPTO_KAPITAL", 10000.0)      # Papierkapital
WAEHRUNG = os.environ.get("KRYPTO_WAEHRUNG", "usd").lower()

RISIKO_JE_TRADE = _zahl("KRYPTO_RISIKO_TRADE", 0.01)   # 1 % des Kapitals
VERLUST_TAG_MAX = _zahl("KRYPTO_VERLUST_TAG", 0.03)    # 3 % Tagesverlust
DRAWDOWN_MAX = _zahl("KRYPTO_DRAWDOWN", 0.15)          # 15 % vom Hoch
POSITION_MAX_ANTEIL = _zahl("KRYPTO_POSITION_MAX", 0.20)   # 20 % je Wert
EXPOSURE_MAX = _zahl("KRYPTO_EXPOSURE_MAX", 0.60)      # 60 % investiert
POSITIONEN_MAX = _ganz("KRYPTO_POSITIONEN_MAX", 5)
TRADES_TAG_MAX = _ganz("KRYPTO_TRADES_TAG", 6)

# Stop-Loss ist Pflicht. Ohne Stop keine Order - das prueft die
# Risikoeinheit, nicht die Hoeflichkeit des Aufrufers.
STOP_PFLICHT = True
STOP_ATR_FAKTOR = _zahl("KRYPTO_STOP_ATR", 2.0)
ZIEL_ATR_FAKTOR = _zahl("KRYPTO_ZIEL_ATR", 3.0)

# Kosten. Wer ohne Gebuehren und Slippage backtestet, betruegt sich.
GEBUEHR = _zahl("KRYPTO_GEBUEHR", 0.001)               # 0.1 % je Seite
SLIPPAGE = _zahl("KRYPTO_SLIPPAGE", 0.0005)            # 0.05 %


# --- Datenqualitaet ---------------------------------------------------
DATEN_MAX_ALTER_S = _ganz("KRYPTO_DATEN_ALTER", 3600)   # 1 h
MIN_KERZEN = _ganz("KRYPTO_MIN_KERZEN", 60)
MIN_VOLUMEN_24H = _zahl("KRYPTO_MIN_VOLUMEN", 50_000_000.0)
MIN_MARKTKAPITAL = _zahl("KRYPTO_MIN_MCAP", 500_000_000.0)


# --- Schwellen fuer Signale -------------------------------------------
CHANCE_SCHWELLE = _zahl("KRYPTO_CHANCE_SCHWELLE", 60.0)   # 0..100
RISIKO_SCHWELLE = _zahl("KRYPTO_RISIKO_SCHWELLE", 70.0)   # darueber: NO TRADE

# Netzwerk
HTTP_TIMEOUT = _ganz("KRYPTO_HTTP_TIMEOUT", 30)
HTTP_VERSUCHE = _ganz("KRYPTO_HTTP_VERSUCHE", 4)
KENNUNG = "KRYPTO/0.1 (nur lesend, privat)"


def zusammenfassung():
    """Konfiguration zum Anzeigen. Enthaelt bewusst keine Geheimnisse."""
    return {
        "LIVE_TRADING_ENABLED": LIVE_TRADING_ENABLED,
        "Betriebsart": BETRIEBSART,
        "Kapital": KAPITAL_START,
        "Waehrung": WAEHRUNG.upper(),
        "Risiko je Trade": RISIKO_JE_TRADE,
        "Tagesverlustgrenze": VERLUST_TAG_MAX,
        "Max. Drawdown": DRAWDOWN_MAX,
        "Max. Positionsanteil": POSITION_MAX_ANTEIL,
        "Max. Exposure": EXPOSURE_MAX,
        "Max. Positionen": POSITIONEN_MAX,
        "Max. Trades/Tag": TRADES_TAG_MAX,
        "Stop-Loss Pflicht": STOP_PFLICHT,
        "Gebuehr": GEBUEHR,
        "Slippage": SLIPPAGE,
    }
