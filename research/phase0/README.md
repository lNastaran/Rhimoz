# Phase 0: pitch-detection feasibility validation

Throwaway research code (not part of the product) that answers one
question before committing to the Phase 1 architecture: is an existing
pitch-detection model accurate/fast enough on real harmonica-family audio?

Findings: see [`PHASE0_FINDINGS.md`](PHASE0_FINDINGS.md).

## Setup

Requires Python 3.11 specifically — TensorFlow/Basic Pitch don't yet support
newer Python releases. Uses [`uv`](https://github.com/astral-sh/uv) to manage
the interpreter so this doesn't depend on Homebrew permissions.

```sh
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

`setuptools<81` is pinned because `resampy` (a `librosa` dependency) still
imports the deprecated `pkg_resources` API, which setuptools removed in 81.

## Run

```sh
.venv/bin/python scripts/validate_pitch_detection.py
```

Writes raw results to `results/phase0_raw_results.json`. Test audio and
licensing are in `samples/ATTRIBUTION.md`.
