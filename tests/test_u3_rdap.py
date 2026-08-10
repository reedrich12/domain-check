"""U3 — RDAP client: IANA bootstrap, lookup, status classification.

Contract: domain_check.rdap exposes
  * lookup(domain: str, *, transport=None) -> RdapResult
    - transport, when given, is an httpx transport used for ALL requests
      (bootstrap and registry), so tests run fully offline.
  * RdapResult has .status in {"registered", "available", "unknown"}
    and .raw_status (the registry's own status value or None).
"""

import httpx

from domain_check.rdap import lookup

BOOTSTRAP = {
    "description": "RDAP bootstrap file for Domain Name System registrations",
    "services": [[["com"], ["https://rdap.example-registry.test/"]]],
}


def transport_for(domain_response: httpx.Response) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "data.iana.org":
            return httpx.Response(200, json=BOOTSTRAP)
        return domain_response

    return httpx.MockTransport(handler)


def test_registered_domain():
    response = httpx.Response(
        200, json={"objectClassName": "domain", "ldhName": "example.com"}
    )
    result = lookup("example.com", transport=transport_for(response))
    assert result.status == "registered"


def test_available_domain_via_404():
    result = lookup(
        "surely-free.com", transport=transport_for(httpx.Response(404))
    )
    assert result.status == "available"


def test_server_error_is_unknown():
    result = lookup(
        "flaky.com", transport=transport_for(httpx.Response(500))
    )
    assert result.status == "unknown"


def test_rate_limit_is_unknown_not_available():
    result = lookup(
        "throttled.com", transport=transport_for(httpx.Response(429))
    )
    assert result.status == "unknown"
