#!/usr/bin/env python3
"""
Cleanup Weekly Words and Phrases

This script:
1. Removes duplicate weekly_word and weekly_phrase entries (keeps one per week)
2. Removes placeholder entries (like "phrase28", "word16")
3. Ensures each week has at most one word and one phrase
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blog-core'))

from config.database import db_manager

def is_placeholder(title, tags):
    """Check if an entry is a placeholder/test entry"""
    if not title:
        return True
    
    title_lower = title.lower()
    
    # Check for placeholder patterns
    if 'phrase' in title_lower and any(char.isdigit() for char in title_lower.split()[-1]):
        # Check if it's like "phrase28" or "Weekly Phrase: phrase28"
        last_word = title_lower.split()[-1]
        if last_word.startswith('phrase') and last_word[6:].isdigit():
            return True
    
    if 'word' in title_lower and any(char.isdigit() for char in title_lower.split()[-1]):
        # Check if it's like "word16" or "Weekly Word: word16"
        last_word = title_lower.split()[-1]
        if last_word.startswith('word') and last_word[4:].isdigit():
            return True
    
    # Check tags for placeholder content
    if isinstance(tags, dict):
        phrase = tags.get('phrase', '')
        word = tags.get('word', '')
        
        if phrase and (phrase.lower().startswith('phrase') and phrase[6:].isdigit()):
            return True
        if word and (word.lower().startswith('word') and word[4:].isdigit()):
            return True
    
    return False

def cleanup_weekly_words_phrases():
    """Clean up duplicate and placeholder entries"""
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get all weekly_word and weekly_phrase entries
            cur.execute("""
                SELECT id, week_number, idea_title, item_classification, tags
                FROM calendar_ideas
                WHERE item_classification IN ('weekly_word', 'weekly_phrase')
                ORDER BY week_number, item_classification, id
            """)
            
            entries = cur.fetchall()
            
            print(f"📊 Found {len(entries)} weekly word/phrase entries")
            
            # Group by week_number and item_classification
            by_week_type = {}
            for entry in entries:
                week = entry['week_number']
                classification = entry['item_classification']
                key = (week, classification)
                
                if key not in by_week_type:
                    by_week_type[key] = []
                by_week_type[key].append(entry)
            
            print(f"📊 Found entries in {len(by_week_type)} week/type combinations\n")
            
            deleted_count = 0
            kept_count = 0
            
            # Process each week/type combination
            for (week, classification), entries_list in by_week_type.items():
                if len(entries_list) == 1:
                    # Only one entry, check if it's a placeholder
                    entry = entries_list[0]
                    if is_placeholder(entry['idea_title'], entry.get('tags')):
                        print(f"  🗑️  Week {week} {classification}: Deleting placeholder '{entry['idea_title'][:50]}'")
                        cur.execute("DELETE FROM calendar_ideas WHERE id = %s", (entry['id'],))
                        deleted_count += 1
                    else:
                        kept_count += 1
                else:
                    # Multiple entries - keep the best one, delete the rest
                    print(f"  ⚠️  Week {week} {classification}: Found {len(entries_list)} entries")
                    
                    # Separate placeholders from real entries
                    placeholders = []
                    real_entries = []
                    
                    for entry in entries_list:
                        if is_placeholder(entry['idea_title'], entry.get('tags')):
                            placeholders.append(entry)
                        else:
                            real_entries.append(entry)
                    
                    # Keep the best real entry (prefer the first one with actual content)
                    if real_entries:
                        keep_entry = real_entries[0]
                        print(f"     ✓ Keeping: '{keep_entry['idea_title'][:50]}'")
                        kept_count += 1
                        
                        # Delete all other real entries
                        for entry in real_entries[1:]:
                            print(f"     🗑️  Deleting duplicate: '{entry['idea_title'][:50]}'")
                            cur.execute("DELETE FROM calendar_ideas WHERE id = %s", (entry['id'],))
                            deleted_count += 1
                    else:
                        # All are placeholders, keep the first one (or delete all?)
                        # Actually, if all are placeholders, we should delete them all
                        print(f"     ⚠️  All entries are placeholders, keeping first")
                        keep_entry = entries_list[0]
                        kept_count += 1
                    
                    # Delete all placeholders
                    for entry in placeholders:
                        print(f"     🗑️  Deleting placeholder: '{entry['idea_title'][:50]}'")
                        cur.execute("DELETE FROM calendar_ideas WHERE id = %s", (entry['id'],))
                        deleted_count += 1
            
            conn.commit()
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Kept: {kept_count}")
    print(f"   Deleted: {deleted_count}")
    print(f"   Total processed: {kept_count + deleted_count}")

if __name__ == '__main__':
    print("🧹 Starting Weekly Words & Phrases Cleanup\n")
    cleanup_weekly_words_phrases()

