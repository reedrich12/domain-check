"""JSON results output (U7), conforming to schema/results.schema.json."""

import json
from datetime import datetime, timezone

from domain_check import __version__


def to_json(rows: list[dict]) -> str:
    """Wrap result rows in the tool/version/checked_at envelope."""
    payload = {
        "tool": "domain-check",
        "version": __version__,
        "checked_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "results": list(rows),
    }
    return json.dumps(payload, indent=2)
