from __future__ import annotations

from pathlib import Path


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}


def validate_media_kind(media_kind: str) -> None:
    if media_kind not in {"image", "audio"}:
        raise ValueError("media_kind must be 'image' or 'audio'")


def validate_source_path(path: Path, media_kind: str) -> None:
    if not path.exists() or not path.is_file():
        raise ValueError("source_path must reference an existing file")

    ext = path.suffix.lower()
    if media_kind == "image" and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"unsupported image extension: {ext}")
    if media_kind == "audio" and ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(f"unsupported audio extension: {ext}")
