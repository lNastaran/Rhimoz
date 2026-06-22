import { useState, type FormEvent } from 'react';

interface UploadFormProps {
  onSubmit: (file: File, instrument: string) => Promise<void>;
}

export function UploadForm({ onSubmit }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit(file, 'chromatic_harmonica');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept="audio/*"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
      />
      <button type="submit" disabled={!file || isSubmitting}>
        {isSubmitting ? 'Transcribing...' : 'Transcribe'}
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
