# Rhimoz frontend

React + TypeScript + Vite web UI: upload audio, see it as standard
notation with a harmonica tab overlay (hole number + blow/draw arrow
under each note), rendered via [OpenSheetMusicDisplay](https://opensheetmusicdisplay.org/),
play the original recording back with the notation cursor tracking
along, download MusicXML/MIDI/PDF.

## Setup

```sh
npm install
```

## Run

```sh
npm run dev
```

Serves on `http://localhost:5173`. Expects the [backend](../backend)
running at `http://localhost:8000` (override via a `VITE_API_BASE_URL`
env var, e.g. in a `.env.local` file, if needed).

## Test

```sh
npm run test
```

Only `src/sync/cursorSync.ts` has automated tests. That's deliberate,
not an oversight: `CursorSync` is pure logic against a small interface
(no DOM/OSMD/React), so it's cheap to unit test and easy to silently
regress (an off-by-one in the stepping loop, a broken backward-seek
path). Component rendering (`UploadForm`, `NotationViewer`,
`AudioPlayer`, `DownloadButtons`) is **not** covered by automated
tests - mocking OSMD's DOM rendering would prove little (OSMD is
tested upstream), and the thing that actually matters here - does the
cursor visibly track the audio in a real browser, does the tab overlay
stay aligned through a resize - is a manual/visual check, not a
headless assertion. This isn't theoretical: a real bug (OSMD's
`render()` clearing its entire container's innerHTML, silently
deleting the tab overlay's sibling label divs on every resize) was only
caught by checking `container.children.length` in an actual browser -
a mocked render would never have reproduced it. Verify the full upload
-> render -> playback -> download flow by running both servers and
trying it in an actual browser after any change to these components.

## Known limitations

- No accounts/persistence (Phase 5) - nothing is saved between sessions.
- No automated UI tests, per the testing note above.
