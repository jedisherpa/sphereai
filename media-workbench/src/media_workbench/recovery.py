from __future__ import annotations

import sqlite3

from .models import JobState, utc_stamp


def recover_jobs_on_start(conn: sqlite3.Connection) -> int:
    """Move interrupted running jobs back into retrying on startup."""
    rows = conn.execute(
        "SELECT id FROM jobs WHERE state = ?",
        (JobState.RUNNING.value,),
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE jobs SET state = ?, last_error = ?, updated_at = ? WHERE id = ?",
            (JobState.RETRYING.value, "Recovered after restart", utc_stamp(), row["id"]),
        )
    conn.commit()
    return len(rows)
