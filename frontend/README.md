# Rhimoz frontend

React + TypeScript + Vite web UI: upload audio, see it as standard
notation with a harmonica tab overlay (hole number + blow/draw arrow
under each note), rendered via [OpenSheetMusicDisplay](https://opensheetmusicdisplay.org/),
play the original recording back with the notation cursor tracking
along, download MusicXML/MIDI/PDF. Sign up/log in to save a
transcription and reopen it later from a dashboard, and search across
your saved songs plus a bundled public-domain library.

## Setup

```sh
npm install
```

Accounts (Phase 5) need the same Supabase project the backend uses. Add
a `.env.local` file (gitignored via the existing `*.local` pattern) with:

```
VITE_SUPABASE_URL=https://<your-project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<the same anon/publishable key backend/.env uses>
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

## Pages

`/` - the upload-and-transcribe flow (works with no login - saving is
the only login-gated action). `/login`, `/signup` - auth forms,
redirect to `/dashboard` if already logged in. `/dashboard` - lists the
current user's saved transcriptions, with delete; redirects to `/login`
if logged out. `/search` - search by title or composer across the user's
saved transcriptions and the bundled public-domain library, shown as two
sections. `/saved/:id` - reopens one saved transcription; `/public/:id` -
reopens a bundled public-domain song (both notation + fresh downloads
only, no audio playback - original audio isn't persisted, see the Phase 5
plan's "File storage fork" section).

## Known limitations

- No automated UI tests, per the testing note above - this now also
  covers the auth/dashboard/reopen flows, verified manually the same way.
