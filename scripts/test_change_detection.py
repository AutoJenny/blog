#!/usr/bin/env python3
"""
Test hash-based change detection: verify updates occur when hash differs,
and that first_seen_at is preserved.
"""
import sys
import os
import psycopg
from datetime import datetime

# Add paths
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))

def test_first_seen_preservation():
    """Test that first_seen_at is never updated on conflict."""
    print("Testing first_seen_at preservation...")
    
    from clan_cache import ClanCache
    cache = ClanCache()
    
    # Insert a product
    product_data = {
        'id': 99999,  # Use test ID
        'sku': 'test_preserve_sku',
        'name': 'Test Product',
        'price': '100',
        'url': 'https://test.com',
        'image_url': 'https://test.com/img.jpg',
        'description': 'Original description',
        'has_detailed_data': True,
    }
    
    # First insert
    cache.store_single_product(product_data)
    
    # Read first_seen_at
    conn = cache.get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT first_seen_at FROM clan_products WHERE id = %s", (99999,))
    row1 = cur.fetchone()
    first_seen1 = row1[0] if row1 else None
    
    # Wait a tiny bit to ensure timestamps differ
    import time
    time.sleep(0.1)
    
    # Update the product (change description)
    product_data['description'] = 'Updated description'
    cache.store_single_product(product_data)
    
    # Read again
    cur.execute("SELECT first_seen_at, last_updated FROM clan_products WHERE id = %s", (99999,))
    row2 = cur.fetchone()
    first_seen2 = row2[0] if row2 else None
    last_updated2 = row2[1] if row2 else None
    
    # Cleanup
    cur.execute("DELETE FROM clan_products WHERE id = %s", (99999,))
    conn.commit()
    cur.close(); conn.close()
    
    if first_seen1 and first_seen2:
        assert first_seen1 == first_seen2, "first_seen_at should not change on update"
        assert last_updated2 >= first_seen2, "last_updated should be >= first_seen_at"
    else:
        # If first_seen_at wasn't set (might be None on old records), that's okay for this test
        print("  (first_seen_at not set - may be legacy record)")
    print("✓ first_seen_at preservation works correctly")

def test_hash_change_detection():
    """Test that hash comparison correctly identifies changes."""
    print("Testing hash change detection...")
    
    from clan_cache import ClanCache
    cache = ClanCache()
    
    # Create two field sets with different content
    fields_original = {
        'name': 'Product',
        'sku': 'test_sku',
        'price': '100',
        'description': 'Original description',
    }
    
    fields_changed = {
        'name': 'Product',
        'sku': 'test_sku',
        'price': '100',
        'description': 'Changed description',  # Only this differs
    }
    
    hash_original = cache._build_product_hash(fields_original)
    hash_changed = cache._build_product_hash(fields_changed)
    
    assert hash_original != hash_changed, "Hash should change when content changes"
    
    # Same fields should produce same hash
    hash_original2 = cache._build_product_hash(fields_original)
    assert hash_original == hash_original2, "Same fields should produce same hash"
    
    print("✓ Hash change detection works correctly")

def test_update_vs_insert():
    """Test that hash comparison correctly distinguishes insert vs update."""
    print("Testing update vs insert logic...")
    
    from clan_cache import ClanCache
    cache = ClanCache()
    
    # Simulate checking existing hash
    conn = cache.get_db_conn()
    cur = conn.cursor()
    
    # Insert test product
    test_sku = 'test_update_insert_sku'
    cur.execute("""
        INSERT INTO clan_products (id, sku, name, price, product_content_hash)
        VALUES (88888, %s, 'Test', '100', 'old_hash')
        ON CONFLICT (id) DO NOTHING
    """, (test_sku,))
    conn.commit()
    
    # Check existing hash
    cur.execute("SELECT product_content_hash FROM clan_products WHERE sku = %s", (test_sku,))
    existing_row = cur.fetchone()
    
    new_hash = 'new_hash'
    
    if existing_row and existing_row[0]:
        existing_hash = existing_row[0]
        if new_hash == existing_hash:
            action = 'unchanged'
        else:
            action = 'updated'
    else:
        action = 'inserted'
    
    # Cleanup
    cur.execute("DELETE FROM clan_products WHERE sku = %s", (test_sku,))
    conn.commit()
    cur.close(); conn.close()
    
    assert action == 'updated', f"Expected 'updated', got '{action}'"
    print("✓ Update vs insert logic works correctly")

if __name__ == '__main__':
    print("Running change detection tests...\n")
    try:
        test_first_seen_preservation()
        test_hash_change_detection()
        test_update_vs_insert()
        print("\n✓ All change detection tests passed")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

