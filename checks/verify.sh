#!/usr/bin/env bash
# Independent verification gate for the domain-check loop.
#
# Usage:
#   checks/verify.sh              # offline gate; step 5 tests ledger-selected units
#                                 # (status done or in_progress) - per-iteration feedback
#   checks/verify.sh --all        # step 5 runs the FULL offline suite regardless of ledger
#   checks/verify.sh --live       # adds live RDAP/DNS tests (tests_live/)
#   checks/verify.sh --all --live # the done_when gate: must pass twice consecutively
#
# Exit code 0 means the gate passed. Any other exit code means the gate is red.
# Amendment A2': ledger-selected step 5 can never satisfy done_when; only
# --all --live (twice consecutively) can. Selection is monotonic: tests of
# done units are always included.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE_ALL=0
MODE_LIVE=0
for arg in "$@"; do
    case "$arg" in
        --all) MODE_ALL=1 ;;
        --live|live) MODE_LIVE=1 ;;
        offline) ;;
        *) echo "verify.sh: unknown argument: $arg" >&2; exit 64 ;;
    esac
done

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
assert ids == [f"U{i}" for i in range(1, 11)], f"unexpected unit ids: {ids}"
for unit in ledger["units"]:
    assert unit["status"] in {"pending", "in_progress", "done", "failed"}, unit
    assert unit["allowed_paths"], f"{unit['id']} has no allowed_paths"
    assert unit["acceptance"], f"{unit['id']} has no acceptance command"
print("ledger ok")
PY

echo "==> [4/5] manifest guard"
python3 manifest_guard.py

if [ "$MODE_ALL" = "1" ]; then
    echo "==> [5/5] offline acceptance tests (--all: full suite)"
    python3 -m pytest tests/ -q
else
    echo "==> [5/5] offline acceptance tests (ledger-selected: done + in_progress units)"
    UNIT_TESTS=$(python3 - <<'PY'
import json
import re

with open(".loop/ledger.json") as fh:
    ledger = json.load(fh)
paths = []
for unit in ledger["units"]:
    if unit["status"] in ("done", "in_progress"):
        match = re.search(r"tests/\S+\.py", unit["acceptance"])
        if match and match.group(0) not in paths:
            paths.append(match.group(0))
print(" ".join(paths))
PY
)
    if [ -n "$UNIT_TESTS" ]; then
        python3 -m pytest $UNIT_TESTS -q
    else
        echo "no units done or in_progress yet - nothing to test"
    fi
fi

if [ "$MODE_LIVE" = "1" ]; then
    echo "==> [live] live acceptance tests (real RDAP/DNS)"
    python3 -m pytest tests_live/ -q -m live
fi

echo "VERIFY: PASS"
