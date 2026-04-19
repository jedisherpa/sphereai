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
from media_workbench.jobs import add_asset, cancel_job, enqueue_job, get_job, retry_job
from media_workbench.pipeline import export_manifest, search
from media_workbench.workspace import ensure_workspace


class Wave5QualityTests(unittest.TestCase):
    def test_cancel_and_retry_flow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)
            add_asset(conn, "asset-cancel", "audio", root / "raw" / "audio.wav")
            job_id = enqueue_job(conn, "asset-cancel", "asr")

            self.assertTrue(cancel_job(conn, job_id))
            self.assertEqual(get_job(conn, job_id)["state"], "canceled")
            self.assertTrue(retry_job(conn, job_id))
            self.assertEqual(get_job(conn, job_id)["state"], "retrying")

    def test_search_and_export_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)
            add_asset(conn, "asset-search", "audio", root / "raw" / "audio.wav")
            enqueue_job(conn, "asset-search", "asr")

            engine = WorkerEngine(conn, workspace_root=root, max_concurrency=1, poll_interval_seconds=0.05)
            engine.start()
            time.sleep(0.3)
            engine.stop()

            rows = search(conn, "welcome")
            self.assertGreaterEqual(len(rows), 1)
            manifest = export_manifest(conn, "asset-search")
            self.assertGreaterEqual(len(manifest["transcripts"]), 1)

    def test_api_rejects_invalid_media_kind(self) -> None:
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
                sample = root / "sample.wav"
                sample.write_bytes(b"RIFF")
                req = Request(
                    f"http://127.0.0.1:{port}/ingest",
                    data=json.dumps({"source_path": str(sample), "media_kind": "video"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(HTTPError):
                    urlopen(req, timeout=2)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
