-- Abrechnung (Phase 4). Abo-Zustand haengt am Mandanten; die kundensichtbare
-- Historie ist mandantengebunden (RLS). Zusaetzlich eine globale Tabelle zur
-- Idempotenz von Webhooks (Stripe UND Shopify liefern Events mehrfach aus).

BEGIN;

-- Abo-Zustand am Mandanten (tenants ist der globale Mandantenkatalog, kein RLS:
-- der Webhook muss den Mandanten anhand der Stripe-Kennung finden, bevor ein
-- Mandantenkontext ueberhaupt existiert).
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS stripe_customer_id     text;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS stripe_subscription_id text;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS subscription_status    text;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS current_period_end     timestamptz;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_stripe_customer
    ON tenants (stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;

-- Kundensichtbare Abrechnungs-Historie (mandantengebunden).
CREATE TABLE IF NOT EXISTS billing_events (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    type           text NOT NULL,            -- subscription_started | plan_changed | invoice_paid | payment_failed | subscription_cancelled
    plan_code      text,
    amount_chf_cents integer,
    occurred_at    timestamptz NOT NULL DEFAULT now(),
    external_id    text
);
CREATE INDEX IF NOT EXISTS idx_billing_events_tenant ON billing_events (tenant_id, occurred_at DESC);

ALTER TABLE billing_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON billing_events;
CREATE POLICY tenant_isolation ON billing_events
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

-- Idempotenz: ein Provider-Event wird genau einmal verarbeitet.
-- Global (kein RLS): der Check laeuft, bevor der Mandant bekannt ist.
CREATE TABLE IF NOT EXISTS processed_webhooks (
    provider     text NOT NULL,              -- stripe | shopify
    event_id     text NOT NULL,
    processed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (provider, event_id)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON billing_events     TO app_rw;
GRANT SELECT, INSERT                 ON processed_webhooks TO app_rw;

COMMIT;
