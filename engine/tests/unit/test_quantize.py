from rhimoz.notes.model import NoteSequence, TranscribedNote
from rhimoz.pipeline.quantize import (
    DEFAULT_FALLBACK_BPM,
    TempoEstimate,
    _resolve_bpm,
    quantize_to_grid,
)


def test_resolve_bpm_keeps_in_range_value():
    bpm, is_fallback = _resolve_bpm(96.0)
    assert bpm == 96.0
    assert is_fallback is False


def test_resolve_bpm_falls_back_when_too_low():
    bpm, is_fallback = _resolve_bpm(10.0)
    assert bpm == DEFAULT_FALLBACK_BPM
    assert is_fallback is True


def test_resolve_bpm_falls_back_when_too_high():
    bpm, is_fallback = _resolve_bpm(400.0)
    assert bpm == DEFAULT_FALLBACK_BPM
    assert is_fallback is True


def test_resolve_bpm_falls_back_when_missing():
    bpm, is_fallback = _resolve_bpm(None)
    assert bpm == DEFAULT_FALLBACK_BPM
    assert is_fallback is True


def test_quantize_to_grid_snaps_to_nearest_sixteenth_at_120bpm():
    # 120 BPM -> beat = 0.5s -> sixteenth-note grid step = 0.125s
    notes = [TranscribedNote(start_s=0.49, end_s=1.01, midi_pitch=60, amplitude=0.8)]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica")
    tempo = TempoEstimate(bpm=120.0, beat_times_s=[0.0, 0.5, 1.0], is_fallback=False)

    result = quantize_to_grid(seq, tempo)

    assert result.notes[0].start_s == 0.5
    assert result.notes[0].end_s == 1.0


def test_quantize_to_grid_propagates_tempo_metadata():
    notes = [TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=60, amplitude=0.8)]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica")
    tempo = TempoEstimate(bpm=96.0, beat_times_s=[0.0, 0.625], is_fallback=False)

    result = quantize_to_grid(seq, tempo)

    assert result.tempo_bpm == 96.0
    assert result.beat_times_s == [0.0, 0.625]
    assert result.instrument_name == "chromatic_harmonica"


def test_quantize_to_grid_never_produces_zero_or_negative_duration():
    # A very short note that snaps start and end to the same grid point
    # must still come out with a positive duration.
    notes = [TranscribedNote(start_s=0.50, end_s=0.52, midi_pitch=60, amplitude=0.8)]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica")
    tempo = TempoEstimate(bpm=120.0, beat_times_s=[], is_fallback=False)

    result = quantize_to_grid(seq, tempo)

    assert result.notes[0].end_s > result.notes[0].start_s


def test_quantize_to_grid_preserves_pitch_and_amplitude():
    notes = [TranscribedNote(start_s=0.49, end_s=1.01, midi_pitch=67, amplitude=0.42)]
    seq = NoteSequence(notes=notes, instrument_name="chromatic_harmonica")
    tempo = TempoEstimate(bpm=120.0, beat_times_s=[], is_fallback=False)

    result = quantize_to_grid(seq, tempo)

    assert result.notes[0].midi_pitch == 67
    assert result.notes[0].amplitude == 0.42
