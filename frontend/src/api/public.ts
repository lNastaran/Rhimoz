import { apiFetch, downloadAuthedFile, KIND_TO_EXTENSION } from './client';
import type { PublicTranscriptionDetailOut } from './types';

export async function getPublic(
  token: string,
  id: string,
): Promise<PublicTranscriptionDetailOut> {
  const response = await apiFetch(`/public/${id}`, {}, token);
  return response.json();
}

export async function downloadPublicFile(
  token: string,
  id: string,
  title: string,
  kind: 'musicxml' | 'midi' | 'pdf',
): Promise<void> {
  await downloadAuthedFile(
    token,
    `/public/${id}/download/${kind}`,
    `${title}.${KIND_TO_EXTENSION[kind]}`,
  );
}
