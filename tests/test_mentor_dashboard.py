"""Contract tests for the mentor-facing local dashboard."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "mentor_dashboard.py"


def _load_dashboard():
    spec = importlib.util.spec_from_file_location("mentor_dashboard_test_module", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dashboard = _load_dashboard()


def test_dashboard_run_specs_match_frozen_project_defined_paths() -> None:
    baseline = dashboard.RUN_SPECS["baseline"]
    response = dashboard.RUN_SPECS["response"]
    profile = dashboard.RUN_SPECS["profile"]

    assert baseline["classification"] == "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE"
    assert baseline["cells"] == 20
    assert baseline["cfl"] == 0.5
    assert baseline["teacher_eq_11_46_tolerance"] == 1.0e-4
    assert baseline["max_steps"] == 8_000
    assert baseline["source_reproduction"] is False

    assert response["classification"] == "P12_PROJECT_DEFINED_RESPONSE_SWEEP"
    assert response["equivalence_ratios"] == [0.10, 0.20, 0.30]
    assert response["teacher_eq_11_46_tolerance"] == 2.0e-5
    assert response["source_reproduction"] is False

    assert profile["classification"] == "PROJECT_DEFINED_H2_FULL_PROFILE_EXPORT"
    assert profile["cells"] == 80
    assert profile["teacher_eq_11_46_tolerance"] == 2.0e-5
    assert profile["source_reproduction"] is False


def test_dashboard_summary_preserves_scientific_claim_boundaries() -> None:
    summary = dashboard.build_summary()
    claims = summary["claim_boundaries"]

    assert summary["project"]["status"] == "DELIVERABLE_COMPLETE"
    assert claims["formal_cao_case2_reproduction"] is False
    assert claims["forward_flow_guard_meaning"] == "solver/model-domain inadmissible"
    assert claims["forward_flow_guard_is_unstart"] is False
    assert claims["lbw_ybw_are_mode_labels"] is False
    assert "diagnostic only" in claims["normalized_residual_role"]
    assert "grid-convergence trend only" in claims["grid_claim"]
    assert summary["source_gate"]["formal_reproduction_ready"] is False
    assert summary["blockers"]


def test_dashboard_frontend_exists_and_states_guard_boundary() -> None:
    index = dashboard.WEB_INDEX
    assert index.is_file()
    text = index.read_text(encoding="utf-8")

    assert "导师控制台" in text
    assert "Deliverable complete" in text
    assert "solver/model-domain inadmissible" in text
    assert "不解释为 unstart" in text
    assert "Cao Case 2" in text
    assert "python tools/mentor_dashboard.py" in text


def test_dashboard_only_exposes_known_run_modes() -> None:
    assert set(dashboard.RUNNERS) == {"baseline", "response", "profile"}


def test_documented_script_resolves_cases_without_pythonpath(tmp_path):
    import os
    import subprocess
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    env['DASHBOARD_DATA_DIR'] = str(tmp_path)
    code = "import runpy,sys; sys.path[0]=str(__import__('pathlib').Path('tools').resolve()); runpy.run_path('tools/mentor_dashboard.py',run_name='dashboard_import'); from cases.studies import p11_4_project_defined_h2_smoke,p12_project_defined_response_sweep,p11_4_profile_output"
    subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, check=True)


def test_job_restart_marks_interrupted_and_keeps_completed(tmp_path):
    import json
    state = tmp_path / 'jobs.json'
    state.write_text(json.dumps([
        dashboard.Job('active', 'baseline', 'test', 'running', 'now').to_dict(),
        dashboard.Job('done', 'baseline', 'test', 'success', 'before', result={'artifact_path': 'done/result.json'}).to_dict(),
    ]))
    store = dashboard.JobStore(state)
    assert store.get('active')['status'] == 'interrupted'
    assert store.get('done')['status'] == 'success'
    assert store.artifacts() == {'done/result.json'}
    assert dashboard.JobStore(state).get('active')['status'] == 'interrupted'


def test_http_auth_job_and_scoped_download(tmp_path, monkeypatch):
    import json
    import threading
    import time
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    import pytest
    monkeypatch.setattr(dashboard, 'ARTIFACT_ROOT', tmp_path)
    monkeypatch.setattr(dashboard, 'JOB_STORE', dashboard.JobStore(tmp_path / 'jobs.json'))
    def fake_run():
        path = dashboard._write_json_artifact('result.json', {'ok': True})
        return {'artifact_path': dashboard._artifact_name(path)}
    monkeypatch.setitem(dashboard.RUNNERS, 'baseline', fake_run)
    monkeypatch.setenv('DASHBOARD_RUN_TOKEN', 'test-password')
    server = dashboard.create_server('127.0.0.1', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        assert urlopen(base + '/api/health').status == 200
        for token in ['', 'wrong']:
            with pytest.raises(HTTPError) as exc:
                urlopen(Request(base + '/api/run/baseline', method='POST', headers={'Authorization': 'Bearer ' + token}))
            assert exc.value.code == 401
        jobs = []
        for _ in range(2):
            job = json.load(urlopen(Request(base + '/api/run/baseline', method='POST', headers={'Authorization': 'Bearer test-password'})))
            for _ in range(100):
                job = json.load(urlopen(base + '/api/jobs/' + job['id']))
                if job['status'] == 'success':
                    break
                time.sleep(.01)
            assert job['status'] == 'success'
            path = job['result']['artifact_path']
            response = urlopen(base + '/api/artifacts/' + path)
            assert 'attachment' in response.headers['Content-Disposition']
            assert json.load(response) == {'ok': True}
            jobs.append(path)
        assert jobs[0] != jobs[1]
        for path in ['jobs.json', '../README.md', 'missing.json']:
            with pytest.raises(HTTPError) as exc:
                urlopen(base + '/api/artifacts/' + path)
            assert exc.value.code == 404
        server.run_token = ''
        with pytest.raises(HTTPError) as exc:
            urlopen(Request(base + '/api/run/baseline', method='POST'))
        assert exc.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
