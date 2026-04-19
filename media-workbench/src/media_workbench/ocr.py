from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def find_tesseract() -> str | None:
    configured = os.environ.get("MEDIA_WORKBENCH_TESSERACT")
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file():
            return str(configured_path)
        return shutil.which(configured)
    return shutil.which("tesseract")


def run_tesseract_ocr(workspace: Path, asset_hash: str, source_path: Path, command: str | None = None) -> Path:
    tesseract = command or find_tesseract()
    if not tesseract:
        raise FileNotFoundError("tesseract executable not found")

    out_dir = workspace / "derived" / "ocr" / asset_hash
    out_dir.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [tesseract, str(source_path), "stdout", "--psm", "6"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    text = completed.stdout.strip()
    if text:
        text = f"{text}\n"

    blocks = [
        {"text": line, "confidence": None, "bbox": None}
        for line in text.splitlines()
        if line.strip()
    ]
    payload = {
        "asset_hash": asset_hash,
        "engine": "tesseract-cli",
        "source_path": str(source_path),
        "blocks": blocks,
    }
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "text.txt").write_text(text, encoding="utf-8")
    return out_dir
