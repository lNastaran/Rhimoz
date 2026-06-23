"""Turn a public-domain music21 corpus melody into a mono WAV.

Kept separate from the corpus/DB scripts so the melody-extraction and
synthesis logic has one home. Synthesis is a few harmonics plus a short
attack/release envelope - deliberately clean (not a realistic harmonica
timbre), since the goal is audio that Basic Pitch transcribes faithfully,
not a convincing performance. Validated end-to-end: a 85-note source
melody round-tripped to 85 detected notes with full tab annotation.
"""
from pathlib import Path

import numpy as np
import soundfile as sf
from music21 import converter, corpus, stream

# Basic Pitch resamples its input to 22050 Hz internally, so generating at
# that rate (and 16-bit PCM) keeps the committed audio small with no loss
# of detection quality.
SAMPLE_RATE = 22050
BPM = 110
_SEC_PER_QUARTER = 60.0 / BPM


def find_score(title: str, corpus_glob: str) -> stream.Score:
    """The first corpus score whose metadata title matches exactly. ABC
    collection files parse to an Opus of many tunes, so we scan inside."""
    for path in corpus.getCorePaths():
        if corpus_glob not in str(path):
            continue
        parsed = converter.parse(path)
        scores = parsed.scores if isinstance(parsed, stream.Opus) else [parsed]
        for score in scores:
            if score.metadata and score.metadata.title == title:
                return score
    raise LookupError(f"No corpus score titled {title!r} under {corpus_glob!r}")


def melody_events(score: stream.Score) -> list[tuple[int, float, float]]:
    """(midi_pitch, start_seconds, duration_seconds) per note, in order."""
    events = []
    for note in score.flatten().notes:
        if not note.isNote:
            continue
        start = float(note.getOffsetInHierarchy(score)) * _SEC_PER_QUARTER
        duration = float(note.duration.quarterLength) * _SEC_PER_QUARTER
        events.append((note.pitch.midi, start, duration))
    return events


def synthesize(events: list[tuple[int, float, float]]) -> np.ndarray:
    """Additive synthesis of the melody into a normalized mono signal."""
    total_s = max(start + dur for _, start, dur in events) + 0.3
    signal = np.zeros(int(total_s * SAMPLE_RATE), dtype=np.float32)

    for midi, start, dur in events:
        f0 = 440.0 * 2 ** ((midi - 69) / 12.0)
        # leave a small gap before the next note so onsets stay distinct
        n = int(dur * 0.92 * SAMPLE_RATE)
        if n <= 0:
            continue
        t = np.arange(n) / SAMPLE_RATE
        wave = sum((1.0 / k) * np.sin(2 * np.pi * f0 * k * t) for k in (1, 2, 3, 4))

        env = np.ones(n)
        attack = min(int(0.01 * SAMPLE_RATE), n)
        release = min(int(0.05 * SAMPLE_RATE), n)
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)

        wave = (wave * env).astype(np.float32)
        i = int(start * SAMPLE_RATE)
        end = min(i + n, len(signal))
        signal[i:end] += wave[: end - i]

    peak = np.max(np.abs(signal))
    if peak > 0:
        signal = signal / peak * 0.9
    return signal


def write_tune_wav(title: str, corpus_glob: str, out_path: str | Path) -> Path:
    """Render the named public-domain melody to a WAV at out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    score = find_score(title, corpus_glob)
    sf.write(out_path, synthesize(melody_events(score)), SAMPLE_RATE, subtype="PCM_16")
    return out_path
