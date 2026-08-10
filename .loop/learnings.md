# Loop learnings

## Iteration 1 — 2026-08-10
- **Attempted:** Pre-flight before implementing U1: read spec/ledger/learnings, ran `bash checks/verify.sh` to establish the gate baseline.
- **Outcome:** No unit attempted. Gate found structurally un-passable per-unit: verify.sh step 5 runs the full suite, and unimplemented unit modules abort pytest at collection (exit 2, 8 collection errors), so no single unit's success can ever flip the exit code to 0. The loop's accept/reset rules would discard every iteration's work and trip the identical-error stall rule by iteration 3.
- **Conclusion:** Check is wrong per the loop contract → wrote HANDOFF.md with a ready-to-apply amendment (A2: gate on done/in_progress units' acceptance tests) and stopped the loop awaiting human approval. Never proceed by weakening a gate without approval; never let a doomed protocol burn its stall budget.

## Iteration 2 — 2026-08-10
- **Attempted:** Applied human-approved amendment A2' (ledger-selected verify step 5 + --all flag, done_when = --all --live twice consecutively), then implemented U1 (CLI skeleton: argparse with DOMAIN positionals, --json, --input, --version; exit 2 on no input, exit 3 for not-yet-wired lookups).
- **Outcome:** U1 accepted. tests/test_u1_cli.py 3/3 passed; ledger-selected verify.sh exit 0; manifest guard clean. Tagged unit/U1-accepted.
- **Conclusion:** parser.exit(2, msg) gives the usage-error contract cleanly; keep __version__ in __init__.py as the single version source (U8 asserts it matches pyproject). The A2' gate gives true per-unit feedback — first green verify with an active unit.

## Iteration 3 — 2026-08-10
- **Attempted:** U2 validate.py: normalize() with lowercase/trailing-dot strip, per-label punycode via Python's idna codec, LDH regex per label, 253-octet total cap.
- **Outcome:** Accepted. 12/12 acceptance, verify 15/15 (U1+U2) exit 0, guard clean. Tagged unit/U2-accepted (1c8290a, local tag only).
- **Conclusion:** Convert IDN labels to punycode BEFORE regex/length checks so limits apply to wire format; the idna codec handles per-label encoding cleanly. Validate each label with one LDH regex rather than separate hyphen/charset checks.
