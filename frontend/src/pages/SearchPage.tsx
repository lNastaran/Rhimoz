import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { searchTranscriptions } from '../api/search';
import type { SearchResults } from '../api/types';

export function SearchPage() {
  const { session, isLoading } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = session?.access_token;

  useEffect(() => {
    if (!token) return;
    const trimmed = query.trim();
    if (!trimmed) {
      setResults(null);
      setError(null);
      return;
    }
    let cancelled = false;
    // Debounce so we don't fire a request on every keystroke.
    const handle = setTimeout(() => {
      searchTranscriptions(token, trimmed)
        .then((res) => {
          if (!cancelled) setResults(res);
        })
        .catch((err) => {
          if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong');
        });
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [token, query]);

  if (isLoading) return null;
  if (!session) return <Navigate to="/login" replace />;

  const hasResults =
    results !== null && (results.personal.length > 0 || results.public.length > 0);

  return (
    <div>
      <h2>Search songs</h2>
      <input
        type="search"
        aria-label="Search songs"
        placeholder="Search by title or composer"
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setError(null);
        }}
        style={{ width: '100%', maxWidth: '24rem' }}
      />
      {error && <p role="alert">{error}</p>}

      {results !== null && !hasResults && <p>No matches.</p>}

      {results !== null && results.personal.length > 0 && (
        <section>
          <h3>Your transcriptions</h3>
          <ul>
            {results.personal.map((row) => (
              <li key={row.id}>
                <Link to={`/saved/${row.id}`}>{row.display_name}</Link>
                {row.composer && <span> by {row.composer}</span>}
                <span> ({row.instrument_name})</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {results !== null && results.public.length > 0 && (
        <section>
          <h3>Public-domain library</h3>
          <ul>
            {results.public.map((row) => (
              <li key={row.id}>
                <Link to={`/public/${row.id}`}>{row.title}</Link>
                {row.composer && <span> by {row.composer}</span>}
                <span> ({row.instrument_name})</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
