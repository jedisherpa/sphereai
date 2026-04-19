from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .asr import find_whisper, run_whisper_asr, run_xenova_asr
from .capabilities import engine_config, xenova_engine_status
from .jobs import append_job_log
from .models import utc_stamp
from .ocr import find_tesseract, run_tesseract_ocr
from .settings import get_settings
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
    config = engine_config(get_settings(conn))
    append_job_log(conn, job_id, f"processing {job_type}")
    asset = conn.execute("SELECT source_path FROM assets WHERE asset_hash = ?", (asset_hash,)).fetchone()
    source_path = Path(asset["source_path"]) if asset else None

    if job_type == "ocr":
        ocr_backend = str(config["ocr_backend"] or "auto").lower()
        tesseract = find_tesseract(config["tesseract_path"])
        if ocr_backend not in {"auto", "tesseract", "spike"}:
            raise ValueError("ocr_backend must be 'auto', 'tesseract', or 'spike'")

        if source_path and source_path.exists() and tesseract and ocr_backend in {"auto", "tesseract"}:
            out = run_tesseract_ocr(workspace_root, asset_hash, source_path, command=tesseract)
            append_job_log(conn, job_id, "ocr engine: tesseract-cli")
        elif ocr_backend == "tesseract":
            raise FileNotFoundError("tesseract OCR requested but unavailable")
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
        asr_backend = str(config["asr_backend"] or "auto").lower()
        if asr_backend == "whisper-cli":
            asr_backend = "whisper"
        if asr_backend not in {"auto", "xenova", "whisper", "spike"}:
            raise ValueError("asr_backend must be 'auto', 'xenova', 'whisper', 'whisper-cli', or 'spike'")

        whisper = find_whisper(config["whisper_path"])
        source_exists = bool(source_path and source_path.exists())
        xenova_available, xenova_reason = xenova_engine_status(config)

        if source_exists and asr_backend == "xenova" and xenova_available:
            out = run_xenova_asr(
                workspace_root,
                asset_hash,
                source_path,
                node_command=config["node_path"],
                model_root=config["xenova_model_root"],
                model=config["xenova_model"],
                node_modules=config["xenova_node_modules"],
            )
            append_job_log(conn, job_id, "asr engine: xenova-transformers")
        elif source_exists and asr_backend == "xenova":
            raise FileNotFoundError(f"xenova ASR requested but unavailable: {xenova_reason}")
        elif source_exists and asr_backend == "whisper" and whisper:
            out = run_whisper_asr(workspace_root, asset_hash, source_path, command=whisper)
            append_job_log(conn, job_id, "asr engine: whisper-cli")
        elif asr_backend == "whisper":
            raise FileNotFoundError("whisper CLI requested but unavailable")
        elif asr_backend == "xenova":
            raise FileNotFoundError("xenova ASR requested but source audio is unavailable")
        elif source_exists and asr_backend == "auto" and xenova_available:
            out = run_xenova_asr(
                workspace_root,
                asset_hash,
                source_path,
                node_command=config["node_path"],
                model_root=config["xenova_model_root"],
                model=config["xenova_model"],
                node_modules=config["xenova_node_modules"],
            )
            append_job_log(conn, job_id, "asr engine: xenova-transformers")
        elif source_exists and asr_backend == "auto" and whisper:
            out = run_whisper_asr(workspace_root, asset_hash, source_path, command=whisper)
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


def _append_unique(paths: list[str], *items: str) -> None:
    for item in items:
        if item not in paths:
            paths.append(item)


def export_manifest(conn: sqlite3.Connection, asset_hash: str) -> dict[str, list[str]]:
    manifests: dict[str, list[str]] = {"ocr": [], "transcripts": [], "clips": []}
    for row in conn.execute("SELECT result_json_path, text_path FROM ocr_results WHERE asset_hash = ?", (asset_hash,)):
        _append_unique(manifests["ocr"], row["result_json_path"], row["text_path"])
    for row in conn.execute(
        "SELECT transcript_json_path, transcript_txt_path, transcript_srt_path FROM transcript_results WHERE asset_hash = ?",
        (asset_hash,),
    ):
        _append_unique(
            manifests["transcripts"],
            row["transcript_json_path"],
            row["transcript_txt_path"],
            row["transcript_srt_path"],
        )
    for row in conn.execute("SELECT clip_path FROM clip_results WHERE asset_hash = ?", (asset_hash,)):
        _append_unique(manifests["clips"], row["clip_path"])
    return manifests
