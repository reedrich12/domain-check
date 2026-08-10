"""U6 — bulk mode.

Contract: domain_check.bulk exposes
  * check_one(domain: str) -> dict (a single result row) — the seam bulk uses
  * check_many(domains: list[str]) -> list[dict]
    - preserves input order
    - one bad domain must not abort the batch: its row gets
      verdict "unknown" and a non-empty "error" string
  * read_domains(path) -> list[str]: one domain per line, blank lines and
    lines starting with '#' skipped, surrounding whitespace stripped
"""

from domain_check import bulk


def ok_row(domain: str) -> dict:
    return {
        "domain": domain,
        "verdict": "registered",
        "confidence": 1.0,
        "sources": ["rdap"],
        "rdap_status": "registered",
        "error": None,
    }


def test_check_many_preserves_order(monkeypatch):
    monkeypatch.setattr(bulk, "check_one", ok_row)
    results = bulk.check_many(["b.com", "a.com", "c.com"])
    assert [r["domain"] for r in results] == ["b.com", "a.com", "c.com"]


def test_one_failure_does_not_abort_the_batch(monkeypatch):
    def flaky(domain: str) -> dict:
        if domain == "boom.com":
            raise RuntimeError("lookup exploded")
        return ok_row(domain)

    monkeypatch.setattr(bulk, "check_one", flaky)
    results = bulk.check_many(["a.com", "boom.com", "z.com"])
    assert len(results) == 3
    failed = results[1]
    assert failed["domain"] == "boom.com"
    assert failed["verdict"] == "unknown"
    assert failed["error"]


def test_read_domains_skips_blanks_and_comments(tmp_path):
    path = tmp_path / "domains.txt"
    path.write_text("# my list\n\n  example.com  \nexample.org\n\n# done\n")
    assert bulk.read_domains(path) == ["example.com", "example.org"]
