#!/usr/bin/env python3
"""
Reallocate recipes to start from the current week.

This script calculates which calendar week corresponds to recipe week 1,
based on the current date, and updates the mapping logic.
"""
import sys
import os
from datetime import datetime, date

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def get_current_week():
    """Get current ISO week number."""
    return datetime.now().isocalendar()[1]

def get_recipe_start_week():
    """
    Get the calendar week that should correspond to recipe week 1.
    This is the current week.
    """
    current_iso = datetime.now().isocalendar()
    return current_iso[1]  # Current week number

def calculate_recipe_calendar_week(recipe_week_number, start_week=45):
    """
    Calculate which calendar week a recipe week number should map to.
    
    Args:
        recipe_week_number: The perpetual recipe week (1-52)
        start_week: The calendar week that recipe week 1 maps to (default: current week)
    
    Returns:
        Calendar week number (1-52, wrapping if needed)
    """
    # Map recipe week to calendar week, wrapping around year boundary
    calendar_week = ((recipe_week_number - 1 + start_week - 1) % 52) + 1
    return calendar_week

def get_recipe_calendar_year_and_week(recipe_week_number, current_year=2025, current_week=45):
    """
    Get the calendar year and week for a recipe week number.
    
    Args:
        recipe_week_number: The perpetual recipe week (1-52)
        current_year: Current year
        current_week: Current calendar week
    
    Returns:
        (year, week_number) tuple
    """
    # Calculate which calendar week this recipe maps to
    calendar_week = ((recipe_week_number - 1 + current_week - 1) % 52) + 1
    
    # Calculate year offset (if we wrap around)
    weeks_ahead = recipe_week_number - 1
    target_week = current_week + weeks_ahead
    
    if target_week > 52:
        # Wrapped to next year
        year = current_year + 1
        week = target_week - 52
    else:
        year = current_year
        week = target_week
    
    return (year, week)

if __name__ == '__main__':
    current_iso = datetime.now().isocalendar()
    current_year = current_iso[0]
    current_week = current_iso[1]
    
    print(f"Current date: {datetime.now().date()}")
    print(f"Current year: {current_year}, week: {current_week}")
    print(f"\nRecipe week 1 will map to calendar week {current_week} ({current_year})")
    print(f"Recipe week 2 will map to calendar week {current_week + 1 if current_week < 52 else 1} ({current_year if current_week < 52 else current_year + 1})")
    print("\nNo database changes needed - mapping is calculated dynamically.")
    print("This script is for reference only.")

