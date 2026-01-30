#!/usr/bin/env python3
"""
Phase P1: Duplicate scan for one-slot-one-row, then apply unique-index migration.

1. Scan posting_queue for duplicate slot rows (per P1 slot keys).
2. Report duplicate groups; optionally resolve by keeping one row per slot and DELETING the rest (not UPDATE to cancelled). See docs/P1_RESOLVE_ROLLBACK_AND_BACKUP.md.
3. Apply migrations/20260129_p1_one_row_per_slot_unique_indexes.sql.

Usage:
  python scripts/p1_duplicate_scan_and_migrate.py --scan-only     # report only
  python scripts/p1_duplicate_scan_and_migrate.py --resolve      # delete duplicates then apply migration
  python scripts/p1_duplicate_scan_and_migrate.py --apply-only   # apply migration only (fails if duplicates exist)
"""

import os
import sys
import argparse
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager


SLOT_QUERIES = [
    ("culture_fact", """
        SELECT platform, scheduled_date, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE content_type = 'culture_fact' AND platform = 'facebook' AND scheduled_date IS NOT NULL
        GROUP BY platform, scheduled_date HAVING count(*) > 1
    """),
    ("tuesday_language", """
        SELECT platform, scheduled_date, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult') AND platform = 'facebook' AND scheduled_date IS NOT NULL
        GROUP BY platform, scheduled_date HAVING count(*) > 1
    """),
    ("message", """
        SELECT platform, scheduled_date, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE content_type = 'message' AND platform = 'facebook' AND scheduled_date IS NOT NULL
        GROUP BY platform, scheduled_date HAVING count(*) > 1
    """),
    ("heritage", """
        SELECT platform, scheduled_date, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE role = 'HERITAGE' AND platform = 'facebook' AND scheduled_date IS NOT NULL
        GROUP BY platform, scheduled_date HAVING count(*) > 1
    """),
    ("authority_short", """
        SELECT platform, scheduled_date, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE role = 'AUTHORITY_SHORT' AND platform = 'facebook' AND scheduled_date IS NOT NULL
        GROUP BY platform, scheduled_date HAVING count(*) > 1
    """),
    ("product", """
        SELECT platform, scheduled_date, scheduled_time, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE content_type = 'product' AND platform = 'facebook' AND scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL
        GROUP BY platform, scheduled_date, scheduled_time HAVING count(*) > 1
    """),
    ("depth_long", """
        SELECT platform, scheduled_date, array_agg(id ORDER BY id) as ids, count(*) as n
        FROM posting_queue
        WHERE content_type = 'depth_long' AND platform = 'facebook' AND scheduled_date IS NOT NULL
        GROUP BY platform, scheduled_date HAVING count(*) > 1
    """),
]


def run_scan():
    """Return dict slot_name -> list of duplicate groups (each with ids, n)."""
    results = {}
    for name, q in SLOT_QUERIES:
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(q)
                rows = cursor.fetchall()
            results[name] = [dict(r) for r in rows] if rows else []
        except Exception as e:
            print(f"Scan error for {name}: {e}", file=sys.stderr)
            results[name] = []
    return results


def choose_keep_id(conn, slot_name: str, ids: list) -> int:
    """Keep one row per slot: prefer status in (ready, approved, scheduled, published), else highest id."""
    placeholders = ",".join(["%s"] * len(ids))
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id, status FROM posting_queue
            WHERE id IN ({placeholders})
            ORDER BY CASE WHEN status IN ('ready', 'approved', 'scheduled', 'published') THEN 0 ELSE 1 END, id DESC
            LIMIT 1
            """,
            ids,
        )
        row = cursor.fetchone()
    return row["id"] if row else ids[0]


def resolve_duplicates(scan_results: dict) -> int:
    """For each duplicate group, keep one row and delete the rest. Return number of rows deleted."""
    deleted = 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            for slot_name, groups in scan_results.items():
                for g in groups:
                    ids = g["ids"] if isinstance(g["ids"], list) else list(g["ids"]) if g.get("ids") else []
                    if len(ids) <= 1:
                        continue
                    keep_id = choose_keep_id(conn, slot_name, ids)
                    to_delete = [i for i in ids if i != keep_id]
                    for id in to_delete:
                        cursor.execute("DELETE FROM posting_queue WHERE id = %s", (id,))
                        deleted += 1
            conn.commit()
    return deleted


def apply_migration():
    """Execute the P1 unique-index migration SQL file."""
    migration_path = project_root / "migrations" / "20260129_p1_one_row_per_slot_unique_indexes.sql"
    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}", file=sys.stderr)
        return False
    sql = migration_path.read_text()
    # Execute each statement (split by semicolon). Strip leading/trailing; drop comment-only lines from each segment.
    statements = []
    for s in sql.split(";"):
        lines = [ln.strip() for ln in s.strip().splitlines() if ln.strip() and not ln.strip().startswith("--")]
        stmt = "\n".join(lines)
        if stmt:
            statements.append(stmt)
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            for stmt in statements:
                if not stmt:
                    continue
                try:
                    cursor.execute(stmt + ";")
                except Exception as e:
                    print(f"Migration statement failed: {e}", file=sys.stderr)
                    print(f"Statement: {stmt[:200]}...", file=sys.stderr)
                    return False
            conn.commit()
    return True


def main():
    parser = argparse.ArgumentParser(description="P1: Duplicate scan and/or apply one-slot-one-row migration")
    parser.add_argument("--scan-only", action="store_true", help="Only report duplicate groups")
    parser.add_argument("--resolve", action="store_true", help="Resolve duplicates (keep one per slot, delete rest) then apply migration")
    parser.add_argument("--apply-only", action="store_true", help="Apply migration only (fails if duplicates exist)")
    args = parser.parse_args()

    scan = run_scan()
    total_dupes = sum(len(groups) for groups in scan.values())
    duplicate_rows = sum(sum(g["n"] for g in groups) - len(groups) for groups in scan.values())  # extra rows per group

    if total_dupes > 0:
        print("Duplicate slot groups found:")
        for name, groups in scan.items():
            if groups:
                print(f"  {name}: {len(groups)} duplicate slot(s)")
                for g in groups:
                    print(f"    ids={g['ids']} n={g['n']}")
    else:
        print("No duplicate slot groups found.")

    if args.scan_only:
        sys.exit(0 if total_dupes == 0 else 1)

    if args.resolve:
        if duplicate_rows > 0:
            n = resolve_duplicates(scan)
            print(f"Resolved: deleted {n} duplicate row(s).")
        if not apply_migration():
            print("Migration failed.", file=sys.stderr)
            sys.exit(1)
        print("Migration applied successfully.")
        sys.exit(0)

    if args.apply_only:
        if total_dupes > 0:
            print("Cannot apply migration: duplicate slot groups exist. Run with --resolve first.", file=sys.stderr)
            sys.exit(1)
        if not apply_migration():
            print("Migration failed.", file=sys.stderr)
            sys.exit(1)
        print("Migration applied successfully.")
        sys.exit(0)

    print("Use --scan-only, --resolve, or --apply-only.")
    sys.exit(0 if total_dupes == 0 else 1)


if __name__ == "__main__":
    main()
