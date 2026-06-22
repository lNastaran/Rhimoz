"""
The one test that genuinely exercises Basic Pitch inference end to end.
Phase 0 (research/phase0/PHASE0_FINDINGS.md) already validated the
detection numbers on this exact file; this test re-checks the same
sanity bounds through the production pipeline rather than re-deriving them.
"""
import pytest

from rhimoz.instruments.harmonica import ChromaticHarmonicaProfile
from rhimoz.transcribe import transcribe_file

pytestmark = pytest.mark.integration


def test_transcribe_file_end_to_end(phase0_sample_path, tmp_path):
    profile = ChromaticHarmonicaProfile()

    result = transcribe_file(phase0_sample_path, profile, tmp_path)

    assert result.musicxml_path.exists() and result.musicxml_path.stat().st_size > 0
    assert result.midi_path.exists() and result.midi_path.stat().st_size > 0
    assert result.pdf_path.exists() and result.pdf_path.stat().st_size > 0
    with open(result.pdf_path, "rb") as f:
        assert f.read(4) == b"%PDF"

    notes = result.note_sequence.notes
    assert len(notes) > 0

    # Sanity bounds mirroring Phase 0's own checks, not exact-count
    # assertions: Basic Pitch isn't pinned to a fixed model version here,
    # and small note-count variation is expected, not a regression.
    duration_s = notes[-1].end_s
    notes_per_second = len(notes) / duration_s
    assert 1.0 <= notes_per_second <= 6.0

    params = profile.detection_params()
    assert all(params.min_midi <= n.midi_pitch <= params.max_midi for n in notes)

    # Monophonic filter + quantization together should never leave two
    # notes overlapping in time.
    assert all(notes[i + 1].start_s >= notes[i].end_s for i in range(len(notes) - 1))

    assert result.note_sequence.tempo_bpm is not None
