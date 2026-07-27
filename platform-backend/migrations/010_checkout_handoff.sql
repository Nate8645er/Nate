-- Schliesst eine echte Onboarding-Luecke: bisher wurde bei einem Stripe-Kauf
-- zwar automatisch ein Mandant + API-Key erzeugt (checkout.session.completed
-- in app/routes/billing.py), aber der Key wurde NIRGENDS an den zahlenden
-- Kunden ausgeliefert -- keine E-Mail, keine Erfolgsseite. Anders als bei
-- ChatGPT/Claude/Kimi (Abo kaufen -> sofort loslegen) haette der Kunde nie
-- Zugriff auf sein eigenes Konto bekommen.
--
-- checkout_handoffs ist eine kurzlebige, EINMAL abrufbare Uebergabe: die
-- Stripe-Checkout-Session-ID (hochentropisch, vom Kunden-Browser beim
-- Redirect auf die eigene Erfolgsseite mitgefuehrt) dient als Abholschein
-- fuer genau diesen einen Klartext-Key. Wird nach dem ersten Abruf geloescht
-- (siehe app/routes/billing.py claim_checkout_handoff) -- kein dauerhafter
-- Klartext-Speicher.

BEGIN;

CREATE TABLE IF NOT EXISTS checkout_handoffs (
    stripe_session_id text PRIMARY KEY,
    tenant_id          uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    api_key_clear      text NOT NULL,
    created_at         timestamptz NOT NULL DEFAULT now()
);

-- Keine RLS: wird VOR jeder Authentifizierung abgefragt (der Kunde hat ja
-- noch keinen API-Key), Zugriff nur ueber admin_tx() wie bei tenants/plans.
GRANT SELECT, INSERT, DELETE ON checkout_handoffs TO app_rw;

COMMIT;
