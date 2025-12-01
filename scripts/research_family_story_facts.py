#!/usr/bin/env python3
"""
Story Facts Research Tool - Second Pass
Extracts narrative elements and story facts for extended content.

Usage:
    python3 scripts/research_family_story_facts.py <family_id_or_name> [--save] [--update]
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager

# Import LLM service
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
    from app.llm.services import LLMService
except ImportError:
    from blueprints.planning_llm import LLMService

# Import modular components
from utils.family_research import (
    get_family_context,
    load_template,
    perform_web_search,
    fetch_page_content,
    chunk_text,
    extract_facts_from_chunk,
    post_process_story_facts,
    generate_narrative
)


def merge_facts(accumulated_facts: Dict, new_facts: Dict):
    """Merge new facts into accumulated facts with deduplication."""
    for key in ['key_figures', 'turning_points', 'places', 
               'legends_and_dark_episodes', 'themes', 'sources_summary', 'quotations']:
        if key in new_facts and new_facts[key]:
            if key not in accumulated_facts:
                accumulated_facts[key] = []
            if isinstance(accumulated_facts[key], list):
                existing_items = accumulated_facts[key]
                for new_item in new_facts[key]:
                    is_duplicate = False
                    
                    if key == 'quotations':
                        for existing in existing_items:
                            if isinstance(existing, dict) and isinstance(new_item, dict):
                                existing_text = existing.get('quoted_text') or ''
                                new_text = new_item.get('quoted_text') or ''
                                if isinstance(existing_text, str) and isinstance(new_text, str):
                                    if existing_text.strip().lower() == new_text.strip().lower():
                                        is_duplicate = True
                                    if existing.get('speaker') != new_item.get('speaker'):
                                        if 'uncertainty_flags' not in existing:
                                            existing['uncertainty_flags'] = []
                                        existing['uncertainty_flags'].append(
                                            f"Also attributed in one source to {new_item.get('speaker', 'unknown')}."
                                        )
                                    break
                    
                    elif key == 'key_figures':
                        for existing in existing_items:
                            if isinstance(existing, dict) and isinstance(new_item, dict):
                                if existing.get('name', '').strip().lower() == new_item.get('name', '').strip().lower():
                                    is_duplicate = True
                                    break
                    
                    elif key == 'turning_points':
                        for existing in existing_items:
                            if isinstance(existing, dict) and isinstance(new_item, dict):
                                if existing.get('id') == new_item.get('id') or \
                                   existing.get('title', '').strip().lower() == new_item.get('title', '').strip().lower():
                                    is_duplicate = True
                                    break
                    
                    elif key == 'places':
                        for existing in existing_items:
                            if isinstance(existing, dict) and isinstance(new_item, dict):
                                if existing.get('name', '').strip().lower() == new_item.get('name', '').strip().lower():
                                    is_duplicate = True
                                    break
                    
                    elif key == 'themes':
                        if isinstance(new_item, str):
                            if new_item.strip().lower() in [t.strip().lower() for t in existing_items if isinstance(t, str)]:
                                is_duplicate = True
                    
                    if not is_duplicate:
                        existing_items.append(new_item)
                
                accumulated_facts[key] = existing_items
    
    # Update time_span if we have better info
    if 'time_span' in new_facts and new_facts['time_span']:
        if 'time_span' not in accumulated_facts:
            accumulated_facts['time_span'] = {}
        ts = new_facts['time_span']
        if ts.get('earliest_century') and ts['earliest_century'] != 'unknown':
            if not accumulated_facts['time_span'].get('earliest_century') or \
               accumulated_facts['time_span']['earliest_century'] == 'unknown':
                accumulated_facts['time_span']['earliest_century'] = ts['earliest_century']
        if ts.get('latest_century') and ts['latest_century'] != 'unknown':
            if not accumulated_facts['time_span'].get('latest_century') or \
               accumulated_facts['time_span']['latest_century'] == 'unknown':
                accumulated_facts['time_span']['latest_century'] = ts['latest_century']


def main():
    """Main story facts research workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Story Facts Research Tool - Second Pass')
    parser.add_argument('family', help='Family ID or name')
    parser.add_argument('--save', action='store_true', help='Save JSON to file and update database')
    parser.add_argument('--no-update', action='store_true', help='Save to file but do NOT update database')
    parser.add_argument('--dry-run', action='store_true', help='Validate but do not update database')
    parser.add_argument('--model', type=str, default='llama3.2:latest', help='LLM model name')
    parser.add_argument('--word-target', type=int, default=2500, help='Target word count for narrative (default: 2500)')
    parser.add_argument('--narrative-only', action='store_true', help='Generate narrative from existing story_facts (skip fact extraction)')
    
    args = parser.parse_args()
    
    # Get family context
    try:
        family_id = int(args.family)
        family_name = None
    except ValueError:
        family_id = None
        family_name = args.family
    
    print("Fetching family context from database...")
    context = get_family_context(family_id, family_name)
    if not context:
        print(f"Error: Family not found: {args.family}")
        return 1
    
    family_id = context['family']['id']
    family_name = context['family']['name']
    
    # Check status of all research components
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT has_history, research_data FROM families WHERE id = %s", (family_id,))
            row = cur.fetchone()
            has_history = row['has_history'] if row else False
            research_data = row['research_data'] if row else None
            
            # Parse research_data if it exists
            if research_data:
                if isinstance(research_data, str):
                    research_data = json.loads(research_data)
            else:
                research_data = {}
            
            # Check each component
            has_json = bool(research_data and len(research_data) > 1)
            has_compiled = bool(research_data.get('metadata', {}).get('narrative'))
            has_openai = bool(research_data.get('metadata', {}).get('narrative_fact_checked'))
            
            # Display status
            print(f"\n{'='*60}")
            print(f"Story Facts Research (Second Pass): {family_name} (ID: {family_id})")
            print(f"{'='*60}")
            print(f"\nStatus:")
            print(f"  {'✓' if has_history else '✗'} CLAN (has_history): {'Yes' if has_history else 'No'}")
            print(f"  {'✓' if has_json else '✗'} JSON (research_data): {'Yes' if has_json else 'No'}")
            print(f"  {'✓' if has_compiled else '✗'} Compiled (narrative): {'Yes' if has_compiled else 'No'}")
            print(f"  {'✓' if has_openai else '✗'} OpenAI (fact-checked): {'Yes' if has_openai else 'No'}")
            print()
    
    # Load existing research data
    template = load_template()
    existing_story_facts = template.get('story_facts', {})
    
    # Check if family already has research_data
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
            existing = cur.fetchone()
            if existing and existing['research_data']:
                existing_data = existing['research_data']
                if isinstance(existing_data, str):
                    existing_data = json.loads(existing_data)
                if 'story_facts' in existing_data:
                    existing_story_facts = existing_data['story_facts']
                    print(f"  Loaded existing story_facts")
    
    # Initialize LLM service
    print("Initializing LLM service...")
    llm_service = LLMService()
    
    # If narrative-only, skip fact extraction
    if args.narrative_only:
        print("\nNarrative-only mode: Generating narrative from existing story_facts...")
        # Load existing research data
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
                existing = cur.fetchone()
                if existing and existing['research_data']:
                    existing_data = existing['research_data']
                    if isinstance(existing_data, str):
                        existing_data = json.loads(existing_data)
                    research_data = existing_data
                else:
                    print("Error: No existing research_data found. Run fact extraction first.")
                    return 1
        
        narrative = generate_narrative(family_name, research_data, llm_service, word_target=args.word_target)
        
        if narrative:
            if 'metadata' not in research_data:
                research_data['metadata'] = {}
            research_data['metadata']['narrative'] = narrative
            research_data['metadata']['narrative_word_count'] = len(narrative.split())
            print(f"\n✓ Generated narrative ({len(narrative.split())} words)")
            
            # Also save narrative to separate text file
            if args.save:
                narrative_file = f"data/narrative_{family_name.replace(' ', '_')}_{family_id}.md"
                with open(narrative_file, 'w') as f:
                    f.write(f"# {family_name}: A Historical Narrative\n\n")
                    f.write(narrative)
                print(f"✓ Narrative saved to: {narrative_file}")
        else:
            print("\n✗ Failed to generate narrative")
            return 1
        
        # Save and update
        if args.save:
            output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}_story_facts.json"
            with open(output_file, 'w') as f:
                json.dump(research_data, f, indent=2)
            print(f"✓ Saved to: {output_file}")
        
        should_update = args.save and not args.no_update
        if should_update:
            import importlib.util
            research_family_path = Path(__file__).parent / 'research_family.py'
            spec = importlib.util.spec_from_file_location("research_family", research_family_path)
            research_family = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(research_family)
            
            success, message = research_family.update_family_research(family_id, research_data, dry_run=args.dry_run)
            if success:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                return 1
        
        return 0
    
    # Search for story-focused content
    print("\nSearching for story-focused content...")
    search_queries = [
        f"{family_name} clan history",
        f"{family_name} Scottish history",
        f"{family_name} key figures",
        f"{family_name} historical events",
        f"{family_name} legends stories"
    ]
    
    all_search_results = []
    for query in search_queries:
        print(f"  Searching: {query}")
        results = perform_web_search(query, max_results=3)
        all_search_results.extend(results)
        time.sleep(1)  # Rate limiting
    
    print(f"  Found {len(all_search_results)} search results")
    
    # Fetch and process pages
    print("\nFetching and processing pages...")
    accumulated_facts = existing_story_facts.copy() if existing_story_facts else {}
    
    for i, result in enumerate(all_search_results[:10], 1):  # Limit to top 10
        print(f"\n  Processing {i}/{min(10, len(all_search_results))}: {result['title']}")
        print(f"    URL: {result['url']}")
        
        # Fetch page content
        content = fetch_page_content(result['url'])
        if not content:
            print("    Skipping: Could not fetch content")
            continue
        
        # Chunk the content
        chunks = chunk_text(content, chunk_size=3000)
        print(f"    Split into {len(chunks)} chunks")
        
        # Process each chunk
        for j, chunk in enumerate(chunks, 1):
            print(f"    Processing chunk {j}/{len(chunks)}...")
            facts = extract_facts_from_chunk(
                family_name,
                chunk,
                accumulated_facts if accumulated_facts else None,
                llm_service
            )
            
            if facts:
                merge_facts(accumulated_facts, facts)
            
            time.sleep(1)  # Rate limiting
    
    # Post-process accumulated_facts to normalize structure
    accumulated_facts = post_process_story_facts(accumulated_facts)
    
    # Load existing research data and merge with accumulated_facts
    research_data = None
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
            existing = cur.fetchone()
            if existing and existing['research_data']:
                existing_data = existing['research_data']
                if isinstance(existing_data, str):
                    existing_data = json.loads(existing_data)
                existing_data['story_facts'] = accumulated_facts
                research_data = existing_data
            else:
                research_data = template.copy()
                research_data['surname'] = family_name
                research_data['story_facts'] = accumulated_facts
    
    if not research_data:
        research_data = template.copy()
        research_data['surname'] = family_name
        research_data['story_facts'] = accumulated_facts
    
    research_data['surname'] = family_name
    if 'metadata' not in research_data:
        research_data['metadata'] = {}
    research_data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Apply Prompt 2 (Story Writing) - Generate final narrative
    print("\n" + "="*60)
    print("Generating immersive narrative (Prompt 2)...")
    print("="*60)
    
    narrative = generate_narrative(family_name, research_data, llm_service, word_target=args.word_target)
    
    if narrative:
        # Store narrative in research_data metadata
        if 'metadata' not in research_data:
            research_data['metadata'] = {}
        research_data['metadata']['narrative'] = narrative
        research_data['metadata']['narrative_word_count'] = len(narrative.split())
        print(f"\n✓ Generated narrative ({len(narrative.split())} words)")
        
        # Also save narrative to separate text file
        if args.save:
            narrative_file = f"data/narrative_{family_name.replace(' ', '_')}_{family_id}.md"
            with open(narrative_file, 'w') as f:
                f.write(f"# {family_name}: A Historical Narrative\n\n")
                f.write(narrative)
            print(f"✓ Narrative saved to: {narrative_file}")
    else:
        print("\n✗ Failed to generate narrative")
        print("Error: Cannot proceed without narrative. Please check LLM service and try again.")
        return 1
    
    # Save to file
    if args.save:
        output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}_story_facts.json"
        with open(output_file, 'w') as f:
            json.dump(research_data, f, indent=2)
        print(f"\n✓ Saved to: {output_file}")
    
    # Update database
    should_update = args.save and not args.no_update
    if should_update:
        # Import validation and update functions
        import importlib.util
        research_family_path = Path(__file__).parent / 'research_family.py'
        spec = importlib.util.spec_from_file_location("research_family", research_family_path)
        research_family = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(research_family)
        
        success, message = research_family.update_family_research(family_id, research_data, dry_run=args.dry_run)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            return 1
    
    print(f"\n{'='*60}")
    print("Story Facts Research Complete")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
