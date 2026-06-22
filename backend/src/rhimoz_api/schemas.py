from pydantic import BaseModel


class TranscribedNoteOut(BaseModel):
    start_s: float
    end_s: float
    midi_pitch: int
    amplitude: float


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
