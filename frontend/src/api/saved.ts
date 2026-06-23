import { apiFetch } from './client';
import type { SavedTranscriptionDetailOut, SavedTranscriptionOut } from './types';

export async function saveTranscription(
  token: string,
  jobId: string,
  displayName: string,
): Promise<SavedTranscriptionOut> {
  const response = await apiFetch(
    '/saved',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, display_name: displayName }),
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

const KIND_TO_EXTENSION = { musicxml: 'musicxml', midi: 'mid', pdf: 'pdf' } as const;

/**
 * Unlike DownloadButtons' plain <a href> links (which work because
 * /jobs/.../download is unauthenticated), /saved/{id}/download/{kind}
 * requires a Bearer token a browser navigation can't attach - so this
 * fetches the file with auth, then triggers a download via a throwaway
 * object URL instead of returning a plain href.
 */
export async function downloadSavedFile(
  token: string,
  id: string,
  displayName: string,
  kind: 'musicxml' | 'midi' | 'pdf',
): Promise<void> {
  const response = await apiFetch(`/saved/${id}/download/${kind}`, {}, token);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = `${displayName}.${KIND_TO_EXTENSION[kind]}`;
  link.click();
  // Revoking immediately after click() can race the browser's download
  // handoff in some browsers (the blob isn't necessarily read yet) - a
  // short delay is the standard workaround for this exact gotcha.
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}
