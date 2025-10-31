#!/usr/bin/env python3
"""Guardrail: warn when files exceed a LOC threshold (default 500).

Usage:
  python3 scripts/check_file_sizes.py --max-loc 500
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable


EXCLUDE_DIRS = {"venv", "venv_sdxl", ".git", "node_modules", "static", "blog-images/static"}
INCLUDE_EXTS = {".py", ".html"}


def iter_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in INCLUDE_EXTS:
                yield os.path.join(dirpath, fn)


def count_loc(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-loc", type=int, default=500)
    parser.add_argument("--root", type=str, default=os.getcwd())
    args = parser.parse_args()

    max_loc = args.max_loc
    root = args.root
    violations = []

    for path in iter_files(root):
        loc = count_loc(path)
        if loc > max_loc:
            violations.append((path, loc))

    if violations:
        print("File-size guardrail warnings (>{} LOC):".format(max_loc))
        for path, loc in sorted(violations, key=lambda x: x[1], reverse=True):
            print(f" - {path} : {loc} lines")
        # Exit 0: warn-only for now; switch to non-zero to enforce in CI
        return 0
    else:
        print("No files exceed the LOC threshold.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())



