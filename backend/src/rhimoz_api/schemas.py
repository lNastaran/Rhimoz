from typing import TYPE_CHECKING, Iterable

from pydantic import BaseModel

if TYPE_CHECKING:
    from rhimoz.notes.model import TranscribedNote


class TabAnnotationOut(BaseModel):
    label: str
    direction: str


class TranscribedNoteOut(BaseModel):
    start_s: float
    end_s: float
    midi_pitch: int
    amplitude: float
    tab: TabAnnotationOut | None = None


def notes_to_out(notes: "Iterable[TranscribedNote]") -> list[TranscribedNoteOut]:
    """Shared engine-dataclass -> API-schema conversion, used by both the
    /transcribe response and saved-transcription storage/retrieval, so the
    per-field copy (deliberately not passing engine dataclasses through to
    Pydantic models directly) only lives in one place."""
    return [
        TranscribedNoteOut(
            start_s=n.start_s,
            end_s=n.end_s,
            midi_pitch=n.midi_pitch,
            amplitude=n.amplitude,
            tab=TabAnnotationOut(label=n.tab.label, direction=n.tab.direction)
            if n.tab
            else None,
        )
        for n in notes
    ]


class TranscribeResponse(BaseModel):
    job_id: str
    instrument_name: str
    tempo_bpm: float | None
    notes: list[TranscribedNoteOut]
    # Inlined rather than only a URL: the frontend needs this immediately
    # for osmd.load(), and a second fetch would be pure latency since the
    # file is already in memory server-side.
    musicxml: str
    download_urls: dict[str, str]


class SaveTranscriptionRequest(BaseModel):
    job_id: str
    display_name: str
    composer: str | None = None


class SavedTranscriptionOut(BaseModel):
    id: str
    display_name: str
    composer: str | None = None
    instrument_name: str
    tempo_bpm: float | None
    created_at: str


class SavedTranscriptionDetailOut(SavedTranscriptionOut):
    musicxml: str
    notes: list[TranscribedNoteOut]


class PublicTranscriptionOut(BaseModel):
    """A row from the bundled public-domain set. Mirrors
    SavedTranscriptionOut (title plays the role of display_name) plus
    provenance, and has no owner."""

    id: str
    title: str
    composer: str | None = None
    instrument_name: str
    tempo_bpm: float | None
    source_url: str | None = None
    license: str | None = None
    created_at: str


class PublicTranscriptionDetailOut(PublicTranscriptionOut):
    musicxml: str
    notes: list[TranscribedNoteOut]


class SearchResultsOut(BaseModel):
    """Search hits split by source so the UI can render the user's own
    saved transcriptions and the bundled public-domain library as
    separate sections."""

    personal: list[SavedTranscriptionOut]
    public: list[PublicTranscriptionOut]
