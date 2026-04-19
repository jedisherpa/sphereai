import sqlite3
import tempfile
import unittest
from pathlib import Path

from media_workbench.db import connect, migrate
from media_workbench.jobs import add_asset, claim_next_jobs, enqueue_job
from media_workbench.spikes import run_asr_spike, run_connector_spike, run_diarization_spike, run_ocr_spike
from media_workbench.workspace import ensure_workspace


class Wave2SpikeTests(unittest.TestCase):
    def test_workspace_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = ensure_workspace(root)
            conn = connect(paths.db_path)
            migrate(conn)

            asset_hash = "abc123"
            add_asset(conn, asset_hash, "audio", root / "raw" / "audio.wav")
            job_id = enqueue_job(conn, asset_hash, "asr")
            claimed = claim_next_jobs(conn, max_active=4)

            self.assertEqual(len(claimed), 1)
            self.assertEqual(claimed[0]["id"], job_id)

            run_ocr_spike(root, asset_hash)
            run_asr_spike(root, asset_hash)
            run_diarization_spike(root, asset_hash)
            run_connector_spike(conn, asset_hash, enabled=False)

            self.assertTrue((root / "derived" / "ocr" / asset_hash / "result.json").exists())
            self.assertTrue((root / "derived" / "transcripts" / asset_hash / "transcript.json").exists())
            self.assertTrue((root / "derived" / "clips" / asset_hash / "speaker-cluster-A").exists())

            rows = conn.execute("SELECT external_compute_used FROM enrichment_audit").fetchall()
            self.assertEqual(rows[0][0], 0)


if __name__ == "__main__":
    unittest.main()
