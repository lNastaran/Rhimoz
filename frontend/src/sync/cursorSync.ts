/**
 * Keeps an OpenSheetMusicDisplay cursor synced to real playback time.
 *
 * Problem: note_sequence_to_stream() (engine) lets music21's
 * makeNotation() fill gaps between notes with rests. Those become real
 * <note><rest/></note> elements in the MusicXML, and OSMD's cursor
 * iterator steps through rests exactly like notes. So calling
 * cursor.next() once per array index in a notes list drifts out of sync
 * the moment a rest appears - step count is not note count.
 *
 * Solution: drive stepping off the iterator's own time position, never
 * off note-array indices. iterator.currentTimeStamp.RealValue is a
 * quarter-note offset from the start of the piece; tempoBpm converts a
 * playback second into the same units, so the two are directly
 * comparable regardless of how many rests sit between notes.
 */

export interface CursorLike {
  next(): void;
  reset(): void;
  update(): void;
  iterator: {
    currentTimeStamp: { RealValue: number };
    EndReached: boolean;
  };
}

export class CursorSync {
  private cursor: CursorLike;
  private tempoBpm: number;
  private lastQuarterOffset = 0;

  constructor(cursor: CursorLike, tempoBpm: number) {
    this.cursor = cursor;
    this.tempoBpm = tempoBpm;
  }

  /** Advances or rewinds the cursor so its position matches currentTimeSec. */
  syncTo(currentTimeSec: number): void {
    const targetQuarterOffset = (currentTimeSec * this.tempoBpm) / 60;

    if (targetQuarterOffset < this.lastQuarterOffset) {
      // next() is forward-only, so the only way to seek backward is to
      // reset to the start and replay forward to the new target.
      this.cursor.reset();
    }

    while (
      !this.cursor.iterator.EndReached &&
      this.cursor.iterator.currentTimeStamp.RealValue < targetQuarterOffset
    ) {
      this.cursor.next();
    }

    this.cursor.update();
    this.lastQuarterOffset = this.cursor.iterator.currentTimeStamp.RealValue;
  }

  reset(): void {
    this.cursor.reset();
    this.lastQuarterOffset = 0;
  }
}
