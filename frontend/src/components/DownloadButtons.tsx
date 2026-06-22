import { downloadUrl } from '../api/transcribe';
import type { TranscribeResponse } from '../api/types';

interface DownloadButtonsProps {
  downloadUrls: TranscribeResponse['download_urls'];
}

export function DownloadButtons({ downloadUrls }: DownloadButtonsProps) {
  return (
    <div>
      <a href={downloadUrl(downloadUrls.pdf)} download>
        Download PDF
      </a>
      <a href={downloadUrl(downloadUrls.musicxml)} download>
        Download MusicXML
      </a>
      <a href={downloadUrl(downloadUrls.midi)} download>
        Download MIDI
      </a>
    </div>
  );
}
