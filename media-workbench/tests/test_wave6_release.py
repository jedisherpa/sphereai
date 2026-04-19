import json
import tempfile
import unittest
from pathlib import Path

from media_workbench.release import run_release_preflight, write_preflight_report


class Wave6ReleaseTests(unittest.TestCase):
    def test_preflight_passes_with_required_files(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        report = run_release_preflight(project_root)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["passed"], report["total"])

    def test_preflight_report_written(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "release").mkdir(parents=True)
            (root / "scripts" / "package").mkdir(parents=True)
            (root / "RELEASE_NOTES.md").write_text("notes")
            (root / "docs" / "release" / "install-matrix.md").write_text("x")
            (root / "docs" / "release" / "release-checklist.md").write_text("x")
            (root / "docs" / "release" / "known-issues.md").write_text("x")
            (root / "docs" / "release" / "rollback-plan.md").write_text("x")
            (root / "scripts" / "package" / "build_release_bundle.sh").write_text("#!/bin/sh")

            report = run_release_preflight(root)
            out = write_preflight_report(root, report)
            payload = json.loads(out.read_text())
            self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
