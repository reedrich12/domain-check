# HANDOFF — loop stopped at iteration 1 (gate contradiction, no unit attempted)

## What happened

The loop prompt requires: *"set the unit's ledger status from the exit code
only"* of `bash checks/verify.sh`, and *"never modify tests/, checks/ or
schema/ — if a check seems wrong, stop and write HANDOFF.md instead."*

`checks/verify.sh` step 5 runs the **full** suite (`pytest tests/`). Test
modules for unimplemented units fail at *collection* (missing
`domain_check.*` modules), which aborts the entire pytest run. So the gate's
exit code cannot be 0 until **all ten** units exist.

Consequence if followed literally, verified against the current tree
(verify exit=2, 8 collection errors, one per missing unit module):

1. Iteration 1 implements U1 → verify.sh still red → U1 marked failed →
   `src/` reset to last accepted tag → work discarded.
2. Iteration 2 repeats U1 with the identical error text.
3. The prompt's own stall rule ("identical error text 3 times") fires →
   HANDOFF. Zero units can ever be accepted.

Per-unit acceptance from this gate's exit code is structurally impossible,
so I stopped before burning iterations. A clarifying question was posed
in-session but not answered before the interactive window closed.

## Decision needed (one word is enough)

**Approve amendment A2** (recommended): verify.sh step 5 tests only the
units whose ledger status is `done` or `in_progress`. Once all 10 are done
this selects the entire suite, so the final bar is unchanged — and
`done_when` still additionally requires `verify.sh --live` passing twice
consecutively. Ready-to-apply patch for step 5:

```bash
echo "==> [5/5] acceptance tests (units done or in_progress; full suite once all units land)"
UNIT_TESTS=$(python3 - <<'PY'
import json, re
ledger = json.load(open(".loop/ledger.json"))
paths = []
for u in ledger["units"]:
    if u["status"] in ("done", "in_progress"):
        m = re.search(r"tests/\S+\.py", u["acceptance"])
        if m:
            paths.append(m.group(0))
print(" ".join(paths))
PY
)
if [ -n "$UNIT_TESTS" ]; then
    python3 -m pytest $UNIT_TESTS -q
else
    echo "no units done or in_progress yet - nothing to test"
fi
```

Plus a ledger `amendments` entry A2 recording the approval.

Alternatives:
- **Gate on each unit's own acceptance command** instead of verify.sh's
  exit code (no file changes, but weaker regression protection and it
  contradicts the loop prompt's wording).
- **Different fix of your choosing** — reply with it.

## Also confirm while you're here

1. The loop prompt says "all **8** ledger units" but the human-approved
   baseline-v2 ledger has **10** units (U9 purchase-links, U10 coverage
   were added by amendment A1). I assume the ledger (10) governs — say so
   if not.
2. `LOOP-domaincheck.md` is still absent from the repo (the reconcile was
   done from your message text). Push it if you want it diffed.

## How to restart

After replying (e.g. "A2 approved"), re-run the same `/loop` command. The
next iteration will apply the amendment, delete this file, and proceed with
U1.
