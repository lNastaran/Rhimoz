from rhimoz.instruments.harmonica import ChromaticHarmonicaProfile
from rhimoz.instruments.profile import InstrumentProfile, PitchDetectionParams

PROFILES: dict[str, type[InstrumentProfile]] = {
    "chromatic_harmonica": ChromaticHarmonicaProfile,
}

__all__ = [
    "InstrumentProfile",
    "PitchDetectionParams",
    "ChromaticHarmonicaProfile",
    "PROFILES",
]
