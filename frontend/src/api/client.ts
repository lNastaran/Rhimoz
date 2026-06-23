export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

/**
 * Shared fetch wrapper: builds the full URL, optionally attaches a Bearer
 * token, and throws with the backend's error detail on a non-OK response -
 * the one place this logic lives instead of being copied into every API
 * module (transcribe.ts, saved.ts, ...).
 */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed with status ${response.status}`);
  }
  return response;
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export const KIND_TO_EXTENSION = { musicxml: 'musicxml', midi: 'mid', pdf: 'pdf' } as const;

/**
 * Fetch an authenticated file (saved or public transcription download) and
 * trigger a browser download via a throwaway object URL. Shared by saved.ts
 * and public.ts: unlike DownloadButtons' plain <a href> links (which work
 * because /jobs/.../download is unauthenticated), these endpoints require a
 * Bearer token a plain navigation can't attach.
 */
export async function downloadAuthedFile(
  token: string,
  path: string,
  filename: string,
): Promise<void> {
  const response = await apiFetch(path, {}, token);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  link.click();
  // Revoking immediately after click() can race the browser's download
  // handoff in some browsers (the blob isn't necessarily read yet) - a
  // short delay is the standard workaround for this exact gotcha.
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}
