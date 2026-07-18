# JAVIER - Die Milliarden-Holding
#
# 10 Divisionen x 100 Companies x 100 Departments x 100 Teams x 1000 Agents
# = 10.000.000.000 adressierbare Agents. Der Trick ist GENERATIV: Die
# Adresse IST die Rolle. Es existieren keine 10 Milliarden Dateien -
# instanziiert (= ein echter API-Aufruf mit deterministisch aus der
# Adresse gebautem Rollen-Prompt) wird nur der Ast, den ein Auftrag
# braucht. Gleiche Adresse -> gleiche Rolle, jederzeit reproduzierbar.
#
# Ehrliche Grenzen: Jeder eingesetzte Agent ist ein zusaetzlicher
# Anthropic-API-Aufruf (Kosten + einige Sekunden). Deshalb sind pro
# Auftrag maximal MAX_AGENTS Agents aktiv - Milliarden sind adressierbar,
# nicht gleichzeitig beschaeftigt.

import os
import re

# Boss/Worker-Aufteilung (wie im Codex-Setup des Repos): Der Boss
# (JAVIER selbst und die Synthese) laeuft auf dem Claude-Modell aus
# JAVIER_MODEL (Standard: Fable 5, mit automatischem Fallback). Die
# Worker-Agents der Holding laufen optional auf OpenAI GPT-5.6-Sol,
# sobald ein OPENAI_API_KEY gesetzt ist - sonst ebenfalls auf Claude.
MODEL = os.environ.get("JAVIER_MODEL", "").strip() or "claude-fable-5"
FALLBACK_MODEL = "claude-sonnet-4-6"
_active_model = {"name": MODEL}
SOL_MODEL = os.environ.get("JAVIER_SOL_MODEL", "").strip() or "gpt-5.6-sol"
# Reasoning-Stufe des Sol-Workers - 'ultra' wie im Codex-Setup des
# Repos (.codex/config.toml). Reasoning verbraucht Completion-Tokens,
# deshalb bekommt der Sol-Worker ein deutlich hoeheres Token-Budget.
SOL_EFFORT = os.environ.get("JAVIER_SOL_EFFORT", "").strip() or "ultra"
SOL_MAX_TOKENS = 6000
MAX_AGENTS = 3
AGENT_MAX_TOKENS = 1200

# Die 10 Divisionen der Holding (feste oberste Ebene). Alle Ebenen
# darunter sind freie, sprechende Slugs - der Adressraum ist damit
# 10 x 100 x 100 x 100 x 1000 gross, ohne dass eine einzige Rolle
# vorab als Datei existieren muss.
DIVISIONS = {
    "engineering": "Software, Systeme, Apps, Infrastruktur",
    "business": "Strategie, Finanzen, Marketing, Vertrieb, Pricing",
    "content": "Texte, Creatives, Video, Social Media, Copywriting",
    "data": "Datenanalyse, Statistik, Machine Learning, Reports",
    "security": "Defensive Sicherheit, Risiko-Checks, Hardening",
    "operations": "Ablaeufe, Automatisierung, Einkauf, Logistik",
    "design": "UI/UX, Branding, Produkt- und Grafikdesign",
    "legal": "Recht, Vertraege, Schweizer Besonderheiten (z.B. PBV)",
    "research": "Recherche, Marktanalysen, Stand der Technik",
    "ventures": "Neue Geschaeftsideen, Experimente, Prototypen",
}

LEVEL_NAMES = ["division", "company", "department", "team", "agent"]

