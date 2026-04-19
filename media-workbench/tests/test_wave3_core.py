import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from media_workbench.api_server import create_server
from media_workbench.db import connect, migrate
from media_workbench.engine import WorkerEngine
from media_workbench.jobs import add_asset, enqueue_job, list_jobs
from media_workbench.recovery import recover_jobs_on_start
from media_workbench.workspace import ensure_workspace


class Wave3CoreTests(unittest.TestCase):
    def test_worker_engine_processes_job(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)
            add_asset(conn, "asset1", "audio", root / "raw" / "audio.wav")
            enqueue_job(conn, "asset1", "asr")

            engine = WorkerEngine(conn, workspace_root=root, max_concurrency=4, poll_interval_seconds=0.05)
            engine.start()
            time.sleep(0.25)
            engine.stop()

            jobs = list_jobs(conn)
            self.assertEqual(jobs[0]["state"], "completed")
            self.assertTrue((root / "derived" / "transcripts" / "asset1" / "transcript.json").exists())

            metrics = conn.execute("SELECT status FROM processing_metrics ORDER BY id DESC").fetchall()
            self.assertEqual(metrics[0]["status"], "completed")

    def test_recovery_marks_running_jobs_retrying(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)
            add_asset(conn, "asset3", "audio", root / "raw" / "audio.wav")
            job_id = enqueue_job(conn, "asset3", "asr")
            conn.execute("UPDATE jobs SET state = 'running' WHERE id = ?", (job_id,))
            conn.commit()

            recovered = recover_jobs_on_start(conn)
            self.assertEqual(recovered, 1)
            row = conn.execute("SELECT state, last_error FROM jobs WHERE id = ?", (job_id,)).fetchone()
            self.assertEqual(row["state"], "retrying")
            self.assertIn("Recovered after restart", row["last_error"])

    def test_api_endpoints_health_jobs_settings(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)

            server = create_server("127.0.0.1", 0, {"conn": conn, "paths": paths})
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(payload["status"], "ok")

                add_asset(conn, "asset2", "image", root / "raw" / "image.png")
                req = Request(
                    f"http://127.0.0.1:{port}/jobs",
                    data=json.dumps({"asset_hash": "asset2", "job_type": "ocr"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    job_id = payload["job_id"]

                with urlopen(f"http://127.0.0.1:{port}/jobs/{job_id}", timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(payload["job"]["job_type"], "ocr")

                settings_req = Request(
                    f"http://127.0.0.1:{port}/settings",
                    data=json.dumps({"max_concurrency": 3}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(settings_req, timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(payload["settings"]["max_concurrency"], 3)

                with urlopen(f"http://127.0.0.1:{port}/status", timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(payload["settings"]["max_concurrency"], 3)
                    self.assertIn("pending", payload["job_counts"])

                bogus = root / "bogus.txt"
                bogus.write_text("bad")
                bad_req = Request(
                    f"http://127.0.0.1:{port}/ingest",
                    data=json.dumps({"source_path": str(bogus), "media_kind": "image"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(HTTPError):
                    urlopen(bad_req, timeout=2)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
