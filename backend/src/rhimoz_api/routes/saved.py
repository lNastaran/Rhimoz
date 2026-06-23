import shutil
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from rhimoz.notes.model import NoteSequence, TabAnnotation, TranscribedNote
from rhimoz.transcribe import render_outputs

from rhimoz_api.auth import User, get_current_user, get_user_scoped_client
from rhimoz_api.jobs import JOBS, JOBS_ROOT
from rhimoz_api.routes.downloads import KIND_TO_ATTR, MEDIA_TYPES
from rhimoz_api.schemas import (
    SavedTranscriptionDetailOut,
    SavedTranscriptionOut,
    SaveTranscriptionRequest,
    notes_to_out,
)

router = APIRouter(prefix="/saved")

# Columns returned by the list endpoint - deliberately excludes musicxml/
# notes_json to keep the dashboard's list payload small; the detail
# endpoint fetches those separately only when a transcription is opened.
LIST_COLUMNS = "id, display_name, instrument_name, tempo_bpm, created_at"
# notes:notes_json - PostgREST's column-aliasing syntax, renaming the
# notes_json column to match SavedTranscriptionDetailOut's `notes` field.
DETAIL_COLUMNS = f"{LIST_COLUMNS}, musicxml, notes:notes_json"


@router.post("", response_model=SavedTranscriptionOut)
async def save_transcription(
    body: SaveTranscriptionRequest,
    user: User = Depends(get_current_user),
) -> SavedTranscriptionOut:
    job = JOBS.get(body.job_id)
    if job is None:
        raise HTTPException(404, f"Unknown job: {body.job_id!r}")

    notes = notes_to_out(job.result.note_sequence.notes)
    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("saved_transcriptions")
        .insert(
            {
                "user_id": user.id,
                "display_name": body.display_name,
                "instrument_name": job.result.note_sequence.instrument_name,
                "tempo_bpm": job.result.note_sequence.tempo_bpm,
                "musicxml": job.result.musicxml_path.read_text(),
                "notes_json": [n.model_dump() for n in notes],
            }
        )
        .select(LIST_COLUMNS)
        .execute()
    )
    return SavedTranscriptionOut(**result.data[0])


@router.get("", response_model=list[SavedTranscriptionOut])
async def list_saved_transcriptions(
    user: User = Depends(get_current_user),
) -> list[SavedTranscriptionOut]:
    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("saved_transcriptions")
        .select(LIST_COLUMNS)
        .order("created_at", desc=True)
        .execute()
    )
    return [SavedTranscriptionOut(**row) for row in result.data]


@router.get("/{saved_id}", response_model=SavedTranscriptionDetailOut)
async def get_saved_transcription(
    saved_id: str,
    user: User = Depends(get_current_user),
) -> SavedTranscriptionDetailOut:
    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("saved_transcriptions")
        .select(DETAIL_COLUMNS)
        .eq("id", saved_id)
        .execute()
    )
    # RLS already hides other users' rows, but a plain 404 here (rather
    # than the empty-list-passed-through-as-a-validation-error FastAPI
    # would otherwise produce) gives a clean, deliberate API contract for
    # "not found" regardless of why the row wasn't returned.
    if not result.data:
        raise HTTPException(404, f"Unknown saved transcription: {saved_id!r}")
    return SavedTranscriptionDetailOut(**result.data[0])


def _note_sequence_from_row(row: dict) -> NoteSequence:
    notes = [
        TranscribedNote(
            start_s=n["start_s"],
            end_s=n["end_s"],
            midi_pitch=n["midi_pitch"],
            amplitude=n["amplitude"],
            tab=TabAnnotation(**n["tab"]) if n.get("tab") else None,
        )
        for n in row["notes"]
    ]
    return NoteSequence(
        notes=notes,
        instrument_name=row["instrument_name"],
        tempo_bpm=row["tempo_bpm"],
        # beat_times_s isn't persisted - confirmed unused by export_musicxml/
        # export_pdf (only quantize_to_grid reads it), so losing it on
        # reopen doesn't affect regenerated output.
    )


@router.get("/{saved_id}/download/{kind}")
async def download_saved_transcription(
    saved_id: str,
    kind: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> FileResponse:
    """Regenerates MIDI/PDF/MusicXML on demand from the saved note data,
    rather than storing those binaries - see the Phase 5 plan's "File
    storage fork" section. Detection is skipped entirely (render_outputs(),
    not transcribe_file()); only the cheap export stages re-run."""
    if kind not in KIND_TO_ATTR:
        raise HTTPException(404, f"Unknown download kind: {kind!r}")

    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("saved_transcriptions")
        .select(DETAIL_COLUMNS)
        .eq("id", saved_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, f"Unknown saved transcription: {saved_id!r}")

    note_sequence = _note_sequence_from_row(result.data[0])
    out_dir = JOBS_ROOT / f"reopened-{uuid.uuid4()}"
    transcription = render_outputs(note_sequence, out_dir, stem="transcription")
    background_tasks.add_task(shutil.rmtree, out_dir, ignore_errors=True)

    path = getattr(transcription, KIND_TO_ATTR[kind])
    return FileResponse(path, media_type=MEDIA_TYPES[kind], filename=path.name)


@router.delete("/{saved_id}", status_code=204)
async def delete_saved_transcription(
    saved_id: str,
    user: User = Depends(get_current_user),
) -> None:
    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("saved_transcriptions")
        .delete()
        .eq("id", saved_id)
        .select(LIST_COLUMNS)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, f"Unknown saved transcription: {saved_id!r}")
