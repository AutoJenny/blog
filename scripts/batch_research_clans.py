#!/usr/bin/env python3
"""
Batch research script for clans without history.

Runs the full research process:
1. First pass: Web research (research_family_web.py)
2. Second pass: Story facts and narrative (research_family_story_facts.py)
3. Third pass: Fact-checking (fact_check_narrative.py)

Usage:
    python3 scripts/batch_research_clans.py [--limit N] [--start-from NAME] [--dry-run]
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
import argparse


def get_clans_to_process(limit=None, start_from=None):
    """Get list of clans without history that need research."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            conditions = [
                'is_clan = TRUE',
                'has_history = FALSE',
                "(research_data IS NULL OR research_data::text = '{}'::text)"
            ]
            params = []
            
            if start_from:
                conditions.append('name >= %s')
                params.append(start_from)
            
            where_clause = ' AND '.join(conditions)
            query = f'''
                SELECT id, name 
                FROM families 
                WHERE {where_clause}
                ORDER BY name ASC
            '''
            
            if limit:
                query += ' LIMIT %s'
                params.append(limit)
            
            cur.execute(query, params)
            return cur.fetchall()


def run_research_process(family_id, family_name, dry_run=False):
    """Run the full research process for a family."""
    print(f"\n{'='*60}")
    print(f"Processing: {family_name} (ID: {family_id})")
    print(f"{'='*60}")
    
    scripts_dir = Path(__file__).parent
    
    # Step 1: Web research
    print(f"\n[1/3] Web Research...")
    if dry_run:
        print(f"  [DRY RUN] Would run: research_family_web.py {family_id} --save")
    else:
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'research_family_web.py'), str(family_id), '--save'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  ✗ Error in web research: {result.stderr}")
            return False
        print(f"  ✓ Web research complete")
    
    # Step 2: Story facts and narrative
    print(f"\n[2/3] Story Facts & Narrative...")
    if dry_run:
        print(f"  [DRY RUN] Would run: research_family_story_facts.py {family_id} --save --word-target 3000")
    else:
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'research_family_story_facts.py'), 
             str(family_id), '--save', '--word-target', '3000'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  ✗ Error in story facts: {result.stderr}")
            return False
        print(f"  ✓ Story facts and narrative complete")
    
    # Step 3: Fact-checking
    print(f"\n[3/3] Fact-Checking...")
    if dry_run:
        print(f"  [DRY RUN] Would run: fact_check_narrative.py {family_id} --update-db")
    else:
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'fact_check_narrative.py'), 
             str(family_id), '--update-db'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  ✗ Error in fact-checking: {result.stderr}")
            return False
        print(f"  ✓ Fact-checking complete")
    
    print(f"\n✓ Complete: {family_name} (ID: {family_id})")
    return True


def main():
    parser = argparse.ArgumentParser(description='Batch research clans without history')
    parser.add_argument('--limit', type=int, help='Limit number of clans to process')
    parser.add_argument('--start-from', type=str, help='Start from this clan name (A-Z)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Get clans to process
    clans = get_clans_to_process(limit=args.limit, start_from=args.start_from)
    
    if not clans:
        print("No clans found to process.")
        return
    
    print("=" * 60)
    print("BATCH RESEARCH: Clans Without History")
    print("=" * 60)
    print(f"Clans to process: {len(clans)}")
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
    print()
    
    # Process each clan
    successful = 0
    failed = 0
    
    # Check for pause file
    pause_file = Path(__file__).parent.parent / 'logs' / 'batch_research_pause.flag'
    
    for i, clan in enumerate(clans, 1):
        # Check for pause flag before starting next clan
        if pause_file.exists():
            print(f"\n{'='*60}")
            print("PAUSE FLAG DETECTED - Stopping after current completion")
            print(f"{'='*60}\n")
            pause_file.unlink()  # Remove the flag
            break
        
        print(f"\n[{i}/{len(clans)}] {clan['name']} (ID: {clan['id']})")
        
        if run_research_process(clan['id'], clan['name'], dry_run=args.dry_run):
            successful += 1
            
            # Check for pause flag after completion
            if pause_file.exists():
                print(f"\n{'='*60}")
                print("PAUSE FLAG DETECTED - Pausing after this completion")
                print(f"Completed: {clan['name']} (ID: {clan['id']})")
                print(f"{'='*60}\n")
                pause_file.unlink()  # Remove the flag
                break
        else:
            failed += 1
            if not args.dry_run:
                print(f"  ⚠️  Failed to complete research for {clan['name']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("BATCH RESEARCH SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(clans)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print("=" * 60)


if __name__ == '__main__':
    main()

