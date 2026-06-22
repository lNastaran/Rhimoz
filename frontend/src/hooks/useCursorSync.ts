import { useEffect, useRef, type RefObject } from 'react';
import type { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import { CursorSync } from '../sync/cursorSync';

interface UseCursorSyncArgs {
  audioRef: RefObject<HTMLAudioElement | null>;
  osmdRef: RefObject<OpenSheetMusicDisplay | null>;
  tempoBpm: number | null;
}

/**
 * Thin React glue around CursorSync. Mutating a ref's .current (as
 * NotationViewer does once OSMD finishes loading) doesn't trigger a
 * re-render, so this can't simply depend on osmdRef.current in a
 * dependency array - that would freeze at whatever its value was when
 * the effect last ran, almost always null. Instead, CursorSync is
 * constructed lazily on the first timeupdate/seeking event after osmd
 * becomes available, by which point the ref has actually been set.
 */
export function useCursorSync({ audioRef, osmdRef, tempoBpm }: UseCursorSyncArgs) {
  const syncRef = useRef<CursorSync | null>(null);

  useEffect(() => {
    const audioEl = audioRef.current;
    if (!audioEl) return;

    function handleSync() {
      if (!syncRef.current) {
        if (!osmdRef.current || !tempoBpm) return;
        syncRef.current = new CursorSync(osmdRef.current.cursor, tempoBpm);
      }
      syncRef.current.syncTo(audioEl!.currentTime);
    }

    audioEl.addEventListener('timeupdate', handleSync);
    audioEl.addEventListener('seeking', handleSync);
    return () => {
      audioEl.removeEventListener('timeupdate', handleSync);
      audioEl.removeEventListener('seeking', handleSync);
      syncRef.current = null;
    };
  }, [audioRef, osmdRef, tempoBpm]);
}
