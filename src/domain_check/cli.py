"""Command-line interface for domain-check.

U1 scope: argument parsing, usage, version, exit codes. Lookup wiring
arrives with U7 (output) and U9 (purchase links).

Exit codes: 0 success, 2 usage error, 3 runtime failure / not implemented.
"""

import argparse
import sys

from domain_check import __version__


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

    print("domain-check: lookups not implemented yet (pending units U2-U7)", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
