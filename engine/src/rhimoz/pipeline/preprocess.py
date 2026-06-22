"""
Audio loading and normalization, the first pipeline stage.
"""
from pathlib import Path

import librosa
import numpy as np

# Basic Pitch resamples to 22050 Hz internally regardless of input rate, so
# loading at that rate up front avoids resampling twice.
BASIC_PITCH_SAMPLE_RATE = 22050


def load_audio(
    path: str | Path, target_sr: int = BASIC_PITCH_SAMPLE_RATE
) -> tuple[np.ndarray, int]:
    """Load an audio file as mono float audio at target_sr."""
    y, sr = librosa.load(str(path), sr=target_sr, mono=True)
    return y, sr


def normalize_audio(y: np.ndarray) -> np.ndarray:
    """Peak-normalize so quiet or loud uploads don't shift onset/frame
    threshold behavior in the detection stage. Silent input (all zeros) is
    returned unchanged rather than dividing by zero."""
    peak = np.max(np.abs(y))
    if peak == 0:
        return y
    return y / peak
