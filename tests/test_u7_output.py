"""U7 — JSON results output conforming to schema/results.schema.json.

Contract: domain_check.output exposes
  * to_json(rows: list[dict]) -> str: full results document as JSON text,
    with tool/version/checked_at envelope, validating against the schema.
"""

import json
from pathlib import Path

import jsonschema

from domain_check.output import to_json

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "schema" / "results.schema.json").read_text()
)

ROWS = [
    {
        "domain": "example.com",
        "verdict": "registered",
        "confidence": 1.0,
        "sources": ["rdap"],
        "rdap_status": "registered",
        "error": None,
    },
    {
        "domain": "surely-free-4q7x9z.com",
        "verdict": "available",
        "confidence": 0.95,
        "sources": ["rdap", "dns"],
        "rdap_status": None,
        "error": None,
    },
]


def test_output_validates_against_schema():
    payload = json.loads(to_json(ROWS))
    jsonschema.validate(payload, SCHEMA)


def test_envelope_fields():
    payload = json.loads(to_json(ROWS))
    assert payload["tool"] == "domain-check"
    assert payload["version"]
    assert payload["checked_at"].endswith("Z") or "+" in payload["checked_at"]


def test_rows_pass_through_in_order():
    payload = json.loads(to_json(ROWS))
    assert [r["domain"] for r in payload["results"]] == [
        "example.com",
        "surely-free-4q7x9z.com",
    ]
    assert payload["results"][1]["verdict"] == "available"
