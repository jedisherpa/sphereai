from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .models import WorkspacePaths


def resolve_workspace(root: Path) -> WorkspacePaths:
    return WorkspacePaths(
        root=root,
        raw_images=root / "raw" / "images",
        raw_audio=root / "raw" / "audio",
        derived_ocr=root / "derived" / "ocr",
        derived_transcripts=root / "derived" / "transcripts",
        derived_clips=root / "derived" / "clips",
        derived_enrichment=root / "derived" / "enrichment",
        exports=root / "exports",
        cache_models=root / "cache" / "models",
        cache_temp=root / "cache" / "temp",
        logs=root / "logs",
        db_path=root / "app.db",
    )


def ensure_workspace(root: Path) -> WorkspacePaths:
    paths = resolve_workspace(root)
    for p in [
        paths.raw_images,
        paths.raw_audio,
        paths.derived_ocr,
        paths.derived_transcripts,
        paths.derived_clips,
        paths.derived_enrichment,
        paths.exports,
        paths.cache_models,
        paths.cache_temp,
        paths.logs,
    ]:
        p.mkdir(parents=True, exist_ok=True)
    return paths


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest_file(paths: WorkspacePaths, source: Path, media_kind: str) -> tuple[str, Path]:
    digest = file_sha256(source)
    now = datetime.now(timezone.utc)
    target_root = paths.raw_images if media_kind == "image" else paths.raw_audio
    target = target_root / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    target.mkdir(parents=True, exist_ok=True)
    ext = source.suffix.lower() or ".bin"
    out = target / f"{digest}{ext}"
    if not out.exists():
        shutil.copy2(source, out)
    return digest, out
