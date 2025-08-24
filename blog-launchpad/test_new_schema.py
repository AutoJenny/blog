#!/usr/bin/env python3
"""
Test script for the new social media database schema
"""

import psycopg2
import json
from psycopg2.extras import RealDictCursor

def test_new_schema():
    """Test the new database schema by retrieving and displaying data"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="blog",
            user="postgres",
            password=""
        )
        
        print("✅ Connected to database successfully")
        
        # Test 1: Get Facebook platform info
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT name, display_name, development_status, description 
                FROM platforms 
                WHERE name = 'facebook'
            """)
            platform = cur.fetchone()
            
            if platform:
                print(f"\n📱 PLATFORM: {platform['display_name']}")
                print(f"   Status: {platform['development_status']}")
                print(f"   Description: {platform['description']}")
            else:
                print("❌ Facebook platform not found")
                return
        
        # Test 2: Get channel types
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT name, display_name, content_type, media_support
                FROM channel_types 
                ORDER BY display_order
            """)
            channels = cur.fetchall()
            
            print(f"\n📺 CHANNELS ({len(channels)} found):")
            for channel in channels:
                print(f"   • {channel['display_name']} ({channel['content_type']})")
                print(f"     Media: {', '.join(channel['media_support'])}")
        
        # Test 3: Get platform capabilities
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT capability_type, capability_name, capability_value, unit, description
                FROM platform_capabilities 
                WHERE platform_id = 1
                ORDER BY display_order
            """)
            capabilities = cur.fetchall()
            
            print(f"\n🔧 PLATFORM CAPABILITIES ({len(capabilities)} found):")
            for cap in capabilities:
                print(f"   • {cap['capability_name']}: {cap['capability_value']} {cap['unit'] or ''}")
                print(f"     Type: {cap['capability_type']} - {cap['description']}")
        
        # Test 4: Get channel requirements for Feed Post
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT cr.requirement_category, cr.requirement_key, cr.requirement_value, 
                       cr.unit, cr.description, rc.display_name as category_display
                FROM channel_requirements cr
                JOIN requirement_categories rc ON cr.requirement_category = rc.name
                JOIN channel_types ct ON cr.channel_type_id = ct.id
                WHERE cr.platform_id = 1 AND ct.name = 'feed_post'
                ORDER BY cr.display_order
            """)
            requirements = cur.fetchall()
            
            print(f"\n📋 FEED POST REQUIREMENTS ({len(requirements)} found):")
            for req in requirements:
                print(f"   • {req['category_display']}: {req['requirement_key']}")
                print(f"     Value: {req['requirement_value']} {req['unit'] or ''}")
                print(f"     Description: {req['description']}")
        
        # Test 5: Get process configurations
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT pc.config_category, pc.config_key, pc.config_value, pc.description,
                       cc.display_name as category_display
                FROM process_configurations pc
                JOIN config_categories cc ON pc.config_category = cc.name
                JOIN content_processes cp ON pc.process_id = cp.id
                WHERE cp.process_name = 'facebook_feed_post'
                ORDER BY pc.display_order
            """)
            configs = cur.fetchall()
            
            print(f"\n⚙️ FEED POST CONFIGURATIONS ({len(configs)} found):")
            for config in configs:
                print(f"   • {config['category_display']}: {config['config_key']}")
                print(f"     Value: {config['config_value']}")
                print(f"     Description: {config['description']}")
        
        # Test 6: Get platform channel support
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT ct.display_name, pcs.development_status, pcs.priority, pcs.notes
                FROM platform_channel_support pcs
                JOIN channel_types ct ON pcs.channel_type_id = ct.id
                WHERE pcs.platform_id = 1
                ORDER BY pcs.priority
            """)
            support = cur.fetchall()
            
            print(f"\n🚀 PLATFORM CHANNEL SUPPORT ({len(support)} found):")
            for s in support:
                print(f"   • {s['display_name']}: {s['development_status']} (Priority: {s['priority']})")
                print(f"     Notes: {s['notes']}")
        
        print("\n✅ All database tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_new_schema()
