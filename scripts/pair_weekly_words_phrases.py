#!/usr/bin/env python3
"""
Pair Weekly Words and Phrases

This script ensures each week has both a weekly_word and a weekly_phrase.
It pairs existing entries or creates missing ones from the CSV files.
"""

import sys
import os
import csv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blog-core'))

from config.database import db_manager
from psycopg.types.json import Json
from datetime import datetime

def pair_weekly_words_phrases():
    """Ensure each week has both a word and a phrase"""
    
    # Get current week
    today = datetime.now()
    start_year, start_week = today.isocalendar()[0], today.isocalendar()[1]
    
    print(f"📅 Current week: {start_week} of {start_year}\n")
    
    # Read words CSV
    words_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'scottish_word_of_the_week.csv')
    words = []
    if os.path.exists(words_csv_path):
        with open(words_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            words = [row for row in reader if row.get('Word', '').strip() and not row.get('Word', '').strip().lower().startswith('word')]
        print(f"📖 Found {len(words)} words in CSV")
    else:
        print(f"❌ CSV file not found: {words_csv_path}")
        return
    
    # Read phrases CSV
    phrases_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'scots_phrase_of_the_week.csv')
    phrases = []
    if os.path.exists(phrases_csv_path):
        with open(phrases_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            phrases = [row for row in reader if row.get('Phrase', '').strip() and not row.get('Phrase', '').strip().lower().startswith('phrase')]
        print(f"📖 Found {len(phrases)} phrases in CSV\n")
    else:
        print(f"❌ CSV file not found: {phrases_csv_path}")
        return
    
    max_pairs = min(len(words), len(phrases))
    print(f"📊 Will pair {max_pairs} words and phrases across 52 weeks\n")
    
    added_words = 0
    added_phrases = 0
    updated_words = 0
    updated_phrases = 0
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Process each week (1-52)
            for week_number in range(1, 53):
                # Calculate which pair index this week should have
                # Start from current week and cycle through
                week_offset = (week_number - start_week) % 52
                if week_offset < 0:
                    week_offset += 52
                
                pair_idx = week_offset % max_pairs
                
                word_data = words[pair_idx]
                phrase_data = phrases[pair_idx]
                
                # Check what exists for this week
                cur.execute("""
                    SELECT id, idea_title, item_classification
                    FROM calendar_ideas
                    WHERE week_number = %s 
                    AND item_classification IN ('weekly_word', 'weekly_phrase')
                """, (week_number,))
                
                existing = cur.fetchall()
                existing_word = next((e for e in existing if e['item_classification'] == 'weekly_word'), None)
                existing_phrase = next((e for e in existing if e['item_classification'] == 'weekly_phrase'), None)
                
                # Process word
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
                    
                    if not existing_word:
                        # Add missing word
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
                            False,
                            'random'
                        ))
                        added_words += 1
                        print(f"  ✓ Week {week_number}: Added word '{word}'")
                    else:
                        # Update existing word if it's different
                        if existing_word['idea_title'] != idea_title:
                            cur.execute("""
                                UPDATE calendar_ideas
                                SET idea_title = %s, idea_description = %s, tags = %s
                                WHERE id = %s
                            """, (idea_title, idea_description, Json(tags_data), existing_word['id']))
                            updated_words += 1
                            print(f"  ↻ Week {week_number}: Updated word to '{word}'")
                
                # Process phrase
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
                    
                    if not existing_phrase:
                        # Add missing phrase
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
                            False,
                            'random'
                        ))
                        added_phrases += 1
                        print(f"  ✓ Week {week_number}: Added phrase '{phrase[:40]}...'")
                    else:
                        # Update existing phrase if it's different
                        if existing_phrase['idea_title'] != idea_title:
                            cur.execute("""
                                UPDATE calendar_ideas
                                SET idea_title = %s, idea_description = %s, tags = %s
                                WHERE id = %s
                            """, (idea_title, idea_description, Json(tags_data), existing_phrase['id']))
                            updated_phrases += 1
                            print(f"  ↻ Week {week_number}: Updated phrase to '{phrase[:40]}...'")
            
            conn.commit()
    
    print(f"\n✅ Pairing complete!")
    print(f"   Added words: {added_words}")
    print(f"   Added phrases: {added_phrases}")
    print(f"   Updated words: {updated_words}")
    print(f"   Updated phrases: {updated_phrases}")

if __name__ == '__main__':
    print("🔗 Starting Weekly Words & Phrases Pairing\n")
    pair_weekly_words_phrases()

