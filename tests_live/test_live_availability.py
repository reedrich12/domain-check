"""Live acceptance tests — real RDAP/DNS via the CLI, end to end.

These hit the public internet and are excluded from the default pytest run
(testpaths = tests). Run them explicitly:

    python -m pytest tests_live/ -q -m live
    # or: checks/verify.sh --live
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

pytestmark = pytest.mark.live

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO_ROOT / "schema" / "results.schema.json").read_text())

# Long random label: effectively guaranteed unregistered.
SURELY_AVAILABLE = "loop-baseline-4q7x9z2j8k5v-domain-check.com"


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


def test_example_com_is_registered():
    proc = run_cli("example.com", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    row = payload["results"][0]
    assert row["domain"] == "example.com"
    assert row["verdict"] == "registered"


def test_random_long_domain_is_available():
    proc = run_cli(SURELY_AVAILABLE, "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["results"][0]["verdict"] == "available"


def test_live_output_conforms_to_schema():
    proc = run_cli("example.com", "iana.org", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    jsonschema.validate(payload, SCHEMA)
    assert [r["domain"] for r in payload["results"]] == ["example.com", "iana.org"]
