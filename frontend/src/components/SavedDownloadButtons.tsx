import { useState } from 'react';
import { downloadSavedFile } from '../api/saved';

interface SavedDownloadButtonsProps {
  token: string;
  id: string;
  displayName: string;
}

const KINDS = [
  { kind: 'pdf' as const, label: 'Download PDF' },
  { kind: 'musicxml' as const, label: 'Download MusicXML' },
  { kind: 'midi' as const, label: 'Download MIDI' },
];

/**
 * Buttons, not <a href> links like the unauthenticated DownloadButtons -
 * /saved/{id}/download/{kind} requires a Bearer token a plain browser
 * navigation can't attach, so each click fetches with auth and triggers
 * a blob-URL download instead (see api/saved.ts's downloadSavedFile()).
 */
export function SavedDownloadButtons({ token, id, displayName }: SavedDownloadButtonsProps) {
  const [pendingKind, setPendingKind] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload(kind: 'musicxml' | 'midi' | 'pdf') {
    setPendingKind(kind);
    setError(null);
    try {
      await downloadSavedFile(token, id, displayName, kind);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setPendingKind(null);
    }
  }

  return (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
      {KINDS.map(({ kind, label }) => (
        <button key={kind} onClick={() => handleDownload(kind)} disabled={pendingKind === kind}>
          {pendingKind === kind ? 'Downloading...' : label}
        </button>
      ))}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
