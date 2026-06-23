import { apiFetch, apiUrl } from './client';
import type { TranscribeResponse } from './types';

export async function postTranscribe(
  file: File,
  instrument = 'chromatic_harmonica',
): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('instrument', instrument);

  const response = await apiFetch('/transcribe', { method: 'POST', body: formData });
  return response.json();
}

export function downloadUrl(path: string): string {
  return apiUrl(path);
}
