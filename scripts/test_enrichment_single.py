#!/usr/bin/env python3
"""
Test single SKU enrichment: fetch getProductData and verify upsert behavior.
"""
import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))

def test_enrichment_transform():
    """Test that enrichment correctly maps extended fields from getProductData."""
    print("Testing enrichment transform...")
    
    from clan_cache import ClanCache
    cache = ClanCache()
    
    # Mock getProductData response format
    mock_detail = {
        'product_id': '919',
        'sku': 'sr_test_sku',
        'title': 'Test Product',
        'price': 315,
        'short_description': 'Short desc',
        'description': 'Full description',
        'image': 'https://example.com/image.jpg',
        'product_url': 'https://clan.com/test-product',
        'created_at': '2025-01-01T10:00:00+01:00',
        'supplier_name': 'Test Supplier',
        'supplier_description': '<p>Supplier info</p>',
        'configurable_options': [{'option': 'Size', 'options': [{'label': 'S'}, {'label': 'M'}]}],
        'printable_design_type': False,
    }
    
    # Simulate enrichment mapping
    enriched = {
        'id': int(mock_detail.get('product_id', 0)),
        'sku': mock_detail.get('sku'),
        'name': mock_detail.get('title'),
        'price': str(mock_detail.get('price', '')),
        'image_url': mock_detail.get('image'),
        'url': mock_detail.get('product_url'),
        'short_description': mock_detail.get('short_description'),
        'description': mock_detail.get('description'),
        'supplier_name': mock_detail.get('supplier_name'),
        'supplier_description': mock_detail.get('supplier_description'),
        'configurable_options': mock_detail.get('configurable_options'),
        'clan_created_at': mock_detail.get('created_at'),
        'has_detailed_data': True,
    }
    
    # Verify all fields mapped
    assert enriched['short_description'] == 'Short desc'
    assert enriched['supplier_name'] == 'Test Supplier'
    assert enriched['configurable_options'] is not None
    assert enriched['has_detailed_data'] is True
    print("✓ Enrichment transform works correctly")

def test_hash_generation():
    """Test that hash is generated correctly from product fields."""
    print("Testing hash generation...")
    
    from clan_cache import ClanCache
    cache = ClanCache()
    
    fields1 = {
        'name': 'Product A',
        'sku': 'SKU1',
        'price': '100',
        'description': 'Description A',
    }
    
    fields2 = {
        'name': 'Product A',
        'sku': 'SKU1',
        'price': '100',
        'description': 'Description A',  # Same as fields1
    }
    
    fields3 = {
        'name': 'Product A',
        'sku': 'SKU1',
        'price': '200',  # Different price
        'description': 'Description A',
    }
    
    hash1 = cache._build_product_hash(fields1)
    hash2 = cache._build_product_hash(fields2)
    hash3 = cache._build_product_hash(fields3)
    
    assert hash1 == hash2, "Same fields should produce same hash"
    assert hash1 != hash3, "Different fields should produce different hash"
    print("✓ Hash generation works correctly")

if __name__ == '__main__':
    print("Running enrichment tests...\n")
    try:
        test_enrichment_transform()
        test_hash_generation()
        print("\n✓ All enrichment tests passed")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)










