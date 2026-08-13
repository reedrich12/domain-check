"""Bulk checking (U6): many domains, order-preserving, error-isolated.

check_one() is the per-domain pipeline (validate -> RDAP -> DNS fallback ->
verdict) and the seam tests monkeypatch. check_many() runs it over a list:
results come back in input order, and one bad domain never aborts the
batch — its row carries verdict "unknown" and a non-empty error string.
"""

from pathlib import Path

from domain_check import dnscheck, purchase, rdap, whois
from domain_check.validate import normalize
from domain_check.verdict import decide


def check_one(domain: str, *, use_whois: bool = False) -> dict:
    """Check a single domain and return one result row."""
    name = normalize(domain)
    rdap_result = rdap.lookup(name)
    dns_status = None
    if rdap_result.status != "registered":
        # Only spend a DNS query when RDAP wasn't authoritative.
        dns_status = dnscheck.probe(name)
    whois_status = None
    if use_whois and rdap_result.status == "unknown":
        # Fallback authority, consulted only when RDAP told us nothing.
        whois_status = whois.probe(name)
    verdict = decide(
        rdap_status=rdap_result.status,
        dns_status=dns_status,
        whois_status=whois_status,
    )
    return {
        "domain": name,
        "verdict": verdict.verdict,
        "confidence": verdict.confidence,
        "sources": verdict.sources,
        "rdap_status": rdap_result.raw_status,
        "error": None,
    }


def check_many(domains: list[str], *, use_whois: bool = False) -> list[dict]:
    results = []
    for domain in domains:
        try:
            # Late-bound module lookup so tests can monkeypatch check_one.
            results.append(check_one(domain, use_whois=use_whois))
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
    # U9: every available row carries a registrar purchase link, as the
    # results schema requires.
    return purchase.attach_purchase_urls(results)


def read_domains(path: str | Path) -> list[str]:
    """One domain per line; blank lines and '#' comments skipped."""
    domains = []
    for line in Path(path).read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            domains.append(stripped)
    return domains
