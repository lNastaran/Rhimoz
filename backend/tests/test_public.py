import uuid

import pytest

from tests.conftest import delete_public_transcription, insert_public_transcription

pytestmark = pytest.mark.requires_supabase


async def test_get_public_requires_auth(client):
    resp = await client.get(f"/public/{uuid.uuid4()}")
    assert resp.status_code == 401


async def test_get_unknown_public_returns_404(authenticated_client):
    resp = await authenticated_client.get(f"/public/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_get_public_returns_detail(authenticated_client):
    public_id = await insert_public_transcription(title="Greensleeves Test")
    try:
        resp = await authenticated_client.get(f"/public/{public_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Greensleeves Test"
        assert body["license"] == "Public Domain"
        assert body["musicxml"]
        assert len(body["notes"]) == 1
    finally:
        await delete_public_transcription(public_id)


async def test_public_download_regenerates_files(authenticated_client):
    public_id = await insert_public_transcription()
    try:
        for kind in ("musicxml", "midi", "pdf"):
            resp = await authenticated_client.get(f"/public/{public_id}/download/{kind}")
            assert resp.status_code == 200, kind
            assert len(resp.content) > 0, kind

        bad = await authenticated_client.get(f"/public/{public_id}/download/nope")
        assert bad.status_code == 404
    finally:
        await delete_public_transcription(public_id)
