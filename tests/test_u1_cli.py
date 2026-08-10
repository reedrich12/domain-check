"""U1 — CLI skeleton: argument parsing, usage, version, exit codes.

Contract: the package is runnable as `python -m domain_check`.
  * no arguments -> exit 2 and usage text
  * --version    -> exit 0, prints a semantic version
  * --help       -> exit 0, documents the --json flag and --input bulk flag
"""

import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(REPO_ROOT, "src")
    return subprocess.run(
        [sys.executable, "-m", "domain_check", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=30,
    )


def test_no_args_shows_usage_and_exits_2():
    proc = run_cli()
    assert proc.returncode == 2
    assert "usage" in (proc.stderr + proc.stdout).lower()


def test_version_flag():
    proc = run_cli("--version")
    assert proc.returncode == 0
    assert re.search(r"\d+\.\d+\.\d+", proc.stdout)


def test_help_documents_json_and_input_flags():
    proc = run_cli("--help")
    assert proc.returncode == 0
    assert "--json" in proc.stdout
    assert "--input" in proc.stdout
