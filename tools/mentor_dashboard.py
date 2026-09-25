"""Local mentor-facing dashboard for the accepted project-defined course deliverable.

The dashboard is deliberately conservative:
- it reads frozen acceptance/evidence JSON from the repository;
- it exposes only already-frozen project-defined run modes;
- it never weakens the forward-flow guard or changes acceptance thresholds;
- it does not promote solver/model-domain inadmissibility into a physical mode claim.

Run from the repository root:

    python tools/mentor_dashboard.py

Then open http://127.0.0.1:8765 if a browser does not open automatically.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import os
import secrets
import sys
from pathlib import Path
import threading
import traceback
from typing import Any, Callable
from urllib.parse import urlparse
import uuid
import webbrowser


REPO_ROOT = Path(__file__).resolve().parents[1]
# Script execution puts tools/, not the repository root, on sys.path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

WEB_INDEX = REPO_ROOT / "web" / "mentor_dashboard" / "index.html"
DATA_ROOT = REPO_ROOT / "cases" / "studies" / "data"
ARTIFACT_ROOT = Path(os.environ.get("DASHBOARD_DATA_DIR", str(REPO_ROOT / "artifacts" / "dashboard"))).resolve()
RUN_CONTEXT = threading.local()


def _output_dir() -> Path:
    return ARTIFACT_ROOT / getattr(RUN_CONTEXT, "job_id", "manual")


def _artifact_name(path: Path) -> str:
    return path.relative_to(ARTIFACT_ROOT).as_posix()

RUN_SPECS: dict[str, dict[str, Any]] = {
    "baseline": {
        "label": "Accepted H2 baseline (20 cells)",
        "classification": "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE",
        "cells": 20,
        "cfl": 0.5,
        "teacher_eq_11_46_tolerance": 1.0e-4,
        "max_steps": 8_000,
        "source_reproduction": False,
    },
    "response": {
        "label": "Accepted P12 response sweep",
        "classification": "P12_PROJECT_DEFINED_RESPONSE_SWEEP",
        "equivalence_ratios": [0.10, 0.20, 0.30],
        "cells": 20,
        "cfl": 0.5,
        "teacher_eq_11_46_tolerance": 2.0e-5,
        "max_steps": 8_000,
        "source_reproduction": False,
    },
    "profile": {
        "label": "Accepted H2 full profile export (80 cells)",
        "classification": "PROJECT_DEFINED_H2_FULL_PROFILE_EXPORT",
        "cells": 80,
        "cfl": 0.5,
        "teacher_eq_11_46_tolerance": 2.0e-5,
        "max_steps": 20_000,
        "source_reproduction": False,
        "note": "High-resolution run; expected to take substantially longer than the 20-cell baseline.",
    },
}


def _load_json(name: str) -> dict[str, Any]:
    path = DATA_ROOT / name
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary() -> dict[str, Any]:
    """Build the read-only dashboard payload from frozen evidence on disk."""

    manifest = _load_json("course_deliverable_manifest.json")
    baseline = _load_json("p11_4_project_defined_h2_smoke_acceptance.json")
    grid = _load_json("p11_4_grid_convergence_acceptance.json")
    response = _load_json("p12_project_defined_response_sweep_acceptance.json")
    continuation = _load_json("p12_thermal_throat_continuation_acceptance.json")
    throat_grid = _load_json("p12_thermal_throat_grid_sensitivity_acceptance.json")
    source_gate = _load_json("p11_4_cao_case2_evidence_gate.json")

    return {
        "project": {
            "name": "Scramjet 1D CFD",
            "status": manifest.get("course_project_status", "UNKNOWN"),
            "status_scope": manifest.get("status_scope"),
            "accepted_packaging_commit": (
                manifest.get("final_packaging_acceptance", {}).get(
                    "accepted_packaging_commit"
                )
            ),
            "dashboard_scope": (
                "Mentor-facing view of accepted project-defined evidence. "
                "Not a Cao Case 2 reproduction."
            ),
        },
        "baseline": baseline,
        "grid": grid,
        "response": response,
        "continuation": continuation,
        "thermal_throat_grid": throat_grid,
        "source_gate": source_gate,
        "blockers": manifest.get("known_blockers", []),
        "run_modes": RUN_SPECS,
        "claim_boundaries": {
            "formal_cao_case2_reproduction": False,
            "forward_flow_guard_meaning": "solver/model-domain inadmissible",
            "forward_flow_guard_is_unstart": False,
            "normalized_residual_role": (
                "independent diagnostic only; teacher Eq.11.46 density change "
                "is the authoritative steady-state gate"
            ),
            "grid_claim": (
                "grid-convergence trend only; no asymptotic GCI/grid-independence claim"
            ),
            "lbw_ybw_are_mode_labels": False,
        },
    }


def _write_json_artifact(filename: str, payload: Any) -> Path:
    _output_dir().mkdir(parents=True, exist_ok=True)
    path = _output_dir() / filename
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _run_baseline() -> dict[str, Any]:
    from cases.studies import p11_4_project_defined_h2_smoke as baseline

    spec = RUN_SPECS["baseline"]
    result = baseline.run_smoke(
        cells=int(spec["cells"]),
        tolerance=float(spec["teacher_eq_11_46_tolerance"]),
        max_steps=int(spec["max_steps"]),
    )
    if not result.converged:
        raise RuntimeError("Accepted H2 baseline did not converge.")
    if result.min_temperature_K <= 0.0 or result.min_pressure_Pa <= 0.0:
        raise RuntimeError("Accepted H2 baseline produced a nonphysical state.")

    payload = {
        "classification": baseline.CASE_CLASSIFICATION,
        "not_a_source_reproduction": baseline.NOT_A_SOURCE_REPRODUCTION,
        "run_spec": spec,
        "result": asdict(result),
    }
    path = _write_json_artifact("latest_p11_4_h2_baseline.json", payload)
    payload["artifact_path"] = _artifact_name(path)
    return payload


def _run_response() -> dict[str, Any]:
    from cases.studies import p12_project_defined_response_sweep as sweep

    points = sweep.run_sweep()
    payload = {
        "classification": sweep.CASE_CLASSIFICATION,
        "not_a_source_reproduction": sweep.NOT_A_SOURCE_REPRODUCTION,
        "mode_label_claim": False,
        "teacher_eq_11_46_steady_tolerance": (
            sweep.TEACHER_EQ_11_46_STEADY_TOLERANCE
        ),
        "equivalence_ratios": list(sweep.PROJECT_EQUIVALENCE_RATIOS),
        "points": [asdict(point) for point in points],
    }
    path = _write_json_artifact("latest_p12_response_sweep.json", payload)
    payload["artifact_path"] = _artifact_name(path)
    return payload


def _run_profile() -> dict[str, Any]:
    from cases.studies import p11_4_profile_output as profile

    spec = RUN_SPECS["profile"]
    output_dir = _output_dir() / "profile"
    csv_path, json_path, summary = profile.write_profile_artifacts(
        output_dir,
        cells=int(spec["cells"]),
        tolerance=float(spec["teacher_eq_11_46_tolerance"]),
        max_steps=int(spec["max_steps"]),
    )
    if not summary.converged:
        raise RuntimeError("Accepted H2 full-profile run did not converge.")

    return {
        "classification": profile.CASE_CLASSIFICATION,
        "not_a_source_reproduction": profile.NOT_A_SOURCE_REPRODUCTION,
        "summary": asdict(summary),
        "csv_artifact_path": _artifact_name(csv_path),
        "json_artifact_path": _artifact_name(json_path),
    }


RUNNERS: dict[str, Callable[[], dict[str, Any]]] = {
    "baseline": _run_baseline,
    "response": _run_response,
    "profile": _run_profile,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    id: str
    mode: str
    label: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JobStore:
    """Small in-process job store; only one solver job may run at a time."""

    def __init__(self, state_path: Path | None = None) -> None:
        self._state_path = state_path
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}
        if state_path is not None and state_path.exists():
            for record in json.loads(state_path.read_text(encoding="utf-8")):
                job = Job(**record)
                if job.status in {"queued", "running"}:
                    job.status = "interrupted"
                    job.error = "服务重启中断了计算，请重新运行。"
                    job.completed_at = _utc_now()
                self._jobs[job.id] = job
            self._persist()

    def _persist(self) -> None:
        if self._state_path is None:
            return
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps([j.to_dict() for j in self._jobs.values()],
                                        ensure_ascii=False), encoding="utf-8")
        temporary.replace(self._state_path)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
            jobs.sort(key=lambda job: job.created_at, reverse=True)
            return [job.to_dict() for job in jobs[:12]]

    def artifacts(self) -> set[str]:
        with self._lock:
            return {value for job in self._jobs.values() if job.status == "success"
                    for key, value in (job.result or {}).items()
                    if key.endswith("artifact_path") and isinstance(value, str)}

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else job.to_dict()

    def start(self, mode: str) -> dict[str, Any]:
        if mode not in RUNNERS:
            raise ValueError(f"Unsupported run mode: {mode}")

        with self._lock:
            active = [
                job
                for job in self._jobs.values()
                if job.status in {"queued", "running"}
            ]
            if active:
                raise RuntimeError(
                    "A solver job is already running. Wait for it to finish "
                    "before starting another."
                )
            job = Job(
                id=uuid.uuid4().hex[:12],
                mode=mode,
                label=str(RUN_SPECS[mode]["label"]),
                status="queued",
                created_at=_utc_now(),
            )
            self._jobs[job.id] = job
            self._persist()

        thread = threading.Thread(target=self._execute, args=(job.id,), daemon=True)
        thread.start()
        return job.to_dict()

    def _execute(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            job.started_at = _utc_now()
            mode = job.mode
            self._persist()

        RUN_CONTEXT.job_id = job_id
        try:
            result = RUNNERS[mode]()
        except Exception as exc:  # pragma: no cover - exercised by live solver jobs
            message = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
            with self._lock:
                job = self._jobs[job_id]
                job.status = "error"
                job.error = message
                job.completed_at = _utc_now()
                self._persist()
            return

        with self._lock:
            job = self._jobs[job_id]
            job.status = "success"
            job.result = result
            job.completed_at = _utc_now()
            self._persist()


JOB_STORE = JobStore(ARTIFACT_ROOT / "jobs.json")


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "ScramjetMentorDashboard/1.0"

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_index(self) -> None:
        if not WEB_INDEX.exists():
            self.send_error(HTTPStatus.NOT_FOUND.value, "Dashboard index missing")
            return
        body = WEB_INDEX.read_bytes()
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_index()
            return
        if path == "/api/health":
            self._send_json({"ok": True, "service": "mentor-dashboard"})
            return
        if path == "/api/summary":
            try:
                payload = build_summary()
            except Exception as exc:
                self._send_json(
                    {"error": f"Failed to read frozen evidence: {exc}"},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            self._send_json(payload)
            return
        if path.startswith("/api/artifacts/"):
            # Only expose files referenced by a completed job, never arbitrary paths.
            artifact = path.removeprefix("/api/artifacts/")
            allowed = JOB_STORE.artifacts()
            if artifact not in allowed:
                self.send_error(HTTPStatus.NOT_FOUND.value)
                return
            target = (ARTIFACT_ROOT / artifact).resolve()
            if not target.is_relative_to(ARTIFACT_ROOT) or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND.value)
                return
            body = target.read_bytes()
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", "text/csv" if target.suffix == ".csv" else "application/json")
            self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/jobs":
            self._send_json({"jobs": JOB_STORE.list()})
            return
        if path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            job = JOB_STORE.get(job_id)
            if job is None:
                self._send_json({"error": "Job not found"}, HTTPStatus.NOT_FOUND)
            else:
                self._send_json(job)
            return
        self.send_error(HTTPStatus.NOT_FOUND.value)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlparse(self.path).path
        prefix = "/api/run/"
        if not path.startswith(prefix):
            self.send_error(HTTPStatus.NOT_FOUND.value)
            return
        token = getattr(self.server, "run_token", "")
        if not token:
            self._send_json({"error": "运行功能未启用：请配置 DASHBOARD_RUN_TOKEN。"}, HTTPStatus.FORBIDDEN)
            return
        supplied = self.headers.get("Authorization", "")
        if not secrets.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
            self._send_json({"error": "运行口令不正确。"}, HTTPStatus.UNAUTHORIZED)
            return
        mode = path[len(prefix) :]
        try:
            job = JOB_STORE.start(mode)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.CONFLICT)
            return
        self._send_json(job, HTTPStatus.ACCEPTED)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[dashboard] {self.address_string()} - {fmt % args}")


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if not WEB_INDEX.exists():
        raise FileNotFoundError(f"Dashboard frontend not found: {WEB_INDEX}")
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    server.run_token = os.environ.get("DASHBOARD_RUN_TOKEN", "")
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the mentor CFD dashboard.")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8765")), type=int)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the dashboard in the default browser.",
    )
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    url = f"http://{args.host}:{args.port}"
    print(f"Mentor dashboard: {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
