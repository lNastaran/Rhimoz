// Encode decoded PCM audio into a 16-bit mono WAV blob.
//
// The mic capture path records via MediaRecorder (webm/opus) and decodes it
// to PCM in the browser with AudioContext.decodeAudioData. The backend can
// only decode WAV without ffmpeg (see backend transcribe route), so we
// re-encode that PCM to WAV here before upload. Mono keeps the upload small;
// Basic Pitch is monophonic for harmonica anyway and resamples internally,
// so the source sample rate is preserved as-is.

const BYTES_PER_SAMPLE = 2; // 16-bit PCM
const WAV_HEADER_BYTES = 44;

/** Average all channels of an AudioBuffer into a single mono Float32 track. */
function downmixToMono(audioBuffer: AudioBuffer): Float32Array {
  const { numberOfChannels, length } = audioBuffer;
  if (numberOfChannels === 1) return audioBuffer.getChannelData(0);

  const mono = new Float32Array(length);
  for (let channel = 0; channel < numberOfChannels; channel += 1) {
    const data = audioBuffer.getChannelData(channel);
    for (let i = 0; i < length; i += 1) mono[i] += data[i];
  }
  for (let i = 0; i < length; i += 1) mono[i] /= numberOfChannels;
  return mono;
}

function writeAscii(view: DataView, offset: number, text: string): void {
  for (let i = 0; i < text.length; i += 1) view.setUint8(offset + i, text.charCodeAt(i));
}

/**
 * Encode a Float32 mono signal as a 16-bit PCM WAV blob (audio/wav).
 * Exposed separately from encodeWav so the pure header/sample math can be
 * unit tested without constructing a real AudioBuffer.
 */
export function encodeWavFromSamples(samples: Float32Array, sampleRate: number): Blob {
  const dataBytes = samples.length * BYTES_PER_SAMPLE;
  const buffer = new ArrayBuffer(WAV_HEADER_BYTES + dataBytes);
  const view = new DataView(buffer);

  // RIFF chunk descriptor
  writeAscii(view, 0, 'RIFF');
  view.setUint32(4, WAV_HEADER_BYTES - 8 + dataBytes, true); // file size minus RIFF+size fields
  writeAscii(view, 8, 'WAVE');

  // "fmt " sub-chunk (PCM)
  writeAscii(view, 12, 'fmt ');
  view.setUint32(16, 16, true); // sub-chunk size for PCM
  view.setUint16(20, 1, true); // audio format 1 = PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * BYTES_PER_SAMPLE, true); // byte rate (mono, 16-bit)
  view.setUint16(32, BYTES_PER_SAMPLE, true); // block align
  view.setUint16(34, 16, true); // bits per sample

  // "data" sub-chunk
  writeAscii(view, 36, 'data');
  view.setUint32(40, dataBytes, true);

  let offset = WAV_HEADER_BYTES;
  for (let i = 0; i < samples.length; i += 1) {
    // clamp to [-1, 1] then scale to signed 16-bit
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    const pcm = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
    view.setInt16(offset, pcm, true);
    offset += BYTES_PER_SAMPLE;
  }

  return new Blob([view], { type: 'audio/wav' });
}

/** Encode a decoded AudioBuffer (any channel count) as a mono 16-bit WAV blob. */
export function encodeWav(audioBuffer: AudioBuffer): Blob {
  return encodeWavFromSamples(downmixToMono(audioBuffer), audioBuffer.sampleRate);
}
