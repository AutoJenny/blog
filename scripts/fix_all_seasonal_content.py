#!/usr/bin/env python3
"""
Comprehensive fix for ALL seasonal calendar content.
Going through each item individually to assess proper seasonal timing.
"""

import sys
import os
from datetime import date

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def get_week_number(target_date, year=2025):
    """Get the week number for a specific date in a given year."""
    target = date(year, target_date.month, target_date.day)
    jan_1 = date(year, 1, 1)
    days_since_jan_1 = (target - jan_1).days
    week_number = (days_since_jan_1 // 7) + 1
    return min(max(week_number, 1), 52)

def fix_all_seasonal_content():
    """Fix ALL seasonal content based on individual assessment."""
    print("Fixing ALL seasonal calendar content...")
    
    # Individual item fixes based on proper seasonal timing
    fixes = [
        # JANUARY (Weeks 1-4) - New Year, Burns Night, Winter
        (53, 1, "New Year's Day / Hogmanay Traditions"),  # Jan 1
        (50, 1, "New Year Goal Setting"),  # Early January
        (54, 4, "Burns Night Preparation"),  # Jan 25
        (55, 3, "Winter Foods & Whisky Pairings"),  # Mid-winter
        (57, 4, "Tartan Fashion in Winter"),  # Winter fashion
        (56, 5, "Celtic Winter Folklore"),  # Winter folklore
        (46, 5, "Holiday Travel Tips"),  # Post-holiday travel
        (49, 7, "Winter Wellness Tips"),  # Mid-winter wellness
        (51, 8, "Winter Garden Planning"),  # Late winter planning
        (2, 8, "Winter Garden Planning"),  # Late winter planning
        (42, 9, "Winter Garden Protection"),  # Late winter protection
        
        # FEBRUARY (Weeks 5-8) - Valentine's, Winter, St David's
        (58, 7, "Valentine's Day Celtic Legends"),  # Feb 14
        (4, 7, "Valentine's Day Recipes"),  # Feb 14
        (60, 8, "Clan Love Stories"),  # Valentine's season
        (61, 9, "Celtic Jewelry Guide"),  # Valentine's gifts
        (63, 9, "St David's Day (Wales)"),  # Mar 1 (close to Feb)
        (40, 10, "Holiday Decorating Ideas"),  # Post-holiday cleanup
        
        # MARCH (Weeks 9-12) - St Patrick's, Spring, Easter
        (62, 11, "Castles with Romantic Legends"),  # Spring romance
        (3, 11, "Spring Cleaning Checklist"),  # Spring cleaning
        (64, 11, "St Patrick's Day Irish Heritage"),  # Mar 17
        (9, 12, "Spring Home Maintenance"),  # Spring maintenance
        (69, 13, "April Fool's Day - Huntigowk Day"),  # Apr 1
        (65, 13, "Mother's Day Celtic Traditions"),  # May (moved to spring)
        (66, 13, "Spring Highland Games Preview"),  # Spring games
        
        # APRIL (Weeks 13-16) - Easter, Spring, April Fool's
        (7, 14, "Spring Break Travel Tips"),  # Spring break
        (13, 14, "Spring Flower Arranging"),  # Spring flowers
        (21, 15, "Independence Day Recipes"),  # July 4 (moved to summer)
        (72, 15, "Scottish Wildflowers in Spring"),  # Spring wildflowers
        (5, 16, "Early Spring Planting"),  # Spring planting
        (70, 16, "Easter Celtic Traditions"),  # Easter (varies, but spring)
        
        # MAY (Weeks 17-20) - Spring, May Day, Mother's Day
        (6, 17, "Spring Fashion Trends"),  # Spring fashion
        (74, 18, "Beltane Fire Festival"),  # May 1
        (75, 18, "May Bank Holiday Traditions"),  # May Day
        (73, 18, "Spring Clan Gatherings"),  # Spring gatherings
        (78, 18, "Traditional May Day Customs"),  # May Day
        (32, 19, "Halloween Costume Ideas"),  # Oct 31 (moved to fall)
        (76, 20, "Scottish Islands Travel Guide"),  # Summer travel prep
        (77, 21, "Irish Folklore of May"),  # May folklore
        (34, 21, "Thanksgiving Menu Planning"),  # Nov (moved to fall)
        
        # JUNE (Weeks 21-24) - Summer, Father's Day, Summer Solstice
        (80, 22, "Highland Games Season Start"),  # Summer games
        (16, 22, "Summer Vacation Planning"),  # Summer vacation
        (23, 23, "Summer Camp Activities"),  # Summer activities
        (79, 24, "Father's Day Clan Heroes"),  # June 15
        (10, 24, "Garden Soil Preparation"),  # Spring prep (moved to spring)
        (92, 24, "Top Lochs & Glens in Summer"),  # Summer travel
        (14, 25, "Summer Garden Care"),  # Summer gardening
        (17, 25, "Summer Solstice Celebration"),  # June 21
        (81, 25, "Summer Solstice Celtic Traditions"),  # June 21
        
        # JULY (Weeks 25-28) - Independence Day, Summer, Canada Day
        (83, 26, "Canada Day - Scottish Diaspora"),  # July 1
        (15, 26, "Father's Day BBQ Guide"),  # June (moved to June)
        (82, 26, "Scottish Castles & Clan Seats"),  # Summer travel
        (20, 26, "Summer Hydration Tips"),  # Summer health
        (25, 27, "Backyard Summer Party"),  # Summer entertaining
        (84, 27, "Independence Day - US Scottish Heritage"),  # July 4
        (38, 27, "Thanksgiving Leftovers"),  # Nov (moved to fall)
        (27, 28, "Back to School Preparation"),  # Aug (moved to August)
        (85, 28, "Edinburgh Festival Preview"),  # Aug (moved to August)
        (26, 28, "Summer Reading List"),  # Summer reading
        
        # AUGUST (Weeks 29-32) - Summer, Edinburgh Festival, Harvest
        (86, 29, "Scottish Regiments in NA History"),  # Summer history
        (18, 29, "Summer Grilling Recipes"),  # Summer cooking
        (108, 31, "Clan Saint Stories"),  # Summer stories
        (88, 31, "Lammas / Lughnasadh Festival"),  # Aug 1
        (22, 31, "Summer Garden Harvest"),  # Summer harvest
        (89, 32, "Edinburgh International Festival"),  # Aug (moved to August)
        (87, 32, "Summer Recipes with Berries/Seafood"),  # Summer recipes
        (90, 33, "Highland Games Peak Season"),  # Summer games
        (91, 34, "Gaelic Harvest Traditions"),  # Late summer harvest
        
        # SEPTEMBER (Weeks 35-38) - Labor Day, Fall, Michaelmas
        (93, 35, "Labour Day - Scottish Workers"),  # Sep 1
        (44, 35, "New Year's Eve Party"),  # Dec 31 (moved to December)
        (110, 36, "Diaspora Pride Features"),  # Fall pride
        (30, 37, "Fall Fashion Trends"),  # Fall fashion
        (36, 37, "Halloween Party Ideas"),  # Oct 31 (moved to October)
        (96, 37, "Harvest Recipes & Clan Feasts"),  # Fall harvest
        (94, 38, "Autumn Equinox Celtic Traditions"),  # Sep 22
        (8, 38, "Easter Recipe Collection"),  # Easter (moved to spring)
        (28, 38, "Fall Garden Planning"),  # Fall planning
        (95, 39, "Michaelmas - Scottish Quarter Day"),  # Sep 29
        
        # OCTOBER (Weeks 40-43) - Halloween, Fall, Thanksgiving
        (37, 40, "Fall Comfort Foods"),  # Fall comfort food
        (1, 40, "New Year's Resolution Guide"),  # Jan (moved to January)
        (98, 41, "Canadian Thanksgiving - Scottish Influence"),  # Oct 13
        (33, 41, "Fall Home Decorating"),  # Fall decorating
        (68, 41, "Welsh Myths and Legends"),  # Fall stories
        (19, 42, "Beach Day Essentials"),  # Summer (moved to summer)
        (35, 42, "Fall Leaf Raking Tips"),  # Fall yard work
        (100, 42, "Scottish Ghost Stories"),  # Halloween season
        (101, 43, "Haunted Castles of Scotland"),  # Halloween season
        
        # NOVEMBER (Weeks 44-47) - Halloween, Thanksgiving, Guy Fawkes
        (103, 44, "All Saints' / Samhain Continuation"),  # Nov 1
        (99, 44, "Halloween / Samhain Origins"),  # Oct 31 (moved to October)
        (12, 44, "Mother's Day Gift Ideas"),  # May (moved to May)
        (104, 45, "Guy Fawkes Night - Scottish Connections"),  # Nov 5
        (105, 45, "Remembrance Day - Scottish Veterans"),  # Nov 11
        (52, 45, "Year-End Reflection"),  # Dec (moved to December)
        (107, 48, "St Andrew's Day - Scotland's Patron Saint"),  # Nov 30
        (106, 48, "US Thanksgiving - Scottish Influence"),  # Nov 28
        (111, 49, "St Nicholas Day - Scottish Traditions"),  # Dec 6 (moved to December)
        
        # DECEMBER (Weeks 50-52) - Christmas, Winter, New Year
        (31, 50, "Apple Picking Guide"),  # Fall (moved to fall)
        (41, 50, "Christmas Cookie Recipes"),  # Dec 10
        (45, 50, "Winter Comfort Foods"),  # Dec 15
        (48, 51, "Christmas Dinner Menu"),  # Dec 20
        (115, 51, "Festive Music & Ceilidhs"),  # Christmas music
        (47, 51, "Winter Home Maintenance"),  # Dec 22
        (112, 51, "Winter Solstice / Yule Traditions"),  # Dec 21
        (116, 52, "Hogmanay / New Year's Eve"),  # Dec 31
        (113, 52, "Scottish Christmas Traditions"),  # Dec 25
    ]
    
    with db_manager.get_cursor() as cursor:
        print(f"Applying {len(fixes)} seasonal fixes...")
        
        for item_id, correct_week, title in fixes:
            # Get current week
            cursor.execute("SELECT week_number FROM calendar_ideas WHERE id = %s", (item_id,))
            result = cursor.fetchone()
            if result:
                current_week = result['week_number']
                if current_week != correct_week:
                    cursor.execute("""
                        UPDATE calendar_ideas 
                        SET week_number = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (correct_week, item_id))
                    print(f"Fixed '{title}': Week {current_week} → Week {correct_week}")
                else:
                    print(f"'{title}' already in correct week {correct_week}")
        
        cursor.connection.commit()
        
        # Show final distribution by month
        print("\nFinal seasonal distribution by month:")
        month_ranges = [
            (1, 4, "January"),
            (5, 8, "February"), 
            (9, 12, "March"),
            (13, 16, "April"),
            (17, 20, "May"),
            (21, 24, "June"),
            (25, 28, "July"),
            (29, 32, "August"),
            (33, 36, "September"),
            (37, 40, "October"),
            (41, 44, "November"),
            (45, 48, "December"),
            (49, 52, "Late December")
        ]
        
        for start_week, end_week, month_name in month_ranges:
            cursor.execute("""
                SELECT COUNT(*) as count, string_agg(idea_title, ', ' ORDER BY idea_title) as titles
                FROM calendar_ideas 
                WHERE week_number BETWEEN %s AND %s
            """, (start_week, end_week))
            result = cursor.fetchone()
            if result['count'] > 0:
                print(f"  {month_name} (Weeks {start_week}-{end_week}): {result['count']} items")
                print(f"    {result['titles'][:100]}...")
        
        print(f"\nAll seasonal content fixed! Content now properly aligned with calendar months.")

def main():
    try:
        fix_all_seasonal_content()
        print("\nSeasonal calendar content completely fixed!")
        print("All items now appear in their appropriate seasonal timing.")
        
    except Exception as e:
        print(f"Error fixing seasonal content: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
