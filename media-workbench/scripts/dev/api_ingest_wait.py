#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TERMINAL_STATES = {"completed", "failed", "canceled"}


def request_json(
    base_url: str,
    path: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout: float = 10,
    api_token: str | None = None,
) -> dict:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    data = None
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc


def wait_for_job(base_url: str, job_id: int, timeout_seconds: float, poll_seconds: float, api_token: str | None = None) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        payload = request_json(base_url, f"/jobs/{job_id}", api_token=api_token)
        job = payload["job"]
        if job["state"] in TERMINAL_STATES:
            return job
        time.sleep(poll_seconds)
    raise TimeoutError(f"job {job_id} did not finish within {timeout_seconds:g} seconds")


def print_text_outputs(manifest: dict) -> None:
    for paths in manifest.values():
        for raw_path in paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".txt" or not path.exists():
                continue
            print(f"\n--- {path} ---")
            print(path.read_text(encoding="utf-8"), end="")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a local media file and wait for the API job to finish.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--media-kind", required=True, choices=["image", "audio"])
    parser.add_argument("--job-type", choices=["ocr", "asr", "diarization", "enrichment"])
    parser.add_argument("--api-token", default=os.environ.get("MEDIA_WORKBENCH_API_TOKEN"))
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--poll", type=float, default=0.5)
    parser.add_argument("--print-output", action="store_true")
    args = parser.parse_args()

    body = {
        "source_path": str(args.file.expanduser().resolve()),
        "media_kind": args.media_kind,
    }
    if args.job_type:
        body["job_type"] = args.job_type

    ingest = request_json(args.base_url, "/ingest-and-enqueue", method="POST", payload=body, api_token=args.api_token)
    job = wait_for_job(args.base_url, int(ingest["job_id"]), args.timeout, args.poll, api_token=args.api_token)
    export = request_json(args.base_url, f"/export/{ingest['asset_hash']}", api_token=args.api_token)
    summary = {
        "asset_hash": ingest["asset_hash"],
        "job_id": ingest["job_id"],
        "job_state": job["state"],
        "job_type": job["job_type"],
        "export": export,
    }
    print(json.dumps(summary, indent=2))
    if args.print_output:
        print_text_outputs(export["manifest"])
    return 0 if job["state"] == "completed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
