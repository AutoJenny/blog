#!/usr/bin/env python3
"""
Import Weekly Insults from CSV file into calendar_ideas

This script reads:
- scots_insult_of_the_week.csv

And imports them as calendar_ideas with:
- item_classification: 'weekly_insult'
- position: Sequential position (1, 2, 3, ...)
- idea_title: The insult text
- idea_description: Formatted as "Translation: ... | Provenance: ..."
"""

import sys
import os
import csv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blog-core'))

from config.database import db_manager

def import_weekly_insults():
    """Import insults from CSV, assigning sequential positions"""
    
    # Read insults CSV
    insults_csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'data', 
        'scots_insult_of_the_week.csv'
    )
    
    insults = []
    if os.path.exists(insults_csv_path):
        with open(insults_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                insult = row.get('insult', '').strip()
                if insult:
                    insults.append({
                        'insult': insult,
                        'translation': row.get('translation', '').strip(),
                        'notes': row.get('notes', '').strip()
                    })
        print(f"📖 Found {len(insults)} insults in CSV")
    else:
        print(f"❌ CSV file not found: {insults_csv_path}")
        return 0
    
    if not insults:
        print("❌ No insults found in CSV")
        return 0
    
    imported_count = 0
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # First, get the current max position for weekly_insult
            cur.execute("""
                SELECT COALESCE(MAX(position), 0) AS max_pos
                FROM calendar_ideas
                WHERE item_classification = 'weekly_insult' AND position IS NOT NULL
            """)
            max_pos_row = cur.fetchone()
            max_pos = max_pos_row['max_pos'] if max_pos_row else 0
            
            # Delete existing weekly_insult entries to start fresh
            print(f"🗑️  Clearing existing weekly_insult entries...")
            cur.execute("""
                DELETE FROM calendar_ideas
                WHERE item_classification = 'weekly_insult'
            """)
            deleted_count = cur.rowcount
            print(f"   Deleted {deleted_count} existing entries")
            
            # Import each insult with sequential position
            for idx, insult_data in enumerate(insults, start=1):
                insult_text = insult_data['insult']
                translation = insult_data['translation']
                notes = insult_data['notes']
                
                # Build description in format: "Translation: ... | Provenance: ..."
                description_parts = []
                if translation:
                    description_parts.append(f"Translation: {translation}")
                if notes:
                    description_parts.append(f"Provenance: {notes}")
                
                idea_description = " | ".join(description_parts) if description_parts else ""
                
                # Insert with position = idx (1, 2, 3, ...)
                # Note: week_number is required NOT NULL, so we set it to position
                # This is a legacy field; the system uses position for cycling
                cur.execute("""
                    INSERT INTO calendar_ideas
                    (position, week_number, idea_title, idea_description, item_classification)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    idx,  # position
                    idx,  # week_number (legacy field, required NOT NULL)
                    insult_text,  # idea_title
                    idea_description,  # idea_description
                    'weekly_insult'  # item_classification
                ))
                imported_count += 1
                
                if imported_count % 20 == 0:
                    print(f"  ✓ Imported {imported_count} insults...")
            
            conn.commit()
    
    print(f"\n✅ Import complete!")
    print(f"   Insults imported: {imported_count}")
    print(f"   Positions assigned: 1 to {imported_count}")
    return imported_count

if __name__ == '__main__':
    print("🚀 Starting Weekly Insults Import\n")
    
    count = import_weekly_insults()
    if count > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Rebuild JSON schedules: python3 scripts/build_calendar_schedules.py --category weekly_insult")
        print(f"   2. Or rebuild all: python3 scripts/build_calendar_schedules.py")

