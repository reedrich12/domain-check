"""U10 — --coverage report over the cached IANA RDAP bootstrap.

Contract: domain_check.coverage exposes
  * report(bootstrap: dict) -> CoverageReport with
      .total_tlds   int, every TLD mentioned in the bootstrap
      .resolvable   sorted list of TLDs that have at least one https RDAP endpoint
      .unresolvable sorted list of TLDs with no usable endpoint — listed by
                    name, never hidden or summarized away
    and total_tlds == len(resolvable) + len(unresolvable) always holds.
  * the CLI grows a --coverage flag (documented in --help); with --json it
    emits {"total_tlds": int, "resolvable": int, "unresolvable": [str, ...]}.

The >=1000 resolvable-TLD assertion against the real cached bootstrap lives
in tests_live/test_live_coverage.py (network required).
"""

import os
import subprocess
import sys

from domain_check import coverage

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAKE_BOOTSTRAP = {
    "description": "fake RDAP bootstrap",
    "services": [
        [["com", "net", "org"], ["https://rdap.example-a.test/"]],
        [["dead"], []],
        [["gone", "lost"], []],
    ],
}


def test_report_counts_and_classifies():
    rep = coverage.report(FAKE_BOOTSTRAP)
    assert rep.total_tlds == 6
    assert rep.resolvable == ["com", "net", "org"]
    assert rep.unresolvable == ["dead", "gone", "lost"]


def test_unresolvable_tlds_are_listed_not_hidden():
    rep = coverage.report(FAKE_BOOTSTRAP)
    assert rep.total_tlds == len(rep.resolvable) + len(rep.unresolvable)
    for tld in ("dead", "gone", "lost"):
        assert tld in rep.unresolvable


def test_cli_help_documents_coverage_flag():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(REPO_ROOT, "src")
    proc = subprocess.run(
        [sys.executable, "-m", "domain_check", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "--coverage" in proc.stdout
