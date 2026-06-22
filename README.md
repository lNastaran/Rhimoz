# Rhimoz

A Music transcription: audio in, downloadable sheet music out
(PDF, MusicXML, MIDI). First and currently only supported instrument is
**chromatic harmonica**.

## Repo layout

```
engine/            production package: file in -> MusicXML/MIDI/PDF out
research/phase0/   throwaway research that validated the approach above -
                   never imported by engine/, kept for its findings
assets/            logo and other static brand assets
```

## Roadmap

1. ✅ Core transcription engine (file-based) - preprocessing, pitch
   detection, tempo/beat quantization, MusicXML/MIDI/PDF export
2. Web frontend: upload UI, notation rendering, playback, downloads
3. Harmonica tab overlay (the differentiator): standard notation rendered
   normally, with a second line underneath each note showing the hole
   number and a blow/draw arrow (↑ = blow, ↓ = draw), the format used in
   published harmonica tab books. This isn't built yet, but the engine
   already produces exactly the note+timing data it will need, with a
   typed-but-empty slot (`TabAnnotation`) ready to attach it.
4. Live "Shazam-style" mic listening, sharing the Phase 1 engine
5. Accounts & saved-transcription history
6. Song search across saved transcriptions + a bundled public-domain set
7. (Stretch) Instrument expansion via the profile abstraction - piano,
   guitar, violin, flute

Explicitly out of scope: fetching arbitrary copyrighted audio by song
title (a licensing problem, not an engineering one), YouTube ingestion,
and training a custom pitch-detection model from scratch.

## Engine dev setup

See [engine/README.md](engine/README.md).
