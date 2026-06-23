"""Shared on-demand re-render of a stored transcription's downloads.

Both saved (per-user) and public (bundled) transcriptions store MusicXML +
note JSON and regenerate MIDI/PDF/MusicXML on demand rather than persisting
the binaries (see the Phase 5 plan's "File storage fork"). This module
holds the row -> NoteSequence -> rendered file path logic so both routers
share one copy of the verovio/render path instead of duplicating it.
"""
import shutil
import uuid

from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from rhimoz.notes.model import NoteSequence, TabAnnotation, TranscribedNote
from rhimoz.transcribe import render_outputs

from rhimoz_api.jobs import JOBS_ROOT
from rhimoz_api.routes.downloads import KIND_TO_ATTR, MEDIA_TYPES


def note_sequence_from_row(row: dict) -> NoteSequence:
    """Reconstruct a NoteSequence from a stored row. Works for both the
    saved and public tables: both expose `notes` (notes_json aliased),
    `instrument_name`, and `tempo_bpm`."""
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


def render_download(row: dict, kind: str, background_tasks: BackgroundTasks) -> FileResponse:
    """Regenerate the requested download (musicxml/midi/pdf) from a stored
    row and return it as a FileResponse. Detection is skipped entirely
    (render_outputs(), not transcribe_file()); only the cheap export stages
    re-run. The temp output dir is cleaned up after the response is sent."""
    if kind not in KIND_TO_ATTR:
        raise HTTPException(404, f"Unknown download kind: {kind!r}")

    note_sequence = note_sequence_from_row(row)
    out_dir = JOBS_ROOT / f"reopened-{uuid.uuid4()}"
    transcription = render_outputs(note_sequence, out_dir, stem="transcription")
    background_tasks.add_task(shutil.rmtree, out_dir, ignore_errors=True)

    path = getattr(transcription, KIND_TO_ATTR[kind])
    return FileResponse(path, media_type=MEDIA_TYPES[kind], filename=path.name)
