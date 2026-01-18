#!/usr/bin/env python3
"""
Test Product Post Workflow
Tests the automated workflow for product posts
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from blueprints.automation_execute import (
    execute_format_for_facebook,
    execute_generate_caption,
    execute_add_hashtags,
    execute_optimize_for_facebook,
    execute_publish_to_facebook
)

def create_test_product_post(product_id=None):
    """Create a test product post in posting_queue"""
    with db_manager.get_cursor() as cursor:
        # Get a product if not provided
        if not product_id:
            cursor.execute("""
                SELECT id, name, image_url
                FROM clan_products
                WHERE image_url IS NOT NULL
                AND image_url != ''
                ORDER BY id DESC
                LIMIT 1
            """)
            product = cursor.fetchone()
            if not product:
                print("❌ No products with images found")
                return None
            product_id = product['id']
            print(f"✅ Using product: {product['name']} (ID: {product_id})")
        
        # Create draft post
        scheduled_date = (datetime.now() + timedelta(days=7)).date()
        cursor.execute("""
            INSERT INTO posting_queue (
                product_id, content_type, platform, status,
                scheduled_date, scheduled_time, created_at, updated_at
            )
            VALUES (%s, 'product', 'facebook', 'draft', %s, '15:00', NOW(), NOW())
            RETURNING id
        """, (product_id, scheduled_date))
        
        result = cursor.fetchone()
        queue_id = result['id'] if isinstance(result, dict) else result[0]
        
        print(f"✅ Created test product post: queue_id={queue_id}")
        return queue_id

def test_workflow_stage(stage_name, function, queue_id):
    """Test a single workflow stage"""
    print(f"\n{'='*60}")
    print(f"Testing: {stage_name}")
    print(f"{'='*60}")
    
    try:
        result = function(queue_id, {})
        
        if isinstance(result, tuple):
            result_dict, status_code = result
        else:
            result_dict = result
            status_code = 200 if result_dict.get('success') else 500
        
        if status_code == 200 and result_dict.get('success'):
            print(f"✅ {stage_name}: SUCCESS")
            if 'formatted_data' in result_dict:
                print(f"   Formatted data keys: {list(result_dict['formatted_data'].keys())}")
            if 'caption' in result_dict:
                print(f"   Caption preview: {result_dict['caption'][:100]}...")
            if 'image_path' in result_dict:
                print(f"   Image path: {result_dict['image_path']}")
            return True
        else:
            print(f"❌ {stage_name}: FAILED")
            print(f"   Error: {result_dict.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ {stage_name}: EXCEPTION")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_queue_state(queue_id):
    """Verify the state of the posting_queue row"""
    print(f"\n{'='*60}")
    print(f"Verifying Queue State (ID: {queue_id})")
    print(f"{'='*60}")
    
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, product_id, content_type, status, platform,
                generated_content, generated_caption, image_path,
                scheduled_date, scheduled_time
            FROM posting_queue
            WHERE id = %s
        """, (queue_id,))
        
        row = cursor.fetchone()
        if not row:
            print("❌ Queue row not found!")
            return False
        
        print(f"Status: {row['status']}")
        print(f"Product ID: {row['product_id']}")
        print(f"Has generated_content: {row['generated_content'] is not None}")
        print(f"Has generated_caption: {row['generated_caption'] is not None}")
        print(f"Has image_path: {row['image_path'] is not None}")
        
        if row['generated_content']:
            try:
                data = json.loads(row['generated_content'])
                print(f"Formatted data type: {data.get('content_type', 'unknown')}")
                print(f"Product name: {data.get('product_name', 'N/A')}")
            except:
                print("Formatted data: (not JSON)")
        
        if row['generated_caption']:
            print(f"Caption preview: {row['generated_caption'][:100]}...")
        
        if row['image_path']:
            print(f"Image path: {row['image_path']}")
        
        return True

def main():
    print("="*60)
    print("PRODUCT POST WORKFLOW TEST")
    print("="*60)
    
    # Create test post
    queue_id = create_test_product_post()
    if not queue_id:
        print("❌ Failed to create test post")
        return
    
    # Test each stage
    stages = [
        ("format_for_facebook", execute_format_for_facebook),
        ("generate_caption", execute_generate_caption),
        ("add_hashtags", execute_add_hashtags),
        ("optimize_for_facebook", execute_optimize_for_facebook),
        # Skip publish_to_facebook since it's disabled
    ]
    
    results = {}
    for stage_name, stage_func in stages:
        success = test_workflow_stage(stage_name, stage_func, queue_id)
        results[stage_name] = success
        
        # Verify state after each stage
        verify_queue_state(queue_id)
        
        if not success:
            print(f"\n❌ Workflow stopped at {stage_name}")
            break
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for stage_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{stage_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All workflow stages passed!")
    else:
        print("\n❌ Some workflow stages failed")
    
    print(f"\nTest post queue_id: {queue_id}")
    print("You can check the database to verify the results")

if __name__ == "__main__":
    main()
