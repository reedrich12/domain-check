"""Verdict engine (U5): combine RDAP and DNS signals into a verdict.

Invariant (baseline amendment A1): only RDAP can assert "available". DNS
evidence may raise or lower confidence or confirm "registered" — NXDOMAIN
is not proof of availability, because unregistered and registered-but-
unresolving domains look identical to DNS. RDAP absence with no other
authority yields "unknown".

Confidence tiers:
  0.99  RDAP says registered (authoritative)
  0.95  RDAP says available, corroborated by absent DNS
  0.70  single moderately-reliable signal (RDAP-available alone, or DNS
        presence alone)
  0.60  conflicting signals resolved toward "registered"
  <=0.40 no conclusive signal
"""

from dataclasses import dataclass, field


@dataclass
class Verdict:
    verdict: str  # "available" | "registered" | "unknown"
    confidence: float
    sources: list[str] = field(default_factory=list)  # signals actually used


def decide(rdap_status: str | None = None, dns_status: str | None = None) -> Verdict:
    """rdap_status: "registered" | "available" | "unknown" | None
    dns_status: "registered" | "no_dns" | "unknown" | None
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

    # RDAP gave no authority (unknown or absent): DNS may only confirm
    # "registered", never "available".
    if dns_status == "registered":
        return Verdict("registered", 0.70, ["dns"])
    if dns_status == "no_dns":
        return Verdict("unknown", 0.40, ["dns"])
    return Verdict("unknown", 0.25, [])
