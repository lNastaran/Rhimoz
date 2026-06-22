import pytest

pytestmark = pytest.mark.integration


async def test_download_endpoints_serve_real_files(client, phase0_sample_path):
    with open(phase0_sample_path, "rb") as f:
        resp = await client.post(
            "/transcribe", files={"file": (phase0_sample_path.name, f, "audio/ogg")}
        )
    job_id = resp.json()["job_id"]

    pdf_resp = await client.get(f"/jobs/{job_id}/download/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content[:4] == b"%PDF"

    midi_resp = await client.get(f"/jobs/{job_id}/download/midi")
    assert midi_resp.status_code == 200
    assert len(midi_resp.content) > 0

    musicxml_resp = await client.get(f"/jobs/{job_id}/download/musicxml")
    assert musicxml_resp.status_code == 200
    assert b"<score-partwise" in musicxml_resp.content


async def test_download_unknown_job_returns_404(client):
    resp = await client.get("/jobs/does-not-exist/download/pdf")
    assert resp.status_code == 404


async def test_download_unknown_kind_returns_404(client, phase0_sample_path):
    with open(phase0_sample_path, "rb") as f:
        resp = await client.post(
            "/transcribe", files={"file": (phase0_sample_path.name, f, "audio/ogg")}
        )
    job_id = resp.json()["job_id"]

    resp = await client.get(f"/jobs/{job_id}/download/wav")
    assert resp.status_code == 404
