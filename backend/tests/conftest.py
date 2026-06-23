import os
import uuid
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

from rhimoz_api.main import app

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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


async def _sign_up_throwaway_user() -> tuple[str, str]:
    """Returns (access_token, user_id) for a freshly signed-up test user.
    Used by both authenticated_client below and tests that need a SECOND,
    independent user (e.g. to check one user can't see another's rows).
    auto_refresh_token=False - this client is only used once and
    discarded, so there's nothing to refresh for and no reason to leave a
    background timer task running past this function returning."""
    from supabase import AsyncClientOptions, create_async_client

    client = await create_async_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_PUBLISHABLE_KEY"],
        AsyncClientOptions(auto_refresh_token=False),
    )
    email = f"rhimoz-test-{uuid.uuid4().hex[:12]}@gmail.com"
    result = await client.auth.sign_up({"email": email, "password": "test-password-123456"})
    return result.session.access_token, result.session.user.id


async def _delete_test_user(user_id: str) -> None:
    from supabase import AsyncClientOptions, create_async_client

    secret_key = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret_key:
        return
    admin_client = await create_async_client(
        os.environ["SUPABASE_URL"], secret_key, AsyncClientOptions(auto_refresh_token=False)
    )
    await admin_client.auth.admin.delete_user(user_id)


@pytest.fixture
async def authenticated_client():
    """A real sign-up per test, not faked via dependency_overrides -
    get_current_user() is trivial to stub out, but the saved-
    transcription routes' real work happens in Postgres under RLS
    (auth.uid() = user_id), and there's no local Postgres+PostgREST+RLS
    emulator in this project to fake that against. These tests are
    therefore genuinely integration tests against the real (free-tier)
    project, not unit tests - skipped if Supabase env vars aren't
    configured, mirroring phase0_sample_path's skip-if-missing pattern
    for the other external test resource (real sample audio) this suite
    already depends on.

    Function-scoped (a fresh user per test) rather than session-scoped:
    pytest-asyncio ties each test's event loop to the test function by
    default (asyncio_default_fixture_loop_scope = "function" above), so
    a session-scoped async fixture would need a session-scoped loop too -
    simpler to just sign up a new throwaway user per test than to fight
    that mismatch for a handful of fast, cheap signups."""
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_PUBLISHABLE_KEY"):
        pytest.skip("SUPABASE_URL/SUPABASE_PUBLISHABLE_KEY not configured")

    token, user_id = await _sign_up_throwaway_user()
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers) as c:
        yield c
    await _delete_test_user(user_id)
