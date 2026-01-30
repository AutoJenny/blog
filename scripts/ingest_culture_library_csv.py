#!/usr/bin/env python3
"""
Ingest CULTURE v1.1 CSV into culture_library.

Reads a CSV with columns: category, title, body_text, tone, source_note, image_idea, confidence_flag, image_style.
Inserts into culture_library (category, title, body_text, source_note, active=TRUE).
Extra columns (tone, image_idea, etc.) are not stored; schema has category, title, body_text, source_note only.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager


def ensure_culture_library_exists() -> bool:
    """Create culture_library table if it does not exist. Returns True if table exists (or was created)."""
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'culture_library'
            """
        )
        if cursor.fetchone():
            return True
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS culture_library (
                id SERIAL PRIMARY KEY,
                category VARCHAR(100),
                title VARCHAR(500) NOT NULL,
                body_text TEXT NOT NULL,
                source_note TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_culture_library_active ON culture_library(active) WHERE active = TRUE"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_culture_library_category ON culture_library(category) WHERE category IS NOT NULL"
        )
    return True


def ingest_csv(csv_path: str, dry_run: bool = False, run_migration: bool = False) -> dict:
    """
    Read CSV and insert rows into culture_library.
    Returns dict with inserted, skipped, errors.
    """
    stats = {"inserted": 0, "skipped": 0, "errors": 0}
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(csv_path)

    if run_migration and not dry_run:
        ensure_culture_library_exists()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = (row.get("category") or "").strip()
            title = (row.get("title") or "").strip()
            body_text = (row.get("body_text") or "").strip()
            source_note = (row.get("source_note") or "").strip()

            if not title or not body_text:
                stats["skipped"] += 1
                continue

            if dry_run:
                stats["inserted"] += 1
                continue

            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO culture_library (category, title, body_text, source_note, active)
                        VALUES (%s, %s, %s, %s, TRUE)
                        """,
                        (category or None, title, body_text, source_note or None),
                    )
                stats["inserted"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error inserting '{title[:50]}...': {e}", file=sys.stderr)

    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest culture_library from CSV.")
    parser.add_argument("csv_path", nargs="?", default="docs/CULTURE_v1_1_FINAL_INGESTION.csv",
                        help="Path to CSV (default: docs/CULTURE_v1_1_FINAL_INGESTION.csv)")
    parser.add_argument("--dry-run", action="store_true", help="Count rows only, do not insert")
    parser.add_argument("--run-migration", action="store_true",
                        help="Create culture_library table if it does not exist (then ingest)")
    args = parser.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = args.csv_path if os.path.isabs(args.csv_path) else os.path.join(base, args.csv_path)

    stats = ingest_csv(csv_path, dry_run=args.dry_run, run_migration=args.run_migration)
    print(f"Inserted: {stats['inserted']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
    if args.dry_run:
        print("(dry-run; no rows written)")
    sys.exit(0 if stats["errors"] == 0 else 1)


if __name__ == "__main__":
    main()
