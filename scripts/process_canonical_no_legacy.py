#!/usr/bin/env python3
"""\
Iterate through canonical names that have NEITHER history_legacy NOR history_legacy_generated.

This script finds all canonical family names (where spelling_of IS NULL) that are missing
both:
  - history_legacy entries (from clan sources)
  - history_legacy_generated entries (generated summaries)

Usage:
    python3 scripts/process_canonical_no_legacy.py [--limit N] [--start-from ID] [--dry-run]

The script currently just lists the families. Add your processing logic in the process_family() function.
"""

import os
import sys
import json
from typing import Optional, List, Dict

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.database import db_manager


def get_canonical_no_legacy(limit: Optional[int] = None, start_from: Optional[int] = None) -> List[Dict]:
    """Fetch canonical names that have neither history_legacy nor history_legacy_generated."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            where_clauses = [
                "f.spelling_of IS NULL",  # canonical names only
                "NOT EXISTS ("
                "   SELECT 1 "
                "   FROM family_resources fr1 "
                "   WHERE fr1.family_id = f.id "
                "     AND fr1.resource_type = 'text' "
                "     AND fr1.resource_category = 'history_legacy' "
                "     AND LENGTH(TRIM(fr1.resource_value)) > 50"
                ")",
                "NOT EXISTS ("
                "   SELECT 1 "
                "   FROM family_resources fr2 "
                "   WHERE fr2.family_id = f.id "
                "     AND fr2.resource_type = 'text' "
                "     AND fr2.resource_category = 'history_legacy_generated' "
                "     AND LENGTH(TRIM(fr2.resource_value)) > 50"
                ")",
            ]
            
            params = []
            if start_from is not None:
                where_clauses.append("f.id >= %s")
                params.append(start_from)
            
            where_sql = " AND ".join(where_clauses)
            
            query = f"""
                SELECT
                    f.id,
                    f.name,
                    f.popularity_rating,
                    f.has_history,
                    CASE 
                        WHEN f.research_data IS NOT NULL 
                             AND f.research_data ? 'metadata' 
                             AND f.research_data->'metadata' ? 'narrative_fact_checked'
                        THEN TRUE 
                        ELSE FALSE 
                    END AS has_openai_narrative
                FROM families f
                WHERE {where_sql}
                ORDER BY f.id
            """
            
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)
            
            cur.execute(query, params)
            return cur.fetchall()


def count_canonical_no_legacy() -> int:
    """Count canonical names missing both legacy history types."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS count
                FROM families f
                WHERE f.spelling_of IS NULL
                  AND NOT EXISTS (
                      SELECT 1 
                      FROM family_resources fr1
                      WHERE fr1.family_id = f.id
                        AND fr1.resource_type = 'text'
                        AND fr1.resource_category = 'history_legacy'
                        AND LENGTH(TRIM(fr1.resource_value)) > 50
                  )
                  AND NOT EXISTS (
                      SELECT 1 
                      FROM family_resources fr2
                      WHERE fr2.family_id = f.id
                        AND fr2.resource_type = 'text'
                        AND fr2.resource_category = 'history_legacy_generated'
                        AND LENGTH(TRIM(fr2.resource_value)) > 50
                  )
            """)
            row = cur.fetchone()
            return row["count"] if row else 0


def call_openai_for_legacy_summary(surname: str) -> Optional[str]:
    """Call OpenAI to generate a concise historical summary for a surname."""
    from openai import OpenAI  # type: ignore

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

    client = OpenAI(api_key=api_key)

    prompt = f"""Please provide a concise, self-contained historical summary of the surname {surname}.

Focus only on what can be stated with confidence: its likely etymology, geographic origins, early appearances, later distribution, and any distinctive historical associations.

Write in a positive, authoritative tone without padding, disclaimers, speculation, or references.

Do not invent people, events, or dates.

