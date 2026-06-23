import { useEffect, useRef, useState } from 'react';
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import { postTranscribe } from '../api/transcribe';
import type { TranscribeResponse } from '../api/types';
import { UploadForm } from '../components/UploadForm';
import { NotationViewer } from '../components/NotationViewer';
import { AudioPlayer } from '../components/AudioPlayer';
import { DownloadButtons } from '../components/DownloadButtons';
import { SaveTranscriptionForm } from '../components/SaveTranscriptionForm';
import { useCursorSync } from '../hooks/useCursorSync';

export function TranscribePage() {
  const [response, setResponse] = useState<TranscribeResponse | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState('');
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  async function handleUpload(file: File, instrument: string) {
    const result = await postTranscribe(file, instrument);
    setResponse(result);
    setFileName(file.name.replace(/\.[^.]+$/, ''));
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

  useCursorSync({ audioRef, osmdRef, tempoBpm: response?.tempo_bpm ?? null });

  return (
    <>
      <UploadForm onSubmit={handleUpload} />
      {response && audioUrl && (
        <>
          <NotationViewer musicxml={response.musicxml} notes={response.notes} osmdRef={osmdRef} />
          <AudioPlayer src={audioUrl} audioRef={audioRef} />
          <DownloadButtons downloadUrls={response.download_urls} />
          <SaveTranscriptionForm jobId={response.job_id} defaultName={fileName} />
        </>
      )}
    </>
  );
}
