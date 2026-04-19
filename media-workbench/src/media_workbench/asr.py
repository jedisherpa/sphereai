from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def find_whisper() -> str | None:
    configured = os.environ.get("MEDIA_WORKBENCH_WHISPER")
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file():
            return str(configured_path)
        return shutil.which(configured)
    return shutil.which("whisper")


def _copy_if_exists(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return True


def run_whisper_asr(workspace: Path, asset_hash: str, source_path: Path, command: str | None = None) -> Path:
    whisper = command or find_whisper()
    if not whisper:
        raise FileNotFoundError("whisper executable not found")

    out_dir = workspace / "derived" / "transcripts" / asset_hash
    out_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            whisper,
            str(source_path),
            "--output_dir",
            str(out_dir),
            "--output_format",
            "all",
            "--verbose",
            "False",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60 * 30,
    )

    stem = source_path.stem
    text_path = out_dir / "transcript.txt"
    srt_path = out_dir / "transcript.srt"
    json_path = out_dir / "transcript.json"

    text_written = _copy_if_exists(out_dir / f"{stem}.txt", text_path)
    srt_written = _copy_if_exists(out_dir / f"{stem}.srt", srt_path)
    json_written = _copy_if_exists(out_dir / f"{stem}.json", json_path)

    if not text_written:
        text_path.write_text("", encoding="utf-8")
    if not srt_written:
        srt_path.write_text("", encoding="utf-8")
    if not json_written:
        payload = {
            "asset_hash": asset_hash,
            "engine": "whisper-cli",
            "source_path": str(source_path),
            "text": text_path.read_text(encoding="utf-8"),
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return out_dir
