"""
Planning Calendar API Module

Backwards compatibility module - re-exports all functions from split modules.
All functions have been moved to smaller modules:
- planning_api_calendar_basics.py: categories, weeks
- planning_api_calendar_ideas.py: all idea-related endpoints
- planning_api_calendar_events.py: all event-related endpoints
- planning_api_calendar_schedule.py: schedule and selection endpoints
- planning_api_calendar_social_focus.py: social focus endpoints
- planning_api_calendar_utils.py: shared utility functions
"""

# Import from basics
from blueprints.planning_api_calendar_basics import (
    api_calendar_categories,
    api_calendar_weeks,
)

# Import from ideas
from blueprints.planning_api_calendar_ideas import (
    api_calendar_ideas,
    api_get_calendar_idea,
    api_add_calendar_idea,
    api_update_calendar_idea,
    api_delete_calendar_idea,
    api_calendar_ideas_for_week,
)

# Import from events
from blueprints.planning_api_calendar_events import (
    api_calendar_events,
    api_add_calendar_event,
    api_update_calendar_event,
    api_delete_calendar_event,
    api_convert_event_to_idea,
)

# Import from schedule
from blueprints.planning_api_calendar_schedule import (
    api_calendar_schedule,
    api_select_theme_idea,
    api_calendar_idea_status,
    api_schedule_update_theme_to_idea,
    api_update_calendar_week_item,
    api_set_calendar_week_item_primary,
)

# Import from social focus
from blueprints.planning_api_calendar_social_focus import (
    api_weekly_social_focus,
    api_weekly_social_focus_day,
    api_add_weekly_social_focus,
    api_update_weekly_social_focus,
    api_delete_weekly_social_focus,
)

# Import from utils
from blueprints.planning_api_calendar_utils import (
    _safe_parse_json_request,
    _current_iso_week,
)

# Re-export everything for backwards compatibility
__all__ = [
    # Basics
    'api_calendar_categories',
    'api_calendar_weeks',
    # Ideas
    'api_calendar_ideas',
    'api_get_calendar_idea',
    'api_add_calendar_idea',
    'api_update_calendar_idea',
    'api_delete_calendar_idea',
    'api_calendar_ideas_for_week',
    # Events
    'api_calendar_events',
    'api_add_calendar_event',
    'api_update_calendar_event',
    'api_delete_calendar_event',
    'api_convert_event_to_idea',
    # Schedule
    'api_calendar_schedule',
    'api_select_theme_idea',
    'api_calendar_idea_status',
    'api_schedule_update_theme_to_idea',
    'api_update_calendar_week_item',
    'api_set_calendar_week_item_primary',
    # Social Focus
    'api_weekly_social_focus',
    'api_weekly_social_focus_day',
    'api_add_weekly_social_focus',
    'api_update_weekly_social_focus',
    'api_delete_weekly_social_focus',
    # Utils
    '_safe_parse_json_request',
    '_current_iso_week',
]
