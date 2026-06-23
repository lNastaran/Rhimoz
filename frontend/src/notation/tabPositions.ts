import { OpenSheetMusicDisplay, VexFlowGraphicalNote } from 'opensheetmusicdisplay';

export interface NotePosition {
  left: number;
  top: number;
}

/**
 * Walks OSMD's rendered score chronologically, one non-rest note at a
 * time, and returns each one's on-screen position (relative to
 * containerRect, NOT the viewport) for placing a tab label underneath
 * its notehead.
 *
 * Matches positions to the backend's `notes` array strictly by array
 * order (index i here corresponds to notes[i]), not by pitch/time
 * matching: the instrument is monophonic, so a chronological walk of the
 * iterator's non-rest entries lines up 1:1 with the backend's
 * chronologically-ordered note list. Known edge case (not solved here):
 * if music21's makeNotation() (export_musicxml.py) ever splits a note
 * into tied fragments across a barline, the rendered note count exceeds
 * the logical note count and this 1:1 assumption breaks - detected via
 * the length check below, which truncates rather than misaligning.
 */
export function extractNotePositions(
  osmd: OpenSheetMusicDisplay,
  containerRect: DOMRect,
  expectedNoteCount: number,
): NotePosition[] {
  const positions: NotePosition[] = [];

  // Walk a CLONE of the cursor's iterator, never the live cursor itself -
  // useCursorSync owns the live cursor's position for playback sync, and
  // this must not disturb it. cursor.reset() repositions the live cursor
  // to the start first (harmless: this runs right after rendering, before
  // playback), so the clone always starts from a known position.
  osmd.cursor.reset();
  const iterator = osmd.cursor.iterator.clone();

  while (!iterator.EndReached) {
    for (const voiceEntry of iterator.CurrentVoiceEntries) {
      for (const note of voiceEntry.Notes) {
        if (note.isRest()) continue;

        const graphicalNote = osmd.EngravingRules.GNote(note);
        if (!(graphicalNote instanceof VexFlowGraphicalNote)) continue;

        const rect = graphicalNote.getSVGGElement().getBoundingClientRect();
        positions.push({
          left: rect.left - containerRect.left + rect.width / 2,
          top: rect.bottom - containerRect.top,
        });
      }
    }
    iterator.moveToNext();
  }

  if (positions.length !== expectedNoteCount) {
    console.warn(
      `extractNotePositions: rendered note count (${positions.length}) does not ` +
        `match backend note count (${expectedNoteCount}) - likely a tied note split ` +
        `across a barline. Truncating to the shorter length.`,
    );
  }

  return positions.slice(0, Math.min(positions.length, expectedNoteCount));
}
