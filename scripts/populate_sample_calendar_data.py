#!/usr/bin/env python3
"""
Populate sample calendar data for testing the calendar system.
This script adds sample ideas, events, and schedule entries.
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def populate_sample_ideas():
    """Populate sample calendar ideas (perpetual)"""
    print("Populating sample calendar ideas...")
    
    sample_ideas = [
        # Spring ideas (weeks 1-13)
        (1, "New Year's Resolution Guide", "Comprehensive guide to setting and achieving goals", "New Year planning and goal setting", "guide", 5, ["General", "Tutorials"]),
        (2, "Winter Garden Planning", "Plan your garden for the upcoming growing season", "Early spring garden preparation", "tutorial", 4, ["Gardening", "Seasonal"]),
        (3, "Spring Cleaning Checklist", "Complete home organization and cleaning guide", "Spring cleaning and organization", "list", 3, ["General", "Lists"]),
        (4, "Valentine's Day Recipes", "Romantic dinner ideas and dessert recipes", "Valentine's Day cooking and romance", "tutorial", 4, ["Cooking", "Holidays"]),
        (5, "Early Spring Planting", "What to plant in early spring for best results", "Spring gardening and planting", "tutorial", 5, ["Gardening", "Seasonal"]),
        (6, "Spring Fashion Trends", "Latest spring fashion and wardrobe updates", "Spring fashion and style", "review", 3, ["General", "Reviews"]),
        (7, "Spring Break Travel Tips", "Budget-friendly spring break destinations", "Spring travel and vacation planning", "guide", 4, ["General", "Tutorials"]),
        (8, "Easter Recipe Collection", "Traditional and modern Easter recipes", "Easter cooking and traditions", "tutorial", 4, ["Cooking", "Holidays"]),
        (9, "Spring Home Maintenance", "Essential home maintenance tasks for spring", "Spring home care and maintenance", "list", 3, ["General", "Lists"]),
        (10, "Garden Soil Preparation", "How to prepare soil for spring planting", "Spring gardening preparation", "tutorial", 5, ["Gardening", "Tutorials"]),
        (11, "Spring Allergy Management", "Natural ways to manage spring allergies", "Spring health and wellness", "guide", 3, ["General", "Tutorials"]),
        (12, "Mother's Day Gift Ideas", "Thoughtful and creative Mother's Day presents", "Mother's Day gifts and celebration", "list", 4, ["General", "Lists", "Holidays"]),
        (13, "Spring Flower Arranging", "Beautiful spring flower arrangements", "Spring floral design and decoration", "tutorial", 3, ["General", "Tutorials"]),
        
        # Summer ideas (weeks 14-26)
        (14, "Summer Garden Care", "Essential summer gardening tasks and tips", "Summer garden maintenance", "tutorial", 5, ["Gardening", "Seasonal"]),
        (15, "Father's Day BBQ Guide", "Perfect Father's Day barbecue recipes and tips", "Father's Day cooking and celebration", "tutorial", 4, ["Cooking", "Holidays"]),
        (16, "Summer Vacation Planning", "Plan the perfect summer getaway", "Summer travel and vacation", "guide", 4, ["General", "Tutorials"]),
        (17, "Summer Solstice Celebration", "Ways to celebrate the longest day of the year", "Summer solstice traditions", "guide", 3, ["General", "Holidays"]),
        (18, "Summer Grilling Recipes", "Delicious summer grilling ideas and techniques", "Summer cooking and grilling", "tutorial", 4, ["Cooking", "Seasonal"]),
        (19, "Beach Day Essentials", "Complete guide to a perfect beach day", "Summer beach and outdoor activities", "list", 3, ["General", "Lists"]),
        (20, "Summer Hydration Tips", "Stay hydrated and healthy during hot weather", "Summer health and wellness", "guide", 3, ["General", "Tutorials"]),
        (21, "Independence Day Recipes", "Patriotic recipes for the 4th of July", "Independence Day cooking and celebration", "tutorial", 4, ["Cooking", "Holidays"]),
        (22, "Summer Garden Harvest", "When and how to harvest summer vegetables", "Summer gardening and harvesting", "tutorial", 5, ["Gardening", "Seasonal"]),
        (23, "Summer Camp Activities", "Fun activities for kids during summer break", "Summer activities and entertainment", "list", 3, ["General", "Lists"]),
        (24, "Summer Skin Care Routine", "Protect your skin during summer months", "Summer health and beauty", "guide", 3, ["General", "Tutorials"]),
        (25, "Backyard Summer Party", "Host the perfect summer gathering", "Summer entertaining and parties", "guide", 4, ["General", "Tutorials"]),
        (26, "Summer Reading List", "Best books to read during summer vacation", "Summer reading and entertainment", "list", 3, ["General", "Lists"]),
        
        # Fall ideas (weeks 27-39)
        (27, "Back to School Preparation", "Get ready for the new school year", "Back to school planning and preparation", "guide", 4, ["General", "Tutorials"]),
        (28, "Fall Garden Planning", "Prepare your garden for autumn and winter", "Fall gardening and preparation", "tutorial", 5, ["Gardening", "Seasonal"]),
        (29, "Labor Day Weekend Ideas", "Make the most of the last summer weekend", "Labor Day activities and celebration", "list", 3, ["General", "Holidays"]),
        (30, "Fall Fashion Trends", "Update your wardrobe for autumn", "Fall fashion and style", "review", 3, ["General", "Reviews"]),
        (31, "Apple Picking Guide", "Best places and tips for apple picking", "Fall activities and apple picking", "guide", 4, ["General", "Tutorials"]),
        (32, "Halloween Costume Ideas", "Creative and easy Halloween costume ideas", "Halloween costumes and celebration", "list", 4, ["General", "Lists", "Holidays"]),
        (33, "Fall Home Decorating", "Cozy autumn home decoration ideas", "Fall home decoration and design", "tutorial", 3, ["General", "Tutorials"]),
        (34, "Thanksgiving Menu Planning", "Plan the perfect Thanksgiving dinner", "Thanksgiving cooking and celebration", "tutorial", 5, ["Cooking", "Holidays"]),
        (35, "Fall Leaf Raking Tips", "Efficient ways to manage autumn leaves", "Fall yard maintenance", "tutorial", 3, ["General", "Tutorials"]),
        (36, "Halloween Party Ideas", "Spooktacular Halloween party planning", "Halloween party and celebration", "guide", 4, ["General", "Holidays"]),
        (37, "Fall Comfort Foods", "Warm and hearty autumn recipes", "Fall cooking and comfort food", "tutorial", 4, ["Cooking", "Seasonal"]),
        (38, "Thanksgiving Leftovers", "Creative ways to use Thanksgiving leftovers", "Thanksgiving cooking and leftovers", "tutorial", 3, ["Cooking", "Tutorials"]),
        (39, "Black Friday Shopping Guide", "Navigate Black Friday deals and crowds", "Black Friday shopping and deals", "guide", 3, ["General", "Tutorials"]),
        
        # Winter ideas (weeks 40-52)
        (40, "Holiday Decorating Ideas", "Festive home decoration for the holidays", "Holiday decoration and design", "tutorial", 4, ["General", "Holidays"]),
        (41, "Christmas Cookie Recipes", "Traditional and modern Christmas cookies", "Christmas cooking and baking", "tutorial", 5, ["Cooking", "Holidays"]),
        (42, "Winter Garden Protection", "Protect your garden from winter weather", "Winter gardening and protection", "tutorial", 4, ["Gardening", "Seasonal"]),
        (43, "Holiday Gift Wrapping", "Beautiful and creative gift wrapping ideas", "Holiday gifts and wrapping", "tutorial", 3, ["General", "Tutorials"]),
        (44, "New Year's Eve Party", "Ring in the new year with style", "New Year's Eve celebration", "guide", 4, ["General", "Holidays"]),
        (45, "Winter Comfort Foods", "Warm and hearty winter recipes", "Winter cooking and comfort food", "tutorial", 4, ["Cooking", "Seasonal"]),
        (46, "Holiday Travel Tips", "Navigate holiday travel like a pro", "Holiday travel and transportation", "guide", 3, ["General", "Tutorials"]),
        (47, "Winter Home Maintenance", "Essential winter home care tasks", "Winter home maintenance", "list", 3, ["General", "Lists"]),
        (48, "Christmas Dinner Menu", "Plan the perfect Christmas feast", "Christmas cooking and celebration", "tutorial", 5, ["Cooking", "Holidays"]),
        (49, "Winter Wellness Tips", "Stay healthy and happy during winter", "Winter health and wellness", "guide", 3, ["General", "Tutorials"]),
        (50, "New Year Goal Setting", "Set and achieve your New Year's resolutions", "New Year planning and goals", "guide", 4, ["General", "Tutorials"]),
        (51, "Winter Garden Planning", "Plan next year's garden during winter", "Winter garden planning", "tutorial", 4, ["Gardening", "Tutorials"]),
        (52, "Year-End Reflection", "Reflect on the past year and plan ahead", "Year-end reflection and planning", "guide", 3, ["General", "Tutorials"])
    ]
    
    with db_manager.get_cursor() as cursor:
        # Get category IDs
        cursor.execute("SELECT id, name FROM calendar_categories")
        categories = {cat['name']: cat['id'] for cat in cursor.fetchall()}
        
        for week_num, title, description, context, content_type, priority, category_names in sample_ideas:
            # Insert idea
            cursor.execute("""
                INSERT INTO calendar_ideas 
                (week_number, idea_title, idea_description, seasonal_context, content_type, priority, tags, is_recurring, can_span_weeks, max_weeks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                week_num, title, description, context, content_type, priority, 
                json.dumps(category_names), True, False, 1
            ))
            
            idea_id = cursor.fetchone()['id']
            
            # Link to categories
            for cat_name in category_names:
                if cat_name in categories:
                    cursor.execute("""
                        INSERT INTO calendar_idea_categories (idea_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (idea_id, categories[cat_name]))
        
        cursor.connection.commit()
        print(f"Inserted {len(sample_ideas)} sample ideas")

def populate_sample_events():
    """Populate sample calendar events for 2025"""
    print("Populating sample calendar events for 2025...")
    
    sample_events = [
        ("Valentine's Day Special", "Romantic dinner and gift ideas", "2025-02-14", "2025-02-14", 7, 2025, "tutorial", 5, ["Cooking", "Holidays"]),
        ("Spring Garden Show", "Annual spring garden and home show", "2025-03-15", "2025-03-16", 11, 2025, "guide", 4, ["Gardening", "General"]),
        ("Easter Celebration", "Easter recipes and family activities", "2025-04-20", "2025-04-20", 16, 2025, "tutorial", 5, ["Cooking", "Holidays"]),
        ("Summer Solstice Festival", "Celebrate the longest day of the year", "2025-06-21", "2025-06-21", 25, 2025, "guide", 3, ["General", "Holidays"]),
        ("Independence Day BBQ", "4th of July celebration and recipes", "2025-07-04", "2025-07-04", 27, 2025, "tutorial", 4, ["Cooking", "Holidays"]),
        ("Fall Harvest Festival", "Local fall festival and activities", "2025-09-21", "2025-09-21", 38, 2025, "guide", 3, ["General", "Seasonal"]),
        ("Halloween Spooktacular", "Halloween party ideas and costumes", "2025-10-31", "2025-10-31", 44, 2025, "guide", 4, ["General", "Holidays"]),
        ("Thanksgiving Feast", "Traditional Thanksgiving recipes and tips", "2025-11-27", "2025-11-27", 47, 2025, "tutorial", 5, ["Cooking", "Holidays"]),
        ("Black Friday Deals", "Best Black Friday shopping strategies", "2025-11-28", "2025-11-28", 47, 2025, "guide", 3, ["General", "Tutorials"]),
        ("Christmas Celebration", "Christmas recipes and decoration ideas", "2025-12-25", "2025-12-25", 51, 2025, "tutorial", 5, ["Cooking", "Holidays"])
    ]
    
    with db_manager.get_cursor() as cursor:
        # Get category IDs
        cursor.execute("SELECT id, name FROM calendar_categories")
        categories = {cat['name']: cat['id'] for cat in cursor.fetchall()}
        
        for title, description, start_date, end_date, week_num, year, content_type, priority, category_names in sample_events:
            # Insert event
            cursor.execute("""
                INSERT INTO calendar_events 
                (event_title, event_description, start_date, end_date, week_number, year, content_type, priority, tags, is_recurring, can_span_weeks, max_weeks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                title, description, start_date, end_date, week_num, year, content_type, priority,
                json.dumps(category_names), False, False, 1
            ))
            
            event_id = cursor.fetchone()['id']
            
            # Link to categories
            for cat_name in category_names:
                if cat_name in categories:
                    cursor.execute("""
                        INSERT INTO calendar_event_categories (event_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (event_id, categories[cat_name]))
        
        cursor.connection.commit()
        print(f"Inserted {len(sample_events)} sample events")

def populate_sample_schedule():
    """Populate sample schedule entries for 2025"""
    print("Populating sample schedule entries for 2025...")
    
    with db_manager.get_cursor() as cursor:
        # Get some ideas and events to schedule
        cursor.execute("SELECT id FROM calendar_ideas LIMIT 10")
        idea_ids = [row['id'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM calendar_events LIMIT 5")
        event_ids = [row['id'] for row in cursor.fetchall()]
        
        # Schedule some ideas
        for i, idea_id in enumerate(idea_ids[:5]):
            week_num = i + 1
            cursor.execute("""
                INSERT INTO calendar_schedule 
                (year, week_number, idea_id, status, scheduled_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (2025, week_num, idea_id, 'planned', f'2025-01-{week_num:02d}', 'Sample scheduled idea'))
        
        # Schedule some events
        for i, event_id in enumerate(event_ids[:3]):
            week_num = i + 10
            cursor.execute("""
                INSERT INTO calendar_schedule 
                (year, week_number, event_id, status, scheduled_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (2025, week_num, event_id, 'planned', f'2025-03-{week_num:02d}', 'Sample scheduled event'))
        
        cursor.connection.commit()
        print("Inserted sample schedule entries")

def main():
    print("Populating sample calendar data...")
    
    try:
        populate_sample_ideas()
        populate_sample_events()
        populate_sample_schedule()
        
        print("\nSample calendar data populated successfully!")
        print("You can now view the calendar at: http://localhost:5000/planning/posts/53/calendar/view")
        
    except Exception as e:
        print(f"Error populating sample data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
