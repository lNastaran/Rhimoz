from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from rhimoz_api.jobs import JOBS

router = APIRouter()

KIND_TO_ATTR = {
    "musicxml": "musicxml_path",
    "midi": "midi_path",
    "pdf": "pdf_path",
}
MEDIA_TYPES = {
    "musicxml": "application/vnd.recordare.musicxml+xml",
    "midi": "audio/midi",
    "pdf": "application/pdf",
}


@router.get("/jobs/{job_id}/download/{kind}")
def download(job_id: str, kind: str) -> FileResponse:
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    if kind not in KIND_TO_ATTR:
        raise HTTPException(404, f"Unknown download kind: {kind!r}")

    path = getattr(JOBS[job_id].result, KIND_TO_ATTR[kind])
    return FileResponse(path, media_type=MEDIA_TYPES[kind], filename=path.name)
