#!/usr/bin/env python3
"""
Phase P1.2: Matrix pre-generation orchestrator.

Invokes each day's creator in order (Mon → Sun) for the next N weeks.
No generation logic — coordinates and reports only.
Exit non-zero if any required slot is unfilled (creator exited non-zero or reported failures).
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def run_creator(name: str, argv: list, env: dict) -> tuple:
    """Run a creator script. Returns (exit_code, stdout_text, stderr_text)."""
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, name)] + argv
    env = env or {}
    env.setdefault("PYTHONPATH", PROJECT_ROOT)
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env={**os.environ, **env},
            capture_output=True,
            text=True,
            timeout=600,
        )
        return (result.returncode, result.stdout or "", result.stderr or "")
    except subprocess.TimeoutExpired:
        return (-1, "", "timeout")
    except Exception as e:
        return (-1, "", str(e))


def main():
    # Log DB target once so creator/validator/schedule API can be verified to use same DB
    try:
        from config.unified_config import get_database_target_for_logging
        print("DB target:", get_database_target_for_logging(), file=sys.stderr)
    except Exception:
        print("DB target: (config unavailable)", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="P1.2: Orchestrate Matrix pre-generation (Mon→Sun). No generation logic."
    )
    parser.add_argument(
        "--weeks-ahead",
        type=int,
        default=8,
        help="Weeks to pre-generate (default 8, min 8)",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="facebook",
        help="Platform (default facebook)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pass --dry-run to all creators",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pass --force to all creators",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Write report to this file (default: stdout only)",
    )
    args = parser.parse_args()

    weeks = max(8, args.weeks_ahead)
    dry = ["--dry-run"] if args.dry_run else []
    force = ["--force"] if args.force else []
    env = {"PYTHONPATH": PROJECT_ROOT}

    # Order: Mon → Tue → Wed → Thu → Fri → Sat → Sun
    creators = [
        ("automated_culture_creator.py", f"Monday (culture_fact)", ["--weeks-ahead", str(weeks)] + dry + force),
        ("automated_weekly_content_creator.py", "Tuesday (language)", ["--weeks-ahead", str(weeks)] + dry + force),
        ("automated_message_post_creator.py", "Wednesday (message)", ["--days-ahead", str(weeks * 7)] + dry + force),
        ("automated_heritage_creator.py", "Thursday (heritage_fact)", ["--weeks-ahead", str(weeks)] + dry + force),
        ("automated_authority_short_creator.py", "Friday (authority_short)", ["--days-ahead", str(weeks * 7)] + dry + force),
        ("automated_product_post_creator.py", "Saturday (product)", ["--days-ahead", str(weeks * 7)] + dry + force),
        ("automated_depth_long_creator.py", "Sunday (depth_long)", ["--weeks-ahead", str(weeks)] + dry + force),
    ]

    report = {
        "weeks_ahead": weeks,
        "platform": args.platform,
        "dry_run": args.dry_run,
        "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "creators": [],
        "exit_codes": [],
        "has_failure": False,
    }

    for script_name, label, creator_argv in creators:
        code, out, err = run_creator(script_name, creator_argv, env)
        report["creators"].append({
            "script": script_name,
            "label": label,
            "exit_code": code,
            "stdout_preview": (out or "")[:500],
            "stderr_preview": (err or "")[:500],
        })
        report["exit_codes"].append(code)
        if code != 0:
            report["has_failure"] = True
        print(f"[{script_name}] exit={code} {label}")
        if out:
            print(out.strip()[-2000:] if len(out) > 2000 else out.strip())
        if err:
            print(err.strip(), file=sys.stderr)

    report["finished_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if args.report:
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.report}")

    # Exit non-zero if any required slot is missing or failed
    sys.exit(1 if report["has_failure"] else 0)


if __name__ == "__main__":
    main()
