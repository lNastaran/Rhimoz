"""
Pitch/onset detection: runs Basic Pitch tuned by the given InstrumentProfile,
then resolves overlaps for monophonic instruments. Direct port of Phase 0's
validated run_basic_pitch() (research/phase0/scripts/validate_pitch_detection.py),
generalized to take its parameters from a profile instead of literals.
"""
from pathlib import Path

from basic_pitch.inference import predict

from rhimoz.instruments.profile import InstrumentProfile
from rhimoz.notes.model import NoteSequence, TranscribedNote


def detect_notes(audio_path: str | Path, profile: InstrumentProfile) -> NoteSequence:
    """Detect notes in the audio file using Basic Pitch, tuned by the
    given instrument profile. For monophonic instruments, overlapping
    detections (harmonic bleed-through, not real chords) are resolved via
    profile.resolve_overlaps()."""
    params = profile.detection_params()
    fmin, fmax = profile.pitch_range_hz()

    _, _, note_events = predict(
        str(audio_path),
        onset_threshold=params.onset_threshold,
        frame_threshold=params.frame_threshold,
        minimum_note_length=params.minimum_note_length_ms,
        minimum_frequency=fmin,
        maximum_frequency=fmax,
    )

    if profile.is_monophonic:
        note_events = profile.resolve_overlaps(note_events)

    notes = [
        TranscribedNote(
            start_s=float(start),
            end_s=float(end),
            midi_pitch=int(pitch),
            amplitude=float(amplitude),
        )
        for start, end, pitch, amplitude, _bends in note_events
    ]
    return NoteSequence(notes=notes, instrument_name=profile.name)
