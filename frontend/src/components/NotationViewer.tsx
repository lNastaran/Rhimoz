import { useEffect, useRef, useState, type MutableRefObject } from 'react';
import { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';
import type { TranscribedNoteOut } from '../api/types';
import { extractNotePositions, type NotePosition } from '../notation/tabPositions';

interface NotationViewerProps {
  musicxml: string;
  notes: TranscribedNoteOut[];
  osmdRef: MutableRefObject<OpenSheetMusicDisplay | null>;
}

const RESIZE_DEBOUNCE_MS = 200;

function directionArrow(direction: string): string {
  return direction === 'blow' ? '↑' : '↓';
}

export function NotationViewer({ musicxml, notes, osmdRef }: NotationViewerProps) {
  // Two separate divs, not one: osmd.render() clears its ENTIRE container's
  // innerHTML on every call (not just its own previous content), which
  // silently deleted React's overlay label divs out from under it when
  // they lived inside the same element OSMD owned - React's virtual DOM
  // had no way to know an external library had removed them, so it never
  // recreated them on the next state update (caught by checking
  // container.children.length before/after osmd.render() in a real
  // browser - it dropped from 161 to 1). osmdContainerRef is OSMD's alone
  // to clear; overlayRef is a sibling React fully owns, positioned via the
  // shared parent's `position: relative`.
  const wrapperRef = useRef<HTMLDivElement>(null);
  const osmdContainerRef = useRef<HTMLDivElement>(null);
  const [positions, setPositions] = useState<NotePosition[]>([]);

  useEffect(() => {
    if (!osmdContainerRef.current || !wrapperRef.current) return;
    const osmdContainer = osmdContainerRef.current;
    const wrapper = wrapperRef.current;

    const osmd = new OpenSheetMusicDisplay(osmdContainer, {
      // Manual resize handling below, not autoResize: OSMD has no public
      // "render complete" event, so there's no reliable hook for "now go
      // recompute overlay positions" if its own internal resize handler
      // (which is protected, not callable from here) does the re-render.
      autoResize: false,
      followCursor: true,
    });
    osmdRef.current = osmd;

    // React StrictMode (dev only) double-invokes effects - mount, cleanup,
    // mount again - to surface exactly this kind of bug. Without this
    // guard, a deferred callback from the first effect run can fire after
    // its own cleanup already ran osmd.clear(), acting on a torn-down
    // instance (caught in Phase 2 by actually loading this in a browser,
    // not just building it - same guard reused here for the new resize
    // and position-recompute code paths too).
    let cancelled = false;
    let resizeTimeout: ReturnType<typeof setTimeout> | undefined;

    function recomputePositions() {
      if (cancelled || !osmd.IsReadyToRender()) return;
      // Position labels relative to the wrapper (the shared positioning
      // context), not osmdContainer - they're siblings, not parent/child.
      const wrapperRect = wrapper.getBoundingClientRect();
      setPositions(extractNotePositions(osmd, wrapperRect, notes.length));
    }

    function handleResize() {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (cancelled) return;
        osmd.render();
        recomputePositions();
      }, RESIZE_DEBOUNCE_MS);
    }

    osmd.load(musicxml).then(() => {
      if (cancelled) return;
      osmd.render();
      osmd.cursor.show();
      recomputePositions();
    });

    window.addEventListener('resize', handleResize);

    return () => {
      cancelled = true;
      clearTimeout(resizeTimeout);
      window.removeEventListener('resize', handleResize);
      osmd.clear();
      osmdRef.current = null;
    };
  }, [musicxml, notes, osmdRef]);

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div ref={osmdContainerRef} />
      {positions.map((pos, i) => {
        const tab = notes[i]?.tab;
        if (!tab) return null;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: pos.left,
              top: pos.top,
              transform: 'translateX(-50%)',
              fontSize: '0.85rem',
              fontWeight: 600,
              pointerEvents: 'none',
            }}
          >
            {tab.label}
            {directionArrow(tab.direction)}
          </div>
        );
      })}
    </div>
  );
}
