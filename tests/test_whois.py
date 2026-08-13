"""WHOIS fallback: response classification, verdict integration, wiring.

The socket is never touched — domain_check.whois._query is monkeypatched.
"""

import pytest

from domain_check import bulk, whois
from domain_check.verdict import decide

IANA_REFERRAL = "refer:         whois.verisign-grs.com\n\nwhois:        whois.verisign-grs.com\n"

NOT_FOUND_RESPONSE = 'No match for "SURELY-FREE-4Q7X9Z.COM".\n>>> Last update of whois database: ...'

REGISTERED_RESPONSE = """
   Domain Name: EXAMPLE.COM
   Registry Domain ID: 2336799_DOMAIN_COM-VRSN
   Registrar: RESERVED-Internet Assigned Numbers Authority
   Creation Date: 1995-08-14T04:00:00Z
   Name Server: A.IANA-SERVERS.NET
"""

RATE_LIMITED_RESPONSE = "WHOIS LIMIT EXCEEDED - SEE WWW.PIR.ORG: you have exceeded the maximum query rate\n"


# --- response classification -------------------------------------------------


def test_not_found_is_available():
    assert whois.classify(NOT_FOUND_RESPONSE) == "available"


def test_registration_fields_mean_registered():
    assert whois.classify(REGISTERED_RESPONSE) == "registered"


def test_rate_limit_is_unknown_not_available():
    # A throttled response must never read as availability.
    assert whois.classify(RATE_LIMITED_RESPONSE) == "unknown"


def test_empty_response_is_unknown():
    assert whois.classify("   \n  ") == "unknown"


def test_unrecognized_response_is_unknown():
    assert whois.classify("something entirely unexpected") == "unknown"


# --- referral and probe ------------------------------------------------------


def fake_transport(monkeypatch, domain_response, referral=IANA_REFERRAL):
    """Route IANA queries to *referral* and everything else to the response."""
    calls = []

    def _query(server, request, timeout=whois.DEFAULT_TIMEOUT):
        calls.append((server, request))
        if server == whois.IANA_WHOIS_SERVER:
            return referral
        return domain_response

    monkeypatch.setattr(whois, "_query", _query)
    return calls


def test_probe_follows_the_iana_referral(monkeypatch):
    calls = fake_transport(monkeypatch, REGISTERED_RESPONSE)
    assert whois.probe("example.com") == "registered"
    assert calls[0] == (whois.IANA_WHOIS_SERVER, "com")
    assert calls[1][0] == "whois.verisign-grs.com"


def test_probe_uses_domain_keyword_for_verisign(monkeypatch):
    calls = fake_transport(monkeypatch, NOT_FOUND_RESPONSE)
    assert whois.probe("surely-free-4q7x9z.com") == "available"
    assert calls[1][1] == "domain surely-free-4q7x9z.com"


def test_probe_without_referral_is_unknown(monkeypatch):
    fake_transport(monkeypatch, REGISTERED_RESPONSE, referral="no referral here\n")
    assert whois.probe("example.nonsense") == "unknown"


def test_probe_survives_socket_errors(monkeypatch):
    def boom(server, request, timeout=whois.DEFAULT_TIMEOUT):
        raise whois.WhoisError("connection reset")

    monkeypatch.setattr(whois, "_query", boom)
    assert whois.probe("example.com") == "unknown"


# --- verdict integration -----------------------------------------------------


def test_whois_registered_when_rdap_unknown():
    v = decide(rdap_status="unknown", whois_status="registered")
    assert v.verdict == "registered"
    assert v.sources == ["whois"]


def test_whois_available_corroborated_by_no_dns():
    v = decide(rdap_status="unknown", dns_status="no_dns", whois_status="available")
    assert v.verdict == "available"
    assert v.confidence >= 0.9
    assert set(v.sources) == {"whois", "dns"}


def test_whois_available_alone_is_lower_confidence_than_rdap():
    whois_only = decide(rdap_status="unknown", whois_status="available")
    rdap_only = decide(rdap_status="available")
    assert whois_only.verdict == "available"
    assert whois_only.confidence < rdap_only.confidence


def test_whois_available_conflicting_with_dns_never_reports_available():
    v = decide(rdap_status="unknown", dns_status="registered", whois_status="available")
    assert v.verdict in {"registered", "unknown"}


def test_whois_unknown_falls_through_to_dns_logic():
    with_whois = decide(rdap_status="unknown", dns_status="no_dns", whois_status="unknown")
    without = decide(rdap_status="unknown", dns_status="no_dns")
    assert (with_whois.verdict, with_whois.confidence) == (without.verdict, without.confidence)


def test_rdap_authority_is_never_overridden_by_whois():
    # RDAP ruled; WHOIS disagreeing must not change the verdict.
    assert decide(rdap_status="registered", whois_status="available").verdict == "registered"
    assert decide(rdap_status="available", whois_status="registered").verdict == "available"


@pytest.mark.parametrize("dns_status", [None, "no_dns", "registered", "unknown"])
def test_dns_alone_still_never_yields_available(dns_status):
    # The A1 invariant survives the new parameter: DNS with no authority
    # (RDAP or WHOIS) can never produce "available".
    assert decide(dns_status=dns_status).verdict != "available"
    assert decide(dns_status=dns_status, whois_status="unknown").verdict != "available"


# --- wiring ------------------------------------------------------------------


class FakeRdap:
    def __init__(self, status):
        self.status = status
        self.raw_status = None


def wire(monkeypatch, rdap_status, dns_status="no_dns"):
    """Stub the whole pipeline; record whether WHOIS was consulted."""
    probed = []
    monkeypatch.setattr(bulk.rdap, "lookup", lambda name: FakeRdap(rdap_status))
    monkeypatch.setattr(bulk.dnscheck, "probe", lambda name: dns_status)

    def fake_whois(name):
        probed.append(name)
        return "available"

    monkeypatch.setattr(bulk.whois, "probe", fake_whois)
    return probed


def test_whois_is_not_consulted_by_default(monkeypatch):
    probed = wire(monkeypatch, rdap_status="unknown")
    row = bulk.check_one("example.com")
    assert probed == []
    assert row["verdict"] == "unknown"


def test_whois_consulted_when_enabled_and_rdap_unknown(monkeypatch):
    probed = wire(monkeypatch, rdap_status="unknown")
    row = bulk.check_one("example.com", use_whois=True)
    assert probed == ["example.com"]
    assert row["verdict"] == "available"
    assert "whois" in row["sources"]


def test_whois_skipped_when_rdap_was_authoritative(monkeypatch):
    probed = wire(monkeypatch, rdap_status="available")
    row = bulk.check_one("example.com", use_whois=True)
    assert probed == []
    assert row["verdict"] == "available"


def test_check_many_passes_the_flag_through(monkeypatch):
    probed = wire(monkeypatch, rdap_status="unknown")
    rows = bulk.check_many(["a.com", "b.com"], use_whois=True)
    assert probed == ["a.com", "b.com"]
    assert [r["verdict"] for r in rows] == ["available", "available"]
    # Schema requires a purchase link on every available row, whatever the
    # authority that produced the verdict.
    assert all(r["purchase_url"] for r in rows)


def test_whois_sourced_rows_conform_to_the_results_schema(monkeypatch):
    import json
    from pathlib import Path

    import jsonschema

    from domain_check.output import to_json

    wire(monkeypatch, rdap_status="unknown")
    rows = bulk.check_many(["a.com"], use_whois=True)
    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "schema" / "results.schema.json").read_text()
    )
    jsonschema.validate(json.loads(to_json(rows)), schema)
    assert "whois" in rows[0]["sources"]
