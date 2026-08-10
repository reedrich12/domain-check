"""U2 — domain validation and normalization.

Contract: domain_check.validate exposes
  * normalize(domain: str) -> str  (lowercase, strip trailing dot, IDN -> punycode)
  * InvalidDomainError raised for syntactically invalid domains
"""

import pytest

from domain_check.validate import InvalidDomainError, normalize


def test_lowercases_and_strips_trailing_dot():
    assert normalize("Example.COM.") == "example.com"


def test_passes_through_already_normalized():
    assert normalize("example.org") == "example.org"


def test_idn_converted_to_punycode():
    assert normalize("bücher.de") == "xn--bcher-kva.de"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "no-dots",
        "-leadinghyphen.com",
        "trailinghyphen-.com",
        "spa ce.com",
        "under_score.com",
        ("a" * 64) + ".com",  # label longer than 63 octets
        "a." + ("b" * 63 + ".") * 4 + "com",  # name longer than 253 octets
    ],
)
def test_rejects_invalid_domains(bad):
    with pytest.raises(InvalidDomainError):
        normalize(bad)
