#!/usr/bin/env bash
# Independent verification gate for domain-check.
#
# Usage:
#   checks/verify.sh              # offline gate: the FULL suite under tests/
#   checks/verify.sh --live       # adds live RDAP/DNS/WHOIS tests (tests_live/)
#   checks/verify.sh --all --live # same as --live; --all is kept as a no-op so
#                                 # the done_when command in .loop/ledger.json
#                                 # stays literally valid
#
# Exit code 0 means the gate passed. Any other exit code means the gate is red.
#
# Step 4 used to run only the test files named in ledger unit acceptance
# commands (amendment A2'), which let the loop verify one unit at a time
# without the not-yet-written units failing collection. With every unit done
# that selection only hid things: any test file not owned by a unit - such as
# tests/test_whois.py - was silently skipped, so the default reported 54
# passing while the real total was 78. The default is now the whole suite.
#
# The manifest guard was retired from this gate once the loop completed. It
# enforced that an in-progress unit touched only its declared paths and that
# the tree was clean between units - both meaningless outside the loop, where
# the clean-tree rule only blocked verifying uncommitted work. manifest_guard.py
# is kept for loop history and can still be run directly.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE_LIVE=0
for arg in "$@"; do
    case "$arg" in
        --all) ;;  # retained as a no-op: the full suite is now the default
        --live|live) MODE_LIVE=1 ;;
        offline) ;;
        *) echo "verify.sh: unknown argument: $arg" >&2; exit 64 ;;
    esac
done

echo "==> [1/4] Python syntax check"
python3 -m compileall -q src tests tests_live manifest_guard.py

echo "==> [2/4] results schema is a valid JSON Schema"
python3 - <<'PY'
import json
from jsonschema import Draft202012Validator
with open("schema/results.schema.json") as fh:
    Draft202012Validator.check_schema(json.load(fh))
print("schema ok")
PY

echo "==> [3/4] ledger well-formed"
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

echo "==> [4/4] offline acceptance tests (full suite)"
python3 -m pytest tests/ -q

if [ "$MODE_LIVE" = "1" ]; then
    echo "==> [live] live acceptance tests (real RDAP/DNS)"
    python3 -m pytest tests_live/ -q -m live
fi

echo "VERIFY: PASS"
