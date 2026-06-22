# Sample audio attribution

All files sourced from Wikimedia Commons, Category:Sounds of harmonicas
(https://commons.wikimedia.org/wiki/Category:Sounds_of_harmonicas), used under
CC BY-SA 3.0 / GFDL 1.2+ dual license. None are chromatic-harmonica melodic
solos specifically (true CC0/permissive chromatic harmonica melodic recordings
were not findable without creating a Freesound account, which was out of scope
for this validation) — see notes below on what each file actually is and why
it's still a useful proxy for Phase 0.

| File | Source | License | Instrument | Notes |
|---|---|---|---|---|
| marineband1.ogg | [File:Marineband1.ogg](https://commons.wikimedia.org/wiki/File:Marineband1.ogg), uploader Grassinger, 2010 | CC BY-SA 3.0 / GFDL | Diatonic harmonica (Hohner Marine Band) | Melodic phrase, monophonic — best proxy for real-world monophonic harmonica melody despite being diatonic, not chromatic |
| meisterklasse1.ogg | [File:Meisterklasse1.ogg](https://commons.wikimedia.org/wiki/File:Meisterklasse1.ogg), 2010 | CC BY-SA (multiple versions) / GFDL | Diatonic harmonica | Melodic phrase, monophonic |
| blues_harp1.ogg | [File:Blues_Harp1.ogg](https://commons.wikimedia.org/wiki/File:Blues_Harp1.ogg), uploader Grassinger, 2010 | CC BY-SA 3.0 / GFDL | Diatonic (blues) harmonica | Melodic phrase, monophonic, includes bends |
| chromatik_mundharmonika.ogg | [File:Chromatik_Mundharmonika.ogg](https://commons.wikimedia.org/wiki/File:Chromatik_Mundharmonika.ogg), uploader Matthias.Gruber, 2006 | CC BY-SA 3.0 / GFDL | **Chromatic harmonica** | The only genuinely chromatic-harmonica clip found under a permissive license. Short (8.4s) and is "chromatische Akkorde" (chromatic chords) — i.e. polyphonic, not the monophonic single-note case the product targets. Useful as a chromatic-instrument timbre spot-check and as a polyphonic stress test, not as a primary accuracy benchmark. |

## Why diatonic harmonica as a proxy

Diatonic and chromatic harmonica are both free-reed instruments with very
similar spectral/timbral characteristics (breath noise, reed harmonics,
similar formant structure). For Phase 0's purpose — checking whether an
existing pitch-detection backbone (Basic Pitch / pYIN) can reliably extract
note onsets and pitches from solo harmonica-family audio — diatonic recordings
are an acceptable stand-in for "harmonica timbre in general." The
chromatic-specific concerns (slide button, hole/direction mapping) are a
post-processing concern on top of pitch detection, not a pitch-detection
accuracy concern, so this proxy doesn't undermine the validation's purpose.

Before Phase 1 implementation, real chromatic harmonica recordings (ideally
from the user) should still be used for final tuning of hole/direction
mapping logic specifically — see follow-up in PHASE0_FINDINGS.md.
