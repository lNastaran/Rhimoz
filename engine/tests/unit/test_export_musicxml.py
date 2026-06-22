import music21

from rhimoz.notes.model import NoteSequence, TranscribedNote
from rhimoz.pipeline.export_musicxml import (
    export_midi,
    export_musicxml,
    note_sequence_to_stream,
)


def _synthetic_sequence() -> NoteSequence:
    # 120 BPM -> quarter note = 0.5s. Notes at beat 0, 1, 2, 3.
    notes = [
        TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=60, amplitude=0.8),
        TranscribedNote(start_s=0.5, end_s=1.0, midi_pitch=62, amplitude=0.7),
        TranscribedNote(start_s=1.0, end_s=1.5, midi_pitch=64, amplitude=0.9),
        TranscribedNote(start_s=1.5, end_s=2.0, midi_pitch=65, amplitude=0.6),
    ]
    return NoteSequence(notes=notes, instrument_name="chromatic_harmonica", tempo_bpm=120.0)


def test_note_sequence_to_stream_places_notes_at_correct_offsets_and_pitches():
    stream = note_sequence_to_stream(_synthetic_sequence())
    notes = list(stream.flatten().notes)

    assert len(notes) == 4
    assert [n.pitch.midi for n in notes] == [60, 62, 64, 65]
    assert [float(n.offset) for n in notes] == [0.0, 1.0, 2.0, 3.0]
    assert [float(n.duration.quarterLength) for n in notes] == [1.0, 1.0, 1.0, 1.0]


def test_note_sequence_to_stream_defaults_tempo_when_missing():
    notes = [TranscribedNote(start_s=0.0, end_s=1.0, midi_pitch=60, amplitude=0.8)]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica", tempo_bpm=None)

    # Should not raise, and should fall back to DEFAULT_BPM (120).
    stream = note_sequence_to_stream(seq)
    notes_in_stream = list(stream.flatten().notes)
    assert len(notes_in_stream) == 1


def test_export_musicxml_round_trips_pitches(tmp_path):
    out_path = tmp_path / "out.musicxml"
    result_path = export_musicxml(_synthetic_sequence(), out_path)

    assert result_path == out_path
    assert out_path.exists()
    assert out_path.stat().st_size > 0

    parsed = music21.converter.parse(str(out_path))
    pitches = [n.pitch.midi for n in parsed.flatten().notes]
    assert pitches == [60, 62, 64, 65]


def test_export_midi_writes_nonempty_file(tmp_path):
    out_path = tmp_path / "out.mid"
    result_path = export_midi(_synthetic_sequence(), out_path)

    assert result_path == out_path
    assert out_path.exists()
    assert out_path.stat().st_size > 0
