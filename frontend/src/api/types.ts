// Mirrors backend/src/rhimoz_api/schemas.py

export interface TabAnnotationOut {
  label: string;
  direction: string;
}

export interface TranscribedNoteOut {
  start_s: number;
  end_s: number;
  midi_pitch: number;
  amplitude: number;
  tab: TabAnnotationOut | null;
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

export interface SavedTranscriptionOut {
  id: string;
  display_name: string;
  instrument_name: string;
  tempo_bpm: number | null;
  created_at: string;
}

export interface SavedTranscriptionDetailOut extends SavedTranscriptionOut {
  musicxml: string;
  notes: TranscribedNoteOut[];
}
