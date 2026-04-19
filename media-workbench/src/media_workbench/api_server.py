from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .jobs import cancel_job, enqueue_job, get_job, get_job_logs, list_jobs, retry_job
from .pipeline import export_manifest, search
from .settings import get_settings, set_setting
from .validation import validate_media_kind, validate_source_path
from .workspace import ingest_file


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "MediaWorkbenchHTTP/0.2"

    def _json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    @property
    def app(self):
        return self.server.app_context  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                return self._json({"status": "ok"})
            if parsed.path == "/status":
                settings = get_settings(self.app["conn"])
                counts = {
                    row["state"]: row["count"]
                    for row in self.app["conn"].execute("SELECT state, COUNT(*) AS count FROM jobs GROUP BY state")
                }
                recent_metrics = [
                    dict(row)
                    for row in self.app["conn"].execute(
                        "SELECT job_id, job_type, duration_ms, status, created_at FROM processing_metrics ORDER BY id DESC LIMIT 20"
                    )
                ]
                return self._json({"status": "ok", "settings": settings, "job_counts": counts, "recent_metrics": recent_metrics})
            if parsed.path == "/jobs":
                jobs = [dict(row) for row in list_jobs(self.app["conn"])]
                return self._json({"jobs": jobs})
            if parsed.path.startswith("/jobs/") and parsed.path.endswith("/logs"):
                job_id = int(parsed.path.split("/")[2])
                logs = [dict(row) for row in get_job_logs(self.app["conn"], job_id)]
                return self._json({"job_id": job_id, "logs": logs})
            if parsed.path.startswith("/jobs/"):
                job_id = int(parsed.path.split("/")[2])
                job = get_job(self.app["conn"], job_id)
                if not job:
                    return self._json({"error": "job not found"}, HTTPStatus.NOT_FOUND)
                return self._json({"job": dict(job)})
            if parsed.path == "/search":
                query = parse_qs(parsed.query).get("q", [""])[0]
                rows = [dict(r) for r in search(self.app["conn"], query)]
                return self._json({"results": rows})
            if parsed.path.startswith("/export/"):
                asset_hash = parsed.path.split("/export/", 1)[1]
                return self._json({"asset_hash": asset_hash, "manifest": export_manifest(self.app["conn"], asset_hash)})
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/ingest":
                body = self._read_json()
                source = Path(body["source_path"]).expanduser().resolve()
                media_kind = body["media_kind"]
                validate_media_kind(media_kind)
                validate_source_path(source, media_kind)
                asset_hash, stored = ingest_file(self.app["paths"], source, media_kind)
                from .jobs import add_asset  # local import to avoid cycle

                add_asset(self.app["conn"], asset_hash, media_kind, stored)
                return self._json({"asset_hash": asset_hash, "stored_path": str(stored)})

            if self.path == "/jobs":
                body = self._read_json()
                job_id = enqueue_job(self.app["conn"], body["asset_hash"], body["job_type"])
                return self._json({"job_id": job_id}, HTTPStatus.CREATED)

            if self.path.startswith("/jobs/") and self.path.endswith("/cancel"):
                job_id = int(self.path.split("/")[2])
                ok = cancel_job(self.app["conn"], job_id)
                return self._json({"ok": ok})

            if self.path.startswith("/jobs/") and self.path.endswith("/retry"):
                job_id = int(self.path.split("/")[2])
                ok = retry_job(self.app["conn"], job_id)
                return self._json({"ok": ok})

            if self.path == "/settings":
                body = self._read_json()
                for key, value in body.items():
                    set_setting(self.app["conn"], key, value)
                return self._json({"settings": get_settings(self.app["conn"])})

            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)


def create_server(host: str, port: int, app_context: dict) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ApiHandler)
    server.app_context = app_context  # type: ignore[attr-defined]
    return server


def run_server(host: str, port: int, app_context: dict) -> None:
    server = create_server(host, port, app_context)
    server.serve_forever()
