import { useEffect, useRef, type MutableRefObject } from 'react';
import { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';

interface NotationViewerProps {
  musicxml: string;
  osmdRef: MutableRefObject<OpenSheetMusicDisplay | null>;
}

export function NotationViewer({ musicxml, osmdRef }: NotationViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const osmd = new OpenSheetMusicDisplay(containerRef.current, {
      autoResize: true,
      followCursor: true,
    });
    osmdRef.current = osmd;

    // React StrictMode (dev only) double-invokes effects - mount, cleanup,
    // mount again - to surface exactly this kind of bug. Without this
    // guard, the first effect run's osmd.load() promise can resolve after
    // its own cleanup already ran osmd.clear(), and calling render() on a
    // cleared instance throws "load() needs to be called before render()"
    // (caught by actually loading this in a browser, not just building it).
    let cancelled = false;

    osmd.load(musicxml).then(() => {
      if (cancelled) return;
      osmd.render();
      osmd.cursor.show();
    });

    return () => {
      cancelled = true;
      osmd.clear();
      osmdRef.current = null;
    };
  }, [musicxml, osmdRef]);

  return <div ref={containerRef} />;
}
