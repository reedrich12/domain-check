"""Entry point for `python -m domain_check`."""

import sys

from domain_check.cli import main

if __name__ == "__main__":
    sys.exit(main())
