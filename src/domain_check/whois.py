"""WHOIS fallback probe.

Port 43 WHOIS, used only when RDAP returns no authority. The TLD's WHOIS
server is discovered through IANA's referral (whois.iana.org answers a TLD
query with a "whois:" line), then the domain is queried against it and the
response text is classified:

  "No match" / "NOT FOUND" / "status: free" ...  -> "available"
  registration fields (Registrar:, Creation Date:, ...) -> "registered"
  rate limits, refusals, unparseable text, errors -> "unknown"

Like RDAP — and unlike DNS — WHOIS is a registry authority, so it may
assert "available". Anything ambiguous maps to "unknown" rather than
guessing; see domain_check.verdict for how the signals combine.

_query() is the socket seam: tests monkeypatch it so no network is used.
"""

import re
import socket

IANA_WHOIS_SERVER = "whois.iana.org"
WHOIS_PORT = 43
DEFAULT_TIMEOUT = 10.0

# Servers that want an explicit "domain <name>" query form; a bare name can
# return unrelated substring matches there.
_DOMAIN_KEYWORD_SERVERS = ("whois.verisign-grs.com",)

_REFERRAL_RE = re.compile(r"^\s*(?:whois|refer):\s*(\S+)\s*$", re.IGNORECASE | re.MULTILINE)

_NOT_FOUND_PATTERNS = (
    "no match",
    "not found",
    "no data found",
    "no entries found",
    "no object found",
    "domain not found",
    "nothing found",
    "status: free",
    "status: available",
    "available for registration",
)

_REGISTERED_PATTERNS = (
    "domain name:",
    "domain:",
    "registrar:",
    "registry domain id:",
    "creation date:",
    "created:",
    "created on:",
    "registered on:",
    "expiry date:",
    "name server:",
    "nserver:",
)

_UNAVAILABLE_PATTERNS = (
    "rate limit",
    "too many requests",
    "quota exceeded",
    "exceeded the maximum",
    "try again later",
    "access denied",
    "connection refused",
    "service unavailable",
)


class WhoisError(Exception):
    """WHOIS could not be reached or produced no usable answer."""


def _query(server: str, request: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Send one WHOIS request and return the raw response text."""
    try:
        with socket.create_connection((server, WHOIS_PORT), timeout=timeout) as sock:
            sock.sendall((request + "\r\n").encode("utf-8"))
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
    except OSError as exc:
        raise WhoisError(f"{server}: {exc}") from exc
    return b"".join(chunks).decode("utf-8", errors="replace")


def server_for_tld(tld: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Ask IANA which WHOIS server is authoritative for *tld*."""
    match = _REFERRAL_RE.search(_query(IANA_WHOIS_SERVER, tld, timeout))
    return match.group(1) if match else None


def classify(response: str) -> str:
    """Map a WHOIS response body to registered / available / unknown."""
    text = response.lower()
    if not text.strip():
        return "unknown"
    # Refusals first: a throttled response must never read as available.
    if any(pattern in text for pattern in _UNAVAILABLE_PATTERNS):
        return "unknown"
    if any(pattern in text for pattern in _NOT_FOUND_PATTERNS):
        return "available"
    if any(pattern in text for pattern in _REGISTERED_PATTERNS):
        return "registered"
    return "unknown"


def probe(domain: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Return "registered", "available" or "unknown" for *domain*."""
    tld = domain.rsplit(".", 1)[-1]
    try:
        server = server_for_tld(tld, timeout)
        if not server:
            return "unknown"
        request = domain
        if server.lower() in _DOMAIN_KEYWORD_SERVERS:
            request = f"domain {domain}"
        return classify(_query(server, request, timeout))
    except WhoisError:
        return "unknown"
    except Exception:
        return "unknown"
