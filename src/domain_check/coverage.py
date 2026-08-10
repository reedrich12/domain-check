"""TLD coverage report (U10) over the IANA RDAP bootstrap.

report() classifies every TLD mentioned in the bootstrap: resolvable when
at least one https RDAP endpoint serves it, unresolvable otherwise.
Unresolvable TLDs are listed by name — never hidden or summarized away —
and total_tlds == len(resolvable) + len(unresolvable) always holds.
"""

from dataclasses import dataclass

import httpx

from domain_check import rdap


@dataclass
class CoverageReport:
    total_tlds: int
    resolvable: list[str]  # sorted TLDs with at least one https endpoint
    unresolvable: list[str]  # sorted TLDs with no usable endpoint


def report(bootstrap: dict) -> CoverageReport:
    resolvable: set[str] = set()
    unresolvable: set[str] = set()
    for tlds, urls in bootstrap.get("services", []):
        usable = any(url.startswith("https://") for url in urls)
        for tld in tlds:
            (resolvable if usable else unresolvable).add(tld.lower())
    # A TLD served by any usable service counts as resolvable.
    unresolvable -= resolvable
    return CoverageReport(
        total_tlds=len(resolvable) + len(unresolvable),
        resolvable=sorted(resolvable),
        unresolvable=sorted(unresolvable),
    )


def live_report() -> CoverageReport:
    """Coverage of the real (cached) IANA bootstrap."""
    with httpx.Client(
        timeout=rdap.DEFAULT_TIMEOUT, follow_redirects=True
    ) as client:
        if rdap._bootstrap_cache is None:
            rdap._bootstrap_cache = rdap.load_bootstrap(client)
    return report(rdap._bootstrap_cache)
