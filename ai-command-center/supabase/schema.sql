-- AI Command Center – Kunden-/Abo-Tabelle für Stripe-Freischaltung.
-- Einmalig im Supabase SQL-Editor ausführen.
--
-- Sicherheit: Row-Level-Security ist AN. Der Server schreibt/liest ausschliesslich
-- mit dem SERVICE_ROLE_KEY (umgeht RLS bewusst, nur serverseitig). Für den
-- öffentlichen Anon-Key gibt es KEINE Policy → keine Client-Zugriffe auf Abodaten.

create table if not exists public.abos (
  customer_id     text primary key,          -- Stripe-Customer-ID (cus_...)
  email           text,                       -- Kunden-E-Mail (Portal-Lookup)
  plan_id         text not null,              -- Plan aus metadata.planId
  status          text not null default 'active',
  event_zeit      bigint not null default 0,  -- Stripe-Event-Zeit (Unix-Sek.), Reihenfolge-Schutz
  license_key     text,                        -- einmalig erzeugter Lizenzschlüssel (nach Kauf)
  aktualisiert_am timestamptz not null default now()
);

create index if not exists abos_email_idx on public.abos (email);

-- aktualisiert_am bei jedem Update automatisch setzen.
create or replace function public.abos_touch() returns trigger as $$
begin
  new.aktualisiert_am := now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists abos_touch_trg on public.abos;
create trigger abos_touch_trg before update on public.abos
  for each row execute function public.abos_touch();

-- RLS an, bewusst OHNE Policy für anon/authenticated:
-- Zugriff nur über den serverseitigen Service-Role-Key.
alter table public.abos enable row level security;
