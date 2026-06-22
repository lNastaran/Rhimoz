import numpy as np

from rhimoz.pipeline.preprocess import normalize_audio


def test_normalize_audio_scales_peak_to_one():
    y = np.array([0.0, 0.25, -0.5, 0.1])
    result = normalize_audio(y)
    assert np.isclose(np.max(np.abs(result)), 1.0)


def test_normalize_audio_preserves_relative_shape():
    y = np.array([0.0, 0.25, -0.5, 0.1])
    result = normalize_audio(y)
    np.testing.assert_allclose(result, y / 0.5)


def test_normalize_audio_handles_silence_without_dividing_by_zero():
    y = np.zeros(10)
    result = normalize_audio(y)
    np.testing.assert_array_equal(result, y)
