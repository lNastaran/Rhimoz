import librosa

from rhimoz.instruments import PROFILES, ChromaticHarmonicaProfile


def test_registry_contains_chromatic_harmonica():
    assert PROFILES["chromatic_harmonica"] is ChromaticHarmonicaProfile


def test_pitch_range_is_c3_to_c7():
    profile = ChromaticHarmonicaProfile()
    fmin, fmax = profile.pitch_range_hz()
    assert fmin == librosa.note_to_hz("C3")
    assert fmax == librosa.note_to_hz("C7")


def test_detection_params_match_phase0_validated_values():
    profile = ChromaticHarmonicaProfile()
    params = profile.detection_params()
    assert params.onset_threshold == 0.6
    assert params.frame_threshold == 0.4
    assert params.minimum_note_length_ms == 100
    assert params.min_midi == 48  # C3
    assert params.max_midi == 96  # C7


def test_is_monophonic():
    assert ChromaticHarmonicaProfile.is_monophonic is True


def test_default_tab_for_note_is_none_for_any_profile():
    profile = ChromaticHarmonicaProfile()
    assert profile.tab_for_note(60) is None


def test_resolve_overlaps_keeps_non_overlapping_notes():
    profile = ChromaticHarmonicaProfile()
    events = [
        (0.0, 0.5, 60, 0.8, None),
        (0.5, 1.0, 62, 0.7, None),
    ]
    result = profile.resolve_overlaps(events)
    assert result == events


def test_resolve_overlaps_drops_quieter_overlapping_note():
    profile = ChromaticHarmonicaProfile()
    loud = (0.0, 1.0, 60, 0.9, None)
    quiet_overlap = (0.2, 0.6, 67, 0.3, None)  # an overtone bleeding through
    events = [loud, quiet_overlap]

    result = profile.resolve_overlaps(events)

    assert result == [loud]


def test_resolve_overlaps_keeps_louder_later_note_when_it_overlaps():
    profile = ChromaticHarmonicaProfile()
    quiet_first = (0.0, 1.0, 60, 0.2, None)
    loud_overlap = (0.3, 0.8, 64, 0.9, None)
    events = [quiet_first, loud_overlap]

    result = profile.resolve_overlaps(events)

    assert result == [loud_overlap]


def test_resolve_overlaps_handles_unsorted_input():
    profile = ChromaticHarmonicaProfile()
    second = (0.5, 1.0, 62, 0.7, None)
    first = (0.0, 0.5, 60, 0.8, None)

    result = profile.resolve_overlaps([second, first])

    assert result == [first, second]
