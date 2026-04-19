from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL UNIQUE,
  media_kind TEXT NOT NULL,
  source_path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL,
  job_type TEXT NOT NULL,
  state TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(asset_hash) REFERENCES assets(asset_hash)
);
CREATE TABLE IF NOT EXISTS job_logs (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS enrichment_audit (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL,
  external_compute_used INTEGER NOT NULL,
  connector_name TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ocr_results (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL,
  result_json_path TEXT NOT NULL,
  text_path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transcript_results (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL,
  transcript_json_path TEXT NOT NULL,
  transcript_txt_path TEXT NOT NULL,
  transcript_srt_path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clip_results (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL,
  cluster_id TEXT NOT NULL,
  clip_path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS search_index (
  id INTEGER PRIMARY KEY,
  asset_hash TEXT NOT NULL,
  source_type TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS processing_metrics (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL,
  asset_hash TEXT NOT NULL,
  job_type TEXT NOT NULL,
  duration_ms INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
