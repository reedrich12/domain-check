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
domain-check example.com --whois         # add a WHOIS fallback when RDAP is unsure
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

Verdicts obey a hard invariant (amendment A1): only a **registry authority**
can assert "available". DNS evidence alone can never produce it — DNS only
raises/lowers confidence or confirms "registered", because unregistered and
registered-but-unresolving domains look identical to DNS. With no authority
at all the verdict is "unknown".

## WHOIS fallback (`--whois`)

RDAP is the primary authority, but some registries are unreachable,
throttling, or have no RDAP service — those all classify as `unknown`
rather than guessing. Passing `--whois` consults port-43 WHOIS in exactly
that case:

- **Only when RDAP returned no authority.** An RDAP ruling is never
  overridden, and no WHOIS query is spent when RDAP already answered.
- The TLD's WHOIS server is discovered via IANA's referral, then the
  response is classified: not-found text → available, registration fields →
  registered, throttling/refusals/anything unrecognized → `unknown`.
- WHOIS is a registry authority, so like RDAP it **may** assert
  "available" — but it scores slightly lower (0.90 corroborated by absent
  DNS, 0.65 alone, versus RDAP's 0.95/0.70) because its responses are free
  text parsed heuristically.
- Rows resolved this way carry `"whois"` in `sources`.

It is off by default: WHOIS adds two round trips per domain and is
aggressively rate-limited by several registries.

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
