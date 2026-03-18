"""Weather summary service for aggregating and analyzing weather data for newsletters."""

from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional
import logging
import re
from collections import Counter
from config.database import db_manager

logger = logging.getLogger(__name__)


# Seasonal norms for Scotland (Glasgow/central Scotland area)
# These are typical averages by month for reference/comparison
SCOTLAND_SEASONAL_NORMS = {
    1: {'high': 6, 'low': 1, 'condition': 'cool, often cloudy with rain', 'description': 'Winter'},
    2: {'high': 7, 'low': 2, 'condition': 'cool, cloudy with frequent rain', 'description': 'Late winter'},
    3: {'high': 9, 'low': 3, 'condition': 'mild, changeable with occasional sunshine', 'description': 'Early spring'},
    4: {'high': 11, 'low': 4, 'condition': 'mild, spring showers', 'description': 'Spring'},
    5: {'high': 14, 'low': 7, 'condition': 'mild, increasing sunshine', 'description': 'Late spring'},
    6: {'high': 17, 'low': 10, 'condition': 'mild to warm, longest days', 'description': 'Early summer'},
    7: {'high': 19, 'low': 12, 'condition': 'warmest month, variable weather', 'description': 'Summer'},
    8: {'high': 19, 'low': 12, 'condition': 'warm, can be humid with rain', 'description': 'Late summer'},
    9: {'high': 16, 'low': 9, 'condition': 'mild, autumn colours begin', 'description': 'Early autumn'},
    10: {'high': 13, 'low': 7, 'condition': 'cool, autumn foliage', 'description': 'Autumn'},
    11: {'high': 9, 'low': 4, 'condition': 'cool, often wet and windy', 'description': 'Late autumn'},
    12: {'high': 7, 'low': 2, 'condition': 'cold, short days, festive season', 'description': 'Winter'},
}


def get_seasonal_norm(target_date: date) -> Dict[str, Any]:
    """Get seasonal norm for a given date (Scotland averages).
    
    Args:
        target_date: Date to get norm for
        
    Returns:
        Dict with high, low, condition, description
    """
    month = target_date.month
    return SCOTLAND_SEASONAL_NORMS.get(month, {
        'high': 10,
        'low': 5,
        'condition': 'variable',
        'description': 'typical'
    })


def get_weather_items(days_back: int = 7, days_ahead: int = 7) -> List[Dict[str, Any]]:
    """Get weather items from database for specified date range.
    
    Args:
        days_back: Number of days in the past to include
        days_ahead: Number of days ahead to include
        
    Returns:
        List of weather items from newsletter_source_item
    """
    today = date.today()
    start_date = today - timedelta(days=days_back)
    end_date = today + timedelta(days=days_ahead)
    
    sql = """
        SELECT id, source_name, title, url, published_at, event_date, 
               raw_data, cached_at
        FROM newsletter_source_item
        WHERE category = 'weather'
          AND (
            (event_date IS NOT NULL AND event_date::date BETWEEN %s AND %s)
            OR (published_at IS NOT NULL AND published_at::date BETWEEN %s AND %s)
          )
        ORDER BY 
          CASE 
            WHEN event_date IS NOT NULL THEN event_date::date
            ELSE published_at::date
          END ASC
    """
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (start_date, end_date, start_date, end_date))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def group_weather_by_date(items: List[Dict[str, Any]]) -> Dict[date, List[Dict[str, Any]]]:
    """Group weather items by date.
    
    Args:
        items: List of weather items
        
    Returns:
        Dict mapping date to list of items for that date
    """
    grouped: Dict[date, List[Dict[str, Any]]] = {}
    
    for item in items:
        # Use event_date if available, otherwise published_at date
        item_date = None
        event_date_val = item.get('event_date')
        published_at_val = item.get('published_at')
        
        # Handle event_date (preferred for forecasts)
        if event_date_val:
            if isinstance(event_date_val, date) and not isinstance(event_date_val, datetime):
                item_date = event_date_val
            elif isinstance(event_date_val, datetime):
                # Extract date from datetime (handles timezone-aware datetimes)
                item_date = event_date_val.date()
            elif isinstance(event_date_val, str):
                try:
                    from dateutil import parser
                    parsed = parser.parse(event_date_val)
                    item_date = parsed.date()
                except:
                    pass
        
        # Fallback to published_at
        if not item_date and published_at_val:
            if isinstance(published_at_val, date) and not isinstance(published_at_val, datetime):
                item_date = published_at_val
            elif isinstance(published_at_val, datetime):
                item_date = published_at_val.date()
            elif isinstance(published_at_val, str):
                try:
                    from dateutil import parser
                    parsed = parser.parse(published_at_val)
                    item_date = parsed.date()
                except:
                    pass
        
        if item_date:
            if item_date not in grouped:
                grouped[item_date] = []
            grouped[item_date].append(item)
    
    return grouped


