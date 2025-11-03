#!/usr/bin/env python3
"""Test API product format"""
import sys
import os
sys.path.append('blog-clan-api')
from clan_client import ClanAPIClient

client = ClanAPIClient()
result = client.make_api_request('/getProducts', {'limit': 5, 'offset': 0})
print(f"Success: {result.get('success')}")
products = result.get('data', [])
print(f"Products returned: {len(products)}")
if products:
    print(f"\nFirst product type: {type(products[0])}")
    print(f"First product: {products[0]}")
    if isinstance(products[0], list):
        print(f"First product length: {len(products[0])}")
        print(f"SKU (index 1): {products[0][1] if len(products[0]) > 1 else 'N/A'}")

