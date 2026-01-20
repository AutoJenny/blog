#!/usr/bin/env python3
"""
Aesthetic analysis script for weekly content images
Generates minimalist and maximalist examples for each type, then reviews them
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from utils.weekly_content_image_renderer_v2 import render_weekly_content_image
from config.weekly_content_image_config import (
    CATEGORY_TITLES,
    SERIES_FOOTER_TEXT,
    LOGO_PATH
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test output directory
TEST_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'content', 'weekly_posts', 'aesthetic_analysis'
)

# Test data: minimalist and maximalist examples for each type
TEST_DATA = {
    'weekly_word': {
        'minimalist': {
            'scots_text': 'wee',
            'translation': 'small',
            'usage_examples': ['A wee bit.', 'Just a wee moment.'],
            'notes': 'Common Scots; universal usage'
        },
        'maximalist': {
            'scots_text': 'scunner',
            'translation': 'disgust; annoyance; strong dislike',
            'usage_examples': [
                'That film gied me a scunner.',
                "I've a scunner for that place noo.",
                "He's a right scunner, that yin."
            ],
            'notes': 'Pan-Scots noun/verb; attested 18th c onwards; widespread usage across all regions'
        }
    },
    'weekly_phrase': {
        'minimalist': {
            'scots_text': 'Aye',
            'translation': 'Yes',
            'usage_examples': [],
            'notes': 'Universal Scots'
        },
        'maximalist': {
            'scots_text': 'Keep yersel tae yersel',
            'translation': 'Keep yourself to yourself; mind your own business',
            'usage_examples': [],
            'notes': 'Scots and Scottish English; 19th–21st c; common in both formal and informal contexts'
        }
    },
    'weekly_insult': {
        'minimalist': {
            'scots_text': 'Eejit',
            'translation': 'Idiot',
            'usage_examples': [],
            'notes': 'Common Scots insult'
        },
        'maximalist': {
            'scots_text': "Ye're as useful as a chocolate fireguard",
            'translation': 'You are completely useless',
            'usage_examples': [],
            'notes': 'UK-wide but common in Scots humour; humorous rather than genuinely offensive'
        }
    }
}

def generate_test_images():
    """Generate all test images for aesthetic analysis"""
    app = Flask(__name__)
    
    with app.app_context():
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
        generated_images = []
        
        for category in ['weekly_word', 'weekly_phrase', 'weekly_insult']:
            title = CATEGORY_TITLES.get(category, category.upper())
            
            for variant in ['minimalist', 'maximalist']:
                data = TEST_DATA[category][variant]
                
                output_dir = os.path.join(TEST_OUTPUT_DIR, category, variant)
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{category}_{variant}.png")
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Generating: {category} - {variant}")
                logger.info(f"Scots: '{data['scots_text']}'")
                logger.info(f"{'='*60}")
                
                result = render_weekly_content_image(
                    category=category,
                    title=title,
                    scots_text=data['scots_text'],
                    translation=data['translation'],
                    series_footer=SERIES_FOOTER_TEXT,
                    logo_path=LOGO_PATH,
                    output_path=output_path,
                    usage_examples=data.get('usage_examples', []),
                    notes=data.get('notes')
                )
                
                if result['success']:
                    logger.info(f"✅ Generated: {output_path}")
                    generated_images.append({
                        'category': category,
                        'variant': variant,
                        'scots_text': data['scots_text'],
                        'path': output_path,
                        'url': f"http://localhost:5000/static/content/weekly_posts/aesthetic_analysis/{category}/{variant}/{category}_{variant}.png"
                    })
                else:
                    logger.error(f"❌ Failed: {result.get('error')}")
        
        return generated_images

if __name__ == '__main__':
    images = generate_test_images()
    
    print("\n" + "="*60)
    print("GENERATED IMAGES FOR AESTHETIC ANALYSIS")
    print("="*60)
    
    for img in images:
        print(f"\n{img['category']} - {img['variant']}:")
        print(f"  Scots: '{img['scots_text']}'")
        print(f"  URL: {img['url']}")
        print(f"  Path: {img['path']}")
