from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    RETRYING = "retrying"


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    raw_images: Path
    raw_audio: Path
    derived_ocr: Path
    derived_transcripts: Path
    derived_clips: Path
    derived_enrichment: Path
    exports: Path
    cache_models: Path
    cache_temp: Path
    logs: Path
    db_path: Path


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
