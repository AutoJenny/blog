#!/usr/bin/env python3
"""
Fix calendar content to use correct week numbers based on actual dates.
This script will map content to the correct weeks based on when events actually occur.
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
    # Create a date object for the target date
    target = date(year, target_date.month, target_date.day)
    
    # Get January 1st of the year
    jan_1 = date(year, 1, 1)
    
    # Calculate the week number (1-based)
    days_since_jan_1 = (target - jan_1).days
    week_number = (days_since_jan_1 // 7) + 1
    
    # Ensure week number is between 1 and 52
    return min(max(week_number, 1), 52)

def fix_calendar_dates():
    """Fix calendar content to use correct week numbers based on actual dates."""
    print("Fixing calendar dates - mapping content to correct weeks based on actual dates...")
    
    # Define the correct dates for seasonal content
    seasonal_dates = {
        # January
        "New Year's Day / Hogmanay Traditions": date(2025, 1, 1),
        "Burns Night Preparation": date(2025, 1, 15),  # Burns Night is Jan 25, prep week before
        "Winter Foods & Whisky Pairings": date(2025, 1, 22),
        "Celtic Winter Folklore": date(2025, 1, 29),
        
        # February
        "Valentine's Day Celtic Legends": date(2025, 2, 14),
        "Six Nations Rugby Preview": date(2025, 2, 1),  # Rugby season starts
        "Clan Love Stories": date(2025, 2, 21),
        "Celtic Jewelry Guide": date(2025, 2, 28),
        
        # March
        "St David's Day (Wales)": date(2025, 3, 1),
        "St Patrick's Day Irish Heritage": date(2025, 3, 17),
        "Mother's Day Celtic Traditions": date(2025, 3, 30),  # UK Mother's Day
        "Spring Highland Games Preview": date(2025, 3, 15),
        
        # April
        "April Fool's Day - Huntigowk Day": date(2025, 4, 1),
        "Easter Celtic Traditions": date(2025, 4, 20),  # Easter 2025
        "Beltane Preparation": date(2025, 4, 25),  # Beltane is May 1
        "Scottish Wildflowers in Spring": date(2025, 4, 15),
        
        # May
        "Beltane Fire Festival": date(2025, 5, 1),
        "May Bank Holiday Traditions": date(2025, 5, 5),  # May Day bank holiday
        "Scottish Islands Travel Guide": date(2025, 5, 15),
        "Irish Folklore of May": date(2025, 5, 22),
        
        # June
        "Father's Day Clan Heroes": date(2025, 6, 15),  # UK Father's Day
        "Highland Games Season Start": date(2025, 6, 1),
        "Summer Solstice Celtic Traditions": date(2025, 6, 21),
        "Scottish Castles & Clan Seats": date(2025, 6, 30),
        
        # July
        "Canada Day - Scottish Diaspora": date(2025, 7, 1),
        "Independence Day - US Scottish Heritage": date(2025, 7, 4),
        "Edinburgh Festival Preview": date(2025, 7, 15),  # Festival starts in August
        "Scottish Regiments in NA History": date(2025, 7, 22),
        
        # August
        "Lammas / Lughnasadh Festival": date(2025, 8, 1),
        "Edinburgh International Festival": date(2025, 8, 8),  # Festival starts
        "Highland Games Peak Season": date(2025, 8, 15),
        "Gaelic Harvest Traditions": date(2025, 8, 22),
        
        # September
        "Labour Day - Scottish Workers": date(2025, 9, 1),  # US Labor Day
        "Autumn Equinox Celtic Traditions": date(2025, 9, 22),
        "Michaelmas - Scottish Quarter Day": date(2025, 9, 29),
        "Harvest Recipes & Clan Feasts": date(2025, 9, 15),
        
        # October
        "Canadian Thanksgiving - Scottish Influence": date(2025, 10, 13),  # Canadian Thanksgiving
        "Halloween / Samhain Origins": date(2025, 10, 31),
        "Scottish Ghost Stories": date(2025, 10, 15),
        "Haunted Castles of Scotland": date(2025, 10, 22),
        
        # November
        "All Saints' / Samhain Continuation": date(2025, 11, 1),
        "Guy Fawkes Night - Scottish Connections": date(2025, 11, 5),
        "Remembrance Day - Scottish Veterans": date(2025, 11, 11),
        "US Thanksgiving - Scottish Influence": date(2025, 11, 27),  # US Thanksgiving
        "St Andrew's Day - Scotland's Patron Saint": date(2025, 11, 30),
        
        # December
        "St Nicholas Day - Scottish Traditions": date(2025, 12, 6),
        "Winter Solstice / Yule Traditions": date(2025, 12, 21),
        "Scottish Christmas Traditions": date(2025, 12, 25),
        "Celtic Yule Lore": date(2025, 12, 15),
        "Festive Music & Ceilidhs": date(2025, 12, 22),
        "Hogmanay / New Year's Eve": date(2025, 12, 31),
    }
    
    with db_manager.get_cursor() as cursor:
        # Get all ideas
        cursor.execute("SELECT id, idea_title, week_number FROM calendar_ideas ORDER BY week_number, idea_title")
        ideas = cursor.fetchall()
        
        print(f"Found {len(ideas)} ideas to process")
        
        # Update week numbers based on actual dates
        for idea in ideas:
            title = idea['idea_title']
            current_week = idea['week_number']
            
            if title in seasonal_dates:
                target_date = seasonal_dates[title]
                correct_week = get_week_number(target_date)
                
                if current_week != correct_week:
                    cursor.execute("""
                        UPDATE calendar_ideas 
                        SET week_number = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (correct_week, idea['id']))
                    
                    print(f"Moved '{title}' from week {current_week} to week {correct_week} ({target_date})")
                else:
                    print(f"'{title}' already in correct week {correct_week}")
            else:
                print(f"No date mapping found for '{title}' - keeping week {current_week}")
        
        # Handle evergreen content that doesn't have specific dates
        # Distribute them evenly across the year
        seasonal_titles = tuple(seasonal_dates.keys())
        placeholders = ','.join(['%s'] * len(seasonal_titles))
        cursor.execute(f"""
            SELECT id, idea_title, week_number 
            FROM calendar_ideas 
            WHERE idea_title NOT IN ({placeholders})
            ORDER BY RANDOM()
        """, seasonal_titles)
        
        evergreen_ideas = cursor.fetchall()
        print(f"\nDistributing {len(evergreen_ideas)} evergreen ideas evenly across the year...")
        
        # Distribute evergreen content evenly across weeks 1-52
        for i, idea in enumerate(evergreen_ideas):
            target_week = (i % 52) + 1
            cursor.execute("""
                UPDATE calendar_ideas 
                SET week_number = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_week, idea['id']))
            
            print(f"Distributed '{idea['idea_title']}' to week {target_week}")
        
        cursor.connection.commit()
        
        # Show final distribution
        cursor.execute("""
            SELECT week_number, COUNT(*) as idea_count 
            FROM calendar_ideas 
            GROUP BY week_number 
            ORDER BY week_number
        """)
        
        final_distribution = {row['week_number']: row['idea_count'] for row in cursor.fetchall()}
        print(f"\nFinal distribution: {final_distribution}")
        
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
            print("\nWeeks with more than 3 ideas:")
            for week in overloaded_weeks:
                print(f"  Week {week['week_number']}: {week['idea_count']} ideas")
        
        print(f"\nCalendar dates fixed! Content now mapped to correct weeks based on actual dates.")

def main():
    try:
        fix_calendar_dates()
        print("\nCalendar dates fixed successfully!")
        print("The calendar should now display content in the correct weeks.")
        
    except Exception as e:
        print(f"Error fixing calendar dates: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
