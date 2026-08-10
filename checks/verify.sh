#!/usr/bin/env bash
# Independent verification gate for the domain-check loop.
#
# Usage:
#   checks/verify.sh          # offline gate (syntax, schema, ledger, guard, tests/)
#   checks/verify.sh --live   # offline gate plus live RDAP/DNS tests (tests_live/)
#
# Exit code 0 means the gate passed. Any other exit code means the gate is red.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-offline}"

echo "==> [1/5] Python syntax check"
python3 -m compileall -q src tests tests_live manifest_guard.py

echo "==> [2/5] results schema is a valid JSON Schema"
python3 - <<'PY'
import json
from jsonschema import Draft202012Validator
with open("schema/results.schema.json") as fh:
    Draft202012Validator.check_schema(json.load(fh))
print("schema ok")
PY

echo "==> [3/5] ledger well-formed"
python3 - <<'PY'
import json
with open(".loop/ledger.json") as fh:
    ledger = json.load(fh)
ids = [u["id"] for u in ledger["units"]]
assert ids == [f"U{i}" for i in range(1, 9)], f"unexpected unit ids: {ids}"
for unit in ledger["units"]:
    assert unit["status"] in {"pending", "in_progress", "done", "failed"}, unit
    assert unit["allowed_paths"], f"{unit['id']} has no allowed_paths"
    assert unit["acceptance"], f"{unit['id']} has no acceptance command"
print("ledger ok")
PY

echo "==> [4/5] manifest guard"
python3 manifest_guard.py

echo "==> [5/5] offline acceptance tests"
python3 -m pytest tests/ -q

if [ "$MODE" = "--live" ] || [ "$MODE" = "live" ]; then
    echo "==> [live] live acceptance tests (real RDAP/DNS)"
    python3 -m pytest tests_live/ -q -m live
fi

echo "VERIFY: PASS"
