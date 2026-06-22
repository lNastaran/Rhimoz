import { useEffect, useRef, useState } from 'react';
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import { postTranscribe } from './api/transcribe';
import type { TranscribeResponse } from './api/types';
import { UploadForm } from './components/UploadForm';
import { NotationViewer } from './components/NotationViewer';
import { AudioPlayer } from './components/AudioPlayer';

function App() {
  const [response, setResponse] = useState<TranscribeResponse | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  async function handleUpload(file: File, instrument: string) {
    const result = await postTranscribe(file, instrument);
    setResponse(result);
    setAudioUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return URL.createObjectURL(file);
    });
  }

  // Revoke the object URL when the component unmounts, not just on re-upload.
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  return (
    <main>
      <h1>Rhimoz</h1>
      <UploadForm onSubmit={handleUpload} />
      {response && audioUrl && (
        <>
          <NotationViewer musicxml={response.musicxml} osmdRef={osmdRef} />
          <AudioPlayer src={audioUrl} audioRef={audioRef} />
        </>
      )}
    </main>
  );
}

export default App;
