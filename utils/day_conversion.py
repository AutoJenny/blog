"""
Day Conversion Utilities

Centralized day-of-week conversion logic to handle different numbering systems.

Standard: ISO 8601 (1=Monday, 7=Sunday)
Legacy: 0-indexed (0=Monday, 6=Sunday) - used in some Content Roles code
"""

def iso_to_zero_indexed(iso_day: int) -> int:
    """
    Convert ISO day (1=Monday, 7=Sunday) to 0-indexed (0=Monday, 6=Sunday).
    
    Args:
        iso_day: ISO day number (1-7)
    
    Returns:
        0-indexed day number (0-6)
    
    Raises:
        ValueError: If iso_day is not 1-7
    """
    if not 1 <= iso_day <= 7:
        raise ValueError(f"ISO day must be 1-7, got {iso_day}")
    return iso_day - 1


def zero_indexed_to_iso(zero_day: int) -> int:
    """
    Convert 0-indexed day (0=Monday, 6=Sunday) to ISO (1=Monday, 7=Sunday).
    
    Args:
        zero_day: 0-indexed day number (0-6)
    
    Returns:
        ISO day number (1-7)
    
    Raises:
        ValueError: If zero_day is not 0-6
    """
    if not 0 <= zero_day <= 6:
        raise ValueError(f"0-indexed day must be 0-6, got {zero_day}")
    return zero_day + 1


def is_sunday_iso(iso_day: int) -> bool:
    """Check if ISO day is Sunday (7)."""
    return iso_day == 7


def is_sunday_zero_indexed(zero_day: int) -> bool:
    """Check if 0-indexed day is Sunday (6)."""
    return zero_day == 6
