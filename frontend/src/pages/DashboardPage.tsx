import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { deleteSaved, listSaved } from '../api/saved';
import type { SavedTranscriptionOut } from '../api/types';

export function DashboardPage() {
  const { session, isLoading, signOut } = useAuth();
  const [saved, setSaved] = useState<SavedTranscriptionOut[]>([]);
  const [isLoadingSaved, setIsLoadingSaved] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const token = session?.access_token;

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    listSaved(token)
      .then((rows) => {
        if (!cancelled) setSaved(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong');
      })
      .finally(() => {
        if (!cancelled) setIsLoadingSaved(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleDelete(id: string) {
    if (!token) return;
    setDeletingId(id);
    try {
      await deleteSaved(token, id);
      setSaved((rows) => rows.filter((row) => row.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) return null;
  if (!session) return <Navigate to="/login" replace />;

  return (
    <div>
      <p>Logged in as {session.user.email}.</p>
      <button onClick={() => void signOut()}>Log out</button>

      <h2>Saved transcriptions</h2>
      {error && <p role="alert">{error}</p>}
      {isLoadingSaved ? (
        <p>Loading...</p>
      ) : saved.length === 0 ? (
        <p>No saved transcriptions yet.</p>
      ) : (
        <ul>
          {saved.map((row) => (
            <li key={row.id} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Link to={`/saved/${row.id}`}>{row.display_name}</Link>
              <span>({row.instrument_name})</span>
              <button onClick={() => handleDelete(row.id)} disabled={deletingId === row.id}>
                {deletingId === row.id ? 'Deleting...' : 'Delete'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
