from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from .jobs import append_job_log, claim_next_jobs, complete_job, fail_job
from .models import utc_stamp
from .pipeline import process_job


class WorkerEngine:
    def __init__(
        self,
        conn: sqlite3.Connection,
        workspace_root: Path,
        max_concurrency: int = 4,
        allow_external_enrichment: bool = False,
        poll_interval_seconds: float = 0.3,
    ) -> None:
        self.conn = conn
        self.workspace_root = workspace_root
        self.max_concurrency = max_concurrency
        self.allow_external_enrichment = allow_external_enrichment
        self.poll_interval_seconds = poll_interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _record_metric(self, job_id: int, asset_hash: str, job_type: str, duration_ms: int, status: str) -> None:
        self.conn.execute(
            "INSERT INTO processing_metrics(job_id, asset_hash, job_type, duration_ms, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, asset_hash, job_type, duration_ms, status, utc_stamp()),
        )
        self.conn.commit()

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            claimed = claim_next_jobs(self.conn, self.max_concurrency)
            if not claimed:
                time.sleep(self.poll_interval_seconds)
                continue

            for row in claimed:
                job_id = int(row["id"])
                job_type = str(row["job_type"])
                asset_hash = str(row["asset_hash"])
                started = time.perf_counter()
                try:
                    process_job(self.conn, self.workspace_root, row, allow_external=self.allow_external_enrichment)
                    complete_job(self.conn, job_id)
                    duration_ms = int((time.perf_counter() - started) * 1000)
                    self._record_metric(job_id, asset_hash, job_type, duration_ms, "completed")
                except Exception as exc:  # noqa: BLE001
                    fail_job(self.conn, job_id, str(exc))
                    append_job_log(self.conn, job_id, f"error: {exc}")
                    duration_ms = int((time.perf_counter() - started) * 1000)
                    self._record_metric(job_id, asset_hash, job_type, duration_ms, "failed")
            time.sleep(self.poll_interval_seconds)
