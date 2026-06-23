import { useState, type FormEvent } from 'react';
import { useAuth } from '../auth/AuthContext';
import { saveTranscription } from '../api/saved';

interface SaveTranscriptionFormProps {
  jobId: string;
  defaultName: string;
}

export function SaveTranscriptionForm({ jobId, defaultName }: SaveTranscriptionFormProps) {
  const { session } = useAuth();
  const [displayName, setDisplayName] = useState(defaultName);
  const [composer, setComposer] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Guest transcription works with no login - saving is the one
  // login-gated action, so this renders nothing at all while logged out
  // rather than a disabled control with no way to act on it.
  if (!session) return null;
  // Captured as a local const, not read as session.access_token inside
  // handleSubmit below - TS doesn't carry the !session narrowing above
  // into a nested function body, so it'd otherwise still see
  // session.access_token as possibly-null there.
  const token = session.access_token;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setSaved(false);
    setError(null);
    try {
      await saveTranscription(token, jobId, displayName, composer.trim() || undefined);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
      <input
        type="text"
        aria-label="Title"
        placeholder="Title"
        value={displayName}
        onChange={(event) => {
          setDisplayName(event.target.value);
          setSaved(false);
        }}
        required
      />
      <input
        type="text"
        aria-label="Composer"
        placeholder="Composer (optional)"
        value={composer}
        onChange={(event) => {
          setComposer(event.target.value);
          setSaved(false);
        }}
      />
      <button type="submit" disabled={isSaving}>
        {isSaving ? 'Saving...' : 'Save'}
      </button>
      {saved && <span>Saved.</span>}
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
