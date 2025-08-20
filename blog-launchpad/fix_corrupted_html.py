#!/usr/bin/env python3
"""
Fix corrupted HTML content in the database that's causing live blog posts to display as blank.
This script cleans up malformed HTML tags and nested paragraph tags.
"""

import re
import psycopg2
import psycopg2.extras
from datetime import datetime

def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        database="blog",
        user="postgres",
        password="postgres"
    )

def clean_html_content(content):
    """Clean corrupted HTML content"""
    if not content:
        return content
    
    content_str = str(content)
    
    print(f"Original content length: {len(content_str)}")
    print(f"First 200 chars: {content_str[:200]}")
    
    # Remove corrupted HTML tags and entities
    content_str = re.sub(r'</html', '', content_str)  # Remove incomplete </html
    content_str = re.sub(r'<html[^>]*>', '', content_str)  # Remove <html tags
    content_str = re.sub(r'<!DOCTYPE[^>]*>', '', content_str)  # Remove DOCTYPE
    
    # Fix nested paragraph tags: <p><p>content</p></p> -> <p>content</p>
    content_str = re.sub(r'<p>\s*<p>', '<p>', content_str)
    content_str = re.sub(r'</p>\s*</p>', '</p>', content_str)
    
    # Remove any remaining HTML structure tags
    content_str = re.sub(r'<head[^>]*>.*?</head>', '', content_str, flags=re.DOTALL)
    content_str = re.sub(r'<body[^>]*>', '', content_str)
    content_str = re.sub(r'</body>', '', content_str)
    
    # Clean up HTML entities
    content_str = re.sub(r'&lt;', '<', content_str)
    content_str = re.sub(r'&gt;', '>', content_str)
    
    # Clean up extra whitespace
    content_str = re.sub(r'\s+', ' ', content_str).strip()
    
    print(f"Cleaned content length: {len(content_str)}")
    print(f"First 200 chars after cleaning: {content_str[:200]}")
    
    return content_str

def fix_post_sections(post_id):
    """Fix corrupted HTML in post sections"""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all sections for the post
        cur.execute("""
            SELECT id, section_heading, draft, polished
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        
        sections = cur.fetchall()
        print(f"Found {len(sections)} sections for post {post_id}")
        
        fixed_count = 0
        for section in sections:
            section_id = section['id']
            section_heading = section['section_heading']
            
            print(f"\n--- Section {section_id}: {section_heading} ---")
            
            # Check and fix draft content
            if section.get('draft'):
                original_draft = section['draft']
                cleaned_draft = clean_html_content(original_draft)
                if cleaned_draft != original_draft:
                    print(f"Fixing draft content for section {section_id}")
                    cur.execute("""
                        UPDATE post_section 
                        SET draft = %s
                        WHERE id = %s
                    """, (cleaned_draft, section_id))
                    fixed_count += 1
            
            # Check and fix polished content
            if section.get('polished'):
                original_polished = section['polished']
                cleaned_polished = clean_html_content(original_polished)
                if cleaned_polished != original_polished:
                    print(f"Fixing polished content for section {section_id}")
                    cur.execute("""
                        UPDATE post_section 
                        SET polished = %s
                        WHERE id = %s
                    """, (cleaned_polished, section_id))
                    fixed_count += 1
        
        if fixed_count > 0:
            conn.commit()
            print(f"\n✅ Fixed {fixed_count} corrupted content fields")
        else:
            print("\n✅ No corrupted content found")
        
        return fixed_count

def main():
    """Main function"""
    print("🔧 HTML Content Corruption Fixer")
    print("=" * 50)
    
    # Fix post 53 specifically
    post_id = 53
    print(f"Fixing corrupted HTML in post {post_id}")
    
    try:
        fixed_count = fix_post_sections(post_id)
        
        if fixed_count > 0:
            print(f"\n🎉 Successfully fixed {fixed_count} corrupted content fields!")
            print("The post should now display correctly on clan.com")
            print("\nNext steps:")
            print("1. Republish the post: curl -X POST 'http://localhost:5001/api/publish/53'")
            print("2. Check the live blog: https://clan.com/blog/the-art-of-scottish-storytelling-oral-traditions-and-modern-literature-53-1755653000")
        else:
            print("\n✅ No corrupted content found - post should be working correctly")
            
    except Exception as e:
        print(f"❌ Error fixing corrupted HTML: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
