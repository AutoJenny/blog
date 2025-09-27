#!/usr/bin/env python3
"""
Comprehensive fix for seasonal calendar content.
This script will properly allocate all seasonal content to the correct weeks
based on actual seasonal timing and events.
"""

import sys
import os
import json
from datetime import datetime, date

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def get_week_number(target_date, year=2025):
    """Get the week number for a specific date in a given year."""
    target = date(year, target_date.month, target_date.day)
    jan_1 = date(year, 1, 1)
    days_since_jan_1 = (target - jan_1).days
    week_number = (days_since_jan_1 // 7) + 1
    return min(max(week_number, 1), 52)

def fix_seasonal_content():
    """Fix all seasonal content to be in the correct weeks."""
    print("Fixing seasonal calendar content...")
    
    # Comprehensive seasonal mapping based on actual dates and seasons
    seasonal_mapping = {
        # WINTER CONTENT (Dec-Feb)
        "Winter Foods & Whisky Pairings": date(2025, 1, 15),  # Mid-winter
        "Tartan Fashion in Winter": date(2025, 1, 22),  # Deep winter
        "Celtic Winter Folklore": date(2025, 1, 29),  # Late winter
        "Scottish Winter Recipes": date(2025, 2, 5),  # Still winter
        "Winter Wellness Tips": date(2025, 2, 12),  # Late winter
        "Winter Garden Planning": date(2025, 2, 19),  # End of winter
        "Winter Garden Protection": date(2025, 2, 26),  # Very late winter
        "Winter Comfort Foods": date(2025, 12, 15),  # Early winter
        "Winter Home Maintenance": date(2025, 12, 22),  # Mid-winter
        "Winter Solstice / Yule Traditions": date(2025, 12, 21),  # Winter solstice
        "Scottish Christmas Traditions": date(2025, 12, 25),  # Christmas
        "Christmas Cookie Recipes": date(2025, 12, 10),  # Pre-Christmas
        "Christmas Dinner Menu": date(2025, 12, 20),  # Pre-Christmas
        
        # SPRING CONTENT (Mar-May)
        "Spring Cleaning Checklist": date(2025, 3, 15),  # Mid-spring
        "Spring Home Maintenance": date(2025, 3, 22),  # Spring cleaning time
        "Spring Highland Games Preview": date(2025, 3, 29),  # Spring season start
        "Spring Flower Arranging": date(2025, 4, 5),  # Spring flowers
        "Scottish Wildflowers in Spring": date(2025, 4, 12),  # Spring wildflowers
        "Early Spring Planting": date(2025, 4, 19),  # Spring planting
        "Spring Fashion Trends": date(2025, 4, 26),  # Spring fashion
        "Spring Break Travel Tips": date(2025, 4, 2),  # Spring break time
        "Spring Clan Gatherings": date(2025, 5, 3),  # Late spring
        
        # SUMMER CONTENT (Jun-Aug)
        "Summer Vacation Planning": date(2025, 6, 1),  # Summer start
        "Summer Camp Activities": date(2025, 6, 8),  # Early summer
        "Top Lochs & Glens in Summer": date(2025, 6, 15),  # Summer travel
        "Summer Garden Care": date(2025, 6, 22),  # Summer gardening
        "Summer Solstice Celtic Traditions": date(2025, 6, 21),  # Summer solstice
        "Summer Hydration Tips": date(2025, 7, 1),  # Peak summer
        "Backyard Summer Party": date(2025, 7, 8),  # Summer entertaining
        "Summer Reading List": date(2025, 7, 15),  # Summer leisure
        "Summer Grilling Recipes": date(2025, 7, 22),  # Summer cooking
        "Summer Garden Harvest": date(2025, 8, 1),  # Summer harvest
        "Summer Recipes with Berries/Seafood": date(2025, 8, 8),  # Summer produce
        "Summer Solstice Celebration": date(2025, 6, 21),  # Summer solstice (duplicate)
        
        # FALL CONTENT (Sep-Nov)
        "Fall Fashion Trends": date(2025, 9, 15),  # Fall fashion
        "Fall Comfort Foods": date(2025, 10, 1),  # Fall cooking
        "Fall Leaf Raking Tips": date(2025, 10, 15),  # Fall yard work
        "Fall Garden Planning": date(2025, 9, 22),  # Fall garden prep
        "Fall Home Decorating": date(2025, 10, 8),  # Fall decorating
    }
    
    with db_manager.get_cursor() as cursor:
        # Get all ideas that need seasonal fixing
        seasonal_titles = tuple(seasonal_mapping.keys())
        placeholders = ','.join(['%s'] * len(seasonal_titles))
        cursor.execute(f"""
            SELECT id, idea_title, week_number 
            FROM calendar_ideas 
            WHERE idea_title IN ({placeholders})
            ORDER BY idea_title
        """, seasonal_titles)
        
        ideas_to_fix = cursor.fetchall()
        print(f"Found {len(ideas_to_fix)} ideas to fix seasonally")
        
        # Fix each idea
        for idea in ideas_to_fix:
            title = idea['idea_title']
            current_week = idea['week_number']
            
            if title in seasonal_mapping:
                target_date = seasonal_mapping[title]
                correct_week = get_week_number(target_date)
                
                if current_week != correct_week:
                    cursor.execute("""
                        UPDATE calendar_ideas 
                        SET week_number = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (correct_week, idea['id']))
                    
                    print(f"Fixed '{title}': Week {current_week} → Week {correct_week} ({target_date})")
                else:
                    print(f"'{title}' already in correct week {correct_week}")
        
        # Now fix any remaining seasonal content that wasn't in our mapping
        seasonal_titles = tuple(seasonal_mapping.keys())
        placeholders = ','.join(['%s'] * len(seasonal_titles))
        query = f"""
            SELECT id, idea_title, week_number, seasonal_context
            FROM calendar_ideas 
            WHERE (idea_title ILIKE '%%winter%%' OR idea_title ILIKE '%%spring%%' 
                   OR idea_title ILIKE '%%summer%%' OR idea_title ILIKE '%%fall%%'
                   OR idea_title ILIKE '%%christmas%%' OR idea_title ILIKE '%%yule%%'
                   OR idea_title ILIKE '%%solstice%%')
            AND idea_title NOT IN ({placeholders})
            ORDER BY week_number
        """
        cursor.execute(query, seasonal_titles)
        
        remaining_seasonal = cursor.fetchall()
        print(f"\nFound {len(remaining_seasonal)} additional seasonal items to review:")
        
        for item in remaining_seasonal:
            print(f"  Week {item['week_number']}: {item['idea_title']} - {item['seasonal_context']}")
        
        # Distribute remaining seasonal content more intelligently
        print("\nDistributing remaining seasonal content...")
        
        # Group by season based on keywords
        winter_items = []
        spring_items = []
        summer_items = []
        fall_items = []
        holiday_items = []
        
        for item in remaining_seasonal:
            title_lower = item['idea_title'].lower()
            if any(word in title_lower for word in ['winter', 'christmas', 'yule', 'holiday']):
                winter_items.append(item)
            elif any(word in title_lower for word in ['spring', 'easter']):
                spring_items.append(item)
            elif any(word in title_lower for word in ['summer', 'solstice']):
                summer_items.append(item)
            elif any(word in title_lower for word in ['fall', 'autumn', 'harvest']):
                fall_items.append(item)
            else:
                holiday_items.append(item)
        
        # Distribute winter items (weeks 1-8, 50-52)
        winter_weeks = list(range(1, 9)) + list(range(50, 53))
        for i, item in enumerate(winter_items):
            target_week = winter_weeks[i % len(winter_weeks)]
            cursor.execute("""
                UPDATE calendar_ideas 
                SET week_number = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_week, item['id']))
            print(f"  Winter: '{item['idea_title']}' → Week {target_week}")
        
        # Distribute spring items (weeks 9-20)
        spring_weeks = list(range(9, 21))
        for i, item in enumerate(spring_items):
            target_week = spring_weeks[i % len(spring_weeks)]
            cursor.execute("""
                UPDATE calendar_ideas 
                SET week_number = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_week, item['id']))
            print(f"  Spring: '{item['idea_title']}' → Week {target_week}")
        
        # Distribute summer items (weeks 21-35)
        summer_weeks = list(range(21, 36))
        for i, item in enumerate(summer_items):
            target_week = summer_weeks[i % len(summer_weeks)]
            cursor.execute("""
                UPDATE calendar_ideas 
                SET week_number = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_week, item['id']))
            print(f"  Summer: '{item['idea_title']}' → Week {target_week}")
        
        # Distribute fall items (weeks 36-49)
        fall_weeks = list(range(36, 50))
        for i, item in enumerate(fall_items):
            target_week = fall_weeks[i % len(fall_weeks)]
            cursor.execute("""
                UPDATE calendar_ideas 
                SET week_number = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_week, item['id']))
            print(f"  Fall: '{item['idea_title']}' → Week {target_week}")
        
        # Distribute holiday items to appropriate weeks
        holiday_weeks = [52, 51, 50, 1, 2]  # Christmas/New Year period
        for i, item in enumerate(holiday_items):
            target_week = holiday_weeks[i % len(holiday_weeks)]
            cursor.execute("""
                UPDATE calendar_ideas 
                SET week_number = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_week, item['id']))
            print(f"  Holiday: '{item['idea_title']}' → Week {target_week}")
        
        cursor.connection.commit()
        
        # Show final distribution
        print("\nFinal seasonal distribution:")
        cursor.execute("""
            SELECT week_number, COUNT(*) as count,
                   string_agg(idea_title, ', ' ORDER BY idea_title) as titles
            FROM calendar_ideas 
            WHERE (idea_title ILIKE '%winter%' OR idea_title ILIKE '%spring%' 
                   OR idea_title ILIKE '%summer%' OR idea_title ILIKE '%fall%'
                   OR idea_title ILIKE '%christmas%' OR idea_title ILIKE '%yule%'
                   OR idea_title ILIKE '%solstice%')
            GROUP BY week_number 
            ORDER BY week_number
        """)
        
        seasonal_distribution = cursor.fetchall()
        for row in seasonal_distribution:
            print(f"  Week {row['week_number']}: {row['count']} items - {row['titles'][:100]}...")
        
        print(f"\nSeasonal content fixed! All seasonal items now properly allocated.")

def main():
    try:
        fix_seasonal_content()
        print("\nSeasonal calendar content fixed successfully!")
        print("The calendar should now show content in seasonally appropriate weeks.")
        
    except Exception as e:
        print(f"Error fixing seasonal content: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
