from rhimoz.instruments.harmonica import ChromaticHarmonicaProfile
from rhimoz.notes.model import NoteSequence, TranscribedNote
from rhimoz.pipeline.tab import annotate_tabs


def test_annotate_tabs_attaches_tab_to_each_note():
    notes = [
        TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=48, amplitude=0.8),
        TranscribedNote(start_s=0.5, end_s=1.0, midi_pitch=60, amplitude=0.7),
    ]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica")

    result = annotate_tabs(seq, ChromaticHarmonicaProfile())

    assert result.notes[0].tab is not None
    assert result.notes[0].tab.label == "1"
    assert result.notes[1].tab is not None
    assert result.notes[1].tab.label == "5"


def test_annotate_tabs_preserves_sequence_metadata():
    notes = [TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=48, amplitude=0.8)]
    seq = NoteSequence(
        notes=notes,
        instrument_name="chromatic_harmonica",
        tempo_bpm=96.0,
        beat_times_s=[0.0, 0.625],
    )

    result = annotate_tabs(seq, ChromaticHarmonicaProfile())

    assert result.instrument_name == "chromatic_harmonica"
    assert result.tempo_bpm == 96.0
    assert result.beat_times_s == [0.0, 0.625]


def test_annotate_tabs_leaves_tab_none_for_out_of_range_note():
    notes = [TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=200, amplitude=0.8)]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica")

    result = annotate_tabs(seq, ChromaticHarmonicaProfile())

    assert result.notes[0].tab is None


def test_annotate_tabs_does_not_mutate_original_notes():
    note = TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=48, amplitude=0.8)
    seq = NoteSequence(notes=[note], instrument_name="chromatic_harmonica")

    annotate_tabs(seq, ChromaticHarmonicaProfile())

    assert note.tab is None
