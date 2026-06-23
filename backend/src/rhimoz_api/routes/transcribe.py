import shutil
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from rhimoz.instruments import PROFILES
from rhimoz.transcribe import transcribe_file

from rhimoz_api.jobs import JOBS, JOBS_ROOT, JobRecord
from rhimoz_api.schemas import TabAnnotationOut, TranscribeResponse, TranscribedNoteOut

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp4",
    "audio/flac",
}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB, generous for a few minutes of audio


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    instrument: str = Form("chromatic_harmonica"),
) -> TranscribeResponse:
    # async def, not def: FastAPI/Starlette runs sync `def` endpoints in a
    # worker thread pool, but verovio's PDF rendering (inside
    # transcribe_file -> export_pdf) crashes the whole process when first
    # invoked off the main thread (confirmed by reproducing the crash with
    # a plain threading.Thread, no FastAPI involved - likely a CoreText
    # font-loading constraint on macOS). async def keeps this on the event
    # loop's thread instead. Tradeoff: transcribe_file() is a blocking,
    # CPU-bound call, so this blocks the event loop - and therefore all
    # other concurrent requests - for the duration of each transcription.
    # Acceptable for this phase's single-user local scope (Phase 0 found
    # Basic Pitch runs ~50-100x realtime, so this is typically under a
    # couple seconds); revisit if concurrent load ever matters.
    if instrument not in PROFILES:
        raise HTTPException(400, f"Unknown instrument profile: {instrument!r}")

    # Cheap first filter for obviously-wrong uploads (e.g. a .txt file).
    # Clients can lie about content_type, so this is not the real
    # gatekeeper - the try/except around transcribe_file() below is.
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, f"Unsupported content type: {file.content_type!r}")

    job_id = str(uuid.uuid4())
    job_dir = JOBS_ROOT / job_id
    job_dir.mkdir(parents=True)

    # Single try/finally around everything that touches job_dir, not just
    # the transcribe_file() call: an exception from the write loop itself
    # (e.g. a disk I/O error mid-upload) used to skip cleanup entirely and
    # leak the directory forever, since the old code only cleaned up on
    # the size-cap check and on transcribe_file() failure specifically.
    succeeded = False
    try:
        upload_path = job_dir / (file.filename or "upload")
        size = 0
        with upload_path.open("wb") as out:
            while chunk := file.file.read(1 << 20):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, "File too large")
                out.write(chunk)

        profile = PROFILES[instrument]()
        try:
            result = transcribe_file(upload_path, profile, job_dir)
        except Exception as exc:
            # soundfile/librosa raise on corrupt/unreadable audio. The
            # most likely cause is a bad upload, not a server bug, so
            # surface this as a client error rather than a raw 500.
            raise HTTPException(422, f"Could not transcribe audio: {exc}") from exc

        JOBS[job_id] = JobRecord(job_dir=job_dir, result=result)
        succeeded = True
    finally:
        # No JobRecord means the directory isn't reachable through any
        # API - clean it up now rather than letting it sit unused forever.
        if not succeeded:
            shutil.rmtree(job_dir, ignore_errors=True)

    return TranscribeResponse(
        job_id=job_id,
        instrument_name=result.note_sequence.instrument_name,
        tempo_bpm=result.note_sequence.tempo_bpm,
        notes=[
            TranscribedNoteOut(
                start_s=n.start_s,
                end_s=n.end_s,
                midi_pitch=n.midi_pitch,
                amplitude=n.amplitude,
                tab=TabAnnotationOut(label=n.tab.label, direction=n.tab.direction)
                if n.tab
                else None,
            )
            for n in result.note_sequence.notes
        ],
        musicxml=result.musicxml_path.read_text(),
        download_urls={
            "musicxml": f"/jobs/{job_id}/download/musicxml",
            "midi": f"/jobs/{job_id}/download/midi",
            "pdf": f"/jobs/{job_id}/download/pdf",
        },
    )
