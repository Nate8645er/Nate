-- Haertung der Abrechnung (Security-Review, Phase 4):
--   - suspended_reason unterscheidet admin- von billing-bedingter Sperre,
--     damit ein regulaeres invoice.paid eine administrative Sperre nicht
--     versehentlich aufhebt.
--   - billing_events braucht nur SELECT+INSERT (die App fuehrt nie UPDATE/
--     DELETE aus); UPDATE/DELETE unnoetig weit gewaehrt.

BEGIN;

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS suspended_reason text;
-- 'admin' (manuell durch Betreiber gesperrt) | 'billing' (Abo inaktiv) | NULL (aktiv)

REVOKE UPDATE, DELETE ON billing_events FROM app_rw;
GRANT SELECT, INSERT ON billing_events TO app_rw;

COMMIT;
