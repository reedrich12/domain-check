"""Command-line interface for domain-check.

U1: argument parsing, usage, version, exit codes.
U7: lookups wired through bulk.check_many with --json output.

Exit codes: 0 success, 2 usage error, 3 runtime failure.
"""

import argparse
import sys

from domain_check import __version__, bulk, output


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
        "--version",
        action="version",
        version=f"domain-check {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