def calculate_day_summary(date_items: List[Dict[str, Any]], target_date: date) -> Dict[str, Any]:
    """Calculate summary for a single day's weather data.
    
    Args:
        date_items: List of weather items for the date
        target_date: The date being summarized
        
    Returns:
        Dict with summary stats (avg_temp, high, low, conditions, etc.)
    """
    if not date_items:
        return {
            'date': target_date,
            'has_data': False,
        }
    
    temps_high = []
    temps_low = []
    temps_avg = []
    conditions = []
    precipitation_prob = []
    wind_speeds = []
    sources = set()
    
    for item in date_items:
        raw_data = item.get('raw_data', {})
        
        # Extract temperatures
        if raw_data.get('temp_high') is not None:
            temps_high.append(raw_data['temp_high'])
        if raw_data.get('temp_low') is not None:
            temps_low.append(raw_data['temp_low'])
        if raw_data.get('temperature'):
            # Try to extract from string like "14°C / 9°C"
            temp_str = raw_data['temperature']
            temp_nums = re.findall(r'(\d+)', temp_str)
            for num in temp_nums[:2]:  # Take first two numbers
                temp_val = int(num)
                if 0 <= temp_val <= 35:  # Reasonable temp range
                    temps_avg.append(temp_val)
        
        # Extract conditions
        condition = raw_data.get('condition')
        if condition:
            conditions.append(condition)
        
        # Extract precipitation
        precip = raw_data.get('precipitation')
        if precip:
            precip_str = str(precip)
            precip_num = re.findall(r'(\d+)', precip_str)
            if precip_num:
                precipitation_prob.append(int(precip_num[0]))
        
        # Extract wind
        wind = raw_data.get('wind')
        if wind:
            wind_nums = re.findall(r'(\d+)', str(wind))
            if wind_nums:
                wind_speeds.append(int(wind_nums[0]))
        
        sources.add(item.get('source_name', 'Unknown'))
    
    # Calculate averages
    summary = {
        'date': target_date,
        'has_data': True,
        'item_count': len(date_items),
        'sources': list(sources),
    }
    
    if temps_high:
        summary['temp_high'] = round(sum(temps_high) / len(temps_high), 1)
        summary['temp_high_max'] = max(temps_high)
    if temps_low:
        summary['temp_low'] = round(sum(temps_low) / len(temps_low), 1)
        summary['temp_low_min'] = min(temps_low)
    if temps_avg:
        summary['temp_avg'] = round(sum(temps_avg) / len(temps_avg), 1)
    
    if conditions:
        # Most common condition
        condition_counts = Counter(conditions)
        summary['primary_condition'] = condition_counts.most_common(1)[0][0]
        summary['all_conditions'] = list(set(conditions))
    
    if precipitation_prob:
        summary['precipitation_avg'] = round(sum(precipitation_prob) / len(precipitation_prob))
    
    if wind_speeds:
        summary['wind_avg'] = round(sum(wind_speeds) / len(wind_speeds))
        summary['wind_max'] = max(wind_speeds)
    
    return summary


