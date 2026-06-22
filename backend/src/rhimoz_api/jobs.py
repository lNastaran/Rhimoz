"""
In-memory job store. Maps a job id to the temp directory transcription
outputs were written into and the TranscriptionResult itself.

Known limitation, deliberately not solved here: JOBS and the directories
under JOBS_ROOT grow unbounded for the life of the process - there's no
TTL eviction, LRU, or max-job-count. Acceptable for now since there's no
persistence requirement yet (Phase 5 introduces real accounts/storage);
revisit before this runs unattended for any length of time.
"""
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rhimoz.transcribe import TranscriptionResult

JOBS_ROOT = Path(tempfile.gettempdir()) / "rhimoz-jobs"


@dataclass
class JobRecord:
    job_dir: Path
    result: TranscriptionResult


JOBS: dict[str, JobRecord] = {}
