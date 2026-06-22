# Rhimoz

AI-powered music transcription: audio in, downloadable sheet music out
(PDF, MusicXML, MIDI). First and currently only supported instrument is
**chromatic harmonica**.

## The differentiator

Generic audio-to-sheet-music tools already exist (Klangio, AnthemScore,
ScoreCloud, Melody Scanner). None specialize in harmonica. Rhimoz's
differentiator is a **harmonica tab overlay**: standard notation rendered
normally, with a second line underneath each note showing the hole number
and a blow/draw arrow (↑ = blow, ↓ = draw) — the format used in published
harmonica tab books. This isn't built yet (it's Phase 3 - see Roadmap
below), but the engine already produces exactly the note+timing data it
will need, with a typed-but-empty slot (`TabAnnotation`) ready to attach it.

## Why the architecture isn't harmonica-only

Every pipeline stage (preprocessing, pitch detection, quantization, export)
takes an `InstrumentProfile` and never branches on "is this harmonica."
Adding piano, guitar, violin, or flute later means writing a new profile
file in [engine/src/rhimoz/instruments/](engine/src/rhimoz/instruments/)
and registering it - not touching pipeline code. See
[engine/README.md](engine/README.md) for the package layout.

## Why Basic Pitch, tuned

[research/phase0/](research/phase0/) validated, against real audio rather
than assumption, that Spotify's Basic Pitch is fast enough (~50-100x
real-time) and accurate enough for monophonic chromatic harmonica - but
only with harmonica-aware tuning (frequency range clamped to the
instrument's real range, raised onset/frame thresholds, and a monophonic
overlap filter), not Basic Pitch's polyphonic-instrument defaults, which
produced heavy harmonic bleed-through and out-of-range artifacts. Full
findings: [research/phase0/PHASE0_FINDINGS.md](research/phase0/PHASE0_FINDINGS.md).

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
3. Harmonica tab overlay (the differentiator)
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
