#!/usr/bin/env python3
"""
Batch process families to generate narratives and fact-check them.
Processes families that have JSON but are missing narrative or fact-checked versions.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
import json


def get_families_needing_processing():
    """Get families that need narrative generation or fact-checking."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, 
                       CASE WHEN research_data IS NOT NULL AND research_data ? 'metadata' AND research_data->'metadata' ? 'narrative' THEN true ELSE false END as has_compiled,
                       CASE WHEN research_data IS NOT NULL AND research_data ? 'metadata' AND research_data->'metadata' ? 'narrative_fact_checked' THEN true ELSE false END as has_openai
                FROM families
                WHERE research_data IS NOT NULL 
                  AND jsonb_typeof(research_data) = 'object' 
                  AND (research_data::text != '{}'::text)
                  AND (
                    NOT (research_data ? 'metadata' AND research_data->'metadata' ? 'narrative')
                    OR NOT (research_data ? 'metadata' AND research_data->'metadata' ? 'narrative_fact_checked')
                  )
                ORDER BY name
            """)
            return cur.fetchall()


def process_family(family_id, family_name, needs_narrative, needs_factcheck):
    """Process a single family: generate narrative and/or fact-check."""
    scripts_dir = Path(__file__).parent
    results = {'narrative': False, 'factcheck': False}
    
    # Generate narrative if needed
    if needs_narrative:
        print(f"\n[{family_id}] {family_name}: Generating narrative...")
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'research_family_story_facts.py'), 
             str(family_id), '--narrative-only', '--save', '--word-target', '1500'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            results['narrative'] = True
            print(f"  ✓ Narrative generated")
        else:
            print(f"  ✗ Narrative generation failed: {result.stderr[:200]}")
            return results
    
    # Fact-check if needed (or if we just generated narrative)
    if needs_factcheck or needs_narrative:
        print(f"[{family_id}] {family_name}: Fact-checking with OpenAI...")
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'fact_check_narrative.py'), 
             str(family_id), '--update-db'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            results['factcheck'] = True
            print(f"  ✓ Fact-checked")
        else:
            print(f"  ✗ Fact-checking failed: {result.stderr[:200]}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch generate narratives and fact-check for families')
    parser.add_argument('--limit', type=int, help='Limit number of families to process')
    parser.add_argument('--start-from', type=int, help='Start from family ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without running')
    
    args = parser.parse_args()
    
    families = get_families_needing_processing()
    
    if args.start_from:
        families = [f for f in families if f['id'] >= args.start_from]
    
    if args.limit:
        families = families[:args.limit]
    
    print(f"\n{'='*60}")
    print(f"Batch Processing: {len(families)} families")
    print(f"{'='*60}\n")
    
    if args.dry_run:
        print("DRY RUN - Would process:")
        for f in families:
            needs_narrative = not f['has_compiled']
            needs_factcheck = not f['has_openai']
            print(f"  {f['id']:5} | {f['name']:30} | Narrative: {'Yes' if needs_narrative else 'No'} | Fact-check: {'Yes' if needs_factcheck else 'No'}")
        return 0
    
    # Process families
    success_count = 0
    failed_count = 0
    
    for i, family in enumerate(families, 1):
        family_id = family['id']
        family_name = family['name']
        needs_narrative = not family['has_compiled']
        needs_factcheck = not family['has_openai']
        
        print(f"\n[{i}/{len(families)}] Processing: {family_name} (ID: {family_id})")
        
        try:
            results = process_family(family_id, family_name, needs_narrative, needs_factcheck)
            if results['narrative'] or (not needs_narrative and results['factcheck']):
                success_count += 1
            else:
                failed_count += 1
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout")
            failed_count += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Batch Processing Complete")
    print(f"{'='*60}")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(families)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