def generate_weather_summary(days_back: int = 7, days_ahead: int = 7) -> Dict[str, Any]:
    """Generate comprehensive weather summary for past and forecast periods.
    
    Args:
        days_back: Days in past to summarize
        days_ahead: Days ahead to forecast
        
    Returns:
        Dict with past_week, forecast_week, and overall summary
    """
    today = date.today()
    
    # Get weather items
    items = get_weather_items(days_back=days_back, days_ahead=days_ahead)
    grouped = group_weather_by_date(items)
    
    # Calculate summaries for each day
    daily_summaries = []
    past_week_summaries = []
    forecast_summaries = []
    
    for check_date in (today - timedelta(days=days_back) + timedelta(days=i) 
                       for i in range(days_back + days_ahead + 1)):
        date_items = grouped.get(check_date, [])
        day_summary = calculate_day_summary(date_items, check_date)
        day_summary['is_past'] = check_date < today
        day_summary['is_today'] = check_date == today
        day_summary['is_future'] = check_date > today
        
        # Add seasonal norm for comparison
        norm = get_seasonal_norm(check_date)
        day_summary['seasonal_norm'] = norm
        
        if day_summary['has_data']:
            # Compare to norm
            if day_summary.get('temp_high'):
                day_summary['temp_vs_norm'] = day_summary['temp_high'] - norm['high']
            if day_summary.get('temp_low'):
                day_summary['temp_low_vs_norm'] = day_summary['temp_low'] - norm['low']
        
        daily_summaries.append(day_summary)
        
        if check_date < today:
            past_week_summaries.append(day_summary)
        elif check_date > today:
            forecast_summaries.append(day_summary)
    
    # Aggregate past week stats
    past_week_with_data = [s for s in past_week_summaries if s.get('has_data')]
    past_week_summary = {}
    if past_week_with_data:
        temps_high = [s['temp_high'] for s in past_week_with_data if s.get('temp_high')]
        temps_low = [s['temp_low'] for s in past_week_with_data if s.get('temp_low')]
        
        past_week_summary = {
            'days_with_data': len(past_week_with_data),
            'avg_high': round(sum(temps_high) / len(temps_high), 1) if temps_high else None,
            'avg_low': round(sum(temps_low) / len(temps_low), 1) if temps_low else None,
            'high_max': max(temps_high) if temps_high else None,
            'low_min': min(temps_low) if temps_low else None,
            'conditions': [s.get('primary_condition') for s in past_week_with_data if s.get('primary_condition')],
        }
    
    # Aggregate forecast stats
    forecast_with_data = [s for s in forecast_summaries if s.get('has_data')]
    forecast_summary = {}
    if forecast_with_data:
        temps_high = [s['temp_high'] for s in forecast_with_data if s.get('temp_high')]
        temps_low = [s['temp_low'] for s in forecast_with_data if s.get('temp_low')]
        
        forecast_summary = {
            'days_with_data': len(forecast_with_data),
            'avg_high': round(sum(temps_high) / len(temps_high), 1) if temps_high else None,
            'avg_low': round(sum(temps_low) / len(temps_low), 1) if temps_low else None,
            'high_max': max(temps_high) if temps_high else None,
            'low_min': min(temps_low) if temps_low else None,
            'conditions': [s.get('primary_condition') for s in forecast_with_data if s.get('primary_condition')],
        }
    
    # Overall summary text
    summary_text = generate_summary_text(past_week_summary, forecast_summary, today)
    
    return {
        'generated_at': datetime.now(),
        'today': today,
        'past_week': {
            'days': days_back,
            'summary': past_week_summary,
            'daily': past_week_summaries,
        },
        'forecast_week': {
            'days': days_ahead,
            'summary': forecast_summary,
            'daily': forecast_summaries,
        },
        'daily_summaries': daily_summaries,
        'summary_text': summary_text,
        'total_items': len(items),
    }


def generate_summary_text(past_summary: Dict[str, Any], forecast_summary: Dict[str, Any], 
                         today: date) -> str:
    """Generate human-readable summary text comparing past week, forecast, and norms.
    
    Args:
        past_summary: Aggregated past week stats
        forecast_summary: Aggregated forecast stats
        today: Today's date
        
    Returns:
        Summary text string
    """
    parts = []
    
    # Past week
    if past_summary.get('days_with_data'):
        parts.append("Past week")
        if past_summary.get('avg_high') and past_summary.get('avg_low'):
            parts.append(f"averaged {past_summary['avg_high']}°C high / {past_summary['avg_low']}°C low")
            if past_summary.get('high_max'):
                parts.append(f"(reaching {past_summary['high_max']}°C)")
        if past_summary.get('conditions'):
            conditions_set = set(past_summary['conditions'])
            if len(conditions_set) <= 3:
                parts.append(f"with {', '.join(conditions_set[:3])}")
    
    # Forecast
    if forecast_summary.get('days_with_data'):
        parts.append("Looking ahead")
        if forecast_summary.get('avg_high') and forecast_summary.get('avg_low'):
            parts.append(f"expect {forecast_summary['avg_high']}°C high / {forecast_summary['avg_low']}°C low")
            if forecast_summary.get('low_min'):
                parts.append(f"(down to {forecast_summary['low_min']}°C)")
        if forecast_summary.get('conditions'):
            conditions_set = set(forecast_summary['conditions'])
            if conditions_set:
                parts.append(f"with {', '.join(list(conditions_set)[:2])}")
    
    # Seasonal comparison
    norm = get_seasonal_norm(today)
    if past_summary.get('avg_high'):
        vs_norm = past_summary['avg_high'] - norm['high']
        if abs(vs_norm) > 2:
            if vs_norm > 0:
                parts.append(f"{abs(vs_norm):.0f}°C warmer than typical {norm['description']}")
            else:
                parts.append(f"{abs(vs_norm):.0f}°C cooler than typical {norm['description']}")
    
    if not parts:
        return "Weather data collection in progress. Summary will be available once data is gathered."
    
    return ". ".join(parts) + "."


def get_daily_summary(target_date: Optional[date] = None) -> Dict[str, Any]:
    """Get daily weather summary for a specific date (default: today).
    
    Args:
        target_date: Date to summarize (default: today)
        
    Returns:
        Daily summary dict
    """
    if target_date is None:
        target_date = date.today()
    
    items = get_weather_items(days_back=14, days_ahead=14)
    grouped = group_weather_by_date(items)
    date_items = grouped.get(target_date, [])
    
    day_summary = calculate_day_summary(date_items, target_date)
    norm = get_seasonal_norm(target_date)
    day_summary['seasonal_norm'] = norm
    
    return day_summary

