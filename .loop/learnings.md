# Loop learnings

## Iteration 1 — 2026-08-10
- **Attempted:** Pre-flight before implementing U1: read spec/ledger/learnings, ran `bash checks/verify.sh` to establish the gate baseline.
- **Outcome:** No unit attempted. Gate found structurally un-passable per-unit: verify.sh step 5 runs the full suite, and unimplemented unit modules abort pytest at collection (exit 2, 8 collection errors), so no single unit's success can ever flip the exit code to 0. The loop's accept/reset rules would discard every iteration's work and trip the identical-error stall rule by iteration 3.
- **Conclusion:** Check is wrong per the loop contract → wrote HANDOFF.md with a ready-to-apply amendment (A2: gate on done/in_progress units' acceptance tests) and stopped the loop awaiting human approval. Never proceed by weakening a gate without approval; never let a doomed protocol burn its stall budget.
