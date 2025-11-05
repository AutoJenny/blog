#!/usr/bin/env python3
"""
Setup tags and categories for Scottish Recipe Series.

Creates:
- "Scottish Recipes" category
- Required tags: "Scottish Recipes", "Traditional Food", "Seasonal Cooking"
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager

def setup_recipe_tags_categories():
    """Create recipe category and tags."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Create "Scottish Recipes" category
                cursor.execute("""
                    INSERT INTO category (name, slug, description)
                    VALUES ('Scottish Recipes', 'scottish-recipes', 'Scottish Recipe Series - traditional and seasonal Scottish dishes')
                    ON CONFLICT (slug) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description
                    RETURNING id
                """)
                
                category_result = cursor.fetchone()
                if category_result:
                    category_id = category_result['id'] if isinstance(category_result, dict) else category_result[0]
                    print(f"✅ Category 'Scottish Recipes' created/updated (ID: {category_id})")
                else:
                    # Try to get existing category
                    cursor.execute("SELECT id FROM category WHERE slug = 'scottish-recipes'")
                    existing = cursor.fetchone()
                    if existing:
                        category_id = existing['id'] if isinstance(existing, dict) else existing[0]
                        print(f"✅ Category 'Scottish Recipes' already exists (ID: {category_id})")
                    else:
                        category_id = None
                        print("⚠️  Warning: Category creation failed but no existing category found")
                
                # Create required tags
                tags = [
                    ('Scottish Recipes', 'scottish-recipes', 'Scottish Recipe Series content'),
                    ('Traditional Food', 'traditional-food', 'Traditional Scottish food and recipes'),
                    ('Seasonal Cooking', 'seasonal-cooking', 'Seasonal and traditional Scottish cooking')
                ]
                
                created_tags = []
                for tag_name, tag_slug, tag_description in tags:
                    cursor.execute("""
                        INSERT INTO tag (name, slug, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (slug) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description
                        RETURNING id
                    """, (tag_name, tag_slug, tag_description))
                    
                    tag_result = cursor.fetchone()
                    if tag_result:
                        tag_id = tag_result['id'] if isinstance(tag_result, dict) else tag_result[0]
                        created_tags.append((tag_name, tag_id))
                
                conn.commit()
                
                print(f"\n✅ Successfully created/updated tags:")
                for tag_name, tag_id in created_tags:
                    print(f"   - {tag_name} (ID: {tag_id})")
                
                return True
                
    except Exception as e:
        print(f"❌ Error setting up tags and categories: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🏷️  Setting up Scottish Recipe Series tags and categories...\n")
    
    success = setup_recipe_tags_categories()
    
    if success:
        print("\n✅ Tags and categories setup complete!")
        sys.exit(0)
    else:
        print("\n❌ Tags and categories setup failed!")
        sys.exit(1)

