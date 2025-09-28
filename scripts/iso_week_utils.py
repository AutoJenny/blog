#!/usr/bin/env python3
"""
ISO 8601 Week Numbering Utilities
Provides consistent week date calculations across the entire application.
"""

from datetime import datetime, timedelta, date
from typing import Tuple

def get_iso_week_dates(year: int, week_number: int) -> Tuple[date, date]:
    """
    Get start and end dates for ISO 8601 week number.
    
    ISO 8601 week numbering:
    - Week 1 is the first week with at least 4 days in the new year
    - Monday is the first day of the week
    - Week numbers range from 1 to 52 or 53
    
    Args:
        year: The year
        week_number: The week number (1-52 or 53)
        
    Returns:
        Tuple of (start_date, end_date) for the week
    """
    # Find the first Thursday of the year
    # ISO 8601 week 1 contains the first Thursday of the year
    jan_4 = date(year, 1, 4)
    first_thursday = jan_4 - timedelta(days=jan_4.weekday())
    
    # Calculate the start of week 1 (Monday)
    week_1_start = first_thursday - timedelta(days=3)
    
    # Calculate the target week
    week_start = week_1_start + timedelta(weeks=week_number - 1)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end

def get_iso_week_number(target_date: date) -> int:
    """
    Get ISO 8601 week number for a given date.
    
    Args:
        target_date: The date to get the week number for
        
    Returns:
        The ISO 8601 week number
    """
    year = target_date.year
    
    # Find the first Thursday of the year
    jan_4 = date(year, 1, 4)
    first_thursday = jan_4 - timedelta(days=jan_4.weekday())
    
    # Calculate the start of week 1 (Monday)
    week_1_start = first_thursday - timedelta(days=3)
    
    # Calculate week number
    days_since_week_1 = (target_date - week_1_start).days
    week_number = (days_since_week_1 // 7) + 1
    
    # Handle edge cases
    if week_number < 1:
        # Date is before week 1 of this year, check previous year
        return get_iso_week_number(date(year - 1, 12, 31))
    elif week_number > 52:
        # Check if week 53 exists for this year
        week_53_start, _ = get_iso_week_dates(year, 53)
        if week_53_start.year == year:
            return 53
        else:
            return 1
    
    return week_number

def get_iso_weeks_in_year(year: int) -> int:
    """
    Get the number of ISO 8601 weeks in a year.
    
    Args:
        year: The year
        
    Returns:
        Number of weeks (52 or 53)
    """
    # Check if week 53 exists by seeing if its start date is still in the same year
    week_53_start, _ = get_iso_week_dates(year, 53)
    return 53 if week_53_start.year == year else 52

def test_iso_week_calculations():
    """Test the ISO 8601 calculations with known examples."""
    print("Testing ISO 8601 week calculations...")
    
    # Test cases from ISO 8601 standard
    test_cases = [
        (2025, 1, date(2024, 12, 30), date(2025, 1, 5)),   # Week 1, 2025
        (2025, 39, date(2025, 9, 22), date(2025, 9, 28)),  # Week 39, 2025
        (2024, 1, date(2024, 1, 1), date(2024, 1, 7)),     # Week 1, 2024
        (2024, 53, date(2024, 12, 30), date(2025, 1, 5)),  # Week 53, 2024 (leap year)
    ]
    
    for year, week_num, expected_start, expected_end in test_cases:
        actual_start, actual_end = get_iso_week_dates(year, week_num)
        print(f"Week {week_num}, {year}: {actual_start} - {actual_end}")
        print(f"  Expected: {expected_start} - {expected_end}")
        print(f"  Match: {actual_start == expected_start and actual_end == expected_end}")
        print()

if __name__ == "__main__":
    test_iso_week_calculations()