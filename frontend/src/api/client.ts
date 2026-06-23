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
