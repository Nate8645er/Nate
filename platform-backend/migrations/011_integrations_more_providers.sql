-- Erweitert die in 007_integrations.sql angelegte provider-CHECK-Constraint
-- um "github" und "shopify" -- beide sind (wie slack/notion/google) echte
-- Composio-App-Slugs (composio_app_slug() in app/composio_client.py gibt sie
-- unveraendert weiter, anders als "google" -> "gmail"). Siehe
-- app/routes/integrations.py::KNOWN_PROVIDERS fuer den zugehoerigen
-- Anwendungs-seitigen Check.

BEGIN;

ALTER TABLE integrations DROP CONSTRAINT IF EXISTS integrations_provider_check;
ALTER TABLE integrations ADD CONSTRAINT integrations_provider_check
    CHECK (provider IN ('slack', 'notion', 'google', 'github', 'shopify'));

COMMIT;
