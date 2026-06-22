# Rhimoz transcription engine

The file-in, sheet-music-out core: audio → preprocessing → pitch detection →
tempo/beat quantization → MusicXML/MIDI/PDF export. Used by both the
file-upload and (later) live-mic input modes.

Built on Phase 0's validated findings — see
[../research/phase0/PHASE0_FINDINGS.md](../research/phase0/PHASE0_FINDINGS.md).

## Setup

Requires Python 3.11 (TensorFlow/Basic Pitch don't support newer Python
yet). Uses [`uv`](https://github.com/astral-sh/uv) to manage the
interpreter without depending on Homebrew.

```sh
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
```

`setuptools<81` is pinned because `resampy` (a `librosa` dependency) still
imports the deprecated `pkg_resources` API.

## Test

```sh
.venv/bin/pytest tests/unit -v          # fast, no model load
.venv/bin/pytest tests/integration -v   # loads Basic Pitch, runs on real audio
.venv/bin/pytest                        # everything
```

## Layout

- `src/rhimoz/instruments/` — the extensibility seam. `InstrumentProfile`
  is the abstract interface; `ChromaticHarmonicaProfile` is the only
  concrete implementation so far. Adding piano/guitar/violin/flute later
  means writing a new profile file here, not touching pipeline code.
- `src/rhimoz/notes/` — the internal note model (`TranscribedNote`,
  `NoteSequence`), independent of any notation library, with a typed slot
  (`TabAnnotation`) for the harmonica tab overlay Phase 3 will attach.
- `src/rhimoz/pipeline/` — one module per stage (preprocess, detect,
  quantize, export to MusicXML/MIDI, export to PDF).
- `src/rhimoz/transcribe.py` — top-level orchestration tying the stages
  together.
