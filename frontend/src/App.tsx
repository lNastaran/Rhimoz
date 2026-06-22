import { useRef, useState } from 'react';
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import { postTranscribe } from './api/transcribe';
import type { TranscribeResponse } from './api/types';
import { UploadForm } from './components/UploadForm';
import { NotationViewer } from './components/NotationViewer';

function App() {
  const [response, setResponse] = useState<TranscribeResponse | null>(null);
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);

  async function handleUpload(file: File, instrument: string) {
    const result = await postTranscribe(file, instrument);
    setResponse(result);
  }

  return (
    <main>
      <h1>Rhimoz</h1>
      <UploadForm onSubmit={handleUpload} />
      {response && <NotationViewer musicxml={response.musicxml} osmdRef={osmdRef} />}
    </main>
  );
}

export default App;
