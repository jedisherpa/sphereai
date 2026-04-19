from __future__ import annotations

import json
from pathlib import Path


def run_release_preflight(project_root: Path) -> dict:
    checks = {
        "release_notes": (project_root / "RELEASE_NOTES.md").exists(),
        "install_matrix": (project_root / "docs" / "release" / "install-matrix.md").exists(),
        "release_checklist": (project_root / "docs" / "release" / "release-checklist.md").exists(),
        "known_issues": (project_root / "docs" / "release" / "known-issues.md").exists(),
        "rollback_plan": (project_root / "docs" / "release" / "rollback-plan.md").exists(),
        "packaging_script": (project_root / "scripts" / "package" / "build_release_bundle.sh").exists(),
    }
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "status": "pass" if passed == total else "fail",
    }


def write_preflight_report(project_root: Path, report: dict) -> Path:
    out = project_root / "docs" / "release" / "preflight-report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out
