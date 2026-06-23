import { useEffect, useRef, useState } from 'react';
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import { Link, Navigate, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { getSaved } from '../api/saved';
import { getPublic } from '../api/public';
import type { TranscribedNoteOut } from '../api/types';
import { NotationViewer } from '../components/NotationViewer';
import { SavedDownloadButtons } from '../components/SavedDownloadButtons';

// A reopened transcription, normalized across both sources so the view
// doesn't branch on display_name vs title below.
interface ReopenedDetail {
  id: string;
  title: string;
  composer: string | null;
  musicxml: string;
  notes: TranscribedNoteOut[];
}

interface ReopenedTranscriptionPageProps {
  source: 'saved' | 'public';
}

export function ReopenedTranscriptionPage({ source }: ReopenedTranscriptionPageProps) {
  const { session, isLoading: isAuthLoading } = useAuth();
  const { id } = useParams<{ id: string }>();
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);
  const [detail, setDetail] = useState<ReopenedDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = session?.access_token;

  useEffect(() => {
    if (!token || !id) return;
    let cancelled = false;
    setDetail(null);
    setError(null);
    const load =
      source === 'public'
        ? getPublic(token, id).then((d) => ({
            id: d.id,
            title: d.title,
            composer: d.composer,
            musicxml: d.musicxml,
            notes: d.notes,
          }))
        : getSaved(token, id).then((d) => ({
            id: d.id,
            title: d.display_name,
            composer: d.composer,
            musicxml: d.musicxml,
            notes: d.notes,
          }));
    load
      .then((normalized) => {
        if (!cancelled) setDetail(normalized);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong');
      });
    return () => {
      cancelled = true;
    };
  }, [token, id, source]);

  if (isAuthLoading) return null;
  if (!session) return <Navigate to="/login" replace />;
  if (!id) return <Navigate to="/dashboard" replace />;
  // Re-derived (not reusing the optional `token` above) so it's a plain
  // string here, not string | undefined - avoids a non-null assertion at
  // the SavedDownloadButtons call site below.
  const accessToken = session.access_token;
  const backTo = source === 'public' ? '/search' : '/dashboard';

  return (
    <div>
      <p>
        <Link to={backTo}>{source === 'public' ? 'Back to search' : 'Back to dashboard'}</Link>
      </p>
      {error && <p role="alert">{error}</p>}
      {detail && (
        <>
          <h2>{detail.title}</h2>
          {detail.composer && <p>by {detail.composer}</p>}
          {/* No AudioPlayer here, deliberately - original audio isn't
              persisted (see the Phase 5 plan's "File storage fork"
              section), only the notation and fresh regenerated
              downloads are available for a reopened transcription. */}
          <NotationViewer musicxml={detail.musicxml} notes={detail.notes} osmdRef={osmdRef} />
          <SavedDownloadButtons
            token={accessToken}
            id={detail.id}
            displayName={detail.title}
            source={source}
          />
        </>
      )}
    </div>
  );
}
