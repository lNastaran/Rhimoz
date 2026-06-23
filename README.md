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
4. ✅ Accounts & saved-transcription history: email/password auth, a
   "Save" action on any transcription, a dashboard listing saved
   transcriptions with reopen and delete. Built on Supabase (Postgres +
   auth), with Row Level Security enforcing per-user ownership at the
   database layer.
5. ✅ Song search across saved transcriptions + a bundled public-domain
   set: a dedicated search page matching title and composer across both
   the user's own saved transcriptions and a small set of bundled
   public-domain songs (traditional Irish airs from O'Neill's Music of
   Ireland, 1903), each reopenable and downloadable like any other
   transcription.

Future work: instrument expansion via the profile abstraction (piano,
guitar, violin, flute), live "Shazam-style" mic listening, fetching
arbitrary copyrighted audio by song title, YouTube ingestion, and training
a custom pitch-detection model from scratch.

## Dev setup

See [engine/README.md](engine/README.md), [backend/README.md](backend/README.md),
and [frontend/README.md](frontend/README.md).
