"""Regenerate the bundled set's source audio from the music21 corpus.

Writes one WAV per tune into seed/audio/. The WAVs are committed so the
seed step (seed_public_transcriptions.py) is reproducible without re-
deriving them, but this script lets anyone regenerate them deterministically
from the public-domain corpus scores.

Run from the backend venv:
    .venv/bin/python -m seed.generate_audio
"""
from pathlib import Path

from seed.audiogen import write_tune_wav
from seed.manifest import CORPUS_GLOB, TUNES

AUDIO_DIR = Path(__file__).parent / "audio"


def main() -> None:
    for tune in TUNES:
        out = AUDIO_DIR / f"{tune.slug}.wav"
        write_tune_wav(tune.title, CORPUS_GLOB, out)
        print(f"wrote {out.relative_to(Path(__file__).parent)}  ({tune.title})")


if __name__ == "__main__":
    main()
