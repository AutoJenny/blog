#!/usr/bin/env python3
"""
Populate description size fields (word/character counts) for all products in clan_products table.
This script calculates and stores the counts for all existing products.
"""
import sys
from pathlib import Path
import re
from html.parser import HTMLParser

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

class HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ' '.join(self.text)

def strip_html(html_text):
    """Strip HTML tags from text."""
    if not html_text:
        return ""
    s = HTMLStripper()
    s.feed(html_text)
    return s.get_text().strip()

def count_words(text):
    """Count words in text (handles HTML and plain text)."""
    if not text:
        return 0
    # Strip HTML if present
    clean_text = strip_html(text)
    # Split on whitespace and count non-empty words
    words = [w for w in re.split(r'\s+', clean_text) if w.strip()]
    return len(words)

def count_characters(text):
    """Count characters in text (HTML stripped)."""
    if not text:
        return 0
    # Strip HTML for character count
    clean_text = strip_html(text)
    return len(clean_text)

def populate_all_products():
    """Populate description size fields for all products."""
    print("Populating description size fields for all products...")
    print("=" * 80)
    
    try:
        with db_manager.get_cursor() as cursor:
            # First, ensure the columns exist
            print("Ensuring columns exist...")
            cursor.execute("""
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS description_word_count INTEGER
            """)
            cursor.execute("""
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS description_char_count INTEGER
            """)
            cursor.execute("""
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS short_description_word_count INTEGER
            """)
            cursor.execute("""
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS short_description_char_count INTEGER
            """)
            print("✓ Columns verified/created\n")
            
            # Get all products
            print("Fetching all products...")
            cursor.execute("""
                SELECT id, sku, name, description, short_description
                FROM clan_products
                ORDER BY id
            """)
            products = cursor.fetchall()
            
            total = len(products)
            print(f"Found {total} products to process\n")
            
            if total == 0:
                print("No products found.")
                return
            
            # Process in batches
            updated = 0
            batch_size = 100
            
            for i, product in enumerate(products, 1):
                desc = product.get('description', '')
                short_desc = product.get('short_description', '')
                
                # Calculate metrics
                desc_words = count_words(desc)
                desc_chars = count_characters(desc)
                short_desc_words = count_words(short_desc) if short_desc else 0
                short_desc_chars = count_characters(short_desc) if short_desc else 0
                
                # Update the product
                cursor.execute("""
                    UPDATE clan_products
                    SET description_word_count = %s,
                        description_char_count = %s,
                        short_description_word_count = %s,
                        short_description_char_count = %s
                    WHERE id = %s
                """, (desc_words, desc_chars, short_desc_words, short_desc_chars, product['id']))
                
                updated += 1
                
                # Progress update every batch_size products
                if i % batch_size == 0:
                    print(f"Processed {i}/{total} products...")
            
            # Commit all changes
            cursor.connection.commit()
            
            print("\n" + "=" * 80)
            print(f"✓ Successfully updated {updated} products")
            print("=" * 80)
            
            # Show summary statistics
            print("\nSummary Statistics:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(description_word_count) as with_desc_counts,
                    COUNT(short_description_word_count) as with_short_desc_counts,
                    AVG(description_word_count) as avg_desc_words,
                    MIN(description_word_count) as min_desc_words,
                    MAX(description_word_count) as max_desc_words,
                    AVG(description_char_count) as avg_desc_chars,
                    AVG(short_description_word_count) as avg_short_desc_words
                FROM clan_products
            """)
            stats = cursor.fetchone()
            
            print(f"  Total products: {stats['total']}")
            print(f"  Products with description counts: {stats['with_desc_counts']}")
            print(f"  Products with short description counts: {stats['with_short_desc_counts']}")
            if stats['avg_desc_words']:
                print(f"  Average description words: {stats['avg_desc_words']:.1f}")
                print(f"  Description words range: {stats['min_desc_words']} - {stats['max_desc_words']}")
                print(f"  Average description characters: {stats['avg_desc_chars']:.1f}")
            if stats['avg_short_desc_words']:
                print(f"  Average short description words: {stats['avg_short_desc_words']:.1f}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = populate_all_products()
    sys.exit(0 if success else 1)

