"""U9 — purchase-link builder.

Contract: domain_check.purchase exposes
  * build_purchase_url(domain: str) -> str: https search URL at the primary
    registrar (Porkbun) containing the exact domain string
  * build_fallback_url(domain: str) -> str: same contract at the fallback
    registrar (Namecheap)
  * attach_purchase_urls(rows: list[dict]) -> list[dict]: adds purchase_url
    to every row whose verdict is "available" (using the primary registrar);
    rows with any other verdict are left without the key.

Registrar choice and fallback are recorded in README.md; switching requires
a logged baseline amendment because the live probe test pins the behavior.
"""

from pathlib import Path
from urllib.parse import urlparse

from domain_check import purchase

REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "example-avail-4q7x9z.com"


def test_primary_url_is_https_porkbun_and_contains_domain():
    url = purchase.build_purchase_url(DOMAIN)
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.hostname and parsed.hostname.endswith("porkbun.com")
    assert DOMAIN in url


def test_fallback_url_is_https_namecheap_and_contains_domain():
    url = purchase.build_fallback_url(DOMAIN)
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.hostname and parsed.hostname.endswith("namecheap.com")
    assert DOMAIN in url


def test_attach_adds_purchase_url_only_to_available_rows():
    rows = [
        {"domain": "taken.com", "verdict": "registered", "confidence": 1.0, "sources": ["rdap"]},
        {"domain": DOMAIN, "verdict": "available", "confidence": 0.95, "sources": ["rdap", "dns"]},
        {"domain": "meh.com", "verdict": "unknown", "confidence": 0.3, "sources": []},
    ]
    out = purchase.attach_purchase_urls(rows)
    assert [r["domain"] for r in out] == ["taken.com", DOMAIN, "meh.com"]
    assert "purchase_url" not in out[0]
    assert out[1]["purchase_url"] == purchase.build_purchase_url(DOMAIN)
    assert "purchase_url" not in out[2]


def test_readme_documents_registrar_choice_and_fallback():
    text = (REPO_ROOT / "README.md").read_text().lower()
    assert "porkbun.com" in text
    assert "namecheap.com" in text
