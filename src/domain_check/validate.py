"""Domain validation and normalization (U2).

normalize() lowercases, strips surrounding whitespace and a single trailing
dot, converts internationalized labels to punycode, and enforces RFC 1035
shape limits (label charset/length, total name length, at least two labels).
"""

import re

# LDH label: starts and ends with a letter or digit, hyphens only inside,
# 1-63 octets.
_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")

_MAX_NAME_OCTETS = 253


class InvalidDomainError(ValueError):
    """Raised when a domain name is syntactically invalid."""


def normalize(domain: str) -> str:
    """Return the canonical form of *domain* or raise InvalidDomainError."""
    if not isinstance(domain, str):
        raise InvalidDomainError(f"not a string: {domain!r}")

    name = domain.strip().lower()
    if name.endswith("."):
        name = name[:-1]
    if not name or "." not in name:
        raise InvalidDomainError(f"invalid domain: {domain!r}")

    labels = []
    for label in name.split("."):
        if not label.isascii():
            try:
                label = label.encode("idna").decode("ascii")
            except UnicodeError as exc:
                raise InvalidDomainError(f"invalid IDN label in: {domain!r}") from exc
        if not _LABEL_RE.match(label):
            raise InvalidDomainError(f"invalid label {label!r} in: {domain!r}")
        labels.append(label)

    name = ".".join(labels)
    if len(name) > _MAX_NAME_OCTETS:
        raise InvalidDomainError(f"domain exceeds {_MAX_NAME_OCTETS} octets: {domain!r}")
    return name
