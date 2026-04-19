from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .asr import find_whisper, run_whisper_asr, run_xenova_asr
from .jobs import append_job_log
from .models import utc_stamp
from .ocr import find_tesseract, run_tesseract_ocr
from .spikes import run_asr_spike, run_connector_spike, run_diarization_spike, run_ocr_spike


def index_text(conn: sqlite3.Connection, asset_hash: str, source_type: str, content: str) -> None:
    conn.execute(
        "INSERT INTO search_index(asset_hash, source_type, content, created_at) VALUES (?, ?, ?, ?)",
        (asset_hash, source_type, content, utc_stamp()),
    )
    conn.commit()


def process_job(conn: sqlite3.Connection, workspace_root: Path, job_row: sqlite3.Row, allow_external: bool = False) -> None:
    asset_hash = job_row["asset_hash"]
    job_type = job_row["job_type"]
    job_id = int(job_row["id"])
    append_job_log(conn, job_id, f"processing {job_type}")
    asset = conn.execute("SELECT source_path FROM assets WHERE asset_hash = ?", (asset_hash,)).fetchone()
    source_path = Path(asset["source_path"]) if asset else None

    if job_type == "ocr":
        if source_path and source_path.exists() and find_tesseract():
            out = run_tesseract_ocr(workspace_root, asset_hash, source_path)
            append_job_log(conn, job_id, "ocr engine: tesseract-cli")
        else:
            out = run_ocr_spike(workspace_root, asset_hash)
            append_job_log(conn, job_id, "ocr engine: spike fallback")
        conn.execute(
            "INSERT INTO ocr_results(asset_hash, result_json_path, text_path, created_at) VALUES (?, ?, ?, ?)",
            (asset_hash, str(out / "result.json"), str(out / "text.txt"), utc_stamp()),
        )
        content = (out / "text.txt").read_text(encoding="utf-8")
        index_text(conn, asset_hash, "ocr", content)
    elif job_type == "asr":
        asr_backend = os.environ.get("MEDIA_WORKBENCH_ASR_BACKEND", "auto").lower()
        if source_path and source_path.exists() and asr_backend == "xenova":
            out = run_xenova_asr(workspace_root, asset_hash, source_path)
            append_job_log(conn, job_id, "asr engine: xenova-transformers")
        elif source_path and source_path.exists() and find_whisper():
            out = run_whisper_asr(workspace_root, asset_hash, source_path)
            append_job_log(conn, job_id, "asr engine: whisper-cli")
        else:
            out = run_asr_spike(workspace_root, asset_hash)
            append_job_log(conn, job_id, "asr engine: spike fallback")
        conn.execute(
            """
            INSERT INTO transcript_results(asset_hash, transcript_json_path, transcript_txt_path, transcript_srt_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                asset_hash,
                str(out / "transcript.json"),
                str(out / "transcript.txt"),
                str(out / "transcript.srt"),
                utc_stamp(),
            ),
        )
        content = (out / "transcript.txt").read_text(encoding="utf-8")
        index_text(conn, asset_hash, "transcript", content)
    elif job_type == "diarization":
        out = run_diarization_spike(workspace_root, asset_hash)
        for clip in out.glob("*.wav"):
            conn.execute(
                "INSERT INTO clip_results(asset_hash, cluster_id, clip_path, created_at) VALUES (?, ?, ?, ?)",
                (asset_hash, "speaker-cluster-A", str(clip), utc_stamp()),
            )
    elif job_type == "enrichment":
        run_connector_spike(conn, asset_hash, enabled=allow_external)
        enrichment_dir = workspace_root / "derived" / "enrichment" / asset_hash
        enrichment_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "asset_hash": asset_hash,
            "summary": "Local spike summary.",
            "external_compute_used": bool(allow_external),
        }
        (enrichment_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported job type: {job_type}")

    conn.commit()
    append_job_log(conn, job_id, f"processed {job_type}")


def search(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    pattern = f"%{query}%"
    return conn.execute(
        "SELECT asset_hash, source_type, content FROM search_index WHERE content LIKE ? ORDER BY id DESC LIMIT 50",
        (pattern,),
    ).fetchall()


def export_manifest(conn: sqlite3.Connection, asset_hash: str) -> dict[str, list[str]]:
    manifests: dict[str, list[str]] = {"ocr": [], "transcripts": [], "clips": []}
    for row in conn.execute("SELECT result_json_path, text_path FROM ocr_results WHERE asset_hash = ?", (asset_hash,)):
        manifests["ocr"].extend([row["result_json_path"], row["text_path"]])
    for row in conn.execute(
        "SELECT transcript_json_path, transcript_txt_path, transcript_srt_path FROM transcript_results WHERE asset_hash = ?",
        (asset_hash,),
    ):
        manifests["transcripts"].extend([row["transcript_json_path"], row["transcript_txt_path"], row["transcript_srt_path"]])
    for row in conn.execute("SELECT clip_path FROM clip_results WHERE asset_hash = ?", (asset_hash,)):
        manifests["clips"].append(row["clip_path"])
    return manifests
