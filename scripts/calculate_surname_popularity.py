#!/usr/bin/env python3
"""
Calculate popularity ratings (0-100) for canonical family names based on web search result counts.

Uses search result counts as a proxy for surname popularity/commonness.
Ratings are normalized to provide roughly even distribution across 0-100.
"""

import sys
import os
import time
import json
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager


def check_wikipedia_page(surname: str) -> bool:
    """Check if a Wikipedia page exists for the surname."""
    try:
        # Try Wikipedia API
        api_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        # Try common page title formats
        titles = [
            f"{surname}_(surname)",
            f"{surname}_family",
            f"Clan_{surname}",
            surname
        ]
        
        for title in titles:
            try:
                response = requests.get(f"{api_url}/{title}", timeout=5)
                if response.status_code == 200:
                    return True
            except:
                continue
    except:
        pass
    return False


def get_search_presence_score(surname: str) -> int:
    """Get a score (0-100) based on web search presence."""
    try:
        ddg_url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        query = f'"{surname}" surname Scotland'
        params = {'q': query}
        response = requests.get(ddg_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.select('.result')
            
            if results:
                # Score based on number of results found
                result_count = len(results)
                # Normalize: 0 results = 0, 10+ results = 100
                return min(result_count * 10, 100)
            
            return 0
    except:
        pass
    return 0


def calculate_popularity_score(surname: str) -> int:
    """Calculate a popularity score (0-100) using multiple signals."""
    score = 0
    
    # Signal 1: Wikipedia page existence (30 points)
    has_wikipedia = check_wikipedia_page(surname)
    if has_wikipedia:
        score += 30
        print(f"    ✓ Wikipedia page found")
    
    # Signal 2: Web search presence (50 points)
    search_score = get_search_presence_score(surname)
    score += int(search_score * 0.5)  # Scale to 50 points max
    if search_score > 0:
        print(f"    ✓ Web search results: {search_score}%")
    
    # Signal 3: Heuristics (20 points)
    heuristics = 0
    
    # Common Scottish prefixes (Mac, Mc) suggest established names
    if surname.startswith('Mac') or surname.startswith('Mc'):
        heuristics += 8
        print(f"    ✓ Mac/Mc prefix")
    
    # Common suffixes
    common_suffixes = ['son', 'ton', 'land', 'head', 'ie', 'ock']
    if any(surname.endswith(s) for s in common_suffixes):
        heuristics += 4
        print(f"    ✓ Common suffix pattern")
    
    # Name length (moderate length names are often more common)
    name_len = len(surname.replace("'", "").replace("-", ""))
    if 4 <= name_len <= 8:
        heuristics += 4
    elif name_len < 4:
        heuristics += 2  # Very short names can be common too
    
    # Vowel count (more vowels often = more common)
    vowels = sum(1 for c in surname if c.lower() in 'aeiou')
    if 2 <= vowels <= 4:
        heuristics += 4
    
    score += min(heuristics, 20)
    
    return min(score, 100)


def normalize_to_rating(counts: List[int], target_min: int = 0, target_max: int = 100) -> Dict[int, int]:
    """Normalize search counts to ratings with roughly even distribution.
    
    Uses percentile-based normalization to ensure even distribution.
    """
    if not counts:
        return {}
    
    # Sort counts
    sorted_counts = sorted(counts)
    n = len(sorted_counts)
    
    # Create mapping: count -> rating
    count_to_rating = {}
    
    for i, count in enumerate(sorted_counts):
        # Calculate percentile (0-100)
        percentile = (i / (n - 1)) * 100 if n > 1 else 50
        
        # Map percentile to target range
        rating = int(target_min + (percentile / 100) * (target_max - target_min))
        count_to_rating[count] = rating
    
    return count_to_rating


def save_checkpoint(checkpoint_file: str, family_scores: Dict[int, int], processed_ids: List[int]):
    """Save progress to checkpoint file."""
    checkpoint_data = {
        'scores': family_scores,
        'processed_ids': processed_ids
    }
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)


