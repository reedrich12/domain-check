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

## Iteration 4 — 2026-08-10
- **Attempted:** U3 rdap.py: bootstrap-driven lookup with injectable httpx transport, https-first endpoint selection, 200/404/else -> registered/available/unknown, raw_status from the RDAP status array.
- **Outcome:** Accepted. 4/4 acceptance, verify 19/19 (U1-U3) exit 0, guard clean. Tagged unit/U3-accepted (61df64b, local tag only).
- **Conclusion:** Injected transports must bypass the module bootstrap cache or tests cross-contaminate. Classify only 404 as available — 429/5xx map to unknown so throttling can't masquerade as availability (mirrors the U5 invariant at the RDAP layer).

## Iteration 5 — 2026-08-10
- **Attempted:** U4 dnscheck.py: probe() over a _query_ns seam (dnspython NS resolve with raise_on_no_answer=False), NxDomain/DnsTimeout exception types per the test contract.
- **Outcome:** Accepted. 4/4 acceptance, verify 23/23 (U1-U4) exit 0, guard clean. Tagged unit/U4-accepted (482841c, local tag only).
- **Conclusion:** raise_on_no_answer=False lets 'name exists but no NS' surface as an empty list -> no_dns, distinct from NXDOMAIN. Catch-all -> unknown keeps SERVFAIL from ever implying anything about availability.

## Iteration 6 — 2026-08-10
- **Attempted:** U5 verdict.py: decide() as an explicit rule cascade with documented confidence tiers (0.99/0.95/0.70/0.60/<=0.40) and sources = signals actually used.
- **Outcome:** Accepted. 15/15 acceptance (incl. the 8-case A1 invariant matrix), verify 38/38 (U1-U5) exit 0, guard clean. Tagged unit/U5-accepted (fe64661, local tag only).
- **Conclusion:** Ordering the cascade by RDAP authority first makes the invariant structural: the available branch is only reachable when rdap_status=='available', so no DNS input can produce it. Conflicts resolve toward registered with sources=['dns'] since DNS presence is the deciding evidence.

## Iteration 7 — 2026-08-10
- **Attempted:** U6 bulk.py: check_one pipeline row builder, check_many with try/except per domain, read_domains file parser.
- **Outcome:** Accepted. 3/3 acceptance, verify 41/41 (U1-U6) exit 0, guard clean. Tagged unit/U6-accepted (c754916, local tag only).
- **Conclusion:** Call check_one via module-global lookup inside check_many so monkeypatch works; skip the DNS probe when RDAP already said registered (halves query volume on the common case). Error rows use str(exc) with class-name fallback so the error field is never empty.

## Iteration 8 — 2026-08-10
- **Attempted:** U7 output.py (envelope with UTC Z timestamp) + cli.py wiring (bulk.check_many over positionals and --input, --json vs text output).
- **Outcome:** Accepted. 3/3 acceptance, verify 44/44 (U1-U7) exit 0 including U1's CLI contract unregressed, guard clean. Tagged unit/U7-accepted (5576374, local tag only).
- **Conclusion:** isoformat(timespec='seconds').replace('+00:00','Z') satisfies both the schema's date-time format and the test's Z/+ check. Rows pass through untouched so U9's purchase_url will flow into the envelope without output.py changes.

## Iteration 9 — 2026-08-10
- **Attempted:** U8: README Install/Usage sections (--json, --input, exit codes); entry point and version parity already existed from U1/baseline.
- **Outcome:** Accepted. 3/3 acceptance, verify 47/47 (U1-U8) exit 0, guard clean. Tagged unit/U8-accepted (6ae7628, local tag only).
- **Conclusion:** Docs-only unit; replacing the stale 'baseline only, tests red' banner mattered as much as adding usage — README now describes the shipped CLI, not the scaffold. Smallest unit so far; front-loading pyproject in the baseline made it so.

## Iteration 10 — 2026-08-10
- **Attempted:** U9 purchase.py (URL builders + attach_purchase_urls) wired into bulk.check_many so available rows always carry purchase_url.
- **Outcome:** Accepted. 4/4 acceptance, verify 51/51 (U1-U9) exit 0, guard clean. Tagged unit/U9-accepted (d440a9c, local tag only).
- **Conclusion:** Attaching in check_many (not check_one) keeps the U6 monkeypatch seam intact — patched check_one rows still flow through attach, and non-available rows are untouched so the schema's conditional holds both ways. quote(domain, safe='.-') future-proofs against odd labels without mangling normal names.

## Iteration 11 — 2026-08-10
- **Attempted:** U10 coverage.py (bootstrap TLD classification, any-service-counts resolvable rule) + CLI --coverage with JSON/text output reusing the rdap bootstrap cache. Then the done-state check: verify.sh --all twice, and a --all --live attempt.
- **Outcome:** U10 accepted (3/3 acceptance, verify 54/54, guard clean; tagged unit/U10-accepted=12caadb, local tag only). ALL 10 UNITS DONE. verify.sh --all passed twice consecutively (54/54, 54/54). --live: 2/6 passed (example.com registered via DNS fallback; schema conformance); 4 failed solely on sandbox egress policy (HTTPS blocked except GitHub: no RDAP bootstrap, no coverage fetch, no registrar probe). The 'random domain available' failure is the A1 invariant behaving correctly without RDAP: DNS absence -> unknown, never available.
- **Conclusion:** Offline done-state fully achieved; done_when's remaining requirement (verify.sh --all --live green twice consecutively) is environmentally unreachable here and needs a network-open run. Loop work is complete — nothing left a further iteration could progress.

## Iteration 12 — 2026-08-10 (local machine, network open)
- **Attempted:** Session teleported to the user's Mac; installed the package into a project venv and ran `checks/verify.sh --all --live` twice consecutively to close out done_when.
- **Outcome:** DONE_WHEN SATISFIED. Run 1 and run 2 both green: 54/54 offline, 6/6 live, VERIFY: PASS, exit 0. Live coverage: 1200 bootstrap TLDs, 1198 resolvable, 2 unresolvable listed by name (kg, mg). Porkbun probe answered <400 and echoed the domain — no registrar fallback needed. CLI spot-check: example.com registered (0.99, rdap), random long domain available (0.95, rdap+dns) with purchase_url attached.
- **Conclusion:** Homebrew `pip` pointed at Python 3.11 while `python3` was 3.13, so a bare `pip install -e` left verify.sh's interpreter without deps; a project venv (already gitignored) aligns them without touching checks/. Every live failure seen in the sandbox was environmental, not a defect — the same code went 6/6 the moment real egress existed.
