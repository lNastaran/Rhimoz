"""
Tempo/beat estimation and note quantization.

Decision: estimate a real per-file tempo via librosa.beat.beat_track
rather than assuming a fixed tempo (e.g. always 120 BPM). A fixed tempo is
simpler but actively produces musically wrong notation whenever the actual
recording isn't at that tempo. Beat tracking on solo monophonic melodic
audio (no strong percussive onsets) is imperfect, so any estimate outside
a sane instrumental range falls back to a fixed default rather than
silently producing nonsense.
"""
from dataclasses import dataclass

import librosa
import numpy as np

from rhimoz.notes.model import NoteSequence, TranscribedNote

MIN_BPM = 40.0
MAX_BPM = 240.0
DEFAULT_FALLBACK_BPM = 120.0
# Subdivisions per quarter-note beat (4 = sixteenth-note grid). Shared with
# export_musicxml.py's quarterLength rounding - that rounding denominator
# must equal this value exactly, or grid steps stop landing on exact
# fractions and notes silently shift position in the exported file. See
# export_musicxml.py's import of this constant.
DEFAULT_GRID_DIVISION = 4


@dataclass
class TempoEstimate:
    bpm: float
    beat_times_s: list[float]
    is_fallback: bool


def _resolve_bpm(raw_bpm: float | None) -> tuple[float, bool]:
    """Pure decision logic, kept separate from beat_track so it's
    unit-testable without needing real audio: falls back to
    DEFAULT_FALLBACK_BPM if raw_bpm is missing or outside [MIN_BPM, MAX_BPM]."""
    if raw_bpm is None or not (MIN_BPM <= raw_bpm <= MAX_BPM):
        return DEFAULT_FALLBACK_BPM, True
    return raw_bpm, False


def estimate_tempo(y: np.ndarray, sr: int) -> TempoEstimate:
    try:
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        raw_bpm = float(np.asarray(tempo).reshape(-1)[0])
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    except Exception:
        raw_bpm = None
        beat_times = []

    bpm, is_fallback = _resolve_bpm(raw_bpm)
    return TempoEstimate(bpm=bpm, beat_times_s=beat_times, is_fallback=is_fallback)


def quantize_to_grid(
    seq: NoteSequence, tempo: TempoEstimate, grid_division: int = DEFAULT_GRID_DIVISION
) -> NoteSequence:
    """Snap each note's start/end to the nearest 1/grid_division-beat
    position (grid_division=4 against a quarter-note beat means snapping
    to sixteenth notes). Pure function on plain floats - no music21 or
    audio involved, fully unit-testable with synthetic data."""
    beat_duration_s = 60.0 / tempo.bpm
    grid_step_s = beat_duration_s / grid_division

    def snap(t: float) -> float:
        return round(t / grid_step_s) * grid_step_s

    quantized_notes = []
    for note in seq.notes:
        start = snap(note.start_s)
        end = snap(note.end_s)
        if end <= start:
            end = start + grid_step_s
        quantized_notes.append(
            TranscribedNote(
                start_s=start,
                end_s=end,
                midi_pitch=note.midi_pitch,
                amplitude=note.amplitude,
                tab=note.tab,
            )
        )

    return NoteSequence(
        notes=quantized_notes,
        instrument_name=seq.instrument_name,
        tempo_bpm=tempo.bpm,
        beat_times_s=tempo.beat_times_s,
    )
