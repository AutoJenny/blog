#!/usr/bin/env python3
"""
Test Clan.com API integration to check for image and category data.
This script tests the API endpoints that should provide the missing data.
"""

import requests
import json
import sys
from datetime import datetime

def test_clan_api():
    """Test Clan.com API endpoints for image and category data."""
    
    base_url = "https://clan.com/clan/api"
    
    print("🔍 Testing Clan.com API Integration")
    print("=" * 50)
    
    # Test 1: Get a single product with images and categories
    print("\n1. Testing single product with images and categories...")
    try:
        response = requests.get(f"{base_url}/getProductData", params={
            'sku': 'sr_swhdr_eightyardkilt_flashes',  # Example SKU from the PHP script
            'all_images': 1,
            'include_categories': 1
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"Success: {data.get('success', 'Unknown')}")
            
            if data.get('success'):
                product = data.get('data', {})
                print(f"Product: {product.get('name', 'Unknown')}")
                print(f"SKU: {product.get('sku', 'Unknown')}")
                
                # Check for images
                images = product.get('images', [])
                print(f"Images found: {len(images)}")
                if images:
                    print("Sample image URLs:")
                    for i, img in enumerate(images[:3]):
                        print(f"  {i+1}. {img}")
                
                # Check for categories
                categories = product.get('categories', [])
                print(f"Categories found: {len(categories)}")
                if categories:
                    print("Sample categories:")
                    for i, cat in enumerate(categories[:3]):
                        print(f"  {i+1}. {cat}")
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    
    # Test 2: Get category tree
    print("\n2. Testing category tree...")
    try:
        response = requests.get(f"{base_url}/getCategoryTree", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"Success: {data.get('success', 'Unknown')}")
            
            if data.get('success'):
                categories = data.get('data', [])
                print(f"Categories found: {len(categories)}")
                if categories:
                    print("Sample categories:")
                    for i, cat in enumerate(categories[:5]):
                        print(f"  {i+1}. {cat.get('name', 'Unknown')} (ID: {cat.get('id', 'Unknown')})")
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    
    # Test 3: Get multiple products (basic)
    print("\n3. Testing multiple products...")
    try:
        response = requests.get(f"{base_url}/getProducts", params={'limit': 5}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"Success: {data.get('success', 'Unknown')}")
            
            if data.get('success'):
                products = data.get('data', [])
                print(f"Products found: {len(products)}")
                if products:
                    print("Sample products:")
                    for i, product in enumerate(products[:3]):
                        print(f"  {i+1}. {product.get('name', 'Unknown')} (SKU: {product.get('sku', 'Unknown')})")
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Conclusion:")
    print("If the API tests succeed, we can:")
    print("1. Import real product images using all_images=1")
    print("2. Import product categories using include_categories=1")
    print("3. Update the daily product posts to show real data")
    print("4. Display product categories in the UI")

if __name__ == "__main__":
    test_clan_api()
