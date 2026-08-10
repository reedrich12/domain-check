# domain-check

CLI that checks whether domains are registered or available, using RDAP as the
authoritative source with a DNS probe as fallback. Supports single and bulk
input and emits JSON results conforming to `schema/results.schema.json`.

> **Status: baseline.** This repository currently contains only the loop
> baseline — acceptance tests, verification gate, manifest guard, results
> schema, and the unit ledger. No units are implemented yet; the acceptance
> tests are intentionally red.

## Loop structure

| Path | Purpose |
|---|---|
| `.loop/ledger.json` | Unit ledger U1–U8: status, allowed paths, acceptance command per unit |
| `tests/` | Offline acceptance tests (one file per unit, network mocked) |
| `tests_live/` | Live acceptance tests against real RDAP/DNS (`pytest tests_live -m live`) |
| `checks/verify.sh` | Independent verification gate (syntax, schema, ledger, manifest guard, tests) |
| `manifest_guard.py` | Fails if the working tree touches files outside the active unit's manifest |
| `schema/results.schema.json` | JSON Schema for the tool's results output |

## Verification

```sh
checks/verify.sh          # offline gate
checks/verify.sh --live   # offline gate + live RDAP/DNS acceptance tests
```

## Units

- **U1** CLI skeleton: argument parsing, usage, version, exit codes
- **U2** Domain validation & normalization (case, trailing dot, IDN/punycode)
- **U3** RDAP client: IANA bootstrap, lookup, status classification
- **U4** DNS fallback probe (NS lookup, NXDOMAIN handling)
- **U5** Verdict engine combining RDAP and DNS signals with confidence
- **U6** Bulk mode: many domains, order-preserving, per-domain error isolation
- **U7** JSON results output conforming to the schema
- **U8** Packaging & docs: console entry point, usage documentation
