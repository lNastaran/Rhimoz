from rhimoz.notes.model import NoteSequence, TabAnnotation, TranscribedNote


def test_duration_s():
    note = TranscribedNote(start_s=1.0, end_s=1.5, midi_pitch=60, amplitude=0.8)
    assert note.duration_s == 0.5


def test_tab_defaults_to_none():
    note = TranscribedNote(start_s=0.0, end_s=0.2, midi_pitch=64, amplitude=0.5)
    assert note.tab is None


def test_tab_annotation_can_be_attached():
    tab = TabAnnotation(label="4", direction="blow")
    note = TranscribedNote(start_s=0.0, end_s=0.2, midi_pitch=64, amplitude=0.5, tab=tab)
    assert note.tab.label == "4"
    assert note.tab.direction == "blow"


def test_sorted_by_start_orders_notes_and_preserves_sequence_metadata():
    notes = [
        TranscribedNote(start_s=1.0, end_s=1.2, midi_pitch=60, amplitude=0.5),
        TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=62, amplitude=0.5),
    ]
    seq = NoteSequence(
        notes=notes, instrument_name="chromatic_harmonica", tempo_bpm=120.0
    )

    sorted_seq = seq.sorted_by_start()

    assert [n.start_s for n in sorted_seq.notes] == [0.0, 1.0]
    assert sorted_seq.instrument_name == "chromatic_harmonica"
    assert sorted_seq.tempo_bpm == 120.0
    # original sequence is untouched
    assert [n.start_s for n in seq.notes] == [1.0, 0.0]
