#!/usr/bin/env python3
"""
Fix corrupted section content in the database by removing DOCTYPE and HTML document tags.
This script cleans up sections that have full HTML documents instead of plain text content.
"""

import psycopg2
import psycopg2.extras
import re
import os
import sys

# Add the parent directory to the path so we can import from blog-core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(
        dbname="blog",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

def clean_html_content(content):
    """Clean HTML content by removing full HTML document structure"""
    if not content:
        return content
    
    content_str = str(content)
    
    # Check if this is a full HTML document (including HTML-encoded versions)
    if ('<!DOCTYPE' in content_str or '<html' in content_str or 
            '<head>' in content_str or '<body>' in content_str or
            '&lt;/html' in content_str or '&lt;html' in content_str or
            '&lt;head' in content_str or '&lt;body' in content_str or
            '</html' in content_str or '</head' in content_str or '</body' in content_str):
        
        print(f"  🔍 Found HTML document, cleaning...")
        print(f"  Original length: {len(content_str)}")
        
        # Strip full HTML document structure (including HTML-encoded versions)
        cleaned = re.sub(r'<!DOCTYPE[^>]*>', '', content_str)
        cleaned = re.sub(r'<html[^>]*>', '', cleaned)
        cleaned = re.sub(r'</html>', '', cleaned)
        cleaned = re.sub(r'<head[^>]*>.*?</head>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<body[^>]*>', '', cleaned)
        cleaned = re.sub(r'</body>', '', cleaned)
        
        # Also clean HTML-encoded versions
        cleaned = re.sub(r'&lt;!DOCTYPE[^&]*&gt;', '', cleaned)
        cleaned = re.sub(r'&lt;html[^&]*&gt;', '', cleaned)
        cleaned = re.sub(r'&lt;/html&gt;', '', cleaned)
        cleaned = re.sub(r'&lt;head[^&]*&gt;.*?&lt;/head&gt;', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'&lt;body[^&]*&gt;', '', cleaned)
        cleaned = re.sub(r'&lt;/body&gt;', '', cleaned)
        
        # Clean up truncated HTML tags at the end
        cleaned = re.sub(r'</ht\s*$', '', cleaned)  # Remove truncated </ht at end
        cleaned = re.sub(r'</h\s*$', '', cleaned)   # Remove truncated </h at end
        cleaned = re.sub(r'</\s*$', '', cleaned)    # Remove truncated </ at end
        
        # Remove any remaining HTML tags but keep text content
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        print(f"  Cleaned length: {len(cleaned)}")
        print(f"  Cleaned preview: {cleaned[:100]}...")
        
        return cleaned
    else:
        return content

def fix_corrupted_sections():
    """Fix all corrupted sections in the database"""
    print("🔧 Fixing corrupted section content in database...")
    
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get all sections with content
                cur.execute("""
                    SELECT id, post_id, section_heading, section_description, ideas_to_include, 
                           facts_to_include, highlighting, image_concepts, image_prompts, 
                           image_meta_descriptions, image_captions, draft, polished 
                    FROM post_section 
                    WHERE section_description IS NOT NULL OR ideas_to_include IS NOT NULL OR 
                          facts_to_include IS NOT NULL OR highlighting IS NOT NULL OR 
                          image_concepts IS NOT NULL OR image_prompts IS NOT NULL OR 
                          image_meta_descriptions IS NOT NULL OR image_captions IS NOT NULL OR 
                          draft IS NOT NULL OR polished IS NOT NULL
                    ORDER BY post_id, id
                """)
                
                sections = cur.fetchall()
                print(f"Found {len(sections)} sections to check")
                
                corrupted_count = 0
                fixed_count = 0
                
                for section in sections:
                    section_id = section['id']
                    post_id = section['post_id']
                    heading = section['section_heading']
                    
                    print(f"\n--- Section {section_id} (Post {post_id}): {heading} ---")
                    
                    # Check each content field
                    fields_to_check = ['section_description', 'ideas_to_include', 'facts_to_include', 
                                     'highlighting', 'image_concepts', 'image_prompts', 
                                     'image_meta_descriptions', 'image_captions', 'draft', 'polished']
                    needs_update = False
                    update_data = {}
                    
                    for field in fields_to_check:
                        field_value = section.get(field)
                        if field_value:
                            cleaned_value = clean_html_content(field_value)
                            if cleaned_value != field_value:
                                update_data[field] = cleaned_value
                                needs_update = True
                                corrupted_count += 1
                    
                    # Update the section if needed
                    if needs_update:
                        print(f"  🔧 Updating section {section_id}...")
                        
                        # Build update query
                        set_clauses = []
                        values = []
                        
                        for field, value in update_data.items():
                            set_clauses.append(f"{field} = %s")
                            values.append(value)
                        
                        values.append(section_id)
                        
                        query = f"""
                            UPDATE post_section 
                            SET {', '.join(set_clauses)}
                            WHERE id = %s
                        """
                        
                        cur.execute(query, values)
                        fixed_count += 1
                        print(f"  ✅ Section {section_id} updated successfully")
                    else:
                        print(f"  ✅ Section {section_id} is clean")
                
                # Commit all changes
                conn.commit()
                
                print(f"\n🎉 Database cleanup complete!")
                print(f"📊 Summary:")
                print(f"  - Sections checked: {len(sections)}")
                print(f"  - Corrupted fields found: {corrupted_count}")
                print(f"  - Sections fixed: {fixed_count}")
                
                if corrupted_count > 0:
                    print(f"\n✅ All corrupted content has been cleaned up!")
                    print(f"   The sections should now display properly without DOCTYPE tags.")
                else:
                    print(f"\n✅ No corrupted content found - all sections are clean!")
                
    except Exception as e:
        print(f"❌ Error fixing corrupted sections: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_corrupted_sections()
