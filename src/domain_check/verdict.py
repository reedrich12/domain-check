"""Verdict engine (U5): combine RDAP, WHOIS and DNS signals into a verdict.

Invariant (baseline amendment A1): only a *registry authority* can assert
"available". DNS evidence may raise or lower confidence or confirm
"registered", never assert availability — NXDOMAIN is not proof of
availability, because unregistered and registered-but-unresolving domains
look identical to DNS. With no authority at all the verdict is "unknown".

RDAP and WHOIS are both registry authorities and both may assert
"available"; WHOIS is scored slightly lower because its responses are
free text and parsed heuristically. WHOIS is consulted only when RDAP
returned no authority, so RDAP's rulings are never overridden.

Confidence tiers:
  0.99  RDAP says registered (authoritative)
  0.95  RDAP says available, corroborated by absent DNS
  0.90  WHOIS says registered, or WHOIS-available corroborated by absent DNS
  0.70  single moderately-reliable signal (RDAP-available alone, or DNS
        presence alone)
  0.65  WHOIS says available, uncorroborated
  0.60  conflicting signals resolved toward "registered"
  <=0.40 no conclusive signal
"""

from dataclasses import dataclass, field


@dataclass
class Verdict:
    verdict: str  # "available" | "registered" | "unknown"
    confidence: float
    sources: list[str] = field(default_factory=list)  # signals actually used


def decide(
    rdap_status: str | None = None,
    dns_status: str | None = None,
    whois_status: str | None = None,
) -> Verdict:
    """rdap_status: "registered" | "available" | "unknown" | None
    dns_status: "registered" | "no_dns" | "unknown" | None
    whois_status: "registered" | "available" | "unknown" | None
    """
    if rdap_status == "registered":
        return Verdict("registered", 0.99, ["rdap"])

    if rdap_status == "available":
        if dns_status == "no_dns":
            return Verdict("available", 0.95, ["rdap", "dns"])
        if dns_status == "registered":
            # Conflict: the name resolves, so never claim available.
            return Verdict("registered", 0.60, ["dns"])
        return Verdict("available", 0.70, ["rdap"])

    # RDAP gave no authority (unknown or absent). WHOIS is the fallback
    # authority and, like RDAP, may assert availability.
    if whois_status == "registered":
        return Verdict("registered", 0.90, ["whois"])

    if whois_status == "available":
        if dns_status == "registered":
            # Same conflict rule: the name resolves, so never claim available.
            return Verdict("registered", 0.60, ["dns"])
        if dns_status == "no_dns":
            return Verdict("available", 0.90, ["whois", "dns"])
        return Verdict("available", 0.65, ["whois"])

    # No authority at all: DNS may only confirm "registered".
    if dns_status == "registered":
        return Verdict("registered", 0.70, ["dns"])
    if dns_status == "no_dns":
        return Verdict("unknown", 0.40, ["dns"])
    return Verdict("unknown", 0.25, [])
