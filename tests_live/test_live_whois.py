"""Live acceptance for the WHOIS fallback — real port 43 traffic.

Excluded from the default run; exercised by `checks/verify.sh --live`.
"""

import pytest

from domain_check import whois

pytestmark = pytest.mark.live

SURELY_AVAILABLE = "loop-baseline-4q7x9z2j8k5v-domain-check.com"


def test_iana_referral_resolves_for_com():
    assert whois.server_for_tld("com")


def test_registered_domain_reads_as_registered():
    assert whois.probe("example.com") == "registered"


def test_unregistered_domain_reads_as_available():
    assert whois.probe(SURELY_AVAILABLE) == "available"


def test_unknown_tld_is_unknown_not_available():
    # No IANA referral exists, so there is no authority to assert anything.
    assert whois.probe("example.invalid-tld-4q7x9z") == "unknown"
