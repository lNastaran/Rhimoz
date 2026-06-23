# Bundled public-domain set: provenance

The bundled "Public-domain library" shipped with Rhimoz is a small set of
traditional Irish airs, all in the **public domain**.

## Source

Every tune comes from Francis O'Neill's *Music of Ireland* (Chicago, 1903),
a collection of traditional Irish dance tunes. The work and its melodies
are in the public domain (published 1903; the tunes themselves are
anonymous traditional folk music, far older).

The scores are not downloaded from the network. They ship inside the
[music21](https://www.music21.org) corpus as the `oneills1850` collection,
which is bundled with music21 (a transitive dependency of this project's
engine). This makes the bundled set fully reproducible offline.

## Tunes

| Title | Composer | License |
| --- | --- | --- |
| The Woods of Kilmurry | Traditional (Irish) | Public Domain |
| The Groves of Blackpool | Traditional (Irish) | Public Domain |
| The Monks of the Screw | Traditional (Irish) | Public Domain |
| The Fun at Donnybrook | Traditional (Irish) | Public Domain |
| My Darling I Am Fond of You | Traditional (Irish) | Public Domain |

## How the audio is made

The source scores are monophonic and sit within the chromatic harmonica's
range (C3-C7). `seed/generate_audio.py` renders each melody to a clean
synthesized WAV (`seed/audiogen.py`: additive synthesis, no external audio
tools). That audio is then run through the real engine pipeline
(`transcribe_file`) by `seed/seed_public_transcriptions.py`, exactly as a
user upload would be, and the resulting MusicXML + note data is stored in
the `public_transcriptions` table.

The synthesized WAVs are deliberately **not committed** (they are
deterministic derivatives of the public-domain corpus, regenerable any
time via `generate_audio.py`); `backend/seed/audio/` is gitignored.
