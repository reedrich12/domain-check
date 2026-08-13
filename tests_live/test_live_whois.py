"""Live acceptance for the WHOIS fallback — real port 43 traffic.

Excluded from the default run; exercised by `checks/verify.sh --live`.

WHOIS servers throttle aggressively and several block outright after a
burst of queries. These tests therefore distinguish two situations:

  * WHOIS is reachable  -> assert the real classification
  * WHOIS refuses us    -> skip, because a throttled host cannot tell us
                           anything about the code under test

Skipping is deliberate: turning "the registry blocked this host" into a
test failure would make the gate flaky, while asserting a weaker
condition would let real regressions through. Classification of
throttled and refused responses is covered offline in tests/test_whois.py,
where it is deterministic.
"""

import pytest

from domain_check import whois

pytestmark = pytest.mark.live

SURELY_AVAILABLE = "loop-baseline-4q7x9z2j8k5v-domain-check.com"


@pytest.fixture(scope="module")
def com_whois_server():
    """The .com WHOIS server, or skip the module if WHOIS is unreachable."""
    try:
        server = whois.server_for_tld("com")
    except whois.WhoisError as exc:
        pytest.skip(f"WHOIS unreachable from this host (throttled or blocked): {exc}")
    if not server:
        pytest.skip("IANA returned no WHOIS referral for .com")
    return server


def probe_or_skip(domain: str, server: str) -> str:
    """Classify *domain*, skipping if the registry refuses this host."""
    try:
        request = domain
        if server.lower() in whois._DOMAIN_KEYWORD_SERVERS:
            request = f"domain {domain}"
        response = whois._query(server, request)
    except whois.WhoisError as exc:
        pytest.skip(f"WHOIS query refused (throttled or blocked): {exc}")
    verdict = whois.classify(response)
    if verdict == "unknown":
        pytest.skip("WHOIS returned no usable answer (likely rate limited)")
    return verdict


def test_iana_referral_resolves_for_com(com_whois_server):
    assert com_whois_server


def test_registered_domain_reads_as_registered(com_whois_server):
    assert probe_or_skip("example.com", com_whois_server) == "registered"


def test_unregistered_domain_reads_as_available(com_whois_server):
    assert probe_or_skip(SURELY_AVAILABLE, com_whois_server) == "available"


def test_unknown_tld_is_unknown_not_available():
    # No IANA referral exists, so there is no authority to assert anything.
    # probe() swallows transport errors by design, so this holds whether or
    # not WHOIS is reachable — it must never read as available.
    assert whois.probe("example.invalid-tld-4q7x9z") == "unknown"
