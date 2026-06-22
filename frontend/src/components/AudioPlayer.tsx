import type { RefObject } from 'react';

interface AudioPlayerProps {
  src: string;
  audioRef: RefObject<HTMLAudioElement | null>;
}

export function AudioPlayer({ src, audioRef }: AudioPlayerProps) {
  return <audio ref={audioRef} src={src} controls />;
}
