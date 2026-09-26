from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PATH = REPO_ROOT / "tools" / "mentor_dashboard.py"


def test_dashboard_bootstraps_repo_root_for_controlled_runner_imports() -> None:
    """Mirror script-style deployment where only tools/ is initially importable."""

    original_sys_path = list(sys.path)
    module_name = "_mentor_dashboard_runtime_test"
    try:
        root = REPO_ROOT.resolve()
        sys.path[:] = [
            entry
            for entry in sys.path
            if Path(entry or ".").resolve() != root
        ]

        spec = importlib.util.spec_from_file_location(module_name, DASHBOARD_PATH)
        assert spec is not None
        assert spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        assert str(root) in sys.path
        module._validate_runtime_imports()
    finally:
        sys.modules.pop(module_name, None)
        sys.path[:] = original_sys_path
