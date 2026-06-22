import { useState } from 'react';
import { postTranscribe } from './api/transcribe';
import type { TranscribeResponse } from './api/types';
import { UploadForm } from './components/UploadForm';

function App() {
  // TODO: replaced by notation/audio/download components in later commits
  // of this phase - this placeholder exists to verify the upload ->
  // backend -> response wiring works end to end before building UI on top.
  const [response, setResponse] = useState<TranscribeResponse | null>(null);

  async function handleUpload(file: File, instrument: string) {
    const result = await postTranscribe(file, instrument);
    setResponse(result);
  }

  return (
    <main>
      <h1>Rhimoz</h1>
      <UploadForm onSubmit={handleUpload} />
      {response && (
        <p>
          Transcribed {response.notes.length} notes at {response.tempo_bpm?.toFixed(1)} BPM
        </p>
      )}
    </main>
  );
}

export default App;
