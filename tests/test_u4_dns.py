"""U4 — DNS fallback probe.

Contract: domain_check.dnscheck exposes
  * probe(domain: str) -> str in {"registered", "no_dns", "unknown"}
  * _query_ns(domain: str) -> list[str] internal resolver hook, raising
    NxDomain when the name does not exist and DnsTimeout on timeouts —
    tests monkeypatch this hook so no real DNS traffic happens.
"""

import pytest

from domain_check import dnscheck


def test_ns_records_mean_registered(monkeypatch):
    monkeypatch.setattr(
        dnscheck, "_query_ns", lambda domain: ["a.iana-servers.net."]
    )
    assert dnscheck.probe("example.com") == "registered"


def test_nxdomain_means_no_dns(monkeypatch):
    def raise_nxdomain(domain):
        raise dnscheck.NxDomain(domain)

    monkeypatch.setattr(dnscheck, "_query_ns", raise_nxdomain)
    assert dnscheck.probe("no-such-name.example") == "no_dns"


def test_empty_answer_means_no_dns(monkeypatch):
    monkeypatch.setattr(dnscheck, "_query_ns", lambda domain: [])
    assert dnscheck.probe("empty.example") == "no_dns"


def test_timeout_means_unknown(monkeypatch):
    def raise_timeout(domain):
        raise dnscheck.DnsTimeout(domain)

    monkeypatch.setattr(dnscheck, "_query_ns", raise_timeout)
    assert dnscheck.probe("slow.example") == "unknown"
