from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .jobs import append_job_log, complete_job, fail_job


def run_ocr_spike(workspace: Path, asset_hash: str) -> Path:
    out_dir = workspace / "derived" / "ocr" / asset_hash
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "asset_hash": asset_hash,
        "engine": "spike-mock-ocr",
        "blocks": [
            {
                "text": "Sample OCR text",
                "confidence": 0.98,
                "bbox": [10, 10, 120, 40],
            }
        ],
    }
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "text.txt").write_text("Sample OCR text\n", encoding="utf-8")
    (out_dir / "preview_overlay.png").write_bytes(b"PNG SPIKE PLACEHOLDER")
    return out_dir


def run_asr_spike(workspace: Path, asset_hash: str) -> Path:
    out_dir = workspace / "derived" / "transcripts" / asset_hash
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "asset_hash": asset_hash,
        "engine": "spike-mock-whisper-large-policy",
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 3.4, "text": "Hello and welcome."},
            {"start": 3.4, "end": 7.2, "text": "This is a spike transcript."},
        ],
    }
    (out_dir / "transcript.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "transcript.txt").write_text(
        "Hello and welcome.\nThis is a spike transcript.\n",
        encoding="utf-8",
    )
    (out_dir / "transcript.srt").write_text(
        "1\n00:00:00,000 --> 00:00:03,400\nHello and welcome.\n\n"
        "2\n00:00:03,400 --> 00:00:07,200\nThis is a spike transcript.\n",
        encoding="utf-8",
    )
    return out_dir


def run_diarization_spike(workspace: Path, asset_hash: str) -> Path:
    out_dir = workspace / "derived" / "clips" / asset_hash / "speaker-cluster-A"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "clip_0000_0034.wav").write_bytes(b"RIFF SPIKE CLIP PLACEHOLDER")
    return out_dir


def run_connector_spike(conn: sqlite3.Connection, asset_hash: str, enabled: bool) -> None:
    conn.execute(
        "INSERT INTO enrichment_audit(asset_hash, external_compute_used, connector_name, created_at) VALUES (?, ?, ?, datetime('now'))",
        (asset_hash, 1 if enabled else 0, "openai-compatible" if enabled else None),
    )
    conn.commit()


def run_job_spike(conn: sqlite3.Connection, job_id: int, should_fail: bool = False) -> None:
    append_job_log(conn, job_id, "job started")
    if should_fail:
        fail_job(conn, job_id, "spike failure")
        append_job_log(conn, job_id, "job failed")
        return
    complete_job(conn, job_id)
    append_job_log(conn, job_id, "job completed")
