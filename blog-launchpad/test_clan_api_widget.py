#!/usr/bin/env python3
"""
Test script to verify clan.com API integration for cross-promotion widgets
"""

import requests
import json

def test_clan_api_endpoints():
    """Test all clan.com API endpoints to ensure they're working"""
    
    print("🔍 Testing Clan.com API Endpoints...")
    print("=" * 50)
    
    # Test 1: Get Products
    print("\n1️⃣ Testing /getProducts endpoint...")
    try:
        response = requests.get("https://clan.com/clan/api/getProducts?limit=3", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Got {len(data.get('data', []))} products")
            print(f"   First product: {data['data'][0][0]}")  # title
            print(f"   SKU: {data['data'][0][1]}")
            print(f"   URL: {data['data'][0][2]}")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Get Product Data
    print("\n2️⃣ Testing /getProductData endpoint...")
    try:
        response = requests.get("https://clan.com/clan/api/getProductData?sku=sr_esssw_tartan_sash_wool", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Got product data")
            print(f"   Title: {data['data']['title']}")
            print(f"   Price: £{data['data']['price']}")
            print(f"   Image: {data['data']['image']}")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Get Category Tree
    print("\n3️⃣ Testing /getCategoryTree endpoint...")
    try:
        response = requests.get("https://clan.com/clan/api/getCategoryTree", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Got category tree with {len(data.get('data', []))} main categories")
            print(f"   First category: {data['data'][0]['name']}")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API Testing Complete!")

def test_widget_data_mapping():
    """Test the data mapping logic used in the widget"""
    
    print("\n🔧 Testing Widget Data Mapping...")
    print("=" * 50)
    
    # Simulate clan.com API response
    clan_api_response = {
        "success": True,
        "data": [
            ["Essential Tartan Sash", "sr_esssw_tartan_sash_wool", "https://clan.com/essential-scotweb-tartan-sash", "A lightweight tartan sash that will add a touch of sophistication to any evening outfit"],
            ["Clan Crest Wall Plaque", "sr_scres_plaque", "https://clan.com/clan-crest-wall-plaque", "Impress your visitors by proudly displaying your clan roots."],
            ["The Balmoral Kilt", "sr_swhdr_eightyardkilt_flashes", "https://clan.com/the-balmoral-kilt-traditional-8-yard-kilt-flashes", "Our best selling classic kilt is made in Scotland by experienced kiltmaking experts."]
        ]
    }
    
    print("📊 Original Clan.com API Response:")
    print(json.dumps(clan_api_response, indent=2))
    
    # Map to widget format (simulating JavaScript logic)
    mapped_products = []
    for item in clan_api_response['data']:
        product = {
            "name": item[0],           # title
            "sku": item[1],            # sku
            "url": item[2],            # product_url
            "description": item[3],    # description
            "image_url": "https://static.clan.com/media/catalog/product/cache/5/image/9df78eab33525d08d6e5fb8d27136e95/e/s/essential.jpg",
            "price": "43"
        }
        mapped_products.append(product)
    
    print("\n🔄 Mapped to Widget Format:")
    print(json.dumps(mapped_products, indent=2))
    
    print("\n✅ Data mapping test complete!")

if __name__ == "__main__":
    test_clan_api_endpoints()
    test_widget_data_mapping()

