#!/usr/bin/env python3
"""
Phase P1.2: Matrix pre-generation orchestrator.

Approach A (shared selection): For each slot, select upstream provenance once,
then create/update rows for both platforms (facebook, instagram).
No platform-order coupling; no creator reads FB row for provenance.

Creators that expose select_for_slot + generate_for_slot are run in-process;
others are run as subprocess (legacy, facebook-only until migrated).
Exit non-zero if any required slot is unfilled (creator failed).
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime, timezone, date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

PLATFORMS = ["facebook", "instagram"]


def run_creator_subprocess(name: str, argv: list, env: dict) -> tuple:
    """Run a creator script as subprocess. Returns (exit_code, stdout_text, stderr_text)."""
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


def run_culture_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for culture: select once per Monday slot, then generate for both platforms.
    Returns (slots_report, has_failure).
    """
    from automated_culture_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
        CONTENT_TYPE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, weekday in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        slot_key = {
            "scheduled_date": target_date,
            "role": ROLE,
            "content_type": CONTENT_TYPE,
        }
        selection = select_for_slot(target_date, weekday, year, week_number)
        if not selection:
            slots_report.append({
                "slot_key": {**slot_key, "scheduled_date": str(target_date)},
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        selection_summary = f"culture_library_id={selection.get('culture_library_id')}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def run_weekly_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for Tuesday (weekly language): select once per slot, then generate for both platforms.
    Returns (slots_report, has_failure).
    """
    from automated_weekly_content_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, weekday in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        content_type = None  # will be set from selection
        selection = select_for_slot(target_date, weekday, year, week_number)
        if not selection:
            content_type = "weekly_word"  # placeholder for report
            slot_key = {
                "scheduled_date": str(target_date),
                "role": ROLE,
                "content_type": content_type,
            }
            slots_report.append({
                "slot_key": slot_key,
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        content_type = selection["content_type"]
        slot_key = {
            "scheduled_date": target_date,
            "role": ROLE,
            "content_type": content_type,
        }
        selection_summary = f"idea_id={selection.get('idea_id')} content_type={content_type}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def run_message_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for Wednesday (message): select once per slot (message_index by year/week), then generate for both platforms.
    Returns (slots_report, has_failure).
    """
    from automated_message_post_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
        CONTENT_TYPE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, weekday in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        slot_key = {
            "scheduled_date": target_date,
            "role": ROLE,
            "content_type": CONTENT_TYPE,
        }
        selection = select_for_slot(target_date, weekday, year, week_number)
        if not selection:
            slots_report.append({
                "slot_key": {**slot_key, "scheduled_date": str(target_date)},
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        selection_summary = f"message_index={selection.get('message_index')}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def run_heritage_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for Thursday (heritage): select once per slot, then generate for both platforms.
    Returns (slots_report, has_failure).
    """
    from automated_heritage_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
        CONTENT_TYPE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, weekday in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        slot_key = {
            "scheduled_date": target_date,
            "role": ROLE,
            "content_type": CONTENT_TYPE,
        }
        selection = select_for_slot(target_date, weekday, year, week_number)
        if not selection:
            slots_report.append({
                "slot_key": {**slot_key, "scheduled_date": str(target_date)},
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        selection_summary = f"heritage_library_id={selection.get('heritage_library_id')}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def run_authority_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for Friday (authority_short): select once per slot, then generate for both platforms.
    Returns (slots_report, has_failure).
    """
    from automated_authority_short_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
        CONTENT_TYPE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, weekday in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        slot_key = {
            "scheduled_date": target_date,
            "role": ROLE,
            "content_type": CONTENT_TYPE,
        }
        selection = select_for_slot(target_date, weekday, year, week_number)
        if not selection:
            slots_report.append({
                "slot_key": {**slot_key, "scheduled_date": str(target_date)},
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        selection_summary = f"topic_id={selection.get('topic_id')} source_page_id={selection.get('source_page_id')}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def run_product_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for Saturday (product): select once per slot (date+time), then generate for both platforms.
    Slot key includes scheduled_time. Returns (slots_report, has_failure).
    """
    from automated_product_post_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
        CONTENT_TYPE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, scheduled_time_str in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        slot_key = {
            "scheduled_date": target_date,
            "scheduled_time": scheduled_time_str,
            "role": ROLE,
            "content_type": CONTENT_TYPE,
        }
        selection = select_for_slot(target_date, scheduled_time_str, year, week_number)
        if not selection:
            slots_report.append({
                "slot_key": {**slot_key, "scheduled_date": str(target_date)},
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        selection_summary = f"product_id={selection.get('product_id')}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def run_depth_creator_slots(weeks_ahead: int, dry_run: bool, force: bool, from_date: date):
    """
    Approach A for Sunday (depth_long): select once per slot, then generate for both platforms.
    Returns (slots_report, has_failure).
    """
    from automated_depth_long_creator import (
        get_slot_dates,
        select_for_slot,
        generate_for_slot,
        ROLE,
        CONTENT_TYPE,
    )

    slots_report = []
    has_failure = False
    slot_dates = get_slot_dates(weeks_ahead, from_date)

    for target_date, weekday in slot_dates:
        year, week_number, _ = target_date.isocalendar()
        slot_key = {
            "scheduled_date": target_date,
            "role": ROLE,
            "content_type": CONTENT_TYPE,
        }
        selection = select_for_slot(target_date, weekday, year, week_number)
        if not selection:
            slots_report.append({
                "slot_key": {**slot_key, "scheduled_date": str(target_date)},
                "selection_summary": None,
                "platforms": {"facebook": {"outcome": "failed"}, "instagram": {"outcome": "failed"}},
            })
            has_failure = True
            continue

        selection_summary = f"topic_id={selection.get('topic_id')} source_page_id={selection.get('source_page_id')}"
        platforms_out = {}
        for platform in PLATFORMS:
            outcome = generate_for_slot(platform, slot_key, selection, dry_run=dry_run, force=force)
            platforms_out[platform] = {"outcome": outcome}
            if outcome == "failed":
                has_failure = True

        slots_report.append({
            "slot_key": {**slot_key, "scheduled_date": str(target_date)},
            "selection_summary": selection_summary,
            "platforms": platforms_out,
        })

    return slots_report, has_failure


def main():
    try:
        from config.unified_config import get_database_target_for_logging
        print("DB target:", get_database_target_for_logging(), file=sys.stderr)
    except Exception:
        print("DB target: (config unavailable)", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="P1.2: Orchestrate Matrix pre-generation (Approach A: select once, generate both platforms)."
    )
    parser.add_argument("--weeks-ahead", type=int, default=8, help="Weeks to pre-generate (default 8, min 8)")
    parser.add_argument("--dry-run", action="store_true", help="Pass --dry-run to creators")
    parser.add_argument("--force", action="store_true", help="Pass --force to creators")
    parser.add_argument("--report", type=str, default=None, help="Write report JSON to this file")
    parser.add_argument("--start-date", type=str, default=None, help="Start date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    weeks = max(8, args.weeks_ahead)
    dry = ["--dry-run"] if args.dry_run else []
    force = ["--force"] if args.force else []
    from_date = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else date.today()
    env = {"PYTHONPATH": PROJECT_ROOT}

    report = {
        "weeks_ahead": weeks,
        "platforms": PLATFORMS,
        "dry_run": args.dry_run,
        "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "slots": {},
        "creators_legacy": [],
        "has_failure": False,
    }

    # --- Culture (Monday): Approach A in-process ---
    culture_slots, culture_fail = run_culture_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["culture_fact"] = culture_slots
    if culture_fail:
        report["has_failure"] = True
    print(f"[culture_fact] slots={len(culture_slots)} failures={culture_fail}")

    # --- Tuesday (weekly language): Approach A in-process ---
    weekly_slots, weekly_fail = run_weekly_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["tuesday_language"] = weekly_slots
    if weekly_fail:
        report["has_failure"] = True
    print(f"[tuesday_language] slots={len(weekly_slots)} failures={weekly_fail}")

    # --- Wednesday (message): Approach A in-process ---
    message_slots, message_fail = run_message_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["message"] = message_slots
    if message_fail:
        report["has_failure"] = True
    print(f"[message] slots={len(message_slots)} failures={message_fail}")

    # --- Thursday (heritage): Approach A in-process ---
    heritage_slots, heritage_fail = run_heritage_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["heritage_fact"] = heritage_slots
    if heritage_fail:
        report["has_failure"] = True
    print(f"[heritage_fact] slots={len(heritage_slots)} failures={heritage_fail}")

    # --- Friday (authority_short): Approach A in-process ---
    authority_slots, authority_fail = run_authority_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["authority_short"] = authority_slots
    if authority_fail:
        report["has_failure"] = True
    print(f"[authority_short] slots={len(authority_slots)} failures={authority_fail}")

    # --- Saturday (product): Approach A in-process ---
    product_slots, product_fail = run_product_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["product"] = product_slots
    if product_fail:
        report["has_failure"] = True
    print(f"[product] slots={len(product_slots)} failures={product_fail}")

    # --- Sunday (depth_long): Approach A in-process ---
    depth_slots, depth_fail = run_depth_creator_slots(weeks, args.dry_run, args.force, from_date)
    report["slots"]["depth_long"] = depth_slots
    if depth_fail:
        report["has_failure"] = True
    print(f"[depth_long] slots={len(depth_slots)} failures={depth_fail}")

    creators_legacy = []
    for script_name, label, creator_argv in creators_legacy:
        code, out, err = run_creator_subprocess(script_name, creator_argv, env)
        report["creators_legacy"].append({
            "script": script_name,
            "label": label,
            "exit_code": code,
            "stdout_preview": (out or "")[:500],
            "stderr_preview": (err or "")[:500],
        })
        if code != 0:
            report["has_failure"] = True
        print(f"[{script_name}] exit={code} {label}")
        if out:
            print(out.strip()[-1500:] if len(out) > 1500 else out.strip())
        if err:
            print(err.strip(), file=sys.stderr)

    report["finished_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if args.report:
        # Serialize slot keys for JSON (date -> str)
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.report}")

    sys.exit(1 if report["has_failure"] else 0)


if __name__ == "__main__":
    main()
