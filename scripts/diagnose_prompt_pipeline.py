#!/usr/bin/env python3
"""
Diagnostic script for GPT-Image-1 prompt rendering pipeline
Usage: python scripts/diagnose_prompt_pipeline.py --post-id 69 --section-id 1 --model gpt-image-1
"""
import sys
import os
import argparse
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager
from modules.prompt_service import prompt_service
from modules.prompt_renderers import PromptRendererFactory

def print_stage(stage_name, status='RUNNING'):
    symbols = {'RUNNING': '⏳', 'PASS': '✅', 'FAIL': '❌', 'WARN': '⚠️'}
    print(f"\n{symbols.get(status, '•')} {stage_name}")
    print("=" * 60)

def diagnose_pipeline(post_id, section_id, model_key='gpt-image-1'):
    print(f"\n🔍 DIAGNOSTIC: Post {post_id}, Section {section_id}, Model {model_key}")
    print("=" * 60)
    
    # Stage 1: Database
    print_stage("Stage 1: Database Retrieval", "RUNNING")
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT id, title, extra_settings FROM post WHERE id = %s", (post_id,))
        post_row = cursor.fetchone()
        
        if not post_row:
            print_stage("Stage 1: Database Retrieval", "FAIL")
            print(f"ERROR: Post {post_id} not found")
            return False
        
        print(f"Post Title: {post_row['title']}")
        
        # Check active style
        extra = post_row.get('extra_settings', {})
        imaging = extra.get('imaging', {})
        styles = imaging.get('styles', [])
        active_index = imaging.get('activeIndex', 0)
        
        print(f"Styles in database: {len(styles)}")
        print(f"Active index: {active_index}")
        
        if not styles or not (0 <= active_index < len(styles)):
            print_stage("Stage 1: Database Retrieval", "WARN")
            print("WARNING: No active style found")
        else:
            active_style = styles[active_index]
            print(f"Active Style: {active_style.get('name')}")
            style_json = active_style.get('style_json', {})
            print(f"Style JSON keys: {list(style_json.keys())}")
            print_stage("Stage 1: Database Retrieval", "PASS")
        
        # Check section data
        cursor.execute("SELECT sections FROM post_development WHERE post_id = %s", (post_id,))
        dev_row = cursor.fetchone()
        
        if not dev_row or not dev_row['sections']:
            print("ERROR: No post_development data found")
            return False
        
        sections_data = dev_row['sections']
        if isinstance(sections_data, str):
            sections_data = json.loads(sections_data)
        
        if isinstance(sections_data, dict) and 'sections' in sections_data:
            sections_list = sections_data['sections']
            print(f"Sections in post_development: {len(sections_list)}")
            
            section_found = False
            for section in sections_list:
                if str(section.get('id')) == str(section_id):
                    section_found = True
                    has_prompts = bool(section.get('image_prompts'))
                    print(f"Section found: ID={section_id}, has_image_prompts={has_prompts}")
                    if has_prompts:
                        prompt_data = section['image_prompts']
                        if isinstance(prompt_data, dict):
                            prompt_text = prompt_data.get('image_prompt', '')
                            print(f"Image prompt length: {len(prompt_text)} chars")
                    break
            
            if not section_found:
                print(f"ERROR: Section {section_id} not found in post_development")
                return False
    
    # Stage 2: Canonical Prompt
    print_stage("Stage 2: Canonical Prompt Creation", "RUNNING")
    try:
        canonical, style_json = prompt_service.get_canonical_prompt(post_id, section_id)
        print(f"Subject length: {len(canonical.subject)} chars")
        print(f"Subject preview: {canonical.subject[:100]}...")
        print(f"Style: {canonical.style}")
        print(f"Constraints: {canonical.constraints}")
        print(f"Negatives: {canonical.negatives}")
        print(f"Style JSON received: {bool(style_json)}")
        if style_json:
            print(f"Style JSON keys: {list(style_json.keys())}")
        print_stage("Stage 2: Canonical Prompt Creation", "PASS")
    except Exception as e:
        print_stage("Stage 2: Canonical Prompt Creation", "FAIL")
        print(f"ERROR: {e}")
        return False
    
    # Stage 3: Renderer
    print_stage("Stage 3: Renderer Selection", "RUNNING")
    try:
        constraints = {'max_prompt_chars': 2000 if model_key == 'gpt-image-1' else 400}
        renderer = PromptRendererFactory.create_renderer(model_key, constraints)
        print(f"Renderer class: {type(renderer).__name__}")
        print(f"Model key: {model_key}")
        print(f"Constraints: {constraints}")
        print_stage("Stage 3: Renderer Selection", "PASS")
    except Exception as e:
        print_stage("Stage 3: Renderer Selection", "FAIL")
        print(f"ERROR: {e}")
        return False
    
    # Stage 4: Style Integration
    print_stage("Stage 4: Style Integration", "RUNNING")
    try:
        style_description = renderer._integrate_style_details(canonical, style_json)
        print(f"Style description length: {len(style_description or '')} chars")
        print(f"Style description: {style_description}")
        print(f"Contains 'watercolor': {'watercolor' in (style_description or '').lower()}")
        print(f"Contains 'pastel': {'pastel' in (style_description or '').lower()}")
        print_stage("Stage 4: Style Integration", "PASS")
    except Exception as e:
        print_stage("Stage 4: Style Integration", "FAIL")
        print(f"ERROR: {e}")
        return False
    
    # Stage 5: Full Rendering
    print_stage("Stage 5: Full Rendering", "RUNNING")
    try:
        rendered_prompt = renderer.render(canonical, style_json)
        print(f"Rendered prompt length: {len(rendered_prompt)} chars")
        print(f"First 200 chars: {rendered_prompt[:200]}...")
        print(f"Last 200 chars: ...{rendered_prompt[-200:]}")
        print("\nStyle Guidelines Check:")
        print(f"  ✓ watercolor: {'watercolor' in rendered_prompt.lower()}")
        print(f"  ✓ pastel: {'pastel' in rendered_prompt.lower()}")
        print(f"  ✓ white margins: {'white margin' in rendered_prompt.lower()}")
        print(f"  ✓ visible brushstrokes: {'visible brushstroke' in rendered_prompt.lower()}")
        print(f"  ✓ pen and ink: {'pen and ink' in rendered_prompt.lower()}")
        print(f"  ✓ avoiding dark: {'avoiding dark' in rendered_prompt.lower()}")
        print(f"  ✓ avoiding saturated: {'avoiding saturated' in rendered_prompt.lower()}")
        print(f"  ✓ avoiding digital: {'avoiding digital' in rendered_prompt.lower()}")
        
        all_present = all([
            'watercolor' in rendered_prompt.lower(),
            'pastel' in rendered_prompt.lower(),
            'white margin' in rendered_prompt.lower(),
            'visible brushstroke' in rendered_prompt.lower(),
            'pen and ink' in rendered_prompt.lower(),
            'avoiding dark' in rendered_prompt.lower()
        ])
        
        if all_present:
            print_stage("Stage 5: Full Rendering", "PASS")
        else:
            print_stage("Stage 5: Full Rendering", "WARN")
            print("WARNING: Some style guidelines missing from rendered prompt")
    except Exception as e:
        print_stage("Stage 5: Full Rendering", "FAIL")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Stage 6: API Integration
    print_stage("Stage 6: API Integration Test", "RUNNING")
    try:
        rendered_via_service, metadata = prompt_service.render_prompt_for_model(
            post_id, section_id, model_key, use_override=True
        )
        print(f"Service prompt length: {len(rendered_via_service)} chars")
        print(f"Matches direct render: {rendered_via_service == rendered_prompt}")
        print(f"Metadata: {metadata}")
        print_stage("Stage 6: API Integration Test", "PASS")
    except Exception as e:
        print_stage("Stage 6: API Integration Test", "FAIL")
        print(f"ERROR: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL STAGES PASSED")
    print("=" * 60)
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Diagnose prompt rendering pipeline')
    parser.add_argument('--post-id', type=int, required=True, help='Post ID')
    parser.add_argument('--section-id', required=True, help='Section ID')
    parser.add_argument('--model', default='gpt-image-1', help='Model key (default: gpt-image-1)')
    
    args = parser.parse_args()
    
    success = diagnose_pipeline(args.post_id, args.section_id, args.model)
    sys.exit(0 if success else 1)
