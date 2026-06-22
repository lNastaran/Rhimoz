"""
MusicXML/MIDI export. This is the only module that imports music21 - the
internal note model (rhimoz.notes.model) stays plain dataclasses through
every other pipeline stage, and gets converted to a music21 Stream once,
here, at the export boundary.
"""
from fractions import Fraction
from pathlib import Path

import music21

from rhimoz.notes.model import NoteSequence
from rhimoz.pipeline.quantize import DEFAULT_GRID_DIVISION

DEFAULT_BPM = 120.0
# Must equal quantize.py's grid_division (imported, not duplicated): a
# quantized note's start/end always lands on an exact multiple of
# 1/grid_division quarter notes, so rounding quarterLength to the nearest
# 1/GRID_DENOMINATOR is only lossless if GRID_DENOMINATOR == grid_division.
# A mismatch wouldn't crash - it would silently round notes to slightly
# wrong positions.
GRID_DENOMINATOR = DEFAULT_GRID_DIVISION


def _seconds_to_quarter_length(seconds: float, bpm: float) -> Fraction:
    quarter_length = seconds * bpm / 60.0
    return Fraction(round(quarter_length * GRID_DENOMINATOR), GRID_DENOMINATOR)


def note_sequence_to_stream(seq: NoteSequence) -> music21.stream.Score:
    """Builds a music21 Score with each note placed at its absolute
    offset (in quarter notes). music21 fills gaps with rests and builds
    measures automatically during write() via makeNotation()."""
    bpm = seq.tempo_bpm or DEFAULT_BPM

    part = music21.stream.Part()
    # Display rounded (e.g. "136" rather than "135.99917...") - the
    # precise bpm is still used for the offset/duration math below, since
    # rounding there would compound into audible drift over a long piece.
    part.append(music21.tempo.MetronomeMark(number=round(bpm)))

    for note in seq.notes:
        offset = _seconds_to_quarter_length(note.start_s, bpm)
        duration_ql = _seconds_to_quarter_length(note.duration_s, bpm)
        if duration_ql <= 0:
            duration_ql = Fraction(1, GRID_DENOMINATOR)

        m21_note = music21.note.Note(note.midi_pitch)
        m21_note.duration = music21.duration.Duration(duration_ql)
        part.insert(float(offset), m21_note)

    score = music21.stream.Score()
    score.insert(0, part)
    return score


def export_musicxml(seq: NoteSequence, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    note_sequence_to_stream(seq).write("musicxml", fp=str(out_path))
    return out_path


def export_midi(seq: NoteSequence, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    note_sequence_to_stream(seq).write("midi", fp=str(out_path))
    return out_path
