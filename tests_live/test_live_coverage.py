"""Live acceptance for U10 — coverage of the real cached IANA bootstrap.

The --coverage report must show at least 1000 TLDs resolvable to an RDAP
endpoint, and must list unresolvable TLDs by name rather than hiding them.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.live

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "domain_check", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=120,
    )


def test_coverage_reports_at_least_1000_resolvable_tlds():
    proc = run_cli("--coverage", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["resolvable"] >= 1000, payload["resolvable"]


def test_unresolvable_tlds_are_listed_and_accounted_for():
    proc = run_cli("--coverage", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert isinstance(payload["unresolvable"], list)
    assert all(isinstance(tld, str) and tld for tld in payload["unresolvable"])
    assert payload["total_tlds"] == payload["resolvable"] + len(payload["unresolvable"])
