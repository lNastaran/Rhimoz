# Rhimoz API

FastAPI service wrapping the [engine](../engine) for the web frontend:
upload audio, get back notation data, MIDI/PDF/MusicXML downloads.

## Setup

Requires Python 3.11, same as `engine/`. Uses
[`uv`](https://github.com/astral-sh/uv) to manage the interpreter
without depending on Homebrew.

```sh
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
```

`rhimoz` (the engine) is installed as an editable path dependency on
`../engine` via `[tool.uv.sources]` in `pyproject.toml` - there's
nothing to install separately.

Accounts and saved transcriptions (Phase 5) need a Supabase project.
Create one at [supabase.com](https://supabase.com), then add a `.env`
file (gitignored) with:

```
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=<anon/publishable key, from Project Settings -> API Keys>
SUPABASE_SECRET_KEY=<service_role/secret key, from the same page - keep private>
```

Then apply the SQL migrations in `migrations/` in order via the Supabase
dashboard's SQL Editor (or the `supabase` CLI, if you have a project
linked):

- `0001_saved_transcriptions.sql` creates the `saved_transcriptions`
  table with Row Level Security policies enforcing `auth.uid() = user_id`
  on every operation.
- `0002_public_and_composer.sql` adds the optional `composer` column to
  `saved_transcriptions` and creates the world-readable
  `public_transcriptions` table for the bundled public-domain set.

### Seeding the public-domain set

After `0002` is applied, populate the bundled "Public-domain library":

```sh
.venv/bin/python -m seed.seed_public_transcriptions
```

This regenerates clean audio from public-domain melodies in the music21
corpus (no network), runs them through the real engine pipeline, and
upserts the results into `public_transcriptions` using the secret key. It
is idempotent. See [seed/PROVENANCE.md](seed/PROVENANCE.md) for the tunes
and their licensing.

## Run

```sh
.venv/bin/uvicorn rhimoz_api.main:app --reload
```

Serves on `http://localhost:8000`. CORS is configured for Vite's dev
server at `http://localhost:5173`.

## Routes

- `POST /transcribe`, `GET /jobs/{id}/download/{kind}` - the core
  file-in/notation-out flow, unauthenticated (anyone who can reach the
  server can transcribe and download - see "Known limitations" below).
- `POST /saved`, `GET /saved`, `GET /saved/{id}`, `DELETE /saved/{id}`,
  `GET /saved/{id}/download/{kind}` - saved-transcription CRUD, all
  protected by `auth.get_current_user` (a Supabase JWT via
  `Authorization: Bearer <token>`). The download route regenerates
  MIDI/PDF/MusicXML on demand from the saved note data rather than
  storing those binaries - see `engine/src/rhimoz/transcribe.py`'s
  `render_outputs()`. `POST /saved` accepts an optional `composer`.
- `GET /public/{id}`, `GET /public/{id}/download/{kind}` - read-only
  reopen and download for the bundled public-domain set. Same
  regenerate-on-demand path as saved downloads (shared in
  `rhimoz_api/render.py`); the table is world-readable, writes happen
  only via the seed script.
- `GET /search?q=...` - song search across both the caller's own saved
  transcriptions (RLS-scoped) and the public set, matching title and
  composer (case-insensitive substring), returned as separate
  `personal`/`public` lists.

## Test

```sh
.venv/bin/pytest -v                          # everything
.venv/bin/pytest -v -m "not requires_supabase"  # skip live-Supabase tests
```

`tests/test_saved.py`, `tests/test_public.py`, and `tests/test_search.py`
are a genuine integration suite, not unit tests with a fake DB: they do
real sign-ups against the Supabase project in `.env` and exercise real
Postgres RLS (including that `/search` never returns another user's
private rows), since there's no local Postgres+PostgREST+RLS emulator in
this project to fake that against. The public-table tests insert a bundled
row with the secret key (which bypasses the read-only RLS) and clean it up
afterward.
Skips automatically (rather than failing) if Supabase env vars aren't
configured, same as `phase0_sample_path` skips when real sample audio
isn't present.

Tests use `httpx.AsyncClient` over `ASGITransport`, **not**
`fastapi.testclient.TestClient`. `TestClient` drives the app from a
background thread, and verovio's PDF rendering (inside
`transcribe_file` -> `export_pdf`) crashes the whole process when
invoked off the main thread - confirmed by reproducing the crash with a
plain `threading.Thread`, with no FastAPI involved. `ASGITransport`
runs the app directly on the calling coroutine's thread instead.

This is also why `/transcribe` is `async def`, not `def`: FastAPI runs
sync `def` endpoints in a worker thread pool, which hits the same
crash on a real server. `async def` keeps the work on the event loop's
thread. Tradeoff: `transcribe_file()` is a blocking, CPU-bound call, so
this blocks the event loop - and therefore all other concurrent
requests - for the duration of each transcription. Acceptable for this
phase's single-user local scope (Basic Pitch runs ~50-100x realtime
per Phase 0's findings); revisit if concurrent load ever matters.

## Known limitations

- No job cleanup: `JOBS` and the directories under
  `tempfile.gettempdir()/rhimoz-jobs` grow unbounded for the process
  lifetime. This is about the *transient*, not-yet-saved transcribe
  session (the thing `POST /saved` reads from to save a transcription) -
  saved transcriptions themselves persist properly in Postgres and don't
  have this problem. Not solved here; revisit before this runs unattended
  for any length of time.
- `/transcribe` and its downloads remain unauthenticated - anyone who can
  reach the server can transcribe and download without an account. Only
  *saving* a transcription requires login (a deliberate "try free, sign
  in to save" choice, not an oversight - see the Phase 5 plan).
- `job_id` is a bearer-capability, not an owned resource: `POST /saved`
  doesn't check that the job belongs to the requesting user's own
  session, so anyone who obtains a `job_id` (random UUID, not
  enumerable) can save a copy of that transcription to their own
  account - the same exposure `/jobs/{id}/download/{kind}` already has
  for downloading, just extended to a new action rather than a new gap.
  Acceptable for now under the same bound (UUIDs aren't guessable);
  would need real per-job ownership if `/transcribe` ever stops being
  open to anyone.
