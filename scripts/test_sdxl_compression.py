#!/usr/bin/env python3
"""
Test SDXL compression levels with sample concepts and styles
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.prompt_renderers import SDXLRenderer, GPTImage1Renderer, CanonicalPrompt
from config.database import db_manager
import json

def test_compression_levels():
    """Test SDXL compression levels with sample concepts and styles"""
    print("=== SDXL Compression Testing ===\n")
    
    # Load sample concept from DB
    try:
        with db_manager.get_cursor() as cursor:
            # Get a sample post with sections
            cursor.execute("""
                SELECT ps.id, ps.post_id, ps.image_prompts, p.extra_settings
                FROM post_section ps
                JOIN post p ON ps.post_id = p.id
                WHERE ps.image_prompts IS NOT NULL
                LIMIT 1
            """)
            sample = cursor.fetchone()
            
            if not sample:
                print("No sample data found. Creating test data...")
                create_test_data()
                return
            
            post_id = sample['post_id']
            section_id = sample['id']
            image_prompts = sample['image_prompts']
            extra_settings = sample['extra_settings'] or {}
            
            print(f"Testing with Post {post_id}, Section {section_id}")
            print(f"Original prompt: {image_prompts}")
            
            # Extract style_json
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            active_index = imaging.get('activeIndex', 0)
            active_style = styles[active_index] if styles and 0 <= active_index < len(styles) else None
            style_json = active_style.get('style_json') if active_style else None
            
            print(f"Active style: {style_json}\n")
            
    except Exception as e:
        print(f"Error loading sample data: {e}")
        return
    
    # Create canonical prompt
    if isinstance(image_prompts, str):
        canonical = CanonicalPrompt({'subject': image_prompts})
    elif isinstance(image_prompts, dict):
        canonical = CanonicalPrompt(image_prompts)
    else:
        canonical = CanonicalPrompt({'subject': 'A beautiful landscape'})
    
    # Test SDXL compression
    print("=== SDXL Compression Levels ===")
    sdxl_renderer = SDXLRenderer('sdxl-lora', {'max_prompt_chars': 400})
    
    # Test each compression level
    full_prompt = sdxl_renderer._build_full_prompt(canonical, style_json)
    print(f"Level 1 (Full): {len(full_prompt)} chars")
    print(f"  {full_prompt}\n")
    
    if len(full_prompt) > 400:
        level_2 = sdxl_renderer._compress_level_2(full_prompt, canonical, style_json)
        print(f"Level 2 (No margins): {len(level_2)} chars")
        print(f"  {level_2}\n")
        
        if len(level_2) > 400:
            level_3 = sdxl_renderer._compress_level_3(level_2)
            print(f"Level 3 (Abbreviated): {len(level_3)} chars")
            print(f"  {level_3}\n")
            
            if len(level_3) > 400:
                level_4 = sdxl_renderer._compress_level_4(canonical, style_json)
                print(f"Level 4 (Core only): {len(level_4)} chars")
                print(f"  {level_4}\n")
    
    # Test final renderer output
    final_prompt = sdxl_renderer.render(canonical, style_json)
    print(f"Final SDXL Output: {len(final_prompt)} chars")
    print(f"  {final_prompt}\n")
    
    # Test GPT-Image-1 for comparison
    print("=== GPT-Image-1 Comparison ===")
    gpt_renderer = GPTImage1Renderer('gpt-image-1', {'max_prompt_chars': 2000})
    gpt_prompt = gpt_renderer.render(canonical, style_json)
    print(f"GPT-Image-1 Output: {len(gpt_prompt)} chars")
    print(f"  {gpt_prompt}\n")
    
    # Test with different style scenarios
    print("=== Style Scenario Testing ===")
    test_scenarios = [
        {
            'name': 'Watercolor Style',
            'style_json': {
                'medium': 'watercolor',
                'palette': ['pastel blue', 'soft pink', 'mint green'],
                'brushwork': 'visible brushstrokes',
                'margins': 'white margins',
                'technique': 'ink wash'
            }
        },
        {
            'name': 'Minimal Style',
            'style_json': {
                'medium': 'ink',
                'palette': ['black', 'white'],
                'brushwork': 'fine lines'
            }
        },
        {
            'name': 'Rich Style',
            'style_json': {
                'medium': 'oil painting',
                'palette': ['deep red', 'golden yellow', 'forest green', 'royal blue'],
                'brushwork': 'thick impasto',
                'composition': 'dramatic',
                'lighting': 'chiaroscuro',
                'margins': 'white margins',
                'technique': 'classical'
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        test_canonical = CanonicalPrompt({
            'subject': 'A serene mountain landscape',
            'mood': 'peaceful',
            'scene': 'sunset over mountains'
        })
        
        sdxl_result = sdxl_renderer.render(test_canonical, scenario['style_json'])
        gpt_result = gpt_renderer.render(test_canonical, scenario['style_json'])
        
        print(f"SDXL ({len(sdxl_result)} chars): {sdxl_result}")
        print(f"GPT-Image-1 ({len(gpt_result)} chars): {gpt_result}")

def create_test_data():
    """Create test data if none exists"""
    print("Creating test data...")
    # This would create sample posts and sections for testing
    # For now, just show how to use the renderers directly
    
    canonical = CanonicalPrompt({
        'subject': 'A beautiful mountain landscape at sunset',
        'mood': 'serene and peaceful',
        'scene': 'rolling hills with a lake',
        'composition': 'rule of thirds',
        'lighting': 'golden hour',
        'colors': ['golden', 'purple', 'blue'],
        'keywords': ['nature', 'landscape', 'serenity']
    })
    
    style_json = {
        'medium': 'watercolor',
        'palette': ['pastel blue', 'soft pink'],
        'brushwork': 'visible brushstrokes',
        'margins': 'white margins'
    }
    
    print("Test Canonical Prompt:")
    print(f"  {canonical.to_dict()}")
    print(f"\nTest Style JSON:")
    print(f"  {style_json}")
    
    # Test renderers
    sdxl_renderer = SDXLRenderer('sdxl-lora', {'max_prompt_chars': 400})
    gpt_renderer = GPTImage1Renderer('gpt-image-1', {'max_prompt_chars': 2000})
    
    sdxl_result = sdxl_renderer.render(canonical, style_json)
    gpt_result = gpt_renderer.render(canonical, style_json)
    
    print(f"\nSDXL Result ({len(sdxl_result)} chars):")
    print(f"  {sdxl_result}")
    print(f"\nGPT-Image-1 Result ({len(gpt_result)} chars):")
    print(f"  {gpt_result}")

if __name__ == "__main__":
    test_compression_levels()
