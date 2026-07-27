-- Schliesst eine dokumentierte Luecke (README "bewusst offen"): das
-- Monats-Token-Limit wurde bisher als reiner Vorab-Check geprueft (Zeile
-- "used >= monthly_token_limit" in app/completions.py) OHNE ihn atomar mit
-- dem spaeteren Verbrauchseintrag zu verbinden -- zwei parallele Anfragen
-- desselben Mandanten sahen beide "noch unter dem Limit" und konnten es
-- gemeinsam ueberschreiten (TOCTOU).
--
-- reserved_tokens haelt eine kurzlebige, atomare Reservierung waehrend ein
-- Chat-Aufruf laeuft: reserviert VOR dem (langsamen) Gateway-Aufruf per
-- einzelnem atomarem UPDATE, freigegeben direkt danach -- die DB-Verbindung
-- wird dafuer NICHT waehrend des externen Aufrufs offengehalten (sonst
-- Gefahr von Pool-Erschoepfung bei gleichzeitigen Anfragen anderer
-- Mandanten, siehe app/completions.py).

BEGIN;

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS reserved_tokens bigint NOT NULL DEFAULT 0;

COMMIT;
