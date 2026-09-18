#!/usr/bin/env python3
"""RETIRED — sound hook removed from hooks.json. No-op if invoked."""
from __future__ import annotations

import sys


def main() -> int:
    try:
        sys.stdout.write("{}\n")
        sys.stdout.flush()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
