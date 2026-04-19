from __future__ import annotations

import argparse
from pathlib import Path

from .api_server import run_server
from .db import connect, migrate
from .engine import WorkerEngine
from .jobs import add_asset, claim_next_jobs, enqueue_job
from .recovery import recover_jobs_on_start
from .release import run_release_preflight, write_preflight_report
from .settings import DEFAULT_SETTINGS
from .spikes import run_asr_spike, run_connector_spike, run_diarization_spike, run_job_spike, run_ocr_spike
from .workspace import ensure_workspace, ingest_file


def run_wave2(workspace_root: Path, sample_file: Path) -> None:
    paths = ensure_workspace(workspace_root)
    conn = connect(paths.db_path)
    migrate(conn)

    media_kind = "image" if sample_file.suffix.lower() in {".png", ".jpg", ".jpeg"} else "audio"
    asset_hash, stored = ingest_file(paths, sample_file, media_kind)
    add_asset(conn, asset_hash, media_kind, stored)

    job_type = "ocr" if media_kind == "image" else "asr"
    job_id = enqueue_job(conn, asset_hash, job_type)
    claimed = claim_next_jobs(conn, max_active=4)
    for row in claimed:
        run_job_spike(conn, row["id"], should_fail=False)

    run_ocr_spike(workspace_root, asset_hash)
    run_asr_spike(workspace_root, asset_hash)
    run_diarization_spike(workspace_root, asset_hash)
    run_connector_spike(conn, asset_hash, enabled=False)

    print(f"Wave 2 spikes completed for asset {asset_hash} (job {job_id}).")


def run_serve(workspace_root: Path, host: str, port: int, max_concurrency: int, allow_external: bool) -> None:
    paths = ensure_workspace(workspace_root)
    conn = connect(paths.db_path)
    migrate(conn)

    recovered = recover_jobs_on_start(conn)
    if recovered:
        print(f"Recovered {recovered} interrupted jobs from previous run.")

    engine = WorkerEngine(
        conn,
        workspace_root=workspace_root,
        max_concurrency=max_concurrency,
        allow_external_enrichment=allow_external,
    )
    engine.start()
    print(f"Server starting on http://{host}:{port} with max_concurrency={max_concurrency}")
    try:
        run_server(host, port, {"conn": conn, "paths": paths, "engine": engine})
    finally:
        engine.stop()




def run_release_preflight_cmd(project_root: Path) -> int:
    report = run_release_preflight(project_root)
    out = write_preflight_report(project_root, report)
    print(f"Release preflight: {report['passed']}/{report['total']} checks passed ({report['status']}).")
    print(f"Report: {out}")
    return 0 if report["status"] == "pass" else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Media Workbench")
    sub = parser.add_subparsers(dest="command", required=False)

    wave2 = sub.add_parser("wave2", help="Run Wave 2 spike workflow")
    wave2.add_argument("--workspace", type=Path, default=Path("./workspace"))
    wave2.add_argument("--sample", type=Path, required=True)

    serve = sub.add_parser("serve", help="Run local API + worker engine")
    serve.add_argument("--workspace", type=Path, default=Path("./workspace"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--max-concurrency", type=int, default=DEFAULT_SETTINGS["max_concurrency"])
    serve.add_argument("--allow-external-enrichment", action="store_true")

    preflight = sub.add_parser("release-preflight", help="Run release documentation/tooling preflight checks")
    preflight.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])

    args = parser.parse_args()
    if args.command == "wave2":
        run_wave2(args.workspace, args.sample)
        return
    if args.command == "serve":
        run_serve(args.workspace, args.host, args.port, args.max_concurrency, args.allow_external_enrichment)
        return
    if args.command == "release-preflight":
        raise SystemExit(run_release_preflight_cmd(args.project_root))

    print("Local Media Workbench scaffold is running. Use `wave2`, `serve`, or `release-preflight`.")


if __name__ == "__main__":
    main()
