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

## Run

```sh
.venv/bin/uvicorn rhimoz_api.main:app --reload
```

Serves on `http://localhost:8000`. CORS is configured for Vite's dev
server at `http://localhost:5173`.

## Test

```sh
.venv/bin/pytest -v
```

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
  lifetime. No persistence requirement yet (Phase 5), so not solved here.
- No auth - anyone who can reach the server can transcribe and download.
