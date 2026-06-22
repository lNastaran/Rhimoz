from pathlib import Path

import pytest

PHASE0_SAMPLES_DIR = Path(__file__).resolve().parents[2] / "research" / "phase0" / "samples"


@pytest.fixture
def phase0_sample_path() -> Path:
    """Points at a real Phase 0 sample recording (read-only). Skips
    (rather than fails) if research/phase0/samples/ isn't present, so the
    suite degrades gracefully for a checkout that doesn't have it."""
    sample = PHASE0_SAMPLES_DIR / "marineband1.ogg"
    if not sample.exists():
        pytest.skip(f"Phase 0 sample audio not found at {sample}")
    return sample
