"""U5 — verdict engine combining RDAP and DNS signals.

Contract: domain_check.verdict exposes
  * decide(rdap_status: str | None, dns_status: str | None) -> Verdict
    - rdap_status in {"registered", "available", "unknown", None}
    - dns_status in {"registered", "no_dns", "unknown", None}
  * Verdict has .verdict in {"available", "registered", "unknown"},
    .confidence in [0, 1], and .sources (list of "rdap"/"dns" actually used).
"""

from domain_check.verdict import decide


def test_rdap_registered_is_authoritative():
    v = decide(rdap_status="registered", dns_status=None)
    assert v.verdict == "registered"
    assert v.confidence >= 0.9
    assert "rdap" in v.sources


def test_rdap_available_confirmed_by_no_dns_is_high_confidence():
    v = decide(rdap_status="available", dns_status="no_dns")
    assert v.verdict == "available"
    assert v.confidence >= 0.9
    assert set(v.sources) == {"rdap", "dns"}


def test_rdap_available_alone_is_positive_but_less_confident():
    v = decide(rdap_status="available", dns_status=None)
    assert v.verdict == "available"
    assert 0.5 <= v.confidence < 0.9


def test_rdap_unknown_with_dns_presence_leans_registered():
    v = decide(rdap_status="unknown", dns_status="registered")
    assert v.verdict == "registered"
    assert v.confidence < 0.9
    assert v.sources == ["dns"]


def test_conflicting_signals_never_report_available():
    # RDAP says available but the name resolves: do not claim available.
    v = decide(rdap_status="available", dns_status="registered")
    assert v.verdict in {"registered", "unknown"}


def test_no_signal_is_unknown():
    v = decide(rdap_status="unknown", dns_status=None)
    assert v.verdict == "unknown"
    assert v.confidence <= 0.5
