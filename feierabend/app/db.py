# Feierabend - Ablage.
#
# SQLite, weil ein Dienst mit fuenf Betrieben keine Datenbankcluster
# braucht und weil eine Datei sich sichern laesst, indem man sie kopiert.
# Der Wechsel auf PostgreSQL ist spaeter eine Frage der Verbindungszeile,
# nicht der Struktur - jede Abfrage traegt bereits die Mandanten-ID.
#
# Mandantentrennung: Es gibt bewusst KEINE Funktion, die einen Rapport
# ohne mandant_id liest. Der klassische Bruch in solchen Diensten ist ein
# vergessener Filter; hier gibt es keinen Weg, ihn zu vergessen.

import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

DB_PFAD = os.environ.get(
    "FEIERABEND_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "feierabend.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS betrieb (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  angelegt      TEXT NOT NULL,
  bexio_token   TEXT,
  bexio_refresh TEXT,
  bexio_ablauf  TEXT
);

CREATE TABLE IF NOT EXISTS mitarbeiter (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  betrieb_id TEXT NOT NULL REFERENCES betrieb(id),
  name       TEXT NOT NULL,
  code       TEXT NOT NULL UNIQUE,
  aktiv      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS kunde (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  betrieb_id TEXT NOT NULL REFERENCES betrieb(id),
  name       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rapport (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  betrieb_id     TEXT NOT NULL REFERENCES betrieb(id),
  mitarbeiter_id INTEGER NOT NULL REFERENCES mitarbeiter(id),
  datum          TEXT NOT NULL,
  kunde          TEXT NOT NULL,
  stunden        REAL NOT NULL,
  taetigkeiten   TEXT NOT NULL DEFAULT '',
  material       TEXT NOT NULL DEFAULT '',
  folgetermin    TEXT NOT NULL DEFAULT '',
  erfasst        TEXT NOT NULL,
  bexio_id       INTEGER
);

CREATE INDEX IF NOT EXISTS idx_rapport_betrieb
  ON rapport(betrieb_id, datum);
CREATE INDEX IF NOT EXISTS idx_mitarbeiter_betrieb
  ON mitarbeiter(betrieb_id);
CREATE INDEX IF NOT EXISTS idx_kunde_betrieb
  ON kunde(betrieb_id);
"""


@contextmanager
def verbindung():
    conn = sqlite3.connect(DB_PFAD)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def anlegen():
    with verbindung() as conn:
        conn.executescript(SCHEMA)


def code_erzeugen():
    """Zugangscode: sechs Stellen, gut vorlesbar.

    Ohne 0/O und 1/I/L - die verwechselt jeder am Telefon, und der Code
    wird am Telefon durchgegeben.
    """
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


# ------------------------------------------------------------- Betriebe

def betrieb_anlegen(betrieb_id, name):
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO betrieb (id, name, angelegt) VALUES (?, ?, ?)",
            (betrieb_id, name, datetime.now().isoformat(timespec="seconds")))
    return betrieb_id


def betrieb_lesen(betrieb_id):
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM betrieb WHERE id = ?",
                         (betrieb_id,)).fetchone()
    return dict(r) if r else None


def bexio_token_speichern(betrieb_id, token, refresh, gueltig_sekunden):
    ablauf = (datetime.now()
              + timedelta(seconds=int(gueltig_sekunden) - 60)).isoformat()
    with verbindung() as conn:
        conn.execute(
            "UPDATE betrieb SET bexio_token=?, bexio_refresh=?, "
            "bexio_ablauf=? WHERE id=?",
            (token, refresh, ablauf, betrieb_id))


# ---------------------------------------------------------- Mitarbeiter

def mitarbeiter_anlegen(betrieb_id, name):
    code = code_erzeugen()
    with verbindung() as conn:
        cur = conn.execute(
            "INSERT INTO mitarbeiter (betrieb_id, name, code) "
            "VALUES (?, ?, ?)", (betrieb_id, name, code))
        return {"id": cur.lastrowid, "name": name, "code": code}


def mitarbeiter_per_code(code):
    """Zugangscode aufloesen. Einziger Weg in einen Mandanten hinein."""
    if not code:
        return None
    with verbindung() as conn:
        r = conn.execute(
            "SELECT m.id, m.name, m.betrieb_id, b.name AS betrieb_name "
            "FROM mitarbeiter m JOIN betrieb b ON b.id = m.betrieb_id "
            "WHERE m.code = ? AND m.aktiv = 1",
            (code.strip().upper(),)).fetchone()
    return dict(r) if r else None


# --------------------------------------------------------------- Kunden

def kunden_lesen(betrieb_id):
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT id, name FROM kunde WHERE betrieb_id = ? ORDER BY name",
            (betrieb_id,)).fetchall()
    return [dict(r) for r in rows]


def kunde_anlegen(betrieb_id, name):
    with verbindung() as conn:
        cur = conn.execute(
            "INSERT INTO kunde (betrieb_id, name) VALUES (?, ?)",
            (betrieb_id, name.strip()))
        return {"id": cur.lastrowid, "name": name.strip()}


# ------------------------------------------------------------- Rapporte

def rapport_speichern(betrieb_id, mitarbeiter_id, daten):
    with verbindung() as conn:
        cur = conn.execute(
            "INSERT INTO rapport (betrieb_id, mitarbeiter_id, datum, kunde, "
            "stunden, taetigkeiten, material, folgetermin, erfasst) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (betrieb_id, mitarbeiter_id, daten["datum"], daten["kunde"],
             float(daten["stunden"]), daten.get("taetigkeiten", ""),
             ", ".join(daten.get("material", [])),
             daten.get("folgetermin", ""),
             datetime.now().isoformat(timespec="seconds")))
        return cur.lastrowid


def rapporte_lesen(betrieb_id, seit=None, mitarbeiter_id=None):
    """Rapporte eines Betriebs. betrieb_id ist nicht optional - Absicht."""
    sql = ("SELECT r.*, m.name AS mitarbeiter FROM rapport r "
           "JOIN mitarbeiter m ON m.id = r.mitarbeiter_id "
           "WHERE r.betrieb_id = ?")
    werte = [betrieb_id]
    if seit:
        sql += " AND r.datum >= ?"
        werte.append(seit)
    if mitarbeiter_id:
        sql += " AND r.mitarbeiter_id = ?"
        werte.append(mitarbeiter_id)
    sql += " ORDER BY r.datum DESC, r.id DESC"
    with verbindung() as conn:
        rows = conn.execute(sql, werte).fetchall()
    return [dict(r) for r in rows]


def wochenauswertung(betrieb_id, tage=7):
    """Auswertung je Kunde, nicht je Mitarbeiter.

    Bewusst so: Art. 328b OR erlaubt Datenbearbeitung nur mit Bezug zur
    Vertragserfuellung, und Art. 26 ArGV 3 verbietet Ueberwachungssysteme
    zur Verhaltenskontrolle. Eine Rangliste 'Stunden je Mitarbeiter'
    kippt genau dorthin. Die Zuordnung zum Mitarbeiter bleibt im
    Einzelrapport, wo sie zur Abrechnung noetig ist - aggregiert wird
    nach Auftrag.
    """
    seit = (datetime.now() - timedelta(days=tage)).strftime("%Y-%m-%d")
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT kunde, SUM(stunden) AS stunden, COUNT(*) AS rapporte "
            "FROM rapport WHERE betrieb_id = ? AND datum >= ? "
            "GROUP BY kunde ORDER BY stunden DESC",
            (betrieb_id, seit)).fetchall()
        summe = conn.execute(
            "SELECT COALESCE(SUM(stunden), 0) AS s FROM rapport "
            "WHERE betrieb_id = ? AND datum >= ?",
            (betrieb_id, seit)).fetchone()["s"]
    return {"seit": seit, "tage": tage, "stunden_total": round(summe, 2),
            "je_kunde": [dict(r) for r in rows]}
