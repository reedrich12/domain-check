"""DNS fallback probe (U4).

probe() checks whether a domain has DNS presence via an NS lookup:

  NS records present -> "registered"   (something is delegated)
  NXDOMAIN or empty  -> "no_dns"       (no delegation - NOT proof of
                                        availability; see the U5 invariant)
  timeouts/servfail  -> "unknown"

_query_ns is the resolver seam: tests monkeypatch it, production uses
dnspython. It raises NxDomain when the name does not exist and DnsTimeout
when resolution times out.
"""

import dns.exception
import dns.resolver

DEFAULT_TIMEOUT = 5.0


class NxDomain(Exception):
    """The domain name does not exist in the DNS."""


class DnsTimeout(Exception):
    """DNS resolution timed out."""


def _query_ns(domain: str) -> list[str]:
    """Return the NS target names for *domain* (empty when none)."""
    try:
        answer = dns.resolver.resolve(
            domain, "NS", lifetime=DEFAULT_TIMEOUT, raise_on_no_answer=False
        )
    except dns.resolver.NXDOMAIN as exc:
        raise NxDomain(domain) from exc
    except (dns.exception.Timeout, dns.resolver.LifetimeTimeout) as exc:
        raise DnsTimeout(domain) from exc
    return [record.target.to_text() for record in answer]


def probe(domain: str) -> str:
    try:
        nameservers = _query_ns(domain)
    except NxDomain:
        return "no_dns"
    except DnsTimeout:
        return "unknown"
    except Exception:
        # SERVFAIL, no reachable nameservers, etc. - no usable signal.
        return "unknown"
    return "registered" if nameservers else "no_dns"
