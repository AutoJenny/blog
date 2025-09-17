#!/usr/bin/env python3
"""
Test script to import a few products with images and categories from Clan.com API
This will help us verify the API is working and test the data structure.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection

def test_clan_api_direct():
    """Test Clan.com API directly to see what data is available."""
    
    print("🔍 Testing Clan.com API Direct Connection")
    print("=" * 50)
    
    # Test with a known SKU from our database
    test_skus = [
        'sr_swhdr_eightyardkilt_flashes',
        'sr_swhdr_jacoutfitboys', 
        'sr_wscot_CLA_G014AH'
    ]
    
    for sku in test_skus:
        print(f"\nTesting SKU: {sku}")
        
        try:
            # Try the main API
            response = requests.get('https://clan.com/clan/api/getProductData', params={
                'sku': sku,
                'all_images': 1,
                'include_categories': 1
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Main API Success: {data.get('success')}")
                
                if data.get('success') and data.get('data'):
                    product = data['data']
                    print(f"  Product: {product.get('title', 'Unknown')}")
                    print(f"  Images: {len(product.get('images', []))}")
                    print(f"  Categories: {len(product.get('categories', []))}")
                    
                    # Show sample data
                    if product.get('images'):
                        print(f"  Sample image: {product['images'][0]}")
                    if product.get('categories'):
                        print(f"  Sample category: {product['categories'][0]}")
                        
                    return True
                else:
                    print(f"  API Error: {data.get('message')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            
            # Try fallback API
            try:
                print("  Trying fallback API...")
                response = requests.get('https://bast-clan.hotcheck.co.uk/clan/api/getProductData', params={
                    'sku': sku,
                    'all_images': 1,
                    'include_categories': 1
                }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Fallback API Success: {data.get('success')}")
                    
                    if data.get('success') and data.get('data'):
                        product = data['data']
                        print(f"  Product: {product.get('title', 'Unknown')}")
                        print(f"  Images: {len(product.get('images', []))}")
                        print(f"  Categories: {len(product.get('categories', []))}")
                        return True
                else:
                    print(f"❌ Fallback HTTP Error: {response.status_code}")
                    
            except Exception as e2:
                print(f"❌ Fallback Connection Error: {e2}")
    
    return False

def create_test_products():
    """Create a few test products with real data for testing."""
    
    print("\n🛠️ Creating Test Products with Real Data")
    print("=" * 50)
    
    # Test products with known good data
    test_products = [
        {
            'clan_product_id': 'TEST001',
            'name': 'Test Highland Kilt',
            'description': 'A beautiful traditional Highland kilt for testing purposes.',
            'category': 'Kilts & Highlandwear',
            'price': 299.99,
            'image_url': 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Test+Kilt',
            'product_url': 'https://clan.com/test-highland-kilt',
            'is_active': True
        },
        {
            'clan_product_id': 'TEST002', 
            'name': 'Test Tartan Scarf',
            'description': 'A warm tartan scarf perfect for Scottish weather.',
            'category': 'Scarves',
            'price': 45.00,
            'image_url': 'https://via.placeholder.com/400x400/DC143C/FFFFFF?text=Test+Scarf',
            'product_url': 'https://clan.com/test-tartan-scarf',
            'is_active': True
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
                    ON CONFLICT (sku) DO UPDATE SET
                        name = EXCLUDED.name,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        url = EXCLUDED.url,
                        description = EXCLUDED.description,
                        category_ids = EXCLUDED.category_ids
                """, (
                    product['clan_product_id'],
                    product['name'],
                    product['clan_product_id'],
                    product['price'],
                    product['image_url'],
                    product['product_url'],
                    product['description'],
                    json.dumps([product['category']])  # Store category as JSON
                ))
            
            conn.commit()
            print(f"✅ Created {len(test_products)} test products")
            
            # Show what was created
            for product in test_products:
                print(f"  - {product['name']} (£{product['price']}) - {product['category']}")
                
    except Exception as e:
        print(f"❌ Error creating test products: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Clan.com API Test and Product Import")
    print("=" * 60)
    
    # Test 1: Direct API connection
    api_working = test_clan_api_direct()
    
    if not api_working:
        print("\n⚠️ API connection failed, creating test products instead...")
        create_test_products()
    
    print("\n✅ Test complete!")
    print("\nNext steps:")
    print("1. Check if API is working with real data")
    print("2. If not, use test products for development")
    print("3. Update daily product posts to use available data")

if __name__ == "__main__":
    main()
