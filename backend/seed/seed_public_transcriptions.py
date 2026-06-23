"""Populate the public_transcriptions table with the bundled set.

Self-contained: for each tune it regenerates clean audio from the
public-domain music21 corpus melody, runs the real engine pipeline
(transcribe_file - the same detection/quantize/tab path users get), and
upserts the result into public_transcriptions. Idempotent: re-running
replaces rows for the same (title, composer) rather than duplicating them.

Uses the Supabase SECRET key (service role), which bypasses RLS - the
public_transcriptions table has only a read policy, so this is the only
way rows get in. Run from the backend venv with backend/.env present:

    .venv/bin/python -m seed.seed_public_transcriptions
"""
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from rhimoz.instruments.harmonica import ChromaticHarmonicaProfile
from rhimoz.transcribe import transcribe_file
from supabase import create_client

from rhimoz_api.schemas import notes_to_out
from seed.audiogen import write_tune_wav
from seed.manifest import COMPOSER, CORPUS_GLOB, LICENSE, SOURCE, TUNES

# Explicit path so load_dotenv resolves backend/.env regardless of cwd
# (load_dotenv() walks from the calling file's location, and this file is
# under backend/, so this is belt-and-suspenders - see CLAUDE.md gotcha).
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def main() -> None:
    url = os.environ["SUPABASE_URL"]
    secret = os.environ["SUPABASE_SECRET_KEY"]
    db = create_client(url, secret)

    profile = ChromaticHarmonicaProfile()
    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        for tune in TUNES:
            wav = write_tune_wav(tune.title, CORPUS_GLOB, work / f"{tune.slug}.wav")
            result = transcribe_file(wav, profile, work / tune.slug)
            seq = result.note_sequence
            notes = notes_to_out(seq.notes)

            row = {
                "title": tune.title,
                "composer": COMPOSER,
                "instrument_name": seq.instrument_name,
                "tempo_bpm": seq.tempo_bpm,
                "musicxml": result.musicxml_path.read_text(),
                "notes_json": [n.model_dump() for n in notes],
                "source_url": SOURCE,
                "license": LICENSE,
            }
            # Delete-then-insert keyed on (title, composer) keeps the seed
            # idempotent without needing a unique constraint on the table.
            db.table("public_transcriptions").delete().eq("title", tune.title).eq(
                "composer", COMPOSER
            ).execute()
            db.table("public_transcriptions").insert(row).execute()
            print(f"seeded {tune.title!r} ({len(notes)} notes)")


if __name__ == "__main__":
    main()
