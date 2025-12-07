#!/usr/bin/env python3
"""
Batch process canonical families with no content through the full research pipeline.
Runs: Web Research → Story Facts & Narrative → Fact-Checking
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager


def get_canonical_no_content_families(clans_only=False, min_popularity=None):
    """Get canonical families with no content (no history, no OpenAI).
    
    Args:
        clans_only: If True, only return canonical clans. If False, return all canonical families.
        min_popularity: Minimum popularity rating (0-100). If None, no popularity filter is applied.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            clan_filter = "AND is_clan = TRUE" if clans_only else ""
            popularity_filter = f"AND popularity_rating >= {min_popularity}" if min_popularity is not None else ""
            cur.execute(f"""
                SELECT id, name, popularity_rating
                FROM families
                WHERE spelling_of IS NULL 
                  AND has_history = FALSE 
                  AND (research_data IS NULL OR NOT (research_data ? 'metadata' AND research_data->'metadata' ? 'narrative_fact_checked'))
                  {clan_filter}
                  {popularity_filter}
                ORDER BY popularity_rating DESC, name
            """)
            return cur.fetchall()


def run_full_research_process(family_id, family_name, dry_run=False):
    """Run the complete 3-step research process for a family."""
    scripts_dir = Path(__file__).parent
    results = {'web': False, 'story': False, 'factcheck': False}
    
    # Step 1: Web research (generates JSON)
    print(f"\n[{family_id}] {family_name}: Step 1/3 - Web Research...")
    if dry_run:
        print(f"  [DRY RUN] Would run: research_family_web.py {family_id} --save")
        results['web'] = True
    else:
        try:
            result = subprocess.run(
                [sys.executable, str(scripts_dir / 'research_family_web.py'), 
                 str(family_id), '--save'],
                capture_output=True,
                text=True,
                timeout=900  # 15 minutes for web research (increased due to network issues)
            )
            if result.returncode == 0:
                results['web'] = True
                print(f"  ✓ Web research complete")
            else:
                error_msg = result.stderr[:300] if result.stderr else result.stdout[:300]
                print(f"  ✗ Web research failed: {error_msg}")
                # Continue anyway - might have partial data
                if "Timeout" in error_msg or "timeout" in error_msg.lower():
                    print(f"  ⚠ Timeout - continuing to next family")
                return results
        except subprocess.TimeoutExpired:
            print(f"  ✗ Web research timed out after 15 minutes")
            return results
    
    # Step 2: Story facts and narrative (compiles JSON into narrative)
    # Use --narrative-only since Step 1 already generated the JSON data
    print(f"[{family_id}] {family_name}: Step 2/3 - Story Facts & Narrative...")
    if dry_run:
        print(f"  [DRY RUN] Would run: research_family_story_facts.py {family_id} --narrative-only --save --word-target 1500")
        results['story'] = True
    else:
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'research_family_story_facts.py'), 
             str(family_id), '--narrative-only', '--save', '--word-target', '1500'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes should be plenty for narrative-only mode
        )
        if result.returncode == 0:
            results['story'] = True
            print(f"  ✓ Story facts and narrative complete")
        else:
            print(f"  ✗ Story facts failed: {result.stderr[:200]}")
            return results
    
    # Step 3: Fact-checking with OpenAI
    print(f"[{family_id}] {family_name}: Step 3/3 - Fact-Checking with OpenAI...")
    if dry_run:
        print(f"  [DRY RUN] Would run: fact_check_narrative.py {family_id} --update-db")
        results['factcheck'] = True
    else:
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'fact_check_narrative.py'), 
             str(family_id), '--update-db'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for fact-checking
        )
        if result.returncode == 0:
            results['factcheck'] = True
            print(f"  ✓ Fact-checking complete")
        else:
            print(f"  ✗ Fact-checking failed: {result.stderr[:200]}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch research canonical families with no content')
    parser.add_argument('--limit', type=int, help='Limit number of families to process')
    parser.add_argument('--start-from', type=int, help='Start from family ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without running')
    parser.add_argument('--clans-only', action='store_true', help='Only process canonical clans (default: all canonical families)')
    parser.add_argument('--min-popularity', type=int, help='Minimum popularity rating (0-100) to filter families')
    parser.add_argument('--skip-timeouts', action='store_true', help='Skip families that timeout and continue processing')
    parser.add_argument('--batch-size', type=int, default=10, help='Process N families then pause (0 = no pause)')
    parser.add_argument('--batch-pause', type=int, default=300, help='Pause seconds between batches (default: 300 = 5 min)')
    
    args = parser.parse_args()
    
    families = get_canonical_no_content_families(clans_only=args.clans_only, min_popularity=args.min_popularity)
    
    if args.start_from:
        families = [f for f in families if f['id'] >= args.start_from]
    
    if args.limit:
        families = families[:args.limit]
    
    print(f"\n{'='*60}")
    print(f"Batch Research: {len(families)} canonical families with no content")
    print(f"{'='*60}\n")
    
    if args.dry_run:
        print("DRY RUN - Would process:")
        for f in families:
            popularity = f.get('popularity_rating', 'N/A')
            print(f"  {f['id']:5} | {f['name']:30} | Popularity: {popularity}")
        return 0
    
    # Process families
    success_count = 0
    failed_count = 0
    
    for i, family in enumerate(families, 1):
        family_id = family['id']
        family_name = family['name']
        
        print(f"\n[{i}/{len(families)}] Processing: {family_name} (ID: {family_id})")
        
        try:
            results = run_full_research_process(family_id, family_name, args.dry_run)
            if results['web'] and results['story'] and results['factcheck']:
                success_count += 1
                print(f"  ✓ Complete success for {family_name}")
            else:
                failed_count += 1
                print(f"  ⚠ Partial or failed for {family_name} (web: {results['web']}, story: {results['story']}, factcheck: {results['factcheck']})")
        except subprocess.TimeoutExpired as e:
            print(f"  ✗ Timeout: {e}")
            if args.skip_timeouts:
                print(f"  ⏭ Skipping {family_name} due to timeout, continuing...")
                failed_count += 1
            else:
                failed_count += 1
                # If not skipping, stop processing
                print(f"\n⚠ Stopping batch due to timeout. Use --skip-timeouts to continue.")
                break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed_count += 1
        
        # Add a delay between families to avoid overwhelming search APIs
        if not args.dry_run and i < len(families):
            import time
            # Longer delay if previous family failed (might be rate limiting)
            if not (results.get('web') and results.get('story') and results.get('factcheck')):
                time.sleep(30)  # 30 second delay after failures
            else:
                time.sleep(5)  # 5 second delay after success
            
            # Batch pause: pause after processing N families
            if args.batch_size > 0 and i % args.batch_size == 0:
                print(f"\n⏸ Pausing for {args.batch_pause} seconds after batch of {args.batch_size} families...")
                time.sleep(args.batch_pause)
    
    print(f"\n{'='*60}")
    print(f"Batch Research Complete")
    print(f"{'='*60}")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(families)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

