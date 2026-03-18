#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clan_publisher import ClanPublisher
from app import get_db_conn

def debug_sections():
    """Debug why sections_list is empty when passed to process_images"""
    
    # Test with post ID 53
    post_id = 53
    
    print(f"=== DEBUGGING SECTIONS FOR POST {post_id} ===")
    
    # Load sections from DB
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id, section_heading, polished, draft FROM post_section WHERE post_id = %s ORDER BY id', (post_id,))
    db_sections = cursor.fetchall()
    
    sections_list = []
    for row in db_sections:
        section_dict = {
            'id': row[0],
            'section_heading': row[1],
            'polished': row[2],
            'draft': row[3]
        }
        sections_list.append(section_dict)
    
    print(f"Loaded {len(sections_list)} sections from DB")
    print(f"sections_list type: {type(sections_list)}")
    print(f"sections_list content: {sections_list}")
    
    # Test process_images call
    publisher = ClanPublisher()
    print(f"\nCalling process_images with {len(sections_list)} sections...")
    
    # Create a dummy post dict
    post_data = {'id': post_id}
    
    try:
        uploaded_images = publisher.process_images(post_data, sections_list)
        print(f"process_images returned: {uploaded_images}")
    except Exception as e:
        print(f"Error in process_images: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sections()





