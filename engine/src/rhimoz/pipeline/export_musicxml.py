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

DEFAULT_BPM = 120.0
# Matches quantize.py's default grid_division=4 against a quarter-note
# beat (tempo_bpm is quarter notes per minute): the finest grid step is a
# sixteenth note, so rounding to 1/16 here removes float noise from the
# seconds->quarterLength conversion without losing any real precision.
GRID_DENOMINATOR = 16


def _seconds_to_quarter_length(seconds: float, bpm: float) -> Fraction:
    quarter_length = seconds * bpm / 60.0
    return Fraction(round(quarter_length * GRID_DENOMINATOR), GRID_DENOMINATOR)


def note_sequence_to_stream(seq: NoteSequence) -> music21.stream.Score:
    """Builds a music21 Score with each note placed at its absolute
    offset (in quarter notes). music21 fills gaps with rests and builds
    measures automatically during write() via makeNotation()."""
    bpm = seq.tempo_bpm or DEFAULT_BPM

    part = music21.stream.Part()
    part.append(music21.tempo.MetronomeMark(number=bpm))

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
