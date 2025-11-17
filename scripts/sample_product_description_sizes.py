#!/usr/bin/env python3
"""
Sample product descriptions and analyze their word/character counts.
This script queries a sample of products and reports on description sizes.
"""
import sys
from pathlib import Path
import re
from html import unescape
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

def count_characters(text, include_html=False):
    """Count characters in text."""
    if not text:
        return 0
    if include_html:
        return len(text)
    else:
        # Strip HTML for character count
        clean_text = strip_html(text)
        return len(clean_text)

def analyze_product_descriptions(sample_size=20):
    """Sample products and analyze their description sizes."""
    print(f"Sampling {sample_size} products from clan_products table...")
    print("=" * 80)
    
    try:
        with db_manager.get_cursor() as cursor:
            # Get a random sample of products with descriptions
            query = """
                SELECT 
                    id,
                    sku,
                    name,
                    description,
                    short_description,
                    LENGTH(description) as desc_char_count_raw,
                    LENGTH(short_description) as short_desc_char_count_raw
                FROM clan_products
                WHERE description IS NOT NULL AND description != ''
                ORDER BY RANDOM()
                LIMIT %s
            """
            cursor.execute(query, (sample_size,))
            products = cursor.fetchall()
            
            if not products:
                print("No products with descriptions found.")
                return
            
            print(f"\nFound {len(products)} products with descriptions\n")
            
            results = []
            for product in products:
                desc = product.get('description', '')
                short_desc = product.get('short_description', '')
                
                # Calculate metrics
                desc_words = count_words(desc)
                desc_chars_raw = len(desc) if desc else 0
                desc_chars_clean = count_characters(desc, include_html=False)
                
                short_desc_words = count_words(short_desc) if short_desc else 0
                short_desc_chars_raw = len(short_desc) if short_desc else 0
                short_desc_chars_clean = count_characters(short_desc, include_html=False) if short_desc else 0
                
                # Preview description (first 100 chars, cleaned)
                desc_preview = strip_html(desc)[:100] if desc else "(empty)"
                if len(strip_html(desc)) > 100:
                    desc_preview += "..."
                
                result = {
                    'id': product['id'],
                    'sku': product['sku'],
                    'name': product['name'][:50] + "..." if len(product['name']) > 50 else product['name'],
                    'description': {
                        'words': desc_words,
                        'chars_raw': desc_chars_raw,
                        'chars_clean': desc_chars_clean,
                        'preview': desc_preview
                    },
                    'short_description': {
                        'words': short_desc_words,
                        'chars_raw': short_desc_chars_raw,
                        'chars_clean': short_desc_chars_clean
                    }
                }
                results.append(result)
            
            # Print results
            print("\n" + "=" * 80)
            print("PRODUCT DESCRIPTION SIZE ANALYSIS")
            print("=" * 80 + "\n")
            
            for i, result in enumerate(results, 1):
                print(f"Product #{i}:")
                print(f"  ID: {result['id']}")
                print(f"  SKU: {result['sku']}")
                print(f"  Name: {result['name']}")
                print(f"  Description:")
                print(f"    - Words: {result['description']['words']}")
                print(f"    - Characters (raw/with HTML): {result['description']['chars_raw']}")
                print(f"    - Characters (clean/no HTML): {result['description']['chars_clean']}")
                print(f"    - Preview: {result['description']['preview']}")
                if result['short_description']['words'] > 0:
                    print(f"  Short Description:")
                    print(f"    - Words: {result['short_description']['words']}")
                    print(f"    - Characters (raw): {result['short_description']['chars_raw']}")
                    print(f"    - Characters (clean): {result['short_description']['chars_clean']}")
                print()
            
            # Summary statistics
            print("=" * 80)
            print("SUMMARY STATISTICS")
            print("=" * 80 + "\n")
            
            desc_words_list = [r['description']['words'] for r in results]
            desc_chars_clean_list = [r['description']['chars_clean'] for r in results]
            short_desc_words_list = [r['short_description']['words'] for r in results if r['short_description']['words'] > 0]
            
            print("Description (full):")
            print(f"  Count: {len(desc_words_list)}")
            print(f"  Word count - Min: {min(desc_words_list)}, Max: {max(desc_words_list)}, Avg: {sum(desc_words_list)/len(desc_words_list):.1f}")
            print(f"  Character count (clean) - Min: {min(desc_chars_clean_list)}, Max: {max(desc_chars_clean_list)}, Avg: {sum(desc_chars_clean_list)/len(desc_chars_clean_list):.1f}")
            
            if short_desc_words_list:
                print(f"\nShort Description:")
                print(f"  Count: {len(short_desc_words_list)}")
                print(f"  Word count - Min: {min(short_desc_words_list)}, Max: {max(short_desc_words_list)}, Avg: {sum(short_desc_words_list)/len(short_desc_words_list):.1f}")
            
            # Check if size fields exist
            print("\n" + "=" * 80)
            print("CHECKING FOR EXISTING SIZE FIELDS")
            print("=" * 80 + "\n")
            
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'clan_products' 
                AND (
                    column_name LIKE '%word%' 
                    OR column_name LIKE '%char%' 
                    OR column_name LIKE '%length%' 
                    OR column_name LIKE '%size%'
                )
                ORDER BY column_name
            """)
            size_fields = cursor.fetchall()
            
            if size_fields:
                print("Existing size-related fields found in clan_products table:")
                for field in size_fields:
                    print(f"  - {field['column_name']} ({field['data_type']})")
            else:
                print("No existing size-related fields found in clan_products table.")
                print("\nSuggested fields to add:")
                print("  - description_word_count INTEGER")
                print("  - description_char_count INTEGER (clean, no HTML)")
                print("  - short_description_word_count INTEGER")
                print("  - short_description_char_count INTEGER (clean, no HTML)")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    sample_size = 20
    if len(sys.argv) > 1:
        try:
            sample_size = int(sys.argv[1])
        except ValueError:
            print(f"Invalid sample size: {sys.argv[1]}. Using default: 20")
    
    analyze_product_descriptions(sample_size)

