"""Command-line interface for domain-check.

U1: argument parsing, usage, version, exit codes.
U7: lookups wired through bulk.check_many with --json output.

Exit codes: 0 success, 2 usage error, 3 runtime failure.
"""

import argparse
import json
import sys

from domain_check import __version__, bulk, output


def _run_coverage(as_json: bool) -> int:
    from domain_check import coverage

    try:
        rep = coverage.live_report()
    except Exception as exc:
        print(f"domain-check: coverage failed: {exc}", file=sys.stderr)
        return 3
    if as_json:
        print(
            json.dumps(
                {
                    "total_tlds": rep.total_tlds,
                    "resolvable": len(rep.resolvable),
                    "unresolvable": rep.unresolvable,
                },
                indent=2,
            )
        )
    else:
        print(f"TLDs in bootstrap: {rep.total_tlds}")
        print(f"resolvable: {len(rep.resolvable)}")
        print(f"unresolvable: {len(rep.unresolvable)}")
        for tld in rep.unresolvable:
            print(f"  {tld}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="domain-check",
        description=(
            "Check whether domains are registered or available, using RDAP "
            "as the authoritative source with a DNS probe as fallback."
        ),
    )
    parser.add_argument(
        "domains",
        nargs="*",
        metavar="DOMAIN",
        help="one or more domains to check",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit results as JSON conforming to schema/results.schema.json",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        help="read domains from FILE (one per line, '#' comments allowed)",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help=(
            "report resolvable vs unresolvable TLDs from the cached IANA "
            "RDAP bootstrap (unresolvable TLDs are listed by name)"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"domain-check {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.coverage:
        return _run_coverage(as_json=args.json)

    if not args.domains and not args.input:
        parser.print_usage(sys.stderr)
        parser.exit(2, "domain-check: error: provide at least one DOMAIN or --input FILE\n")

    domains = []
    if args.input:
        try:
            domains.extend(bulk.read_domains(args.input))
        except OSError as exc:
            print(f"domain-check: cannot read {args.input}: {exc}", file=sys.stderr)
            return 3
    domains.extend(args.domains)

    rows = bulk.check_many(domains)

    if args.json:
        print(output.to_json(rows))
    else:
        for row in rows:
            detail = row["error"] or f"confidence {row['confidence']:.2f}"
            print(f"{row['domain']}: {row['verdict']} ({detail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
