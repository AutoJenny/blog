#!/usr/bin/env python3
"""
Evergreen Content Scheduler
Manages evergreen content usage to prevent overuse and ensure appropriate distribution.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

class EvergreenScheduler:
    """Manages evergreen content scheduling and usage tracking."""
    
    def __init__(self):
        self.frequency_rules = {
            'high-frequency': {'max_per_year': 12, 'min_interval_weeks': 4},
            'medium-frequency': {'max_per_year': 3, 'min_interval_weeks': 16},
            'low-frequency': {'max_per_year': 1, 'min_interval_weeks': 52},
            'one-time': {'max_per_year': 1, 'min_interval_weeks': 999}
        }
    
    def get_available_evergreen_content(self, week_number: int, year: int, 
                                      frequency: str = None) -> List[Dict]:
        """Get evergreen content available for a specific week."""
        with db_manager.get_cursor() as cursor:
            # Build query based on frequency
            where_clause = "ci.is_evergreen = TRUE"
            params = []
            
            if frequency:
                where_clause += " AND ci.evergreen_frequency = %s"
                params.append(frequency)
            
            # Get evergreen ideas with usage tracking
            cursor.execute(f"""
                SELECT ci.*, 
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'::json
                       ) as categories
                FROM calendar_ideas ci
                LEFT JOIN calendar_idea_categories cic ON ci.id = cic.idea_id
                LEFT JOIN calendar_categories cc ON cic.category_id = cc.id
                WHERE {where_clause}
                GROUP BY ci.id
                ORDER BY ci.usage_count ASC, ci.last_used_date ASC NULLS FIRST, ci.priority DESC
            """, params)
            
            ideas = cursor.fetchall()
            
            # Filter based on frequency rules
            available_ideas = []
            for idea in ideas:
                if self._is_content_available(idea, week_number, year):
                    available_ideas.append(idea)
            
            return available_ideas
    
    def _is_content_available(self, idea: Dict, week_number: int, year: int) -> bool:
        """Check if evergreen content is available for use based on frequency rules."""
        frequency = idea['evergreen_frequency']
        rules = self.frequency_rules.get(frequency, {})
        
        # Check if we've exceeded yearly limit
        if idea['usage_count'] >= rules.get('max_per_year', 1):
            return False
        
        # Check minimum interval since last use
        if idea['last_used_date']:
            last_used = idea['last_used_date']
            weeks_since_last_use = self._weeks_between_dates(last_used, f"{year}-01-01") + week_number
            min_interval = rules.get('min_interval_weeks', 52)
            
            if weeks_since_last_use < min_interval:
                return False
        
        return True
    
    def _weeks_between_dates(self, start_date, end_date_str):
        """Calculate weeks between two dates."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        return (end_date - start_date).days // 7
    
    def schedule_evergreen_content(self, idea_id: int, week_number: int, year: int) -> bool:
        """Schedule evergreen content and update usage tracking."""
        try:
            with db_manager.get_cursor() as cursor:
                # Update usage tracking
                cursor.execute("""
                    UPDATE calendar_ideas 
                    SET usage_count = usage_count + 1,
                        last_used_date = CURRENT_DATE,
                        updated_at = NOW()
                    WHERE id = %s
                """, (idea_id,))
                
                # Create schedule entry
                cursor.execute("""
                    INSERT INTO calendar_schedule 
                    (year, week_number, idea_id, status, scheduled_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    year, week_number, idea_id, 'planned',
                    f"{year}-01-{week_number:02d}",
                    'Evergreen content scheduled automatically'
                ))
                
                cursor.connection.commit()
                return True
                
        except Exception as e:
            print(f"Error scheduling evergreen content: {e}")
            return False
    
    def get_evergreen_usage_report(self, year: int) -> Dict:
        """Get usage report for evergreen content in a year."""
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    evergreen_frequency,
                    COUNT(*) as total_ideas,
                    AVG(usage_count) as avg_usage,
                    MAX(usage_count) as max_usage,
                    COUNT(CASE WHEN usage_count > 0 THEN 1 END) as used_ideas
                FROM calendar_ideas 
                WHERE is_evergreen = TRUE
                GROUP BY evergreen_frequency
                ORDER BY evergreen_frequency
            """)
            
            frequency_stats = cursor.fetchall()
            
            cursor.execute("""
                SELECT 
                    ci.idea_title,
                    ci.evergreen_frequency,
                    ci.usage_count,
                    ci.last_used_date
                FROM calendar_ideas ci
                WHERE ci.is_evergreen = TRUE
                ORDER BY ci.usage_count DESC, ci.last_used_date DESC
            """)
            
            usage_details = cursor.fetchall()
            
            return {
                'year': year,
                'frequency_stats': frequency_stats,
                'usage_details': usage_details
            }

def main():
    """Test the evergreen scheduler."""
    scheduler = EvergreenScheduler()
    
    # Test getting available content for week 1 of 2025
    print("Testing evergreen content availability for Week 1, 2025...")
    available = scheduler.get_available_evergreen_content(1, 2025)
    print(f"Found {len(available)} available evergreen ideas")
    
    for idea in available[:5]:  # Show first 5
        print(f"  - {idea['idea_title']} ({idea['evergreen_frequency']})")
    
    # Test usage report
    print("\nEvergreen usage report for 2025:")
    report = scheduler.get_evergreen_usage_report(2025)
    for stat in report['frequency_stats']:
        print(f"  {stat['evergreen_frequency']}: {stat['used_ideas']}/{stat['total_ideas']} used (avg: {stat['avg_usage']:.1f})")

if __name__ == "__main__":
    main()
