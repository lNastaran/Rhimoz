"""The curated bundled public-domain set.

Every tune is a traditional Irish air from Francis O'Neill's "Music of
Ireland" (1903), which is in the public domain. The scores ship inside the
music21 corpus (the `oneills1850` collection), so no external download is
needed and provenance is fully reproducible. See PROVENANCE.md.

Each tune is selected to be monophonic and to sit within the chromatic
harmonica's range (C3-C7, MIDI 48-96) so it transcribes cleanly through
the real engine pipeline.
"""
from dataclasses import dataclass

CORPUS_GLOB = "/oneills1850/"
COMPOSER = "Traditional (Irish)"
SOURCE = "O'Neill's Music of Ireland (1903); music21 corpus 'oneills1850'"
LICENSE = "Public Domain"


@dataclass(frozen=True)
class Tune:
    slug: str  # filename stem for the generated audio
    title: str  # must match the score's metadata title exactly


TUNES: list[Tune] = [
    Tune("woods-of-kilmurry", "The Woods of Kilmurry"),
    Tune("groves-of-blackpool", "The Groves of Blackpool"),
    Tune("monks-of-the-screw", "The Monks of the Screw"),
    Tune("fun-at-donnybrook", "The Fun at Donnybrook"),
    Tune("my-darling-i-am-fond-of-you", "My Darling I Am Fond of You"),
]
