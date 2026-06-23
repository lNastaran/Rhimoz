import uuid

import httpx
import pytest

from rhimoz_api.auth import get_user_scoped_client
from rhimoz_api.main import app
from tests.conftest import (
    _delete_test_user,
    _sign_up_throwaway_user,
    delete_public_transcription,
    insert_public_transcription,
)

pytestmark = pytest.mark.requires_supabase


async def test_search_requires_auth(client):
    resp = await client.get("/search?q=anything")
    assert resp.status_code == 401


async def test_blank_query_returns_empty(authenticated_client):
    resp = await authenticated_client.get("/search?q=%20")
    assert resp.status_code == 200
    assert resp.json() == {"personal": [], "public": []}


async def test_search_handles_reserved_grammar_chars(authenticated_client):
    # A query with parentheses/commas must be treated as literal text, not
    # as PostgREST or=() grammar. Regression: the bundled composer is
    # literally "Traditional (...)", so "(Reserved)" must match it.
    public_id = await insert_public_transcription(
        title="Reserved Chars Tune", composer="Traditional (Reserved), Arr."
    )
    try:
        resp = await authenticated_client.get("/search?q=(Reserved),")
        assert resp.status_code == 200
        assert any(row["id"] == public_id for row in resp.json()["public"])
    finally:
        await delete_public_transcription(public_id)


async def _insert_saved(token: str, user_id: str, display_name: str, composer=None) -> str:
    db = await get_user_scoped_client(token)
    result = await (
        db.table("saved_transcriptions")
        .insert(
            {
                "user_id": user_id,
                "display_name": display_name,
                "composer": composer,
                "instrument_name": "chromatic_harmonica",
                "musicxml": "<score-partwise/>",
                "notes_json": [],
            }
        )
        .select("id")
        .execute()
    )
    return result.data[0]["id"]


async def test_search_matches_own_and_public_but_not_others():
    # A search term unique to this test run, so matches are unambiguous.
    tag = uuid.uuid4().hex[:8]

    token, user_id = await _sign_up_throwaway_user()
    other_token, other_user_id = await _sign_up_throwaway_user()

    mine_id = await _insert_saved(token, user_id, f"My Song {tag}")
    # Same user, matched via composer rather than title.
    mine_by_composer_id = await _insert_saved(
        token, user_id, "Untitled", composer=f"Composer {tag}"
    )
    others_id = await _insert_saved(other_token, other_user_id, f"Their Song {tag}")
    public_id = await insert_public_transcription(title=f"Public Song {tag}")

    headers = {"Authorization": f"Bearer {token}"}
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", headers=headers
        ) as c:
            resp = await c.get(f"/search?q={tag}")
            assert resp.status_code == 200
            body = resp.json()

            personal_ids = {row["id"] for row in body["personal"]}
            public_ids = {row["id"] for row in body["public"]}

            assert mine_id in personal_ids
            assert mine_by_composer_id in personal_ids  # matched on composer
            assert public_id in public_ids
            # RLS must keep the other user's private row out of the results.
            assert others_id not in personal_ids
    finally:
        own_db = await get_user_scoped_client(token)
        await own_db.table("saved_transcriptions").delete().eq("id", mine_id).execute()
        await own_db.table("saved_transcriptions").delete().eq(
            "id", mine_by_composer_id
        ).execute()
        other_db = await get_user_scoped_client(other_token)
        await other_db.table("saved_transcriptions").delete().eq("id", others_id).execute()
        await delete_public_transcription(public_id)
        await _delete_test_user(user_id)
        await _delete_test_user(other_user_id)
