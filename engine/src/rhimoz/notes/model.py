"""
The internal note model. Deliberately plain dataclasses, not music21
objects: the stages between detection and export (overlap filtering,
quantization) only need start/end/pitch/amplitude as numbers, and pulling
music21's heavier object graph in that early would couple every pipeline
stage to an external API. music21 enters only at the export boundary
(pipeline/export_musicxml.py), where this model gets converted once.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TabAnnotation:
    """Instrument-idiomatic tab metadata (e.g. harmonica hole number +
    blow/draw direction). Phase 1 never constructs one of these - no
    profile implements InstrumentProfile.tab_for_note() yet - but the field
    needs a real type now so Phase 3 has a clean place to attach it."""

    label: str
    direction: str


@dataclass
class TranscribedNote:
    start_s: float
    end_s: float
    midi_pitch: int
    amplitude: float
    tab: TabAnnotation | None = None

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass
class NoteSequence:
    """Ordered, instrument-tagged collection of notes for one transcribed
    audio file. The unit passed between detect -> quantize -> export."""

    notes: list[TranscribedNote]
    instrument_name: str
    tempo_bpm: float | None = None
    beat_times_s: list[float] | None = None

    def sorted_by_start(self) -> "NoteSequence":
        return NoteSequence(
            notes=sorted(self.notes, key=lambda n: n.start_s),
            instrument_name=self.instrument_name,
            tempo_bpm=self.tempo_bpm,
            beat_times_s=self.beat_times_s,
        )