def load_checkpoint(checkpoint_file: str) -> tuple[Dict[int, int], List[int]]:
    """Load progress from checkpoint file."""
    if not os.path.exists(checkpoint_file):
        return {}, []
    
    with open(checkpoint_file, 'r') as f:
        checkpoint_data = json.load(f)
    
    # Convert keys back to int (JSON saves them as strings)
    scores = {int(k): v for k, v in checkpoint_data.get('scores', {}).items()}
    processed_ids = [int(id) for id in checkpoint_data.get('processed_ids', [])]
    
    return scores, processed_ids


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate popularity ratings for canonical surnames')
    parser.add_argument('--limit', type=int, help='Limit number of families to process')
    parser.add_argument('--start-from', type=int, help='Start from family ID')
    parser.add_argument('--dry-run', action='store_true', help='Calculate but do not update database')
    parser.add_argument('--force-recalculate', action='store_true', help='Recalculate even if rating exists')
    parser.add_argument('--checkpoint-file', type=str, default='/tmp/popularity_checkpoint.json', 
                       help='Checkpoint file path for saving/loading progress')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--save-interval', type=int, default=100, 
                       help='Save checkpoint every N families')
    parser.add_argument('--save-raw-scores', action='store_true', 
                       help='Save raw scores to database incrementally (before normalization)')
    
    args = parser.parse_args()
    
    # Get all canonical families
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, name, popularity_rating
                FROM families
                WHERE spelling_of IS NULL
                ORDER BY name
            """
            if args.start_from:
                query += f" AND id >= {args.start_from}"
            if args.limit:
                query += f" LIMIT {args.limit}"
            
            cur.execute(query)
            families = cur.fetchall()
    
    print(f"\n{'='*60}")
    print(f"Calculating Popularity Ratings")
    print(f"{'='*60}")
    print(f"Total families to process: {len(families)}\n")
    
    if args.dry_run:
        print("DRY RUN MODE - No database updates will be made\n")
    
    # Load checkpoint if resuming
    family_scores = {}
    processed_ids = []
    if args.resume:
        print(f"Loading checkpoint from {args.checkpoint_file}...")
        family_scores, processed_ids = load_checkpoint(args.checkpoint_file)
        print(f"  Resuming with {len(family_scores)} already calculated scores")
    
    # Step 1: Calculate popularity scores for all families
    print("Step 1: Calculating popularity scores...")
    
    for i, family in enumerate(families, 1):
        family_id = family['id']
        family_name = family['name']
        existing_rating = family.get('popularity_rating')
        
        # Skip if already processed in this session
        if family_id in processed_ids:
            if family_id in family_scores:
                print(f"[{i}/{len(families)}] {family_name}: Using checkpoint score {family_scores[family_id]}")
            continue
        
        if existing_rating is not None and not args.force_recalculate:
            print(f"[{i}/{len(families)}] {family_name}: Using existing rating {existing_rating}")
            # Still add to processed_ids to skip in future runs
            processed_ids.append(family_id)
            continue
        
        print(f"[{i}/{len(families)}] {family_name}: Calculating score...")
        score = calculate_popularity_score(family_name)
        family_scores[family_id] = score
        processed_ids.append(family_id)
        print(f"  Score: {score}/100")
        
        # Save raw score to database incrementally if requested
        if args.save_raw_scores and not args.dry_run:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE families 
                        SET popularity_rating = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (score, family_id))
                conn.commit()
        
        # Save checkpoint periodically
        if i % args.save_interval == 0:
            save_checkpoint(args.checkpoint_file, family_scores, processed_ids)
            print(f"  ✓ Checkpoint saved ({len(family_scores)} scores)")
        
        # Rate limiting
        time.sleep(0.5)
    
    # Final checkpoint save
    save_checkpoint(args.checkpoint_file, family_scores, processed_ids)
    print(f"\n✓ Final checkpoint saved ({len(family_scores)} scores)")
    
    # Step 2: Normalize scores to ensure even distribution
    print(f"\nStep 2: Normalizing to ensure even distribution...")
    all_scores = list(family_scores.values())
    if all_scores:
        score_to_rating = normalize_to_rating(all_scores)
    else:
        print("  No scores to normalize")
        score_to_rating = {}
    
    # Step 3: Update database with normalized ratings
    if not args.dry_run:
        print(f"\nStep 3: Updating database with normalized ratings...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                updated = 0
                for family_id, score in family_scores.items():
                    # Use normalized rating for even distribution
                    rating = score_to_rating.get(score, score)  # Fallback to raw score if not in mapping
                    cur.execute("""
                        UPDATE families 
                        SET popularity_rating = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (rating, family_id))
                    updated += 1
                conn.commit()
                print(f"✓ Updated {updated} families with normalized ratings")
    else:
        print(f"\nStep 3: Would update database with ratings:")
        for family_id, score in list(family_scores.items())[:10]:
            rating = score_to_rating.get(score, score)
            family_name = next(f['name'] for f in families if f['id'] == family_id)
            print(f"  {family_name}: raw_score={score} -> normalized_rating={rating}")
        if len(family_scores) > 10:
            print(f"  ... and {len(family_scores) - 10} more")
    
    print(f"\n{'='*60}")
    print("Complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()

