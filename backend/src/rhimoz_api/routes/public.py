"""Read-only access to the bundled public-domain set.

The public_transcriptions table is world-readable (RLS `using (true)`), so
these routes serve the same reopen + on-demand-download experience as
saved transcriptions, without ownership. Seeding is done out-of-band by
seed/seed_public_transcriptions.py with the secret key; there is
deliberately no write route here.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from rhimoz_api.auth import User, get_current_user, get_user_scoped_client
from rhimoz_api.render import render_download
from rhimoz_api.schemas import PublicTranscriptionDetailOut

router = APIRouter(prefix="/public")

LIST_COLUMNS = (
    "id, title, composer, instrument_name, tempo_bpm, source_url, license, created_at"
)
# notes:notes_json - PostgREST column aliasing, matching the `notes` field.
DETAIL_COLUMNS = f"{LIST_COLUMNS}, musicxml, notes:notes_json"


@router.get("/{public_id}", response_model=PublicTranscriptionDetailOut)
async def get_public_transcription(
    public_id: str,
    user: User = Depends(get_current_user),
) -> PublicTranscriptionDetailOut:
    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("public_transcriptions")
        .select(DETAIL_COLUMNS)
        .eq("id", public_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, f"Unknown public transcription: {public_id!r}")
    return PublicTranscriptionDetailOut(**result.data[0])


@router.get("/{public_id}/download/{kind}")
async def download_public_transcription(
    public_id: str,
    kind: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> FileResponse:
    """Regenerates MIDI/PDF/MusicXML on demand from the stored note data,
    same as the saved-transcription download path."""
    db = await get_user_scoped_client(user.token)
    result = await (
        db.table("public_transcriptions")
        .select(DETAIL_COLUMNS)
        .eq("id", public_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, f"Unknown public transcription: {public_id!r}")

    return render_download(result.data[0], kind, background_tasks)
