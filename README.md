# Rhimoz

A Music transcription: audio in, downloadable sheet music out
(PDF, MusicXML, MIDI). First and currently only supported instrument is
**chromatic harmonica**.

## Repo layout

```
engine/            production package: file in -> MusicXML/MIDI/PDF out
backend/           FastAPI service wrapping engine/ for the web frontend
frontend/          React + TypeScript + Vite web UI (upload, notation, playback, downloads)
research/phase0/   throwaway research that validated the approach above -
                   never imported by engine/, kept for its findings
assets/            logo and other static brand assets
```

## Roadmap

1. ✅ Core transcription engine (file-based) - preprocessing, pitch
   detection, tempo/beat quantization, MusicXML/MIDI/PDF export
2. ✅ Web frontend: upload UI, notation rendering, playback, downloads
3. ✅ Harmonica tab overlay (the differentiator): standard notation
   rendered normally, with a second line underneath each note showing
   the hole number and a blow/draw arrow (↑ = blow, ↓ = draw), the
   format used in published harmonica tab books.
4. Accounts & saved-transcription history
5. Song search across saved transcriptions + a bundled public-domain set
6. (Stretch) Instrument expansion via the profile abstraction - piano,
   guitar, violin, flute
7. Live "Shazam-style" mic listening, sharing the Phase 1 engine -
   deferred for now in favor of the items above, picked up later

Explicitly out of scope: fetching arbitrary copyrighted audio by song
title (a licensing problem, not an engineering one), YouTube ingestion,
and training a custom pitch-detection model from scratch.

## Dev setup

See [engine/README.md](engine/README.md), [backend/README.md](backend/README.md),
and [frontend/README.md](frontend/README.md).
