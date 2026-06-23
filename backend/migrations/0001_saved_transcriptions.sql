-- Phase 5: saved transcriptions, owned per-user.
--
-- Stores MusicXML + note data (small text/JSON) rather than rendered
-- MIDI/PDF binaries - those are regenerated on demand from this data when
-- a saved transcription is reopened, since they're fully derivable from
-- it and this avoids needing object storage in this phase. See the
-- "File storage fork" section of the Phase 5 plan for the full reasoning.

create table saved_transcriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  display_name text not null,
  instrument_name text not null,
  tempo_bpm double precision,
  musicxml text not null,
  notes_json jsonb not null,
  created_at timestamptz not null default now()
);

create index saved_transcriptions_user_id_created_at_idx
  on saved_transcriptions (user_id, created_at desc);

alter table saved_transcriptions enable row level security;

-- One policy per operation rather than a single ALL policy, so each
-- operation's predicate is visible on its own and any future divergence
-- (e.g. allowing shared/public transcriptions later) only touches the
-- one policy that needs to change.
create policy "select own saved transcriptions"
  on saved_transcriptions for select
  using (auth.uid() = user_id);

create policy "insert own saved transcriptions"
  on saved_transcriptions for insert
  with check (auth.uid() = user_id);

create policy "update own saved transcriptions"
  on saved_transcriptions for update
  using (auth.uid() = user_id);

create policy "delete own saved transcriptions"
  on saved_transcriptions for delete
  using (auth.uid() = user_id);
