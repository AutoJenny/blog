"""
Content Roles Schedule Rails Configuration

Defines fixed schedule slots for role-based content generation.
This is Phase 2.1 - Facebook Sunday DEPTH_LONG only.

Each rail defines:
- platform: Social media platform
- day: Day of week (ISO 8601: 1=Monday, 7=Sunday)
- time: Time in HH:MM format (UK timezone)
- role: Content role code
- max_posts: Maximum posts per slot (default: 1)

NOTE: Day numbering standardized to ISO 8601 (1=Monday, 7=Sunday) for consistency.
"""

# Facebook Schedule Rails (v1 - LOCKED)
FACEBOOK_SCHEDULE_RAILS = [
    {
        'platform': 'facebook',
        'day': 7,  # Sunday (ISO: 1=Monday, 7=Sunday)
        'time': '15:00',  # 3:00 PM UK time
        'role': 'DEPTH_LONG',
        'max_posts': 1,
        'timezone': 'Europe/London',
        'is_active': True,
        'notes': 'Sunday long-form post from weekly KB topic'
    }
    # Future rails will be added here:
    # Monday 09:00 CULTURE (Word)
    # Tuesday 17:00 COMMERCE (Product)
    # Wednesday 09:00 CULTURE (Phrase)
    # Thursday 17:00 COMMERCE (Product)
    # Friday 11:07 CULTURE (Insult)
    # Saturday 14:30 REASSURANCE (Message)
]

def get_rails_for_platform(platform: str, role: str = None, is_active: bool = True):
    """
    Get schedule rails for a platform, optionally filtered by role.
    
    Args:
        platform: Platform name (e.g., 'facebook')
        role: Optional role code to filter by
        is_active: Only return active rails (default: True)
    
    Returns:
        List of rail definitions
    """
    rails = FACEBOOK_SCHEDULE_RAILS if platform == 'facebook' else []
    
    if is_active:
        rails = [r for r in rails if r.get('is_active', True)]
    
    if role:
        rails = [r for r in rails if r.get('role') == role]
    
    return rails

def get_rail_for_slot(platform: str, day: int, time: str, role: str = None):
    """
    Get a specific rail for a platform/day/time/role combination.
    
    Args:
        platform: Platform name
        day: Day of week (ISO 8601: 1=Monday, 7=Sunday)
        time: Time in HH:MM format
        role: Optional role code
    
    Returns:
        Rail definition or None
    """
    rails = get_rails_for_platform(platform, role=role)
    
    for rail in rails:
        if rail['day'] == day and rail['time'] == time:
            return rail
    
    return None

def has_depths_long_rail_for_week(platform: str, year: int, week: int):
    """
    Check if there's a DEPTH_LONG rail for a given week.
    
    This answers: "Is there a DEPTH_LONG Facebook post for this coming Sunday?"
    
    Args:
        platform: Platform name
        year: ISO year
        week: ISO week number
    
    Returns:
        Boolean indicating if rail exists
    """
    rails = get_rails_for_platform(platform, role='DEPTH_LONG')
    return len(rails) > 0