Present the information as a single strong paragraph."""

    model = os.environ.get("OPENAI_MODEL_LEGACY_SUMMARY", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a historical researcher specializing in surname etymology and family history."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        content = resp.choices[0].message.content or ""
        return content.strip()
    except Exception as e:
        print(f"  ✗ OpenAI API error: {e}")
        return None


def save_legacy_generated(family_id: int, summary: str, dry_run: bool = False):
    """Save the generated summary into family_resources as history_legacy_generated."""
    if dry_run:
        print(f"  [DRY RUN] Would save history_legacy_generated (length {len(summary)} chars)")
        return

    metadata = {
        "source": "openai_direct_summary",
        "created_from": "openai_api_direct",
    }

    metadata_json = json.dumps(metadata)

    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Check if entry already exists
            cur.execute(
                """
                SELECT id FROM family_resources
                WHERE family_id = %s
                  AND resource_type = 'text'
                  AND resource_category = 'history_legacy_generated'
                """,
                (family_id,),
            )
            existing = cur.fetchone()
            
            if existing:
                # Update existing entry
                cur.execute(
                    """
                    UPDATE family_resources
                    SET resource_value = %s,
                        resource_metadata = %s::jsonb
                    WHERE id = %s
                    """,
                    (summary, metadata_json, existing["id"]),
                )
            else:
                # Insert new entry
                cur.execute(
                    """
                    INSERT INTO family_resources (
                        family_id,
                        resource_type,
                        resource_category,
                        resource_value,
                        resource_metadata
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        family_id,
                        "text",
                        "history_legacy_generated",
                        summary,
                        metadata_json,
                    ),
                )
        conn.commit()


def process_family(family: Dict, dry_run: bool = False) -> bool:
    """Process a single family by generating a legacy summary from OpenAI.
    
    Returns True if successful, False otherwise.
    """
    family_id = family["id"]
    family_name = family["name"]
    
    print(f"  Calling OpenAI for {family_name}...")
    
    summary = call_openai_for_legacy_summary(family_name)
    
    if not summary or not summary.strip():
        print(f"  ✗ Failed to generate summary")
        return False
    
    print(f"  ✓ Generated summary ({len(summary)} chars)")
    print(f"  Preview: {summary[:100]}...")
    
    save_legacy_generated(family_id, summary, dry_run=dry_run)
    
    if not dry_run:
        print(f"  ✓ Saved to database")
    
    return True


def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process canonical names missing both legacy history types"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of families to process (for testing)",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        help="Start from family ID (inclusive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--count-only",
        action="store_true",
        help="Just count and exit",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Process families in batches of this size (default: 10)",
    )
    
    args = parser.parse_args()
    
    # Count total
    total_count = count_canonical_no_legacy()
    
    print("\n" + "=" * 80)
    print("Process Canonical Names Missing Legacy Histories")
    print("=" * 80)
    print(f"Total canonical names missing both history_legacy and history_legacy_generated: {total_count}")
    
    if args.count_only:
        return 0
    
    # Fetch families
    families = get_canonical_no_legacy(limit=args.limit, start_from=args.start_from)
    total = len(families)
    
    if total == 0:
        print("No families found matching criteria.")
        return 0
    
    print(f"Families to process: {total}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    success = 0
    failed = 0
    batch_size = args.batch_size
    
    for i, family in enumerate(families, 1):
        family_id = family["id"]
        family_name = family["name"]
        
        print(f"[{i}/{total}] {family_name} (ID: {family_id})")
        
        try:
            if process_family(family, dry_run=args.dry_run):
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
            continue
        
        # Batch checkpoint: commit and report after every batch_size families
        if i % batch_size == 0:
            batch_num = i // batch_size
            print(f"\n--- Batch {batch_num} complete ({i}/{total} families processed) ---")
            print(f"  Success: {success}, Failed: {failed}\n")
    
    print("\n" + "=" * 80)
    print("Processing complete")
    print("=" * 80)
    print(f"Total families processed: {total}")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    
    if args.dry_run:
        print("\nNOTE: This was a dry run. No changes were made.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

