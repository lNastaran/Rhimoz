import { apiFetch, downloadAuthedFile, KIND_TO_EXTENSION } from './client';
import type { SavedTranscriptionDetailOut, SavedTranscriptionOut } from './types';

export async function saveTranscription(
  token: string,
  jobId: string,
  displayName: string,
  composer?: string,
): Promise<SavedTranscriptionOut> {
  const response = await apiFetch(
    '/saved',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: jobId,
        display_name: displayName,
        composer: composer || null,
      }),
    },
    token,
  );
  return response.json();
}

export async function listSaved(token: string): Promise<SavedTranscriptionOut[]> {
  const response = await apiFetch('/saved', {}, token);
  return response.json();
}

export async function getSaved(token: string, id: string): Promise<SavedTranscriptionDetailOut> {
  const response = await apiFetch(`/saved/${id}`, {}, token);
  return response.json();
}

export async function deleteSaved(token: string, id: string): Promise<void> {
  await apiFetch(`/saved/${id}`, { method: 'DELETE' }, token);
}

export async function downloadSavedFile(
  token: string,
  id: string,
  displayName: string,
  kind: 'musicxml' | 'midi' | 'pdf',
): Promise<void> {
  await downloadAuthedFile(
    token,
    `/saved/${id}/download/${kind}`,
    `${displayName}.${KIND_TO_EXTENSION[kind]}`,
  );
}
