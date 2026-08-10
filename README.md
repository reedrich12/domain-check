# domain-check

CLI that checks whether domains are registered or available, using RDAP as the
authoritative source with a DNS probe as fallback. Supports single and bulk
input and emits JSON results conforming to `schema/results.schema.json`.

## Install

```sh
pip install .            # installs the `domain-check` console script
```

## Usage

```sh
domain-check example.com                 # human-readable verdict
domain-check example.com iana.org --json # JSON conforming to the results schema
domain-check --input domains.txt --json  # bulk: one domain per line, '#' comments
```

Or without installing: `python -m domain_check ... ` (with `src` on
`PYTHONPATH`). Exit codes: 0 success, 2 usage error, 3 runtime failure.

`--json` emits the envelope defined by `schema/results.schema.json`:
verdict (`available` / `registered` / `unknown`), confidence, the evidence
sources used, and — for every available domain — a `purchase_url`.

## Loop structure

| Path | Purpose |
|---|---|
| `.loop/ledger.json` | Unit ledger U1–U10: status, allowed paths, acceptance command per unit, amendment log |
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
- **U9** Purchase-link builder: registrar search URL for every available domain
- **U10** `--coverage` report: resolvable vs unresolvable TLDs from the cached IANA bootstrap

Verdicts also obey a hard invariant (amendment A1): DNS evidence alone can
never produce "available" — DNS only raises/lowers confidence or confirms
"registered". RDAP absence with no other authority yields "unknown".

## Registrar choice (U9)

Every result row with verdict `available` carries a `purchase_url` — a
registrar search URL for that exact domain (required by the results schema).

- **Primary: Porkbun** — `https://porkbun.com/checkout/search?q=<domain>`.
  Chosen as the probe-friendly option: the search page answers a plain GET
  with a server-rendered page that echoes the queried domain.
- **Fallback: Namecheap** — `https://www.namecheap.com/domains/registration/results/?domain=<domain>`.

The live gate (`tests_live/test_live_purchase.py`) asserts the primary URL
answers HTTP <400 and echoes the domain in the body. If Porkbun starts
blocking probes, switch to the fallback via a logged baseline amendment in
`.loop/ledger.json` — do not silently change registrars.
