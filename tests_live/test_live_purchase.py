"""Live acceptance for U9 — the purchase URL must actually answer.

For an available domain, the emitted registrar search URL must respond to a
plain GET with HTTP < 400 and echo the exact domain string in the body.
If the primary registrar (Porkbun) starts blocking probes, switch to the
documented fallback (Namecheap) via a logged baseline amendment.
"""

import httpx
import pytest

pytestmark = pytest.mark.live

DOMAIN = "loop-baseline-4q7x9z2j8k5v-domain-check.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) domain-check-live-test"
    )
}


def test_purchase_url_answers_and_echoes_domain():
    from domain_check import purchase

    url = purchase.build_purchase_url(DOMAIN)
    resp = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
    assert resp.status_code < 400, f"{url} -> {resp.status_code}"
    assert DOMAIN in resp.text, f"domain string not echoed in body of {url}"
