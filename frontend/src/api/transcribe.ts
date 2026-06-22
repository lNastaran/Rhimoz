import type { TranscribeResponse } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function postTranscribe(
  file: File,
  instrument = 'chromatic_harmonica',
): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('instrument', instrument);

  const response = await fetch(`${API_BASE_URL}/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Transcription failed with status ${response.status}`);
  }

  return response.json();
}

export function downloadUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
