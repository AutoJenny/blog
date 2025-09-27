#!/usr/bin/env python3
"""
Fix calendar content to only use weeks 1-52 instead of 1-64.
This script will redistribute the content ideas across the proper 52-week calendar.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def fix_calendar_weeks():
    """Redistribute content ideas to only use weeks 1-52."""
    print("Fixing calendar weeks - redistributing content to weeks 1-52...")
    
    with db_manager.get_cursor() as cursor:
        # Get all ideas with week numbers > 52
        cursor.execute("""
            SELECT * FROM calendar_ideas 
            WHERE week_number > 52 
            ORDER BY week_number, priority DESC
        """)
        
        extra_ideas = cursor.fetchall()
        print(f"Found {len(extra_ideas)} ideas with week numbers > 52")
        
        # Get current distribution of ideas in weeks 1-52
        cursor.execute("""
            SELECT week_number, COUNT(*) as idea_count 
            FROM calendar_ideas 
            WHERE week_number <= 52 
            GROUP BY week_number 
            ORDER BY week_number
        """)
        
        current_distribution = {row['week_number']: row['idea_count'] for row in cursor.fetchall()}
        print(f"Current distribution: {current_distribution}")
        
        # Find weeks with fewer ideas (target: 2-3 ideas per week)
        target_ideas_per_week = 2
        weeks_needing_ideas = []
        
        for week in range(1, 53):
            current_count = current_distribution.get(week, 0)
            if current_count < target_ideas_per_week:
                weeks_needing_ideas.extend([week] * (target_ideas_per_week - current_count))
        
        print(f"Weeks needing more ideas: {len(weeks_needing_ideas)} slots")
        
        # Redistribute extra ideas to weeks that need them
        for i, idea in enumerate(extra_ideas):
            if i < len(weeks_needing_ideas):
                new_week = weeks_needing_ideas[i]
                
                # Update the idea's week number
                cursor.execute("""
                    UPDATE calendar_ideas 
                    SET week_number = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_week, idea['id']))
                
                print(f"Moved '{idea['idea_title']}' from week {idea['week_number']} to week {new_week}")
            else:
                # If we run out of slots, just update to week 52
                cursor.execute("""
                    UPDATE calendar_ideas 
                    SET week_number = 52, updated_at = NOW()
                    WHERE id = %s
                """, (idea['id'],))
                
                print(f"Moved '{idea['idea_title']}' from week {idea['week_number']} to week 52")
        
        # Delete any ideas that are still > week 52 (shouldn't happen, but just in case)
        cursor.execute("DELETE FROM calendar_ideas WHERE week_number > 52")
        deleted_count = cursor.rowcount
        if deleted_count > 0:
            print(f"Deleted {deleted_count} ideas that were still > week 52")
        
        cursor.connection.commit()
        
        # Show final distribution
        cursor.execute("""
            SELECT week_number, COUNT(*) as idea_count 
            FROM calendar_ideas 
            GROUP BY week_number 
            ORDER BY week_number
        """)
        
        final_distribution = {row['week_number']: row['idea_count'] for row in cursor.fetchall()}
        print(f"Final distribution: {final_distribution}")
        
        # Show weeks with most ideas
        cursor.execute("""
            SELECT week_number, COUNT(*) as idea_count 
            FROM calendar_ideas 
            GROUP BY week_number 
            HAVING COUNT(*) > 3
            ORDER BY idea_count DESC
        """)
        
        overloaded_weeks = cursor.fetchall()
        if overloaded_weeks:
            print("Weeks with more than 3 ideas:")
            for week in overloaded_weeks:
                print(f"  Week {week['week_number']}: {week['idea_count']} ideas")
        
        print(f"Calendar weeks fixed! All content now uses weeks 1-52")

def main():
    try:
        fix_calendar_weeks()
        print("\nCalendar weeks fixed successfully!")
        print("The calendar should now display content properly.")
        
    except Exception as e:
        print(f"Error fixing calendar weeks: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
