#!/usr/bin/env python3
"""Manifest guard for the domain-check loop.

Fails (exit 1) when the git working tree touches files outside the active
unit's allowed_paths as declared in .loop/ledger.json. With no unit
in_progress, any working-tree change at all is a violation — between units
the tree must be clean.

The ledger itself is always allowed to change: the loop must be able to
flip unit statuses while a unit is in progress.
"""

import fnmatch
import json
import subprocess
import sys

LEDGER_PATH = ".loop/ledger.json"
ALWAYS_ALLOWED = {".loop/ledger.json"}


def _git_lines(*args: str) -> list[str]:
    out = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def changed_files() -> list[str]:
    tracked = _git_lines("diff", "--name-only", "HEAD")
    untracked = _git_lines("ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))


def main() -> int:
    with open(LEDGER_PATH) as fh:
        ledger = json.load(fh)

    active = [u for u in ledger["units"] if u["status"] == "in_progress"]
    changed = [f for f in changed_files() if f not in ALWAYS_ALLOWED]

    if len(active) > 1:
        ids = [u["id"] for u in active]
        print(f"manifest_guard: FAIL - more than one unit in_progress: {ids}", file=sys.stderr)
        return 1

    if not active:
        if changed:
            print("manifest_guard: FAIL - no unit in_progress but the working tree has changes:", file=sys.stderr)
            for f in changed:
                print(f"  {f}", file=sys.stderr)
            return 1
        print("manifest_guard: OK - clean tree, no active unit")
        return 0

    unit = active[0]
    allowed = list(unit["allowed_paths"])
    violations = [
        f for f in changed if not any(fnmatch.fnmatch(f, pat) for pat in allowed)
    ]
    if violations:
        print(f"manifest_guard: FAIL - {unit['id']} touched files outside its manifest:", file=sys.stderr)
        for f in violations:
            print(f"  {f}", file=sys.stderr)
        print(f"allowed_paths: {allowed}", file=sys.stderr)
        return 1

    print(f"manifest_guard: OK - {unit['id']} within manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
