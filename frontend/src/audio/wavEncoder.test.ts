import { describe, expect, test } from 'vitest';
import { encodeWavFromSamples } from './wavEncoder';

async function bytes(blob: Blob): Promise<DataView> {
  return new DataView(await blob.arrayBuffer());
}

function ascii(view: DataView, offset: number, length: number): string {
  let s = '';
  for (let i = 0; i < length; i += 1) s += String.fromCharCode(view.getUint8(offset + i));
  return s;
}

describe('encodeWavFromSamples', () => {
  test('writes a valid 16-bit mono PCM WAV header', async () => {
    const samples = new Float32Array([0, 0.5, -0.5, 1, -1]);
    const view = await bytes(encodeWavFromSamples(samples, 22050));

    expect(ascii(view, 0, 4)).toBe('RIFF');
    expect(ascii(view, 8, 4)).toBe('WAVE');
    expect(ascii(view, 12, 4)).toBe('fmt ');
    expect(view.getUint16(20, true)).toBe(1); // PCM
    expect(view.getUint16(22, true)).toBe(1); // mono
    expect(view.getUint32(24, true)).toBe(22050); // sample rate
    expect(view.getUint32(28, true)).toBe(22050 * 2); // byte rate
    expect(view.getUint16(32, true)).toBe(2); // block align
    expect(view.getUint16(34, true)).toBe(16); // bits per sample
    expect(ascii(view, 36, 4)).toBe('data');
    expect(view.getUint32(40, true)).toBe(samples.length * 2); // data byte count
  });

  test('total byte length is header + 2 bytes per sample', async () => {
    const samples = new Float32Array(100);
    const blob = encodeWavFromSamples(samples, 44100);
    expect(blob.size).toBe(44 + 100 * 2);
    expect(blob.type).toBe('audio/wav');
  });

  test('quantizes and clamps samples to signed 16-bit', async () => {
    const samples = new Float32Array([0, 1, -1, 2, -2]); // 2/-2 must clamp
    const view = await bytes(encodeWavFromSamples(samples, 8000));
    const data = 44;
    expect(view.getInt16(data + 0, true)).toBe(0);
    expect(view.getInt16(data + 2, true)).toBe(32767); // +1 -> max
    expect(view.getInt16(data + 4, true)).toBe(-32768); // -1 -> min
    expect(view.getInt16(data + 6, true)).toBe(32767); // +2 clamped to max
    expect(view.getInt16(data + 8, true)).toBe(-32768); // -2 clamped to min
  });

  test('riff chunk size equals 36 + data bytes', async () => {
    const samples = new Float32Array(10);
    const view = await bytes(encodeWavFromSamples(samples, 16000));
    expect(view.getUint32(4, true)).toBe(36 + 10 * 2);
  });
});
