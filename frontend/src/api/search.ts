import { apiFetch } from './client';
import type { SearchResults } from './types';

export async function searchTranscriptions(
  token: string,
  query: string,
): Promise<SearchResults> {
  const response = await apiFetch(`/search?q=${encodeURIComponent(query)}`, {}, token);
  return response.json();
}
