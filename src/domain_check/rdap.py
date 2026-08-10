"""RDAP client (U3): IANA bootstrap, registry lookup, status classification.

lookup() resolves the domain's TLD to a registry RDAP base URL via the IANA
DNS bootstrap file, queries /domain/<name>, and classifies the answer:

  200         -> "registered"
  404         -> "available"
  anything else (429, 5xx, network errors, no endpoint for the TLD)
              -> "unknown"  (never guess "available" from a non-404)

A custom httpx transport can be injected for all requests (bootstrap and
registry), which is how the offline acceptance tests run. The real IANA
bootstrap is fetched once per process and cached module-wide; injected
transports bypass the cache so tests stay isolated.
"""

from dataclasses import dataclass

import httpx

from domain_check.validate import normalize

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
DEFAULT_TIMEOUT = 10.0

_bootstrap_cache: dict | None = None


@dataclass
class RdapResult:
    status: str  # "registered" | "available" | "unknown"
    raw_status: str | None = None  # registry's own status values, if any
    source_url: str | None = None


def endpoints_for_tld(bootstrap: dict, tld: str) -> list[str]:
    """Return RDAP base URLs serving *tld*, https entries first."""
    for tlds, urls in bootstrap.get("services", []):
        if tld in (t.lower() for t in tlds):
            return sorted(urls, key=lambda u: not u.startswith("https://"))
    return []


def load_bootstrap(client: httpx.Client) -> dict:
    resp = client.get(BOOTSTRAP_URL)
    resp.raise_for_status()
    return resp.json()


def lookup(
    domain: str,
    *,
    transport: httpx.BaseTransport | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> RdapResult:
    global _bootstrap_cache

    domain = normalize(domain)
    tld = domain.rsplit(".", 1)[1]

    with httpx.Client(
        transport=transport, timeout=timeout, follow_redirects=True
    ) as client:
        try:
            if transport is None:
                if _bootstrap_cache is None:
                    _bootstrap_cache = load_bootstrap(client)
                bootstrap = _bootstrap_cache
            else:
                bootstrap = load_bootstrap(client)
        except (httpx.HTTPError, ValueError):
            return RdapResult(status="unknown")

        bases = endpoints_for_tld(bootstrap, tld)
        if not bases:
            return RdapResult(status="unknown")

        url = bases[0].rstrip("/") + f"/domain/{domain}"
        try:
            resp = client.get(url)
        except httpx.HTTPError:
            return RdapResult(status="unknown", source_url=url)

    if resp.status_code == 200:
        raw = None
        try:
            statuses = resp.json().get("status", [])
            if statuses:
                raw = ",".join(statuses)
        except ValueError:
            pass
        return RdapResult(status="registered", raw_status=raw, source_url=url)
    if resp.status_code == 404:
        return RdapResult(status="available", source_url=url)
    return RdapResult(status="unknown", source_url=url)
