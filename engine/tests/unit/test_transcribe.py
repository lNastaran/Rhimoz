from rhimoz.notes.model import NoteSequence, TranscribedNote
from rhimoz.transcribe import render_outputs


def _synthetic_sequence() -> NoteSequence:
    notes = [
        TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=60, amplitude=0.8),
        TranscribedNote(start_s=0.5, end_s=1.0, midi_pitch=62, amplitude=0.7),
    ]
    return NoteSequence(notes=notes, instrument_name="chromatic_harmonica", tempo_bpm=120.0)


def test_render_outputs_writes_all_three_files_without_detection(tmp_path):
    """No audio/model involved at all - this is the whole point of
    render_outputs() existing separately from transcribe_file(): a known
    NoteSequence (e.g. one loaded back from a saved transcription) can be
    re-exported without ever touching Basic Pitch."""
    seq = _synthetic_sequence()
    result = render_outputs(seq, tmp_path, stem="reopened")

    assert result.note_sequence is seq
    assert result.musicxml_path == tmp_path / "reopened.musicxml"
    assert result.midi_path == tmp_path / "reopened.mid"
    assert result.pdf_path == tmp_path / "reopened.pdf"
    for path in (result.musicxml_path, result.midi_path, result.pdf_path):
        assert path.exists()
        assert path.stat().st_size > 0


def test_render_outputs_creates_out_dir_if_missing(tmp_path):
    out_dir = tmp_path / "does-not-exist-yet"
    result = render_outputs(_synthetic_sequence(), out_dir)

    assert out_dir.exists()
    assert result.musicxml_path.exists()
