import { useEffect, useRef, useState } from 'react';
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import { Link, Navigate, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { getSaved } from '../api/saved';
import type { SavedTranscriptionDetailOut } from '../api/types';
import { NotationViewer } from '../components/NotationViewer';
import { SavedDownloadButtons } from '../components/SavedDownloadButtons';

export function ReopenedTranscriptionPage() {
  const { session, isLoading: isAuthLoading } = useAuth();
  const { id } = useParams<{ id: string }>();
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);
  const [saved, setSaved] = useState<SavedTranscriptionDetailOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = session?.access_token;

  useEffect(() => {
    if (!token || !id) return;
    let cancelled = false;
    setSaved(null);
    setError(null);
    getSaved(token, id)
      .then((detail) => {
        if (!cancelled) setSaved(detail);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong');
      });
    return () => {
      cancelled = true;
    };
  }, [token, id]);

  if (isAuthLoading) return null;
  if (!session) return <Navigate to="/login" replace />;
  if (!id) return <Navigate to="/dashboard" replace />;
  // Re-derived (not reusing the optional `token` above) so it's a plain
  // string here, not string | undefined - avoids a non-null assertion at
  // the SavedDownloadButtons call site below.
  const accessToken = session.access_token;

  return (
    <div>
      <p>
        <Link to="/dashboard">Back to dashboard</Link>
      </p>
      {error && <p role="alert">{error}</p>}
      {saved && (
        <>
          <h2>{saved.display_name}</h2>
          {/* No AudioPlayer here, deliberately - original audio isn't
              persisted (see the Phase 5 plan's "File storage fork"
              section), only the notation and fresh regenerated
              downloads are available for a reopened transcription. */}
          <NotationViewer musicxml={saved.musicxml} notes={saved.notes} osmdRef={osmdRef} />
          <SavedDownloadButtons token={accessToken} id={saved.id} displayName={saved.display_name} />
        </>
      )}
    </div>
  );
}
