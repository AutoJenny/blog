#!/usr/bin/env python3
"""
Import Weekly Words and Phrases from CSV files into calendar_ideas

This script reads:
- scottish_word_of_the_week.csv
- scots_phrase_of_the_week.csv

And imports them as calendar_ideas with:
- item_classification: 'weekly_word' or 'weekly_phrase'
- week_number: Starting from current week, distributed across next 104 weeks (2 years)
- is_recurring: FALSE (one-time, not annually recurring)
- tags: JSON containing Word/Phrase, Meaning, Provenance, Example Usage

Note: calendar_ideas uses week_number (1-52) only, not year. Items will appear
in the correct week each year, but since is_recurring=FALSE, they are marked
as one-time items.
"""

import sys
import os
import csv
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blog-core'))

from config.database import db_manager
from psycopg.types.json import Json

def import_weekly_words_and_phrases():
    """Import both words and phrases, distributing across next 104 weeks"""
    
    # Get current week
    today = datetime.now()
    start_year, start_week = today.isocalendar()[0], today.isocalendar()[1]
    
    print(f"📅 Current week: {start_week} of {start_year}")
    print(f"📅 Distributing across next 104 weeks (2 years)\n")
    
    # Read words CSV
    words_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'scottish_word_of_the_week.csv')
    words = []
    if os.path.exists(words_csv_path):
        with open(words_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            words = [row for row in reader if row.get('Word', '').strip()]
        print(f"📖 Found {len(words)} words in CSV")
    else:
        print(f"❌ CSV file not found: {words_csv_path}")
    
    # Read phrases CSV
    phrases_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'scots_phrase_of_the_week.csv')
    phrases = []
    if os.path.exists(phrases_csv_path):
        with open(phrases_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            phrases = [row for row in reader if row.get('Phrase', '').strip()]
        print(f"📖 Found {len(phrases)} phrases in CSV")
    else:
        print(f"❌ CSV file not found: {phrases_csv_path}")
    
    total_items = len(words) + len(phrases)
    total_weeks = 104  # 2 years
    
    print(f"📊 Total items: {total_items}")
    print(f"📊 Weeks available: {total_weeks}")
    print(f"📊 Average: ~{total_items / total_weeks:.1f} items per week\n")
    
    imported_words = 0
    imported_phrases = 0
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Combine words and phrases, interleaving them
            all_items = []
            for i in range(max(len(words), len(phrases))):
                if i < len(words):
                    all_items.append(('word', words[i], i))
                if i < len(phrases):
                    all_items.append(('phrase', phrases[i], i))
            
            # Now distribute all items across 104 weeks
            for item_idx, (item_type, item_data, original_idx) in enumerate(all_items):
                # Calculate which week this item goes to (distribute evenly across 104 weeks)
                week_offset = item_idx % total_weeks
                
                # Calculate actual week number (1-52, wrapping as needed)
                # Start from current week, then cycle through next 104 weeks
                if week_offset < (52 - start_week + 1):
                    # Still in first year (weeks 45-52)
                    week_number = start_week + week_offset
                else:
                    # Into second year - wrap around to weeks 1-52
                    remaining_offset = week_offset - (52 - start_week + 1)
                    week_number = (remaining_offset % 52) + 1
                
                # Import word if available
                if item_type == 'word':
                    word_data = item_data
                    word = word_data.get('Word', '').strip()
                    
                    if word:
                        meaning = word_data.get('Meaning', '').strip()
                        provenance = word_data.get('Provenance / Notes', '').strip()
                        example = word_data.get('Example Usage', '').strip()
                        
                        tags_data = {
                            'word': word,
                            'meaning': meaning,
                            'provenance': provenance,
                            'example_usage': example,
                            'type': 'weekly_word',
                            'original_week_offset': week_offset,  # Store original offset for reference
                            'start_year': start_year,
                            'start_week': start_week
                        }
                        
                        idea_title = f"Weekly Word: {word}"
                        
                        description_parts = []
                        if meaning:
                            description_parts.append(f"Meaning: {meaning}")
                        if example:
                            description_parts.append(f"Example: {example}")
                        if provenance:
                            description_parts.append(f"Notes: {provenance}")
                        
                        idea_description = "\n\n".join(description_parts) if description_parts else f"Scottish word: {word}"
                        
                        # Check for duplicate (by title and week)
                        cur.execute("""
                            SELECT id FROM calendar_ideas
                            WHERE week_number = %s 
                            AND item_classification = 'weekly_word'
                            AND idea_title = %s
                        """, (week_number, idea_title))
                        
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO calendar_ideas
                                (week_number, idea_title, idea_description, item_classification, tags, is_recurring, priority)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                week_number,
                                idea_title,
                                idea_description,
                                'weekly_word',
                                Json(tags_data),
                                False,  # NOT recurring annually
                                'random'
                            ))
                            imported_words += 1
                
                # Import phrase if available
                elif item_type == 'phrase':
                    phrase_data = item_data
                    phrase = phrase_data.get('Phrase', '').strip()
                    
                    if phrase:
                        meaning = phrase_data.get('Meaning', '').strip()
                        provenance = phrase_data.get('Provenance / Notes', '').strip()
                        example = phrase_data.get('Example Usage', '').strip()
                        
                        tags_data = {
                            'phrase': phrase,
                            'meaning': meaning,
                            'provenance': provenance,
                            'example_usage': example,
                            'type': 'weekly_phrase',
                            'original_week_offset': week_offset,  # Store original offset for reference
                            'start_year': start_year,
                            'start_week': start_week
                        }
                        
                        idea_title = f"Weekly Phrase: {phrase}"
                        
                        description_parts = []
                        if meaning:
                            description_parts.append(f"Meaning: {meaning}")
                        if example:
                            description_parts.append(f"Example: {example}")
                        if provenance:
                            description_parts.append(f"Notes: {provenance}")
                        
                        idea_description = "\n\n".join(description_parts) if description_parts else f"Scots phrase: {phrase}"
                        
                        # Check for duplicate (by title and week)
                        cur.execute("""
                            SELECT id FROM calendar_ideas
                            WHERE week_number = %s 
                            AND item_classification = 'weekly_phrase'
                            AND idea_title = %s
                        """, (week_number, idea_title))
                        
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO calendar_ideas
                                (week_number, idea_title, idea_description, item_classification, tags, is_recurring, priority)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                week_number,
                                idea_title,
                                idea_description,
                                'weekly_phrase',
                                Json(tags_data),
                                False,  # NOT recurring annually
                                'random'
                            ))
                            imported_phrases += 1
                
                if (imported_words + imported_phrases) % 20 == 0 and (imported_words + imported_phrases) > 0:
                    print(f"  ✓ Imported {imported_words + imported_phrases}/{total_items} items...")
            
            conn.commit()
    
    print(f"\n✅ Import complete!")
    print(f"   Words: {imported_words}")
    print(f"   Phrases: {imported_phrases}")
    print(f"   Total: {imported_words + imported_phrases}")
    print(f"\n📝 Note: Items are stored with week_number only (calendar_ideas structure).")
    print(f"   They will appear in the correct week each year, but is_recurring=FALSE")
    print(f"   marks them as one-time items (not automatically repeating).")
    return imported_words, imported_phrases

if __name__ == '__main__':
    print("🚀 Starting Weekly Words & Phrases Import\n")
    
    words_count, phrases_count = import_weekly_words_and_phrases()
