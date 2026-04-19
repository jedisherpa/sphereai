from __future__ import annotations

import json
import sqlite3

from .models import utc_stamp

DEFAULT_SETTINGS = {
    "max_concurrency": 4,
    "allow_external_enrichment": False,
    "ocr_backend": "auto",
    "tesseract_path": None,
    "asr_backend": "auto",
    "whisper_path": None,
    "node_path": None,
    "xenova_model_root": None,
    "xenova_model": "Xenova/whisper-small",
    "xenova_node_modules": None,
}


def get_settings(conn: sqlite3.Connection) -> dict:
    settings = dict(DEFAULT_SETTINGS)
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    for row in rows:
        try:
            settings[row["key"]] = json.loads(row["value"])
        except json.JSONDecodeError:
            settings[row["key"]] = row["value"]
    return settings


def set_setting(conn: sqlite3.Connection, key: str, value) -> None:
    conn.execute(
        "INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        (key, json.dumps(value), utc_stamp()),
    )
    conn.commit()
