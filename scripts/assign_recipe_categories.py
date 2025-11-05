#!/usr/bin/env python3
"""
Assign recipe categories to existing recipes in calendar_recipes table.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager

# Recipe category mapping: week_number -> category
RECIPE_CATEGORIES = {
    # Soups
    1: "soups",   # Cullen Skink
    2: "soups",   # Cock-a-Leekie Soup
    4: "soups",   # Scotch Broth
    34: "soups",  # Leek & Barley Broth
    35: "soups",  # Haddock Chowder with Oats
    
    # Mains
    3: "mains",   # Haggis, Neeps & Tatties
    6: "mains",   # Mince & Tatties
    7: "mains",   # Stovies
    22: "mains",  # Fish Pie with Leeks & Cheddar Mash
    23: "mains",  # Kedgeree (Scottish Colonial Twist)
    24: "mains",  # Venison Stew with Juniper
    25: "mains",  # Salmon en Croute (Scottish Style)
    30: "mains",  # Scottish Lamb Hotpot
    31: "mains",  # Beef & Ale Stew with Root Vegetables
    32: "mains",  # Roe Deer with Rowan Jelly
    33: "mains",  # Game Pie
    46: "mains",  # Scottish Kedgeree with Smoked Haddock
    52: "mains",  # Scotch Collops (New Year's Dish)
    
    # Breads
    11: "breads",  # Bannocks (Oat & Bere)
    12: "breads",  # Oatcakes
    13: "breads",  # Selkirk Bannock
    14: "breads",  # Soda & Potato Scones
    28: "breads",  # Treacle Scones
    44: "breads",  # Bere Bread
    
    # Desserts
    15: "desserts",  # Shortbread (Three Regional Styles)
    16: "desserts",  # Dundee Cake
    17: "desserts",  # Clootie Dumpling
    18: "desserts",  # Cranachan
    19: "desserts",  # Rhubarb Fool
    26: "desserts",  # Raspberry Cranachan Parfait
    27: "desserts",  # Ecclefechan Tart
    29: "desserts",  # Clootie Dumpling (Harvest Version)
    36: "desserts",  # Black Bun
    37: "desserts",  # Tablet
    49: "desserts",  # Cranberry Cranachan (Modern Twist)
    50: "desserts",  # Whisky Truffles
    51: "desserts",  # Festive Shortbread Selection
    
    # Drinks
    38: "drinks",  # Atholl Brose
    39: "drinks",  # Hot Toddy
    
    # Preserves
    40: "preserves",  # Whisky Marmalade
    41: "preserves",  # Rowan Jelly
    42: "preserves",  # Elderflower Cordial
    43: "preserves",  # Raspberry Jam
    
    # Snacks
    5: "snacks",   # Rumbledethumps
    8: "snacks",   # Arbroath Smokies
    9: "snacks",   # Forfar Bridie
    10: "snacks",  # Scotch Pie
    20: "snacks",  # Smoked Salmon with Whisky Cream Sauce
    21: "snacks",  # Hot-Smoked Trout Salad
    45: "snacks",  # Crowdie Cheese with Oatcakes
    47: "snacks",  # Fishcakes with Oat Crumb
    48: "snacks",  # Hogmanay Sausage Rolls
}

def assign_recipe_categories():
    """Assign categories to recipes in calendar_recipes table."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                updated = 0
                
                for week_number, category in RECIPE_CATEGORIES.items():
                    cursor.execute("""
                        UPDATE calendar_recipes
                        SET recipe_category = %s, updated_at = NOW()
                        WHERE week_number = %s
                    """, (category, week_number))
                    
                    if cursor.rowcount > 0:
                        updated += 1
                
                conn.commit()
                print(f"✅ Successfully assigned categories to {updated} recipes")
                print(f"\nCategory breakdown:")
                
                # Show category counts
                cursor.execute("""
                    SELECT recipe_category, COUNT(*) as count
                    FROM calendar_recipes
                    WHERE recipe_category IS NOT NULL
                    GROUP BY recipe_category
                    ORDER BY recipe_category
                """)
                categories = cursor.fetchall()
                for cat in categories:
                    cat_name = cat['recipe_category'] if isinstance(cat, dict) else cat[0]
                    count = cat['count'] if isinstance(cat, dict) else cat[1]
                    print(f"   - {cat_name}: {count} recipes")
                
                return True
                
    except Exception as e:
        print(f"❌ Error assigning recipe categories: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🏷️  Assigning recipe categories...\n")
    
    success = assign_recipe_categories()
    
    if success:
        print("\n✅ Recipe categories assigned successfully!")
        sys.exit(0)
    else:
        print("\n❌ Failed to assign recipe categories!")
        sys.exit(1)

