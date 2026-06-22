import { describe, expect, test } from 'vitest';
import { CursorSync, type CursorLike } from './cursorSync';

function makeFakeCursor(quarterTimestamps: number[]): CursorLike & { position: number } {
  let i = 0;
  return {
    get position() {
      return i;
    },
    next() {
      i = Math.min(i + 1, quarterTimestamps.length - 1);
    },
    reset() {
      i = 0;
    },
    update() {
      // visual-only in the real OSMD cursor; no-op for the fake
    },
    iterator: {
      get currentTimeStamp() {
        return { RealValue: quarterTimestamps[i] };
      },
      get EndReached() {
        return i >= quarterTimestamps.length - 1;
      },
    },
  };
}

describe('CursorSync', () => {
  test('steps forward through interspersed rests to reach the target time', () => {
    // Quarter-note offsets 0, 0.5 (rest), 1, 1.5 (rest), 2 - mimics a rest
    // inserted between every note by music21's makeNotation().
    const cursor = makeFakeCursor([0, 0.5, 1, 1.5, 2]);
    const sync = new CursorSync(cursor, 120); // 120bpm -> 1 quarter = 0.5s

    sync.syncTo(1.0); // target quarter offset = 1.0 * 120 / 60 = 2.0

    expect(cursor.iterator.currentTimeStamp.RealValue).toBe(2);
  });

  test('does not advance past the current position when already there', () => {
    const cursor = makeFakeCursor([0, 1, 2, 3]);
    const sync = new CursorSync(cursor, 60); // 1 quarter = 1s

    sync.syncTo(1); // advances to offset 1
    const positionAfterFirstSync = cursor.position;
    sync.syncTo(1); // same target again

    expect(cursor.position).toBe(positionAfterFirstSync);
  });

  test('seeking backward resets and replays forward to the new target', () => {
    const cursor = makeFakeCursor([0, 1, 2, 3, 4]);
    const sync = new CursorSync(cursor, 60); // 1 quarter = 1s

    sync.syncTo(3); // advances to offset 3
    sync.syncTo(1); // backward seek -> should reset then replay to offset 1

    expect(cursor.iterator.currentTimeStamp.RealValue).toBe(1);
  });

  test('stops advancing once EndReached, even if target time is further out', () => {
    const cursor = makeFakeCursor([0, 1, 2]);
    const sync = new CursorSync(cursor, 60);

    sync.syncTo(10); // way past the end of a 3-step sheet

    expect(cursor.iterator.EndReached).toBe(true);
    expect(cursor.iterator.currentTimeStamp.RealValue).toBe(2);
  });

  test('reset() returns the cursor to the start and clears internal position tracking', () => {
    const cursor = makeFakeCursor([0, 1, 2, 3]);
    const sync = new CursorSync(cursor, 60);

    sync.syncTo(3);
    sync.reset();

    expect(cursor.position).toBe(0);
    // After reset, syncing to an earlier time than the pre-reset position
    // should NOT trigger a redundant reset - it should just step forward
    // from the already-reset start.
    sync.syncTo(1);
    expect(cursor.iterator.currentTimeStamp.RealValue).toBe(1);
  });
});
