#!/usr/bin/env python3
"""
Populate calendar_weeks table with week data for a given year.
This script generates all 52 weeks with proper start/end dates and month names.
"""

import sys
import os
from datetime import datetime, timedelta
from calendar import month_name

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def get_week_dates(year, week_number):
    """Get start and end dates for a given week number in a year."""
    # January 1st of the year
    jan_1 = datetime(year, 1, 1)
    
    # Find the first Monday of the year (or the Monday of the first week)
    # ISO week starts on Monday
    days_since_monday = jan_1.weekday()  # Monday is 0
    if days_since_monday == 6:  # Sunday
        days_since_monday = -1
    
    first_monday = jan_1 - timedelta(days=days_since_monday)
    
    # Calculate the start date for the given week
    week_start = first_monday + timedelta(weeks=week_number - 1)
    week_end = week_start + timedelta(days=6)
    
    return week_start.date(), week_end.date()

def populate_calendar_weeks(year):
    """Populate calendar_weeks table for a given year."""
    print(f"Populating calendar weeks for year {year}...")
    
    with db_manager.get_cursor() as cursor:
        # Check if year already exists
        cursor.execute("SELECT COUNT(*) FROM calendar_weeks WHERE year = %s", (year,))
        existing_count = cursor.fetchone()['count']
        
        if existing_count > 0:
            print(f"Year {year} already has {existing_count} weeks. Skipping.")
            return
        
        # Get current date to mark current week
        today = datetime.now().date()
        
        weeks_data = []
        for week_num in range(1, 53):  # 1-52
            start_date, end_date = get_week_dates(year, week_num)
            
            # Determine which month this week belongs to
            # Use the month of the start date
            month_name_str = month_name[start_date.month][:3]  # Jan, Feb, etc.
            
            # Check if this is the current week
            is_current = start_date <= today <= end_date
            
            weeks_data.append((
                week_num,
                year,
                start_date,
                end_date,
                month_name_str,
                is_current
            ))
        
        # Insert all weeks
        insert_sql = """
            INSERT INTO calendar_weeks 
            (week_number, year, start_date, end_date, month_name, is_current_week)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.executemany(insert_sql, weeks_data)
        cursor.connection.commit()
        
        print(f"Successfully inserted 52 weeks for year {year}")
        
        # Show some sample data
        cursor.execute("""
            SELECT week_number, start_date, end_date, month_name, is_current_week
            FROM calendar_weeks 
            WHERE year = %s 
            ORDER BY week_number 
            LIMIT 5
        """, (year,))
        
        print("\nSample weeks:")
        for row in cursor.fetchall():
            current_marker = " (CURRENT)" if row['is_current_week'] else ""
            print(f"  Week {row['week_number']}: {row['start_date']} to {row['end_date']} ({row['month_name']}){current_marker}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python populate_calendar_weeks.py <year>")
        print("Example: python populate_calendar_weeks.py 2025")
        sys.exit(1)
    
    try:
        year = int(sys.argv[1])
        if year < 2020 or year > 2030:
            print("Year must be between 2020 and 2030")
            sys.exit(1)
        
        populate_calendar_weeks(year)
        
    except ValueError:
        print("Year must be a valid integer")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
