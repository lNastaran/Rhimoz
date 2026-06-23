# Rhimoz

![Song to Rhimoz to harmonica sheet music](assets/flow.png)

AI music transcription: audio in, downloadable sheet music out (PDF,
MusicXML, MIDI). First and currently only supported instrument is
**chromatic harmonica**.

What makes it harmonica-specific is the tab overlay: the standard notation
is rendered normally, with a second line underneath each note showing the
hole number and a blow/draw arrow (up = blow, down = draw), the format used
in published harmonica tab books. Sign in to save transcriptions and reopen
them later, and search across your own songs plus a bundled public-domain
library.

## Dev setup

See [engine/README.md](engine/README.md), [backend/README.md](backend/README.md),
and [frontend/README.md](frontend/README.md).

## Future

Next steps, in rough priority order:

- Instrument expansion via the profile abstraction: piano, guitar, violin,
  flute.
- Live "Shazam-style" mic listening.
- Fetching arbitrary copyrighted audio by song title, and YouTube
  ingestion.
- Training a custom pitch-detection model from scratch.
