import pytest

pytestmark = pytest.mark.integration


async def test_transcribe_endpoint_returns_expected_shape(client, phase0_sample_path):
    with open(phase0_sample_path, "rb") as f:
        resp = await client.post(
            "/transcribe", files={"file": (phase0_sample_path.name, f, "audio/ogg")}
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["instrument_name"] == "chromatic_harmonica"
    assert body["tempo_bpm"] is not None
    assert len(body["notes"]) > 0
    assert "start_s" in body["notes"][0]
    assert "<score-partwise" in body["musicxml"]
    assert set(body["download_urls"]) == {"musicxml", "midi", "pdf"}


async def test_transcribe_rejects_unknown_instrument(client, phase0_sample_path):
    with open(phase0_sample_path, "rb") as f:
        resp = await client.post(
            "/transcribe",
            data={"instrument": "bagpipes"},
            files={"file": (phase0_sample_path.name, f, "audio/ogg")},
        )
    assert resp.status_code == 400


async def test_transcribe_rejects_unsupported_content_type(client):
    resp = await client.post(
        "/transcribe", files={"file": ("not_audio.txt", b"hello", "text/plain")}
    )
    assert resp.status_code == 415
