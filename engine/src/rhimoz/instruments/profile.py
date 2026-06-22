"""
The extensibility seam: the pipeline (preprocess, detect, quantize, export)
never branches on instrument identity. It only calls methods on whatever
InstrumentProfile it's given. Adding piano/guitar/violin/flute later means
writing a new profile here, not touching pipeline code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rhimoz.notes.model import TabAnnotation


@dataclass(frozen=True)
class PitchDetectionParams:
    """Backbone-tuning knobs an instrument profile hands to the
    pitch-detection stage. Mirrors Basic Pitch's predict() kwargs so a
    profile's values can be passed straight through."""

    onset_threshold: float
    frame_threshold: float
    minimum_note_length_ms: float
    min_midi: int
    max_midi: int


class InstrumentProfile(ABC):
    """One subclass per supported instrument."""

    name: str
    is_monophonic: bool

    @abstractmethod
    def pitch_range_hz(self) -> tuple[float, float]:
        """(fmin, fmax) for this instrument's playable range."""

    @abstractmethod
    def detection_params(self) -> PitchDetectionParams:
        """Tuned Basic Pitch kwargs for this instrument's timbre/range."""

    def resolve_overlaps(self, note_events: list) -> list:
        """Default: no-op. Polyphonic instruments can legitimately produce
        simultaneous notes (chords), so the default keeps everything.
        Monophonic profiles override this to drop overlap artifacts."""
        return note_events

    def tab_for_note(self, midi_pitch: int) -> TabAnnotation | None:
        """Phase 3 hook: map a MIDI pitch to instrument-idiomatic tab
        notation (e.g. harmonica hole number + blow/draw direction).
        Returns None by default - no profile implements this yet, and
        nothing in Phase 1 calls it. Exists so the note model has a real,
        typed attachment point ready for Phase 3."""
        return None
