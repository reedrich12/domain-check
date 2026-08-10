"""Purchase-link builder (U9).

Every result row with verdict "available" gets a purchase_url: a registrar
search URL for that exact domain (required by schema/results.schema.json).

Primary registrar: Porkbun. Fallback: Namecheap. Both are documented in
README.md; the live gate probes the primary URL, and switching registrars
requires a logged baseline amendment - never a silent change.
"""

from urllib.parse import quote

PRIMARY_SEARCH_URL = "https://porkbun.com/checkout/search?q={domain}"
FALLBACK_SEARCH_URL = (
    "https://www.namecheap.com/domains/registration/results/?domain={domain}"
)


def build_purchase_url(domain: str) -> str:
    """Primary registrar search URL for *domain* (already normalized)."""
    return PRIMARY_SEARCH_URL.format(domain=quote(domain, safe=".-"))


def build_fallback_url(domain: str) -> str:
    """Fallback registrar search URL for *domain*."""
    return FALLBACK_SEARCH_URL.format(domain=quote(domain, safe=".-"))


def attach_purchase_urls(rows: list[dict]) -> list[dict]:
    """Add purchase_url to every available row; leave other rows untouched."""
    for row in rows:
        if row.get("verdict") == "available":
            row["purchase_url"] = build_purchase_url(row["domain"])
    return rows
