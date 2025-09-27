#!/usr/bin/env python3
"""
Populate Celtic/Scottish/Irish content ideas for the calendar system.
Based on the user's specific content plan with seasonal and evergreen content.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def populate_celtic_content_ideas():
    """Populate the calendar with Celtic/Scottish/Irish content ideas."""
    print("Populating Celtic content ideas...")
    
    # Content ideas organized by month and week
    content_ideas = [
        # JANUARY
        (1, "New Year's Day / Hogmanay Traditions", "Explore Scottish New Year celebrations, first-footing customs, and Hogmanay traditions", "New Year celebrations and Scottish customs", "guide", 5, ["Holidays", "General"], True, "low-frequency", "Traditional Scottish New Year customs and first-footing rituals"),
        (2, "Burns Night Preparation", "Guide to hosting a Burns Night celebration with poetry, haggis, and whisky", "Burns Night celebration planning", "tutorial", 5, ["Holidays", "Cooking"], True, "low-frequency", "Complete guide to Burns Night traditions and hosting"),
        (3, "Winter Foods & Whisky Pairings", "Traditional Scottish winter dishes paired with appropriate whiskies", "Winter comfort food and whisky", "tutorial", 4, ["Cooking", "General"], True, "high-frequency", "Evergreen content about Scottish cuisine and whisky culture"),
        (4, "Celtic Winter Folklore", "Myths and legends of winter in Celtic tradition", "Winter folklore and mythology", "guide", 4, ["General", "Seasonal"], True, "medium-frequency", "Evergreen content about Celtic winter traditions"),
        (5, "Tartan Fashion in Winter", "How to wear tartan and traditional Scottish clothing in winter", "Winter fashion and tartan styling", "guide", 3, ["General", "Reviews"], True, "medium-frequency", "Evergreen content about Scottish fashion and style"),
        
        # FEBRUARY
        (6, "Valentine's Day Celtic Legends", "Romantic Scottish and Irish legends, love poetry, and Celtic knot symbolism", "Valentine's Day with Celtic romance", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Romantic Celtic legends and love stories"),
        (7, "Six Nations Rugby Preview", "Scottish rugby in the Six Nations championship", "Rugby and Scottish sports", "review", 4, ["General", "Reviews"], True, "low-frequency", "Annual rugby championship coverage"),
        (8, "Clan Love Stories", "Romantic tales from Scottish clan history", "Romantic clan history", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about romantic clan stories"),
        (9, "Celtic Jewelry Guide", "Traditional Celtic jewelry and its meanings", "Celtic jewelry and symbolism", "guide", 3, ["General", "Reviews"], True, "medium-frequency", "Evergreen content about Celtic jewelry and culture"),
        (10, "Castles with Romantic Legends", "Scottish castles known for their love stories and romantic history", "Romantic castle stories", "guide", 4, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about romantic castle legends"),
        
        # MARCH
        (11, "St David's Day (Wales)", "Welsh traditions, daffodils, and St David's Day celebrations", "Welsh traditions and St David's Day", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Welsh cultural celebration and traditions"),
        (12, "St Patrick's Day Irish Heritage", "Irish traditions, diaspora in North America, and St Patrick's Day", "Irish heritage and St Patrick's Day", "guide", 5, ["Holidays", "General"], True, "low-frequency", "Irish cultural celebration and diaspora stories"),
        (13, "Mother's Day Celtic Traditions", "Celtic mother goddesses and traditional Mother's Day customs", "Mother's Day with Celtic traditions", "guide", 3, ["Holidays", "General"], True, "low-frequency", "Celtic mother goddesses and traditions"),
        (14, "Spring Highland Games Preview", "What to expect at spring Highland Games events", "Highland Games spring season", "guide", 4, ["General", "Tutorials"], True, "medium-frequency", "Evergreen content about Highland Games"),
        (15, "Celtic Saints and Their Stories", "Lives and legends of Celtic saints", "Celtic saints and spirituality", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Celtic saints"),
        (16, "Welsh Myths and Legends", "Traditional Welsh mythology and folklore", "Welsh mythology and culture", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Welsh mythology"),
        
        # APRIL
        (17, "April Fool's Day - Huntigowk Day", "Scottish April Fool's traditions and Huntigowk Day customs", "Scottish April Fool's traditions", "guide", 3, ["Holidays", "General"], True, "low-frequency", "Scottish April Fool's Day traditions"),
        (18, "Easter Celtic Traditions", "Easter customs with Celtic roots and spring celebrations", "Easter with Celtic traditions", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Celtic Easter traditions and spring customs"),
        (19, "Beltane Preparation", "Getting ready for the Celtic fire festival of Beltane", "Beltane festival preparation", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Beltane festival traditions and preparation"),
        (20, "Scottish Wildflowers in Spring", "Native Scottish wildflowers and their folklore", "Scottish wildflowers and folklore", "guide", 3, ["General", "Tutorials"], True, "medium-frequency", "Evergreen content about Scottish flora"),
        (21, "Spring Clan Gatherings", "Traditional spring clan meetings and celebrations", "Spring clan traditions", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about clan gatherings"),
        
        # MAY
        (22, "Beltane Fire Festival", "Edinburgh Beltane celebrations and Celtic fire traditions", "Beltane fire festival traditions", "guide", 5, ["Holidays", "General"], True, "low-frequency", "Beltane fire festival in Edinburgh"),
        (23, "May Bank Holiday Traditions", "Traditional May Day customs and celebrations", "May Day traditions", "guide", 3, ["Holidays", "General"], True, "low-frequency", "May Day customs and celebrations"),
        (24, "Scottish Islands Travel Guide", "Best Scottish islands to visit in spring and summer", "Scottish islands travel", "guide", 4, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish travel"),
        (25, "Irish Folklore of May", "May traditions in Irish folklore and mythology", "Irish May folklore", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Irish folklore"),
        (26, "Traditional May Day Customs", "Celtic May Day traditions and celebrations", "May Day Celtic customs", "guide", 3, ["General", "Tutorials"], True, "medium-frequency", "Evergreen content about May Day traditions"),
        
        # JUNE
        (27, "Father's Day Clan Heroes", "Stories of famous clan fathers and Scottish heroes", "Father's Day with clan heroes", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Clan fathers and Scottish heroes"),
        (28, "Highland Games Season Start", "Beginning of Highland Games season and what to expect", "Highland Games season", "guide", 4, ["General", "Tutorials"], True, "medium-frequency", "Evergreen content about Highland Games season"),
        (29, "Summer Solstice Celtic Traditions", "Celtic celebrations of the longest day of the year", "Summer solstice traditions", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Celtic summer solstice traditions"),
        (30, "Scottish Castles & Clan Seats", "Famous Scottish castles and their clan connections", "Scottish castles and clans", "guide", 4, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish castles"),
        
        # JULY
        (31, "Canada Day - Scottish Diaspora", "Scottish influence in Canada and diaspora celebrations", "Canada Day with Scottish heritage", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Scottish diaspora in Canada"),
        (32, "Independence Day - US Scottish Heritage", "Scottish influence in American independence and culture", "Independence Day with Scottish heritage", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Scottish influence in American history"),
        (33, "Edinburgh Festival Preview", "What to expect at the Edinburgh International Festival", "Edinburgh Festival guide", "guide", 4, ["General", "Tutorials"], True, "low-frequency", "Edinburgh Festival preview and guide"),
        (34, "Scottish Regiments in NA History", "Scottish military regiments in North American history", "Scottish military history", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish military history"),
        (35, "Summer Recipes with Berries/Seafood", "Traditional Scottish summer recipes using local ingredients", "Scottish summer recipes", "tutorial", 4, ["Cooking", "Seasonal"], True, "high-frequency", "Evergreen content about Scottish cuisine"),
        
        # AUGUST
        (36, "Lammas / Lughnasadh Festival", "Celtic harvest festival traditions and celebrations", "Lammas harvest festival", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Celtic harvest festival traditions"),
        (37, "Edinburgh International Festival", "Complete guide to the Edinburgh Festival and Fringe", "Edinburgh Festival guide", "guide", 5, ["General", "Tutorials"], True, "low-frequency", "Edinburgh Festival comprehensive guide"),
        (38, "Highland Games Peak Season", "Best Highland Games events during peak season", "Highland Games peak season", "guide", 4, ["General", "Tutorials"], True, "medium-frequency", "Evergreen content about Highland Games events"),
        (39, "Gaelic Harvest Traditions", "Traditional Gaelic harvest customs and celebrations", "Gaelic harvest traditions", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Gaelic traditions"),
        (40, "Top Lochs & Glens in Summer", "Best Scottish lochs and glens to visit in summer", "Scottish lochs and glens", "guide", 4, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish geography"),
        
        # SEPTEMBER
        (41, "Labour Day - Scottish Workers", "Scottish labor history and workers' contributions", "Labour Day with Scottish history", "guide", 3, ["Holidays", "General"], True, "low-frequency", "Scottish labor history and workers"),
        (42, "Autumn Equinox Celtic Traditions", "Celtic celebrations of the autumn equinox", "Autumn equinox traditions", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Celtic autumn equinox traditions"),
        (43, "Michaelmas - Scottish Quarter Day", "Scottish quarter day traditions and harvest customs", "Michaelmas traditions", "guide", 3, ["Holidays", "General"], True, "low-frequency", "Scottish quarter day traditions"),
        (44, "Harvest Recipes & Clan Feasts", "Traditional harvest recipes and clan feast traditions", "Harvest recipes and feasts", "tutorial", 4, ["Cooking", "General"], True, "high-frequency", "Evergreen content about harvest traditions"),
        (45, "Folklore of Autumn", "Celtic folklore and traditions associated with autumn", "Autumn folklore", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about autumn folklore"),
        
        # OCTOBER
        (46, "Canadian Thanksgiving - Scottish Influence", "Scottish influence on Canadian Thanksgiving traditions", "Canadian Thanksgiving with Scottish heritage", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Scottish influence on Canadian Thanksgiving"),
        (47, "Halloween / Samhain Origins", "Celtic roots of Halloween and Samhain traditions", "Halloween Celtic origins", "guide", 5, ["Holidays", "General"], True, "low-frequency", "Celtic origins of Halloween and Samhain"),
        (48, "Scottish Ghost Stories", "Traditional Scottish ghost stories and haunted tales", "Scottish ghost stories", "guide", 4, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish ghost stories"),
        (49, "Haunted Castles of Scotland", "Most haunted castles in Scotland and their ghostly legends", "Haunted Scottish castles", "guide", 4, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about haunted castles"),
        (50, "Celtic Spirituality & Samhain", "Celtic spiritual traditions and Samhain celebrations", "Celtic spirituality", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Celtic spirituality"),
        
        # NOVEMBER
        (51, "All Saints' / Samhain Continuation", "Continuation of Samhain traditions into All Saints' Day", "All Saints' Day traditions", "guide", 3, ["Holidays", "General"], True, "low-frequency", "All Saints' Day with Celtic traditions"),
        (52, "Guy Fawkes Night - Scottish Connections", "Scottish connections to Guy Fawkes Night and gunpowder plot", "Guy Fawkes Night Scottish connections", "guide", 3, ["Holidays", "General"], True, "low-frequency", "Scottish connections to Guy Fawkes Night"),
        (53, "Remembrance Day - Scottish Veterans", "Scottish veterans and military service in world wars", "Remembrance Day Scottish veterans", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Scottish veterans and military service"),
        (54, "US Thanksgiving - Scottish Influence", "Scottish influence on American Thanksgiving traditions", "Thanksgiving with Scottish heritage", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Scottish influence on American Thanksgiving"),
        (55, "St Andrew's Day - Scotland's Patron Saint", "Celebrating Scotland's patron saint and national day", "St Andrew's Day celebration", "guide", 5, ["Holidays", "General"], True, "low-frequency", "St Andrew's Day and Scotland's patron saint"),
        (56, "Clan Saint Stories", "Stories of saints associated with Scottish clans", "Clan saint stories", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about clan saints"),
        (57, "Scottish Winter Recipes", "Traditional Scottish recipes perfect for winter", "Scottish winter recipes", "tutorial", 4, ["Cooking", "Seasonal"], True, "high-frequency", "Evergreen content about Scottish winter cuisine"),
        (58, "Diaspora Pride Features", "Celebrating Scottish diaspora achievements and contributions", "Scottish diaspora pride", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish diaspora"),
        
        # DECEMBER
        (59, "St Nicholas Day - Scottish Traditions", "Scottish traditions around St Nicholas Day", "St Nicholas Day traditions", "guide", 3, ["Holidays", "General"], True, "low-frequency", "St Nicholas Day Scottish traditions"),
        (60, "Winter Solstice / Yule Traditions", "Celtic winter solstice and Yule celebrations", "Winter solstice traditions", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Celtic winter solstice and Yule traditions"),
        (61, "Scottish Christmas Traditions", "Traditional Scottish Christmas customs and celebrations", "Scottish Christmas traditions", "guide", 4, ["Holidays", "General"], True, "low-frequency", "Scottish Christmas customs and traditions"),
        (62, "Celtic Yule Lore", "Celtic mythology and lore surrounding Yule and winter", "Celtic Yule mythology", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Celtic Yule traditions"),
        (63, "Festive Music & Ceilidhs", "Traditional Scottish music and ceilidh dancing for the holidays", "Scottish festive music", "guide", 3, ["General", "Tutorials"], True, "high-frequency", "Evergreen content about Scottish music and dance"),
        (64, "Hogmanay / New Year's Eve", "Complete guide to Scottish New Year's Eve celebrations", "Hogmanay traditions", "guide", 5, ["Holidays", "General"], True, "low-frequency", "Hogmanay and Scottish New Year traditions"),
    ]
    
    with db_manager.get_cursor() as cursor:
        # Get category IDs
        cursor.execute("SELECT id, name FROM calendar_categories")
        categories = {cat['name']: cat['id'] for cat in cursor.fetchall()}
        
        # Get evergreen frequency category IDs
        cursor.execute("SELECT id, name FROM calendar_categories WHERE name IN ('High-Frequency', 'Medium-Frequency', 'Low-Frequency', 'One-Time')")
        frequency_categories = {cat['name']: cat['id'] for cat in cursor.fetchall()}
        
        for week_num, title, description, context, content_type, priority, category_names, is_evergreen, evergreen_freq, evergreen_notes in content_ideas:
            # Insert idea
            cursor.execute("""
                INSERT INTO calendar_ideas 
                (week_number, idea_title, idea_description, seasonal_context, content_type, priority, tags, 
                 is_recurring, can_span_weeks, max_weeks, is_evergreen, evergreen_frequency, evergreen_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                week_num, title, description, context, content_type, priority, 
                json.dumps(category_names), True, False, 1, is_evergreen, evergreen_freq, evergreen_notes
            ))
            
            idea_id = cursor.fetchone()['id']
            
            # Link to content categories
            for cat_name in category_names:
                if cat_name in categories:
                    cursor.execute("""
                        INSERT INTO calendar_idea_categories (idea_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (idea_id, categories[cat_name]))
            
            # Link to evergreen frequency category
            if evergreen_freq in frequency_categories:
                cursor.execute("""
                    INSERT INTO calendar_idea_categories (idea_id, category_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (idea_id, frequency_categories[evergreen_freq]))
            
            # Link to evergreen category
            if is_evergreen and 'Evergreen' in categories:
                cursor.execute("""
                    INSERT INTO calendar_idea_categories (idea_id, category_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (idea_id, categories['Evergreen']))
        
        cursor.connection.commit()
        print(f"Inserted {len(content_ideas)} Celtic content ideas")

def main():
    print("Populating Celtic content ideas...")
    
    try:
        populate_celtic_content_ideas()
        print("\nCeltic content ideas populated successfully!")
        print("You can now view the calendar at: http://localhost:5000/planning/posts/53/calendar/view")
        
    except Exception as e:
        print(f"Error populating Celtic content: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
