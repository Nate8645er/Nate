-- Das KI-Team (13 Anbieter ueber OpenRouter) den Tarifen zuordnen.
-- Gestaffelt: hoehere Tarife schalten mehr und staerkere Modelle frei.
-- Idempotent: setzt allowed_models pro Tarif-Code neu (kein Anhaengen von
-- Duplikaten bei erneutem Lauf).
--
-- Alle IDs sind gegen den OpenRouter-Live-Katalog geprueft und per
-- ops/council_check.py real getestet (13/13 haben geantwortet).

BEGIN;

-- Free bleibt bewusst lokal-only (keine laufenden Kosten pro Anfrage).

-- Starter: ein guenstiges, schnelles Team-Modell zusaetzlich.
UPDATE plans SET allowed_models = '[
  "anthropic/claude-haiku-4-5",
  "ollama/llama3.2",
  "openrouter/microsoft/phi-4"
]'::jsonb WHERE code = 'starter';

-- Pro: solide Auswahl quer ueber die Anbieter.
UPDATE plans SET allowed_models = '[
  "anthropic/claude-sonnet-5",
  "anthropic/claude-haiku-4-5",
  "ollama/llama3.2",
  "openrouter/openai/gpt-5.6-sol-pro",
  "openrouter/google/gemini-3.1-pro-preview",
  "openrouter/deepseek/deepseek-v4-pro",
  "openrouter/meta-llama/llama-4-maverick",
  "openrouter/mistralai/mistral-large-2512",
  "openrouter/microsoft/phi-4"
]'::jsonb WHERE code = 'pro';

-- Business: das vollstaendige 13-koepfige Team.
UPDATE plans SET allowed_models = '[
  "anthropic/claude-opus-4-8",
  "anthropic/claude-sonnet-5",
  "anthropic/claude-haiku-4-5",
  "openai/gpt-4o",
  "ollama/llama3.2",
  "openrouter/openai/gpt-5.6-sol-pro",
  "openrouter/anthropic/claude-opus-4.8",
  "openrouter/google/gemini-3.1-pro-preview",
  "openrouter/x-ai/grok-4.5",
  "openrouter/moonshotai/kimi-k3",
  "openrouter/deepseek/deepseek-v4-pro",
  "openrouter/qwen/qwen3.7-max",
  "openrouter/meta-llama/llama-4-maverick",
  "openrouter/mistralai/mistral-large-2512",
  "openrouter/z-ai/glm-5.2",
  "openrouter/microsoft/phi-4",
  "openrouter/cohere/command-a",
  "openrouter/nvidia/nemotron-3-ultra-550b-a55b"
]'::jsonb WHERE code = 'business';

-- Enterprise hat bereits ["*"] und damit automatisch alles Registrierte.

COMMIT;
