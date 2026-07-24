-- Tarif-Seed gemaess Master-Prompt 3.3. Preise CHF inkl. MwSt in Rappen.
-- Modelle sind pro Tarif freigeschaltet (nicht pro Nutzer hart kodiert).
-- idempotent: ON CONFLICT (code) DO UPDATE haelt den Katalog aktuell.

INSERT INTO plans (code, name, price_chf_cents, allowed_models, max_agents, monthly_token_limit, max_integrations, features) VALUES
  ('free',       'Free',       0,
     '["ollama/llama3.2"]'::jsonb,
     1,   100000,     0, '{"support":"none"}'::jsonb),

  ('starter',    'Starter',    1900,
     '["anthropic/claude-haiku-4-5","ollama/llama3.2"]'::jsonb,
     3,  2000000,     1, '{"support":"email"}'::jsonb),

  ('pro',        'Pro',        4900,
     '["anthropic/claude-sonnet-5","anthropic/claude-haiku-4-5","ollama/llama3.2"]'::jsonb,
     10, 10000000,    3, '{"support":"email","local_models":true}'::jsonb),

  ('business',   'Business',   14900,
     '["anthropic/claude-opus-4-8","anthropic/claude-sonnet-5","anthropic/claude-haiku-4-5","openai/gpt-4o","ollama/llama3.2"]'::jsonb,
     30, 50000000,    99, '{"support":"priority","sso":true,"team":true}'::jsonb),

  ('enterprise', 'Enterprise', 0,
     '["*"]'::jsonb,
     2147483647, 9223372036854775807, 99, '{"support":"sla","dedicated":true,"custom":true}'::jsonb)
ON CONFLICT (code) DO UPDATE SET
    name                = EXCLUDED.name,
    price_chf_cents     = EXCLUDED.price_chf_cents,
    allowed_models      = EXCLUDED.allowed_models,
    max_agents          = EXCLUDED.max_agents,
    monthly_token_limit = EXCLUDED.monthly_token_limit,
    max_integrations    = EXCLUDED.max_integrations,
    features            = EXCLUDED.features;
