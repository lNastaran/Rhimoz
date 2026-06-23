from fastapi import APIRouter, Depends, HTTPException

from rhimoz_api.auth import User, get_current_user, get_user_scoped_client
from rhimoz_api.jobs import JOBS
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
