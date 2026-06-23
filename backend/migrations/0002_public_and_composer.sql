-- Roadmap #5: song search across saved transcriptions + a bundled
-- public-domain set.
--
-- Two changes:
--   1. Add an optional `composer` to saved_transcriptions so search can
--      match composer/artist as well as title (display_name).
--   2. Add a separate `public_transcriptions` table for the bundled
--      public-domain library. It is modeled as its own table rather than
--      an is_public flag on saved_transcriptions because public rows have
--      no owner (the user_id FK + RLS model assumes one) and carry extra
--      provenance columns (source_url, license) that user rows don't.

alter table saved_transcriptions
  add column composer text;

-- The bundled public-domain set. Same stored shape as saved_transcriptions
-- (MusicXML + note JSON, MIDI/PDF regenerated on demand) minus ownership,
-- plus provenance. `title` mirrors saved_transcriptions.display_name.
create table public_transcriptions (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  composer text,
  instrument_name text not null,
  tempo_bpm double precision,
  musicxml text not null,
  notes_json jsonb not null,
  source_url text,
  license text,
  created_at timestamptz not null default now()
);

alter table public_transcriptions enable row level security;

-- World-readable: every authenticated request (each using a fresh
-- user-scoped client) can read the bundled set, so one search endpoint can
-- query both tables with the same client. No insert/update/delete policies
-- are defined on purpose - seeding runs with the secret key, which bypasses
-- RLS, so there is no path for a normal user to mutate the bundled set.
create policy "read public transcriptions"
  on public_transcriptions for select
  using (true);
