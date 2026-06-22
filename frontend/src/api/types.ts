// Mirrors backend/src/rhimoz_api/schemas.py

export interface TranscribedNoteOut {
  start_s: number;
  end_s: number;
  midi_pitch: number;
  amplitude: number;
}

export interface TranscribeResponse {
  job_id: string;
  instrument_name: string;
  tempo_bpm: number | null;
  notes: TranscribedNoteOut[];
  musicxml: string;
  download_urls: {
    musicxml: string;
    midi: string;
    pdf: string;
  };
}
