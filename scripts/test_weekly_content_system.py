#!/usr/bin/env python3
"""
Test script for weekly content image and caption generation system
Tests all components without live Facebook posting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.weekly_content_data_extractor import extract_weekly_content_data
from utils.weekly_content_caption_generator import generate_weekly_content_caption
from utils.weekly_content_image_renderer import render_weekly_content_image
from utils.posting_queue_helpers import create_weekly_social_post, get_posting_queue_row
from blueprints.automation_execute import (
    execute_format_for_facebook,
    execute_generate_caption,
    execute_add_translation,
    execute_add_hashtags,
    execute_optimize_for_facebook
)
import json

def test_data_extraction():
    """Test 1: Data extraction from calendar_ideas"""
    print("\n" + "="*60)
    print("TEST 1: Data Extraction")
    print("="*60)
    
    # Get a real weekly content idea from database
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, idea_title, idea_description, item_classification
            FROM calendar_ideas
            WHERE item_classification IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
               OR idea_title ILIKE '%word%' 
               OR idea_title ILIKE '%phrase%'
               OR idea_title ILIKE '%insult%'
            LIMIT 1
        """)
        idea = cursor.fetchone()
    
    if not idea:
        print("❌ No weekly content ideas found in calendar_ideas")
        print("   Please create a test idea first")
        return None
    
    print(f"✅ Found idea: ID={idea['id']}, Title='{idea['idea_title']}'")
    
    # Determine category from item_classification or guess
    category = idea.get('item_classification')
    if not category or category not in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
        # Try to guess from title
        title_lower = idea['idea_title'].lower()
        if 'word' in title_lower:
            category = 'weekly_word'
        elif 'phrase' in title_lower:
            category = 'weekly_phrase'
        elif 'insult' in title_lower:
            category = 'weekly_insult'
        else:
            category = 'weekly_word'  # Default
    
    print(f"   Using category: {category}")
    
    try:
        data = extract_weekly_content_data(idea['id'], category)
        print(f"✅ Data extraction successful")
        print(f"   Scots text: {data['scots_text']}")
        print(f"   Translation: {data['translation'] or '(none)'}")
        print(f"   Output path: {data['output_path']}")
        return data
    except Exception as e:
        print(f"❌ Data extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_caption_generation(data):
    """Test 2: Caption generation with Ollama"""
    print("\n" + "="*60)
    print("TEST 2: Caption Generation")
    print("="*60)
    
    if not data:
        print("⚠️  Skipping (no data from previous test)")
        return None
    
    try:
        result = generate_weekly_content_caption(
            category=data['category'],
            scots_text=data['scots_text'],
            translation=data['translation'],
            notes=data.get('notes')
        )
        
        print(f"✅ Caption generation successful")
        print(f"   Caption: {result['caption']}")
        print(f"   Prompt style ID: {result['chosen_prompt_style_id']}")
        print(f"   Model: {result['ollama_model']}")
        
        if result.get('error'):
            print(f"   ⚠️  Warning: {result['error']}")
        
        return result
    except Exception as e:
        print(f"❌ Caption generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_image_generation(data):
    """Test 3: Image generation with ImageMagick"""
    print("\n" + "="*60)
    print("TEST 3: Image Generation")
    print("="*60)
    
    if not data:
        print("⚠️  Skipping (no data from previous test)")
        return None
    
    try:
        result = render_weekly_content_image(
            category=data['category'],
            title=data['title'],
            scots_text=data['scots_text'],
            translation=data['translation'],
            series_footer=data['series_footer'],
            logo_path=data.get('logo_path'),
            output_path=data['output_path']
        )
        
        if result['success']:
            print(f"✅ Image generation successful")
            print(f"   Output: {result['output_path']}")
            
            # Verify file exists and check size
            if os.path.exists(result['output_path']):
                file_size = os.path.getsize(result['output_path'])
                print(f"   File size: {file_size:,} bytes")
                
                # Try to get image dimensions (requires PIL)
                try:
                    from PIL import Image
                    img = Image.open(result['output_path'])
                    print(f"   Dimensions: {img.size[0]}×{img.size[1]}")
                    if img.size[0] == 1080 and img.size[1] == 1080:
                        print(f"   ✅ Correct size (1080×1080)")
                    else:
                        print(f"   ⚠️  Wrong size (expected 1080×1080)")
                except ImportError:
                    print(f"   (Install PIL to verify dimensions)")
            else:
                print(f"   ⚠️  Warning: File not found at output path")
        else:
            print(f"❌ Image generation failed: {result['error']}")
            return None
        
        return result
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_complete_workflow():
    """Test 4: Complete workflow via substage execution"""
    print("\n" + "="*60)
    print("TEST 4: Complete Workflow")
    print("="*60)
    
    # Get a real weekly content idea
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, idea_title, item_classification
            FROM calendar_ideas
            WHERE item_classification IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
            LIMIT 1
        """)
        idea = cursor.fetchone()
    
    if not idea:
        print("❌ No weekly content ideas found")
        return False
    
    category = idea.get('item_classification') or 'weekly_word'
    
    print(f"Creating posting_queue row for idea_id={idea['id']}, category={category}")
    
    try:
        # Step 1: Create posting_queue row
        queue_id = create_weekly_social_post(
            idea_id=idea['id'],
            content_type=category,
            platform='facebook',
            generated_content='Test content',
            status='draft'
        )
        print(f"✅ Created posting_queue row: ID={queue_id}")
        
        # Step 2: Format for Facebook
        print("\nExecuting: format_for_facebook")
        result = execute_format_for_facebook(queue_id, {})
        if result[0].get('success'):
            print(f"✅ Format successful")
        else:
            print(f"❌ Format failed: {result[0].get('error')}")
            return False
        
        # Step 3: Generate caption
        print("\nExecuting: generate_caption")
        result = execute_generate_caption(queue_id, {})
        if result[0].get('success'):
            print(f"✅ Caption generated: {result[0].get('caption', '')[:80]}...")
        else:
            print(f"❌ Caption generation failed: {result[0].get('error')}")
            return False
        
        # Step 4: Add translation (if phrase/insult)
        if category in ('weekly_phrase', 'weekly_insult'):
            print("\nExecuting: add_translation")
            result = execute_add_translation(queue_id, {})
            if result[0].get('success'):
                print(f"✅ Translation verified")
            else:
                print(f"⚠️  Translation check: {result[0].get('error')}")
        
        # Step 5: Add hashtags
        print("\nExecuting: add_hashtags")
        result = execute_add_hashtags(queue_id, {})
        if result[0].get('success'):
            print(f"✅ Hashtags added: {result[0].get('caption', '')[-30:]}")
        else:
            print(f"❌ Hashtag addition failed: {result[0].get('error')}")
            return False
        
        # Step 6: Generate image
        print("\nExecuting: optimize_for_facebook")
        result = execute_optimize_for_facebook(queue_id, {})
        if result[0].get('success'):
            print(f"✅ Image generated: {result[0].get('image_path')}")
        else:
            print(f"❌ Image generation failed: {result[0].get('error')}")
            return False
        
        # Step 7: Verify final state
        print("\nVerifying final state...")
        queue_row = get_posting_queue_row(queue_id)
        if queue_row:
            print(f"✅ Final verification:")
            print(f"   Status: {queue_row.get('status')}")
            print(f"   Caption: {queue_row.get('generated_caption', '')[:60]}...")
            print(f"   Image path: {queue_row.get('image_path', 'None')}")
            print(f"   Prompt style ID: {queue_row.get('chosen_prompt_style_id', 'None')}")
            print(f"   Generation timestamp: {queue_row.get('generation_timestamp', 'None')}")
            
            # Verify image exists
            if queue_row.get('image_path') and os.path.exists(queue_row['image_path']):
                print(f"   ✅ Image file exists")
            else:
                print(f"   ⚠️  Image file not found")
        
        print(f"\n✅ Complete workflow test successful!")
        print(f"   Queue ID: {queue_id}")
        print(f"   (Skipping publish_to_facebook - no live posting)")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("WEEKLY CONTENT SYSTEM - COMPONENT TESTS")
    print("="*60)
    print("\nTesting components without live Facebook posting...")
    
    # Test 1: Data extraction
    data = test_data_extraction()
    
    # Test 2: Caption generation
    caption_result = test_caption_generation(data)
    
    # Test 3: Image generation
    image_result = test_image_generation(data)
    
    # Test 4: Complete workflow
    workflow_success = test_complete_workflow()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Data Extraction: {'✅' if data else '❌'}")
    print(f"Caption Generation: {'✅' if caption_result else '❌'}")
    print(f"Image Generation: {'✅' if image_result else '❌'}")
    print(f"Complete Workflow: {'✅' if workflow_success else '❌'}")
    
    if all([data, caption_result, image_result, workflow_success]):
        print("\n🎉 All tests passed! System is ready for integration.")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")


if __name__ == '__main__':
    main()
