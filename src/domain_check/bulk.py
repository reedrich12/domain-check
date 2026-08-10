"""Bulk checking (U6): many domains, order-preserving, error-isolated.

check_one() is the per-domain pipeline (validate -> RDAP -> DNS fallback ->
verdict) and the seam tests monkeypatch. check_many() runs it over a list:
results come back in input order, and one bad domain never aborts the
batch — its row carries verdict "unknown" and a non-empty error string.
"""

from pathlib import Path

from domain_check import dnscheck, rdap
from domain_check.validate import normalize
from domain_check.verdict import decide


def check_one(domain: str) -> dict:
    """Check a single domain and return one result row."""
    name = normalize(domain)
    rdap_result = rdap.lookup(name)
    dns_status = None
    if rdap_result.status != "registered":
        # Only spend a DNS query when RDAP wasn't authoritative.
        dns_status = dnscheck.probe(name)
    verdict = decide(rdap_status=rdap_result.status, dns_status=dns_status)
    return {
        "domain": name,
        "verdict": verdict.verdict,
        "confidence": verdict.confidence,
        "sources": verdict.sources,
        "rdap_status": rdap_result.raw_status,
        "error": None,
    }


def check_many(domains: list[str]) -> list[dict]:
    results = []
    for domain in domains:
        try:
            # Late-bound module lookup so tests can monkeypatch check_one.
            results.append(check_one(domain))
        except Exception as exc:
            results.append(
                {
                    "domain": domain,
                    "verdict": "unknown",
                    "confidence": 0.0,
                    "sources": [],
                    "rdap_status": None,
                    "error": str(exc) or exc.__class__.__name__,
                }
            )
    return results


def read_domains(path: str | Path) -> list[str]:
    """One domain per line; blank lines and '#' comments skipped."""
    domains = []
    for line in Path(path).read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            domains.append(stripped)
    return domains
