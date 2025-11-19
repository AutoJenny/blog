"""Weather analysis service: aggregates weather data for conversational summaries.

Analyzes weather patterns over a week period (before/after target week) to identify
trends, unusual conditions, and generate chatty, conversational weather comments.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
from newsletter.db.queries_sources import get_cached_items


# Seasonal temperature norms for Scotland (approximate averages)
SCOTLAND_SEASONAL_NORMS = {
    'winter': {'high': 7, 'low': 2},   # Dec-Feb
    'spring': {'high': 12, 'low': 5},  # Mar-May
    'summer': {'high': 18, 'low': 11}, # Jun-Aug
    'autumn': {'high': 13, 'low': 7},  # Sep-Nov
}


def get_season(date_obj: date) -> str:
    """Get season for a date (winter, spring, summer, autumn)."""
    month = date_obj.month
    if month in (12, 1, 2):
        return 'winter'
    elif month in (3, 4, 5):
        return 'spring'
    elif month in (6, 7, 8):
        return 'summer'
    else:
        return 'autumn'


def get_week_date_range(target_week: str) -> Tuple[date, date]:
    """Get start and end dates for a target week (ISO week format: 2025W44).
    
    Returns (week_start, week_end) as date objects.
    """
    if 'W' not in target_week:
        # Fallback: assume current week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    try:
        year_str, week_str = target_week.split('W')
        year = int(year_str)
        week_num = int(week_str)
        
        # Find first Monday of the year
        jan1 = date(year, 1, 1)
        # Monday is 0, so if Jan 1 is Monday, offset is 0
        # If Jan 1 is Tuesday (1), offset is 6 days back to previous Monday
        days_to_monday = (jan1.weekday()) % 7
        if days_to_monday == 0:
            first_monday = jan1
        else:
            first_monday = jan1 - timedelta(days=days_to_monday)
        
        # Calculate week start (Monday of target week)
        week_start = first_monday + timedelta(weeks=week_num - 1, days=0)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    except Exception:
        # Fallback to current week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end


def analyze_weather_period(
    target_week: str,
    days_before: int = 7,
    days_after: int = 7
) -> Dict[str, Any]:
    """Analyze weather data for a period around the target week.
    
    Args:
        target_week: Target week string (e.g., "2025W44")
        days_before: Days before target week to include
        days_after: Days after target week to include
    
    Returns:
        Dict with:
        - period_start: Start date of analysis period
        - period_end: End date of analysis period
        - items: List of weather items in period
        - avg_temp_high: Average high temperature
        - avg_temp_low: Average low temperature
        - temp_trend: 'warmer', 'colder', 'normal', 'variable'
        - conditions: List of common conditions
        - unusual_conditions: List of unusual/extreme conditions
        - seasonal_norm: Expected temps for this time of year
        - is_unusual: Whether weather is significantly different from norm
        - summary_patterns: List of patterns (e.g., ['chilly', 'rainy', 'stormy'])
    """
    # Get target week date range
    week_start, week_end = get_week_date_range(target_week)
    
    # Calculate analysis period
    period_start = week_start - timedelta(days=days_before)
    period_end = week_end + timedelta(days=days_after)
    
    # Get all weather items from database
    all_weather = get_cached_items(category='weather', days_back=30, limit=200)
    
    # Filter to period
    period_items = []
    for item in all_weather:
        event_date = item.get('event_date')
        if not event_date:
            continue
        
        # Convert to date if datetime
        if isinstance(event_date, datetime):
            event_date = event_date.date()
        elif isinstance(event_date, str):
            try:
                from dateutil import parser
                event_date = parser.parse(event_date).date()
            except:
                continue
        
        if period_start <= event_date <= period_end:
            period_items.append(item)
    
    if not period_items:
        return {
            'period_start': period_start,
            'period_end': period_end,
            'items': [],
            'avg_temp_high': None,
            'avg_temp_low': None,
            'temp_trend': 'normal',
            'conditions': [],
            'unusual_conditions': [],
            'seasonal_norm': None,
            'is_unusual': False,
            'summary_patterns': [],
        }
    
    # Calculate averages
    temps_high = []
    temps_low = []
    conditions_list = []
    
    for item in period_items:
        raw_data = item.get('raw_data', {})
        temp_high = raw_data.get('temp_high')
        temp_low = raw_data.get('temp_low')
        condition = raw_data.get('condition', '')
        
        if temp_high is not None:
            temps_high.append(temp_high)
        if temp_low is not None:
            temps_low.append(temp_low)
        if condition:
            conditions_list.append(condition.lower())
    
    avg_temp_high = sum(temps_high) / len(temps_high) if temps_high else None
    avg_temp_low = sum(temps_low) / len(temps_low) if temps_low else None
    
    # Get seasonal norm for target week
    season = get_season(week_start)
    seasonal_norm = SCOTLAND_SEASONAL_NORMS.get(season, {'high': 10, 'low': 5})
    
    # Determine if unusual
    is_unusual = False
    temp_trend = 'normal'
    if avg_temp_high is not None and seasonal_norm:
        diff_high = avg_temp_high - seasonal_norm['high']
        if diff_high > 3:
            temp_trend = 'warmer'
            is_unusual = True
        elif diff_high < -3:
            temp_trend = 'colder'
            is_unusual = True
    
    # Analyze conditions
    condition_counts = {}
    for cond in conditions_list:
        # Normalize condition text
        cond_lower = cond.lower()
        if any(word in cond_lower for word in ['rain', 'drizzle', 'shower']):
            condition_counts['rainy'] = condition_counts.get('rainy', 0) + 1
        if any(word in cond_lower for word in ['snow', 'sleet', 'frost']):
            condition_counts['snowy'] = condition_counts.get('snowy', 0) + 1
        if any(word in cond_lower for word in ['wind', 'breeze', 'gust']):
            condition_counts['windy'] = condition_counts.get('windy', 0) + 1
        if any(word in cond_lower for word in ['storm', 'gale', 'severe']):
            condition_counts['stormy'] = condition_counts.get('stormy', 0) + 1
        if any(word in cond_lower for word in ['clear', 'sunny', 'bright']):
            condition_counts['clear'] = condition_counts.get('clear', 0) + 1
        if any(word in cond_lower for word in ['cloud', 'overcast']):
            condition_counts['cloudy'] = condition_counts.get('cloudy', 0) + 1
    
    # Identify patterns
    summary_patterns = []
    if temp_trend == 'colder':
        summary_patterns.append('chilly')
    elif temp_trend == 'warmer':
        summary_patterns.append('mild')
    
    # Add condition patterns (if frequent)
    for pattern, count in condition_counts.items():
        if count >= len(period_items) * 0.3:  # 30% or more of days
            summary_patterns.append(pattern)
    
    # Identify unusual conditions
    unusual_conditions = []
    if condition_counts.get('stormy', 0) > 0:
        unusual_conditions.append('storms')
    if condition_counts.get('snowy', 0) > 0 and season != 'winter':
        unusual_conditions.append('snow')
    if avg_temp_high and avg_temp_high > seasonal_norm['high'] + 5:
        unusual_conditions.append('unusually warm')
    if avg_temp_low and avg_temp_low < seasonal_norm['low'] - 3:
        unusual_conditions.append('unusually cold')
    
    return {
        'period_start': period_start,
        'period_end': period_end,
        'items': period_items,
        'avg_temp_high': avg_temp_high,
        'avg_temp_low': avg_temp_low,
        'temp_trend': temp_trend,
        'conditions': list(condition_counts.keys()),
        'unusual_conditions': unusual_conditions,
        'seasonal_norm': seasonal_norm,
        'is_unusual': is_unusual,
        'summary_patterns': summary_patterns,
        'item_count': len(period_items),
    }


def generate_weather_summary_text(analysis: Dict[str, Any]) -> str:
    """Generate a conversational, chatty weather summary from analysis using LLM.
    
    Uses LLM to analyze actual weather data compared to seasonal norms and identify
    unusual conditions, then generates a natural, conversational summary.
    
    Returns a single sentence suitable for inclusion in intro paragraph.
    """
    if not analysis.get('items'):
        return ""  # No weather data available
    
    import os
    import sys
    import logging
    logger = logging.getLogger(__name__)
    
    # Import LLM service
    try:
        # Try header blueprint LLM service first
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
        from blueprints.header.llm_service import LLMService
        llm_service = LLMService()
    except ImportError:
        logger.error("Failed to import LLMService")
        return ""  # Can't generate without LLM
    
    # Extract weather data for LLM prompt
    avg_high = analysis.get('avg_temp_high')
    avg_low = analysis.get('avg_temp_low')
    seasonal_norm = analysis.get('seasonal_norm', {})
    period_start = analysis.get('period_start', date.today())
    period_end = analysis.get('period_end', date.today())
    season = get_season(period_start)
    temp_trend = analysis.get('temp_trend', 'normal')
    patterns = analysis.get('summary_patterns', [])
    unusual = analysis.get('unusual_conditions', [])
    
    # Get sample weather items for context
    items = analysis.get('items', [])
    recent_items = [item for item in items[:7]]  # Last week
    forecast_items = [item for item in items[7:14]] if len(items) > 7 else []  # Next week
    
    # Build detailed weather context for LLM
    recent_conditions = []
    forecast_conditions = []
    
    for item in recent_items:
        raw = item.get('raw_data', {})
        event_date = item.get('event_date')
        if isinstance(event_date, datetime):
            event_date = event_date.date()
        elif isinstance(event_date, str):
            try:
                from dateutil import parser
                event_date = parser.parse(event_date).date()
            except:
                event_date = None
        
        if event_date:
            temp_high = raw.get('temp_high')
            temp_low = raw.get('temp_low')
            condition = raw.get('condition', '')
            recent_conditions.append(f"{event_date.strftime('%A %d %B')}: High {temp_high}°C / Low {temp_low}°C - {condition}")
    
    for item in forecast_items:
        raw = item.get('raw_data', {})
        event_date = item.get('event_date')
        if isinstance(event_date, datetime):
            event_date = event_date.date()
        elif isinstance(event_date, str):
            try:
                from dateutil import parser
                event_date = parser.parse(event_date).date()
            except:
                event_date = None
        
        if event_date:
            temp_high = raw.get('temp_high')
            temp_low = raw.get('temp_low')
            condition = raw.get('condition', '')
            forecast_conditions.append(f"{event_date.strftime('%A %d %B')}: High {temp_high}°C / Low {temp_low}°C - {condition}")
    
    # Build LLM prompt
    system_prompt = """You are writing a conversational weather summary for a Scottish heritage newsletter. 
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, observational tone - like you're chatting with a friend about the weather.
Focus on what's unusual or notable compared to seasonal norms, not specific daily forecasts.
Keep it to ONE sentence, maximum 25 words.
Write naturally - don't use clichés or repeated phrases. Each summary should be unique based on the actual weather conditions."""
    
    user_prompt = f"""Analyze the weather data below and write a single conversational sentence about the weather in Scotland.

SEASON: {season.capitalize()}
PERIOD: {period_start.strftime('%d %B')} to {period_end.strftime('%d %B')}

SEASONAL NORMALS FOR {season.upper()}:
- Average High: {seasonal_norm.get('high', 'N/A')}°C
- Average Low: {seasonal_norm.get('low', 'N/A')}°C

ACTUAL WEATHER:
- Average High (this period): {avg_high}°C
- Average Low (this period): {avg_low}°C
- Temperature Trend: {temp_trend}
- Weather Patterns: {', '.join(patterns) if patterns else 'normal'}
- Unusual Conditions: {', '.join(unusual) if unusual else 'none'}

RECENT WEATHER (past week):
{chr(10).join(recent_conditions[:5]) if recent_conditions else 'No recent data'}

FORECAST (next week):
{chr(10).join(forecast_conditions[:5]) if forecast_conditions else 'No forecast data'}

Write ONE conversational sentence that:
1. Highlights anything unusual compared to seasonal norms
2. Mentions notable patterns in natural, varied language
3. Responds to the weather as a human would - with appropriate observations, concerns, or comments
4. Does NOT mention specific dates or days
5. Focuses on the overall pattern, not individual days
6. Uses fresh, natural language - avoid clichés or repeated phrases

Think about how a person would actually talk about this weather:
- If it's unusually cold: what would they say? (not "woolies" - be creative)
- If storms are coming: what's their concern?
- If it's unseasonably warm: what's notable about that?
- If it's normal for the season: what's a natural observation?

If nothing is particularly unusual, write a brief, natural seasonal observation.

Your response should be ONLY the sentence, nothing else."""
    
    try:
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        # Use Ollama by default (local, fast)
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in result:
            logger.error(f"LLM error generating weather summary: {result['error']}")
            return ""  # Return empty on error
        
        summary_text = result.get('content', '').strip()
        
        # Clean up the response (remove quotes, extra whitespace, etc.)
        summary_text = summary_text.strip('"\'')
        summary_text = summary_text.strip()
        
        # Ensure it ends with proper punctuation
        if summary_text and not summary_text[-1] in '.!?':
            summary_text += '.'
        
        return summary_text if summary_text else ""
        
    except Exception as e:
        logger.error(f"Error generating weather summary with LLM: {e}", exc_info=True)
        return ""  # Return empty on error


def get_weather_for_intro(target_week: str) -> Optional[Dict[str, Any]]:
    """Get weather analysis for intro block.
    
    Returns dict with:
    - summary_text: Conversational weather summary (one sentence)
    - analysis: Full analysis data
    - source_name: Weather source name
    - url: Weather source URL
    """
    analysis = analyze_weather_period(target_week, days_before=7, days_after=7)
    
    if not analysis.get('items'):
        return None
    
    # Generate summary text
    summary_text = generate_weather_summary_text(analysis)
    
    if not summary_text:
        return None
    
    # Get source info from first item
    first_item = analysis['items'][0]
    
    return {
        'summary_text': summary_text,
        'analysis': analysis,
        'source_name': first_item.get('source_name', 'Weather Service'),
        'url': first_item.get('url', ''),
        'category': 'weather',
    }

