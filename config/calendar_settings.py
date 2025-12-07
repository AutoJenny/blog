"""
Calendar Scheduling Configuration

Single authoritative configuration source for the JSON-backed calendar scheduling system.

This module provides:
- JSON schedule base directory paths
- Supported categories list
- Default display window settings
- File naming conventions
- Range validation rules
- Paths used by builders and display API
"""

import os
from typing import List

# Base directory for JSON schedule files
# Relative to project root: data/calendar/schedule/
BASE_SCHEDULE_DIR = "data/calendar/schedule"

# Supported categories (must match across all layers)
CATEGORIES: List[str] = [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase",
]

# Display window defaults
DEFAULT_RANGE_WEEKS = 52  # Default number of weeks to show
MAX_RANGE_WEEKS = 260  # Maximum allowed weeks in a single request (5 years)
MIN_RANGE_WEEKS = 1  # Minimum allowed weeks

# JSON file naming pattern
# Format: {category}_{year}.json
# Example: theme_2025.json, recipe_2026.json
JSON_FILENAME_PATTERN = "{category}_{year}.json"

# Category display names (for UI)
CATEGORY_DISPLAY_NAMES = {
    "theme": "Theme",
    "recipe": "Recipe",
    "profile_product": "Product Profile",
    "profile_surname": "Surname Profile",
    "weekly_word": "Weekly Word",
    "weekly_phrase": "Weekly Phrase",
}

# Category to table mapping (for reference, actual mapping in calendar_resolver)
CATEGORY_TABLES = {
    "theme": "calendar_themes",
    "recipe": "calendar_recipes",
    "profile_product": "calendar_profile_sequence",
    "profile_surname": "calendar_profile_sequence",
    "weekly_word": "calendar_ideas",
    "weekly_phrase": "calendar_ideas",
}

# Cycle configuration
DEFAULT_CYCLE_START_WEEK = 1  # Default if not set in calendar_category_cycles

# JSON generation settings
JSON_INDENT = 2  # JSON file indentation (for readability)
JSON_ENSURE_ASCII = False  # Allow Unicode characters in JSON

# Validation rules
MIN_YEAR = 2020  # Minimum supported year
MAX_YEAR = 2100  # Maximum supported year
WEEKS_PER_YEAR = 52  # ISO weeks per year (some years have 53, but we use 52)

# File system paths (computed at runtime)
def get_project_root() -> str:
    """Get project root directory."""
    # From config/calendar_settings.py -> project root
    return os.path.dirname(os.path.dirname(__file__))


def get_schedule_base_dir() -> str:
    """
    Get absolute path to schedule base directory.
    
    Returns:
        Absolute path to data/calendar/schedule/
    """
    project_root = get_project_root()
    return os.path.join(project_root, BASE_SCHEDULE_DIR)


def get_schedule_json_path(category: str, year: int) -> str:
    """
    Get absolute path to a schedule JSON file.
    
    Args:
        category: Category name (must be in CATEGORIES)
        year: ISO year
    
    Returns:
        Absolute path to {category}_{year}.json
    """
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}. Must be one of {CATEGORIES}")
    
    base_dir = get_schedule_base_dir()
    filename = JSON_FILENAME_PATTERN.format(category=category, year=year)
    return os.path.join(base_dir, filename)


def validate_year(year: int) -> bool:
    """Validate year is within supported range."""
    return MIN_YEAR <= year <= MAX_YEAR


def validate_weeks(weeks: int) -> bool:
    """Validate weeks is within allowed range."""
    return MIN_RANGE_WEEKS <= weeks <= MAX_RANGE_WEEKS


def validate_category(category: str) -> bool:
    """Validate category is supported."""
    return category in CATEGORIES