_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def parse_address(adresse):
    # 'holding/<division>[/company[/department[/team[/agent]]]]'
    # Returns (levels-dict, None) or (None, error-string).
    parts = [p for p in str(adresse or "").strip().lower().split("/") if p]
    if not parts or parts[0] != "holding":
        return None, "Adresse muss mit 'holding/' beginnen: %s" % adresse
    parts = parts[1:]
    if not parts:
        return None, "Adresse braucht mindestens eine Division: " \
                     "holding/<division>/..."
    if len(parts) > len(LEVEL_NAMES):
        return None, "Adresse hat zu viele Ebenen (max: holding/division/" \
                     "company/department/team/agent): %s" % adresse
    for p in parts:
        if not _SLUG.match(p):
            return None, "Ungueltiger Adressteil '%s' (erlaubt: " \
                         "kleinbuchstaben, ziffern, bindestrich)" % p
    if parts[0] not in DIVISIONS:
        return None, "Unbekannte Division '%s'. Die 10 Divisionen: %s" \
                     % (parts[0], ", ".join(DIVISIONS))
    return dict(zip(LEVEL_NAMES, parts)), None


def role_prompt(levels):
    # Deterministic role instantiation: the address alone defines the
    # role (Rollen-Template: Mission/Auftrag/DoD/Veto der ULTRA-Org).
    division = levels["division"]
    chain = " -> ".join(levels[n] for n in LEVEL_NAMES if n in levels)
    deepest = [levels[n] for n in LEVEL_NAMES if n in levels][-1]
    return (
        "Du bist ein Agent der Milliarden-Holding von Nate. "
        "Deine Adresse: holding/%s. Zustaendigkeitskette: %s. "
        "Division '%s' verantwortet: %s. "
        "Deine Rolle ist die tiefste Ebene der Adresse ('%s') - du bist "
        "genau dafuer der Spezialist und fuer nichts anderes.\n\n"
        "Arbeitsregeln:\n"
        "- Liefere ein konkretes, sofort verwendbares Ergebnis - kein "
        "Meta-Gerede, keine Rueckfragen-Listen.\n"
        "- Definition of Done: Das Ergebnis ist vollstaendig, praezise "
        "und ehrlich; Annahmen und Unsicherheiten sind als solche "
        "gekennzeichnet.\n"
        "- Nichts Irreversibles: Du empfiehlst und lieferst Entwuerfe, "
        "Entscheidungen trifft Nate.\n"
        "- Antworte auf Deutsch, kompakt (maximal etwa 300 Woerter)."
        % ("/".join(levels[n] for n in LEVEL_NAMES if n in levels),
           chain, division, DIVISIONS[division], deepest)
    )


def _client():
    # Separate function so tests can monkeypatch it.
    import anthropic
    return anthropic.Anthropic()


def _sol_configured():
    return bool(os.environ.get("OPENAI_API_KEY"))


def worker_description():
    if _sol_configured():
        return "%s (reasoning: %s)" % (SOL_MODEL, SOL_EFFORT)
    return _active_model["name"]


def _ask(client, system, user_text, max_tokens=AGENT_MAX_TOKENS):
    import anthropic
    try:
        response = client.messages.create(
            model=_active_model["name"], max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_text}])
    except anthropic.NotFoundError:
        # Key has no access to the configured model - fall back once,
        # permanently for this process. JAVIER stays functional.
        if _active_model["name"] == FALLBACK_MODEL:
            raise
        _active_model["name"] = FALLBACK_MODEL
        response = client.messages.create(
            model=FALLBACK_MODEL, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user_text}])
    return "\n".join(b.text for b in response.content
                     if b.type == "text").strip()


def _ask_worker(client, system, user_text):
    # Worker path: GPT-5.6-Sol via OpenAI, wenn ein Key da ist - bei
    # jedem Fehler ehrlicher Rueckfall auf den Claude-Weg, damit ein
    # kaputter OpenAI-Key nie die ganze Holding lahmlegt.
    if not _sol_configured():
        return _ask(client, system, user_text)
    import requests

    def call_sol(with_effort):
        payload = {"model": SOL_MODEL,
                   "max_completion_tokens": SOL_MAX_TOKENS,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user_text}]}
        if with_effort:
            payload["reasoning_effort"] = SOL_EFFORT
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer %s"
                     % os.environ["OPENAI_API_KEY"]},
            json=payload, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    try:
        try:
            text = call_sol(True)
        except requests.HTTPError as e:
            # Kennt der Endpoint die Reasoning-Stufe nicht (400), einmal
            # ohne sie versuchen statt Sol ganz aufzugeben.
            if e.response is not None and e.response.status_code == 400:
                text = call_sol(False)
            else:
                raise
        if text:
            return text
    except (requests.RequestException, KeyError, IndexError, ValueError):
        pass
    return _ask(client, system, user_text)


