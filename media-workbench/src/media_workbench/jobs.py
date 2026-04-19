from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import JobState, utc_stamp


VALID_RETRY_FROM = {JobState.FAILED.value, JobState.CANCELED.value}


def add_asset(conn: sqlite3.Connection, asset_hash: str, media_kind: str, source_path: Path) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO assets(asset_hash, media_kind, source_path, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (asset_hash, media_kind, str(source_path), utc_stamp()),
    )
    conn.commit()


def enqueue_job(conn: sqlite3.Connection, asset_hash: str, job_type: str) -> int:
    now = utc_stamp()
    cur = conn.execute(
        """
        INSERT INTO jobs(asset_hash, job_type, state, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (asset_hash, job_type, JobState.PENDING.value, now, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()


def get_job(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()




def get_job_logs(conn: sqlite3.Connection, job_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM job_logs WHERE job_id = ? ORDER BY id ASC", (job_id,)).fetchall()


def claim_next_jobs(conn: sqlite3.Connection, max_active: int) -> list[sqlite3.Row]:
    active = conn.execute(
        "SELECT COUNT(*) AS c FROM jobs WHERE state = ?",
        (JobState.RUNNING.value,),
    ).fetchone()["c"]
    slots = max(0, max_active - active)
    if slots == 0:
        return []

    rows = conn.execute(
        """
        SELECT * FROM jobs
        WHERE state IN (?, ?)
          AND cancel_requested = 0
        ORDER BY id ASC LIMIT ?
        """,
        (JobState.PENDING.value, JobState.RETRYING.value, slots),
    ).fetchall()

    for r in rows:
        conn.execute(
            "UPDATE jobs SET state = ?, attempts = attempts + 1, updated_at = ? WHERE id = ?",
            (JobState.RUNNING.value, utc_stamp(), r["id"]),
        )
    conn.commit()
    return rows


def complete_job(conn: sqlite3.Connection, job_id: int) -> None:
    conn.execute(
        "UPDATE jobs SET state = ?, updated_at = ? WHERE id = ?",
        (JobState.COMPLETED.value, utc_stamp(), job_id),
    )
    conn.commit()


def cancel_job(conn: sqlite3.Connection, job_id: int) -> bool:
    row = get_job(conn, job_id)
    if row is None:
        return False

    if row["state"] in {JobState.PENDING.value, JobState.RETRYING.value}:
        conn.execute(
            "UPDATE jobs SET state = ?, updated_at = ? WHERE id = ?",
            (JobState.CANCELED.value, utc_stamp(), job_id),
        )
    elif row["state"] == JobState.RUNNING.value:
        conn.execute(
            "UPDATE jobs SET cancel_requested = 1, updated_at = ? WHERE id = ?",
            (utc_stamp(), job_id),
        )
    else:
        return False

    conn.commit()
    return True


def retry_job(conn: sqlite3.Connection, job_id: int) -> bool:
    row = get_job(conn, job_id)
    if row is None or row["state"] not in VALID_RETRY_FROM:
        return False

    conn.execute(
        "UPDATE jobs SET state = ?, cancel_requested = 0, last_error = NULL, updated_at = ? WHERE id = ?",
        (JobState.RETRYING.value, utc_stamp(), job_id),
    )
    conn.commit()
    return True


def fail_job(conn: sqlite3.Connection, job_id: int, error: str) -> None:
    row = get_job(conn, job_id)
    if row is None:
        return
    if row["cancel_requested"] == 1:
        state = JobState.CANCELED.value
    else:
        state = JobState.FAILED.value if row["attempts"] >= row["max_attempts"] else JobState.RETRYING.value
    conn.execute(
        "UPDATE jobs SET state = ?, last_error = ?, updated_at = ? WHERE id = ?",
        (state, error, utc_stamp(), job_id),
    )
    conn.commit()


def append_job_log(conn: sqlite3.Connection, job_id: int, message: str) -> None:
    conn.execute(
        "INSERT INTO job_logs(job_id, message, created_at) VALUES (?, ?, ?)",
        (job_id, message, utc_stamp()),
    )
    conn.commit()
