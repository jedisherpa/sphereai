import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
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

    def test_ingest_and_enqueue_chooses_default_job_type(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)
            image = root / "sample.png"
            image.write_bytes(b"PNG placeholder")

            server = create_server("127.0.0.1", 0, {"conn": conn, "paths": paths})
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            try:
                req = Request(
                    f"http://127.0.0.1:{port}/ingest-and-enqueue",
                    data=json.dumps({"source_path": str(image), "media_kind": "image"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))

                self.assertEqual(payload["job_type"], "ocr")
                job = conn.execute("SELECT asset_hash, job_type, state FROM jobs WHERE id = ?", (payload["job_id"],)).fetchone()
                self.assertEqual(job["asset_hash"], payload["asset_hash"])
                self.assertEqual(job["job_type"], "ocr")
                self.assertEqual(job["state"], "pending")
            finally:
                server.shutdown()
                server.server_close()

    def test_capabilities_reports_persisted_engine_settings(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)

            fake_tesseract = root / "tesseract"
            fake_tesseract.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            fake_node = root / "node"
            fake_node.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            model_root = root / "models"
            (model_root / "Xenova" / "whisper-small").mkdir(parents=True)
            node_modules = root / "node_modules"
            (node_modules / "@xenova" / "transformers").mkdir(parents=True)
            (node_modules / "wavefile").mkdir(parents=True)

            server = create_server("127.0.0.1", 0, {"conn": conn, "paths": paths})
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            engine_env = {
                "MEDIA_WORKBENCH_OCR_BACKEND": "",
                "MEDIA_WORKBENCH_TESSERACT": "",
                "MEDIA_WORKBENCH_ASR_BACKEND": "",
                "MEDIA_WORKBENCH_WHISPER": "",
                "MEDIA_WORKBENCH_NODE": "",
                "MEDIA_WORKBENCH_XENOVA_MODEL_ROOT": "",
                "MEDIA_WORKBENCH_XENOVA_MODEL": "",
                "MEDIA_WORKBENCH_XENOVA_NODE_MODULES": "",
            }
            try:
                with patch.dict(os.environ, engine_env):
                    settings_req = Request(
                        f"http://127.0.0.1:{port}/settings",
                        data=json.dumps(
                            {
                                "ocr_backend": "tesseract",
                                "tesseract_path": str(fake_tesseract),
                                "asr_backend": "xenova",
                                "node_path": str(fake_node),
                                "xenova_model_root": str(model_root),
                                "xenova_model": "Xenova/whisper-small",
                                "xenova_node_modules": str(node_modules),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urlopen(settings_req, timeout=2) as r:
                        payload = json.loads(r.read().decode("utf-8"))
                        self.assertEqual(payload["settings"]["asr_backend"], "xenova")

                    with urlopen(f"http://127.0.0.1:{port}/capabilities", timeout=2) as r:
                        payload = json.loads(r.read().decode("utf-8"))

                self.assertTrue(payload["local_first"])
                self.assertFalse(payload["external_enrichment_enabled"])
                self.assertEqual(payload["config"]["ocr_backend"], "tesseract")
                self.assertEqual(payload["config"]["asr_backend"], "xenova")
                self.assertEqual(payload["config"]["xenova_model_root"], str(model_root))
                ocr_engines = {engine["id"]: engine for engine in payload["engines"]["ocr"]}
                asr_engines = {engine["id"]: engine for engine in payload["engines"]["asr"]}
                self.assertTrue(ocr_engines["tesseract"]["available"])
                self.assertTrue(asr_engines["xenova"]["available"])
            finally:
                server.shutdown()
                server.server_close()

    def test_api_token_protects_non_health_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)

            server = create_server("127.0.0.1", 0, {"conn": conn, "paths": paths, "api_token": "local-test-token"})
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(payload["status"], "ok")
                    self.assertTrue(payload["auth_required"])

                with self.assertRaises(HTTPError) as raised:
                    urlopen(f"http://127.0.0.1:{port}/status", timeout=2)
                self.assertEqual(raised.exception.code, 401)

                req = Request(
                    f"http://127.0.0.1:{port}/status",
                    headers={"Authorization": "Bearer local-test-token"},
                )
                with urlopen(req, timeout=2) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(payload["status"], "ok")
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
