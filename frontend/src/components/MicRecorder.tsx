import { useEffect, useRef, useState } from 'react';
import { encodeWav } from '../audio/wavEncoder';

interface MicRecorderProps {
  // Same shape as UploadForm's onSubmit, so TranscribePage.handleUpload is
  // reused unchanged: a recorded clip becomes a File and flows through the
  // exact same transcribe -> notation/tab/downloads/save path as an upload.
  onRecorded: (file: File, instrument: string) => Promise<void>;
}

type Status = 'idle' | 'recording' | 'processing';

const AudioCtx: typeof AudioContext | undefined =
  typeof window !== 'undefined'
    ? window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    : undefined;

const micSupported =
  typeof navigator !== 'undefined' &&
  !!navigator.mediaDevices?.getUserMedia &&
  typeof window !== 'undefined' &&
  typeof window.MediaRecorder !== 'undefined' &&
  !!AudioCtx;

export function MicRecorder({ onRecorded }: MicRecorderProps) {
  const [status, setStatus] = useState<Status>('idle');
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mimeTypeRef = useRef<string>('audio/webm');
  // recorder.onstop fires asynchronously, so a recording that's stopped by
  // unmount (below) would otherwise run setState/onRecorded after the
  // component is gone. This guards handleStopped against that.
  const mountedRef = useRef(true);

  function stopTracks() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function clearTimer() {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  // Stop the mic, the recorder, and any timer if the user navigates away
  // mid-recording. Set the flag back to true on (re)mount so React
  // StrictMode's mount/unmount/remount in dev doesn't leave it stuck false.
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearTimer();
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop();
      }
      stopTracks();
    };
  }, []);

  async function startRecording() {
    setError(null);
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      // NotAllowedError = permission denied; NotFoundError = no microphone.
      const name = err instanceof DOMException ? err.name : '';
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        setError('Microphone permission was denied. Allow mic access and try again.');
      } else if (name === 'NotFoundError') {
        setError('No microphone was found on this device.');
      } else {
        setError(err instanceof Error ? err.message : 'Could not access the microphone.');
      }
      return;
    }

    streamRef.current = stream;
    chunksRef.current = [];
    const recorder = new MediaRecorder(stream);
    recorderRef.current = recorder;
    // Capture the container type now rather than reading recorderRef back in
    // the async onstop handler.
    mimeTypeRef.current = recorder.mimeType || 'audio/webm';
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };
    recorder.onstop = () => void handleStopped();
    recorder.start();

    setSeconds(0);
    setStatus('recording');
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
  }

  function stopRecording() {
    clearTimer();
    // The actual work happens in recorder.onstop -> handleStopped, after the
    // final chunk is flushed.
    recorderRef.current?.stop();
  }

  async function handleStopped() {
    stopTracks();
    // Unmounted while the final chunk was flushing: don't touch state or
    // fire a transcribe request for a component that's gone.
    if (!mountedRef.current) return;
    setStatus('processing');
    try {
      const recorded = new Blob(chunksRef.current, { type: mimeTypeRef.current });
      if (recorded.size === 0) {
        throw new Error('Nothing was recorded. Try again and play closer to the mic.');
      }

      // Decode the browser's own webm/opus to PCM here, then re-encode as
      // WAV - the backend can't decode webm without ffmpeg, but WAV is fine.
      const audioCtx = new AudioCtx!();
      let audioBuffer: AudioBuffer;
      try {
        audioBuffer = await audioCtx.decodeAudioData(await recorded.arrayBuffer());
      } catch {
        // decodeAudioData throws an opaque DOMException for an empty or
        // too-short clip; give the user something actionable instead.
        throw new Error('Could not read the recording. Try a longer, louder clip.');
      } finally {
        void audioCtx.close();
      }

      const wav = encodeWav(audioBuffer);
      const file = new File([wav], 'Mic recording.wav', { type: 'audio/wav' });
      if (!mountedRef.current) return;
      await onRecorded(file, 'chromatic_harmonica');
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Could not process the recording.');
      }
    } finally {
      if (mountedRef.current) setStatus('idle');
    }
  }

  if (!micSupported) {
    return (
      <p>
        Recording from the microphone needs a secure context (it works on
        localhost; over the network it needs HTTPS) and a browser with
        microphone support.
      </p>
    );
  }

  return (
    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
      {status === 'recording' ? (
        <>
          <button type="button" onClick={stopRecording}>
            Stop recording
          </button>
          <span aria-live="polite">
            <span aria-hidden="true">&#9210;</span> Recording... {seconds}s
          </span>
        </>
      ) : (
        <button type="button" onClick={() => void startRecording()} disabled={status === 'processing'}>
          {status === 'processing' ? 'Transcribing...' : 'Record from microphone'}
        </button>
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
