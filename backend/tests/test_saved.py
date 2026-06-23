import os
import uuid

import pytest

from rhimoz_api.auth import get_user_scoped_client
from tests.conftest import _delete_test_user, _sign_up_throwaway_user

pytestmark = pytest.mark.requires_supabase


async def test_save_requires_auth(client):
    resp = await client.post("/saved", json={"job_id": "x", "display_name": "n"})
    assert resp.status_code == 401


async def test_list_requires_auth(client):
    resp = await client.get("/saved")
    assert resp.status_code == 401


async def test_save_unknown_job_returns_404(authenticated_client):
    resp = await authenticated_client.post(
        "/saved", json={"job_id": "does-not-exist", "display_name": "n"}
    )
    assert resp.status_code == 404


async def test_delete_unknown_id_returns_404(authenticated_client):
    resp = await authenticated_client.delete(f"/saved/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_save_list_get_delete_round_trip(authenticated_client, phase0_sample_path):
    with open(phase0_sample_path, "rb") as f:
        transcribe_resp = await authenticated_client.post(
            "/transcribe", files={"file": (phase0_sample_path.name, f, "audio/ogg")}
        )
    assert transcribe_resp.status_code == 200
    job_id = transcribe_resp.json()["job_id"]

    save_resp = await authenticated_client.post(
        "/saved",
        json={"job_id": job_id, "display_name": "Round trip test", "composer": "J. S. Test"},
    )
    assert save_resp.status_code == 200
    saved_id = save_resp.json()["id"]
    assert save_resp.json()["composer"] == "J. S. Test"

    list_resp = await authenticated_client.get("/saved")
    assert list_resp.status_code == 200
    listed = next(row for row in list_resp.json() if row["id"] == saved_id)
    assert listed["composer"] == "J. S. Test"

    detail_resp = await authenticated_client.get(f"/saved/{saved_id}")
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["composer"] == "J. S. Test"
    assert body["musicxml"]
    assert len(body["notes"]) > 0

    delete_resp = await authenticated_client.delete(f"/saved/{saved_id}")
    assert delete_resp.status_code == 204

    after_resp = await authenticated_client.get(f"/saved/{saved_id}")
    assert after_resp.status_code == 404


async def test_cannot_see_or_modify_another_users_saved_transcription(authenticated_client):
    other_token, other_user_id = await _sign_up_throwaway_user()
    other_db = await get_user_scoped_client(other_token)
    insert_result = await (
        other_db.table("saved_transcriptions")
        .insert(
            {
                "user_id": other_user_id,
                "display_name": "Not yours",
                "instrument_name": "chromatic_harmonica",
                "musicxml": "<score-partwise/>",
                "notes_json": [],
            }
        )
        .select("id")
        .execute()
    )
    other_saved_id = insert_result.data[0]["id"]

    try:
        list_resp = await authenticated_client.get("/saved")
        assert all(row["id"] != other_saved_id for row in list_resp.json())

        get_resp = await authenticated_client.get(f"/saved/{other_saved_id}")
        assert get_resp.status_code == 404

        delete_resp = await authenticated_client.delete(f"/saved/{other_saved_id}")
        assert delete_resp.status_code == 404
    finally:
        await other_db.table("saved_transcriptions").delete().eq("id", other_saved_id).execute()
        await _delete_test_user(other_user_id)
