"""U8 — packaging and docs.

Contract:
  * pyproject.toml declares the domain-check console script -> domain_check.cli:main
  * the package version is importable as domain_check.__version__ and matches
    pyproject.toml
  * README documents real CLI usage including the --json flag
"""

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())


def test_console_script_declared():
    meta = load_pyproject()
    assert meta["project"]["scripts"]["domain-check"] == "domain_check.cli:main"


def test_package_version_matches_pyproject():
    import domain_check

    meta = load_pyproject()
    assert domain_check.__version__ == meta["project"]["version"]


def test_readme_documents_usage():
    text = (REPO_ROOT / "README.md").read_text()
    assert "domain-check" in text
    assert "--json" in text
    assert "--input" in text