def konzern_struktur(adresse=""):
    # Pure lookup, no API calls: explain the org or one address.
    if not adresse:
        return {
            "holding": "10 Divisionen x 100 Companies x 100 Departments "
                       "x 100 Teams x 1000 Agents = 10.000.000.000 "
                       "adressierbare Agents",
            "divisionen": {k: v for k, v in DIVISIONS.items()},
            "adressformat": "holding/<division>/<company>/<department>/"
                            "<team>/<agent> - Division aus der festen "
                            "Liste, alle Ebenen darunter frei waehlbare "
                            "sprechende Namen (z.B. holding/content/"
                            "copywriting/ads/meta/hook-writer-1)",
            "note": "Adressierbar sind alle, instanziiert wird nur, was "
                    "ein Auftrag braucht (max. %d Agents gleichzeitig)."
                    % MAX_AGENTS,
        }
    levels, err = parse_address(adresse)
    if err:
        return {"error": err}
    return {
        "adresse": "holding/" + "/".join(
            levels[n] for n in LEVEL_NAMES if n in levels),
        "ebenen": levels,
        "division_mission": DIVISIONS[levels["division"]],
        "rolle": role_prompt(levels),
        "note": "Diese Rolle existiert generativ - gleiche Adresse "
                "ergibt jederzeit wieder exakt diese Rolle.",
    }


def konzern_auftrag(auftrag, adressen):
    auftrag = (auftrag or "").strip()
    if not auftrag:
        return {"error": "auftrag darf nicht leer sein"}
    if isinstance(adressen, str):
        adressen = [a.strip() for a in adressen.split(",") if a.strip()]
    if not adressen:
        return {"error": "Mindestens eine Agent-Adresse angeben "
                         "(holding/<division>/...)"}
    if len(adressen) > MAX_AGENTS:
        return {"error": "Maximal %d Agents pro Auftrag - die Holding "
                         "arbeitet fokussiert, nicht in Massen. "
                         "Waehle die %d wichtigsten Adressen."
                         % (MAX_AGENTS, MAX_AGENTS)}
    parsed = []
    for a in adressen:
        levels, err = parse_address(a)
        if err:
            return {"error": err}
        parsed.append(levels)

    try:
        client = _client()
    except Exception as e:
        return {"error": "Kein API-Zugang fuer die Holding: %s" % e}

    agents = []
    for levels in parsed:
        addr = "holding/" + "/".join(
            levels[n] for n in LEVEL_NAMES if n in levels)
        try:
            result = _ask_worker(client, role_prompt(levels), auftrag)
        except Exception as e:
            result = "(Agent-Fehler: %s)" % e
        agents.append({"adresse": addr, "ergebnis": result})

    out = {"auftrag": auftrag, "agents": agents,
           "worker_modell": worker_description(),
           "note": "Nenne Nate kurz, welche Adressen gearbeitet haben, "
                   "und fasse das Ergebnis gesprochen knapp zusammen."}
    if len(agents) > 1:
        try:
            bundle = "\n\n".join(
                "=== %s ===\n%s" % (a["adresse"], a["ergebnis"])
                for a in agents)
            out["synthese"] = _ask(
                client,
                "Du bist der Chef der Holding. Fasse die Ergebnisse der "
                "Agents zu EINEM konsolidierten Ergebnis zusammen. "
                "Widersprueche offen benennen statt glaetten. Deutsch, "
                "kompakt.",
                "Auftrag: %s\n\nErgebnisse:\n%s" % (auftrag, bundle))
        except Exception as e:
            out["synthese"] = "(Synthese fehlgeschlagen: %s)" % e
    return out
