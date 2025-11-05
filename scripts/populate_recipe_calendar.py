#!/usr/bin/env python3
"""
Populate calendar_ideas table with 52 Scottish Recipe ideas (one per week).

Each recipe is assigned to a perpetual week_number (1-52) and will recur every year.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager

# Recipe calendar: Week -> Recipe Title mapping
RECIPES = {
    1: "Cullen Skink",
    2: "Cock-a-Leekie Soup",
    3: "Haggis, Neeps & Tatties",
    4: "Scotch Broth",
    5: "Rumbledethumps",
    6: "Mince & Tatties",
    7: "Stovies",
    8: "Arbroath Smokies",
    9: "Forfar Bridie",
    10: "Scotch Pie",
    11: "Bannocks (Oat & Bere)",
    12: "Oatcakes",
    13: "Selkirk Bannock",
    14: "Soda & Potato Scones",
    15: "Shortbread (Three Regional Styles)",
    16: "Dundee Cake",
    17: "Clootie Dumpling",
    18: "Cranachan",
    19: "Rhubarb Fool",
    20: "Smoked Salmon with Whisky Cream Sauce",
    21: "Hot-Smoked Trout Salad",
    22: "Fish Pie with Leeks & Cheddar Mash",
    23: "Kedgeree (Scottish Colonial Twist)",
    24: "Venison Stew with Juniper",
    25: "Salmon en Croute (Scottish Style)",
    26: "Raspberry Cranachan Parfait",
    27: "Ecclefechan Tart",
    28: "Treacle Scones",
    29: "Clootie Dumpling (Harvest Version)",
    30: "Scottish Lamb Hotpot",
    31: "Beef & Ale Stew with Root Vegetables",
    32: "Roe Deer with Rowan Jelly",
    33: "Game Pie",
    34: "Leek & Barley Broth",
    35: "Haddock Chowder with Oats",
    36: "Black Bun",
    37: "Tablet",
    38: "Atholl Brose",
    39: "Hot Toddy",
    40: "Whisky Marmalade",
    41: "Rowan Jelly",
    42: "Elderflower Cordial",
    43: "Raspberry Jam",
    44: "Bere Bread",
    45: "Crowdie Cheese with Oatcakes",
    46: "Scottish Kedgeree with Smoked Haddock",
    47: "Fishcakes with Oat Crumb",
    48: "Hogmanay Sausage Rolls",
    49: "Cranberry Cranachan (Modern Twist)",
    50: "Whisky Truffles",
    51: "Festive Shortbread Selection",
    52: "Scotch Collops (New Year's Dish)"
}

# Seasonal context mapping (brief descriptions)
SEASONAL_CONTEXT = {
    1: "New Year warmth; origin in Moray coast fishing towns",
    2: "Traditional winter starter; Burns season",
    3: "Burns Night classic",
    4: "Deep winter comfort",
    5: "Borders winter vegetable bake",
    6: "Everyday Scots home cooking",
    7: "Leftover dish of the crofting north",
    8: "Fishmongers' specialty from Angus coast",
    9: "Savoury pie from the northeast",
    10: "Butcher-shop staple",
    11: "Simple Highland bread",
    12: "Everyday table bread and travel ration",
    13: "Easter and festive bread",
    14: "Breakfast tradition",
    15: "Highland, Edinburgh, and Ayrshire variants",
    16: "Spring celebration cake",
    17: "Old-style pudding; Easter or spring gathering",
    18: "Start of berry season; May–June",
    19: "Seasonal early summer pudding",
    20: "Elegant midsummer entertaining dish",
    21: "Light summer main",
    22: "Comfort from Scottish dairy and fish",
    23: "Historical breakfast dish",
    24: "Highland game heritage",
    25: "Celebration dish for summer events",
    26: "High summer berries",
    27: "Borders fruit tart",
    28: "Late summer tea favourite",
    29: "Autumn renewal of traditional pudding",
    30: "Early autumn comfort",
    31: "Braemar Gathering season",
    32: "Highland autumn flavours",
    33: "Field-to-table cooking",
    34: "Cold weather returns",
    35: "Modern coastal take",
    36: "Pre-Hogmanay tradition",
    37: "Sweetmaker's treat",
    38: "Oat, whisky and honey drink",
    39: "Seasonal comfort drink",
    40: "Autumn preserve",
    41: "Seasonal berry preserve",
    42: "Late summer-for-autumn bridge",
    43: "Classic preserve season",
    44: "Heritage grain revival",
    45: "Simple Highland snack",
    46: "Reinvented breakfast classic",
    47: "Everyday Scottish family fare",
    48: "Festive savoury bake",
    49: "Holiday season",
    50: "Gift and celebration",
    51: "Christmas tables",
    52: "Historic meat dish for Hogmanay and New Year"
}

def populate_recipe_ideas():
    """Insert 52 recipe definitions into calendar_recipes table."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                inserted = 0
                updated = 0
                
                for week_number, recipe_title in RECIPES.items():
                    seasonal_context = SEASONAL_CONTEXT.get(week_number, "")
                    
                    # Check if recipe already exists for this week_number
                    cursor.execute("""
                        SELECT id FROM calendar_recipes 
                        WHERE week_number = %s
                    """, (week_number,))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing recipe
                        cursor.execute("""
                            UPDATE calendar_recipes
                            SET recipe_title = %s,
                                recipe_description = %s,
                                seasonal_context = %s,
                                priority = %s,
                                tags = %s,
                                is_recurring = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            recipe_title,
                            f"Scottish Recipe: {recipe_title}",
                            seasonal_context,
                            'mandatory',
                            '["Scottish Recipes", "Traditional Food", "Seasonal Cooking"]',
                            True,
                            existing['id'] if isinstance(existing, dict) else existing[0]
                        ))
                        updated += 1
                    else:
                        # Insert new recipe
                        cursor.execute("""
                            INSERT INTO calendar_recipes (
                                week_number, recipe_title, recipe_description,
                                seasonal_context, priority, tags, is_recurring,
                                created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, (
                            week_number,
                            recipe_title,
                            f"Scottish Recipe: {recipe_title}",
                            seasonal_context,
                            'mandatory',
                            '["Scottish Recipes", "Traditional Food", "Seasonal Cooking"]',
                            True
                        ))
                        inserted += 1
                
                conn.commit()
                print(f"✅ Successfully populated recipe calendar:")
                print(f"   - Inserted: {inserted} new recipes")
                print(f"   - Updated: {updated} existing recipes")
                print(f"   - Total: {len(RECIPES)} recipes (weeks 1-52)")
                return True
                
    except Exception as e:
        print(f"❌ Error populating recipe calendar: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🥄 Populating Scottish Recipe Series calendar...")
    print(f"   {len(RECIPES)} recipes to add to calendar_recipes table (weeks 1-52)\n")
    
    success = populate_recipe_ideas()
    
    if success:
        print("\n✅ Recipe calendar population complete!")
        print("   Recipes are now in calendar_recipes table (separate from calendar_ideas)")
        sys.exit(0)
    else:
        print("\n❌ Recipe calendar population failed!")
        sys.exit(1)

