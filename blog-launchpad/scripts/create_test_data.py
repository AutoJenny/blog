#!/usr/bin/env python3
"""
Create test data for daily product posts with categories and images.
This will allow us to test the daily product posts functionality while the API issues are resolved.
"""

import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection

def create_test_products_with_categories():
    """Create test products with category associations for testing daily product posts."""
    
    print("🛠️ Creating Test Products with Categories")
    print("=" * 50)
    
    # Test products with realistic data and category associations
    test_products = [
        {
            'id': 999001,
            'name': 'Highland Whisky Glencairn Glass Set',
            'sku': 'TEST_WHISKY_GLASS',
            'price': '24.99',
            'image_url': 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Whisky+Glass',
            'url': 'https://clan.com/test-whisky-glass',
            'description': 'Premium crystal whisky glasses designed specifically for tasting single malt Scotch whisky. Set of 2 glasses with elegant presentation box.',
            'category_ids': json.dumps([19, 37])  # Jewellery, Homeware
        },
        {
            'id': 999002,
            'name': 'Tartan Wool Scarf - Royal Stewart',
            'sku': 'TEST_TARTAN_SCARF',
            'price': '45.00',
            'image_url': 'https://via.placeholder.com/400x400/DC143C/FFFFFF?text=Tartan+Scarf',
            'url': 'https://clan.com/test-tartan-scarf',
            'description': 'Authentic Scottish tartan scarf in Royal Stewart pattern. 100% pure wool, hand-woven in Scotland. Perfect for any occasion.',
            'category_ids': json.dumps([307, 18])  # Scarves, Gifts
        },
        {
            'id': 999003,
            'name': 'Celtic Knot Silver Pendant',
            'sku': 'TEST_CELTIC_PENDANT',
            'price': '89.99',
            'image_url': 'https://via.placeholder.com/400x400/C0C0C0/000000?text=Celtic+Pendant',
            'url': 'https://clan.com/test-celtic-pendant',
            'description': 'Handcrafted silver pendant featuring intricate Celtic knotwork design. Comes with 18-inch sterling silver chain. Made in Scotland.',
            'category_ids': json.dumps([19, 92])  # Jewellery, Necklaces & Pendants
        },
        {
            'id': 999004,
            'name': 'Scottish Heather Honey',
            'sku': 'TEST_HEATHER_HONEY',
            'price': '12.50',
            'image_url': 'https://via.placeholder.com/400x400/FFD700/000000?text=Heather+Honey',
            'url': 'https://clan.com/test-heather-honey',
            'description': 'Pure Scottish heather honey collected from the Highlands. 340g jar with traditional tartan label. A taste of Scotland.',
            'category_ids': json.dumps([18, 83])  # Gifts, Dining
        },
        {
            'id': 999005,
            'name': 'Highland Games Caber Toss Game',
            'sku': 'TEST_CABER_TOSS',
            'price': '35.00',
            'image_url': 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Caber+Toss',
            'url': 'https://clan.com/test-caber-toss',
            'description': 'Miniature caber toss game for indoor fun. Wooden caber and target board. Perfect for Scottish-themed parties and events.',
            'category_ids': json.dumps([86, 18])  # Toys & Books, Gifts
        }
    ]
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Insert test products
            for product in test_products:
                cur.execute("""
                    INSERT INTO clan_products (id, name, sku, price, image_url, url, description, category_ids)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        sku = EXCLUDED.sku,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        url = EXCLUDED.url,
                        description = EXCLUDED.description,
                        category_ids = EXCLUDED.category_ids
                """, (
                    product['id'],
                    product['name'],
                    product['sku'],
                    product['price'],
                    product['image_url'],
                    product['url'],
                    product['description'],
                    product['category_ids']
                ))
            
            conn.commit()
            print(f"✅ Created {len(test_products)} test products with categories")
            
            # Show what was created
            for product in test_products:
                categories = json.loads(product['category_ids'])
                print(f"  - {product['name']} (£{product['price']}) - Categories: {categories}")
                
    except Exception as e:
        print(f"❌ Error creating test products: {e}")
        return False
    
    return True

def create_test_categories():
    """Create test categories if they don't exist."""
    
    print("\n🏷️ Creating Test Categories")
    print("=" * 50)
    
    test_categories = [
        {'id': 19, 'name': 'Jewellery', 'level': 2, 'parent_id': 267, 'description': 'Choose something special from our broad selection of jewellery.'},
        {'id': 37, 'name': 'Homeware', 'level': 2, 'parent_id': 267, 'description': 'From our traditional tartan tableware to gorgeous glassware.'},
        {'id': 307, 'name': 'Scarves', 'level': 2, 'parent_id': 300, 'description': 'Beautiful scarves in various tartans and styles.'},
        {'id': 18, 'name': 'Gifts', 'level': 2, 'parent_id': 267, 'description': 'Whether you\'re looking for a gift or something to treat yourself.'},
        {'id': 92, 'name': 'Necklaces & Pendants', 'level': 3, 'parent_id': 19, 'description': 'Elegant necklaces and pendants.'},
        {'id': 83, 'name': 'Dining', 'level': 3, 'parent_id': 37, 'description': 'Dining accessories and tableware.'},
        {'id': 86, 'name': 'Toys & Books', 'level': 3, 'parent_id': 18, 'description': 'Toys and books for children and adults.'}
    ]
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Insert test categories
            for category in test_categories:
                cur.execute("""
                    INSERT INTO clan_categories (id, name, level, parent_id, description)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        level = EXCLUDED.level,
                        parent_id = EXCLUDED.parent_id,
                        description = EXCLUDED.description
                """, (
                    category['id'],
                    category['name'],
                    category['level'],
                    category['parent_id'],
                    category['description']
                ))
            
            conn.commit()
            print(f"✅ Created {len(test_categories)} test categories")
            
            # Show what was created
            for category in test_categories:
                print(f"  - {category['name']} (Level {category['level']}, ID: {category['id']})")
                
    except Exception as e:
        print(f"❌ Error creating test categories: {e}")
        return False
    
    return True

def main():
    """Main function to create test data."""
    print("🚀 Creating Test Data for Daily Product Posts")
    print("=" * 60)
    
    # Create test categories first
    categories_created = create_test_categories()
    
    # Create test products with categories
    products_created = create_test_products_with_categories()
    
    if categories_created and products_created:
        print("\n✅ Test data created successfully!")
        print("\nNow you can test the daily product posts with:")
        print("1. Products that have real category associations")
        print("2. Products with unique placeholder images")
        print("3. Complete category hierarchy")
        print("\nVisit: http://localhost:5001/daily-product-posts")
    else:
        print("\n❌ Failed to create test data")

if __name__ == "__main__":
    main()
