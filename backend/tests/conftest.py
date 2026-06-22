from pathlib import Path

import httpx
import pytest

from rhimoz_api.main import app

PHASE0_SAMPLES_DIR = Path(__file__).resolve().parents[2] / "research" / "phase0" / "samples"


@pytest.fixture
def phase0_sample_path() -> Path:
    """Points at a real Phase 0 sample recording (read-only). Skips
    (rather than fails) if research/phase0/samples/ isn't present,
    mirroring engine/tests/conftest.py's fixture."""
    sample = PHASE0_SAMPLES_DIR / "marineband1.ogg"
    if not sample.exists():
        pytest.skip(f"Phase 0 sample audio not found at {sample}")
    return sample


@pytest.fixture
async def client():
    """httpx.AsyncClient over ASGITransport, NOT fastapi.testclient.TestClient.

    TestClient drives the app from a background thread (its "portal"),
    and verovio's PDF rendering crashes the whole process when invoked
    off the main thread (see routes/transcribe.py's docstring comment -
    confirmed by reproducing the crash with a plain threading.Thread and
    with a real uvicorn server using a sync `def` endpoint). ASGITransport
    runs the app directly on the calling coroutine's thread instead, which
    is what makes async def endpoints actually safe to test here.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
