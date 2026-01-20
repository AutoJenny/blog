#!/usr/bin/env python3
"""
Test script for generating weekly content images with corrected approach
Generates test images for this week's three language post types
Outputs to review directory (NOT production paths)
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from utils.weekly_content_data_extractor import extract_weekly_content_data
from utils.weekly_content_image_renderer_v2 import render_weekly_content_image
from utils.calendar_resolver import resolve_item_for_week

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Review output directory (separate from production)
REVIEW_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'content', 'weekly_posts', 'review_v2'
)

def main():
    app = Flask(__name__)
    
    with app.app_context():
        # Get current ISO week
        now = datetime.now()
        current_year, current_week, _ = now.isocalendar()
        
        logger.info(f"Generating test images for week {current_year}-W{current_week:02d}")
        logger.info(f"Review output directory: {REVIEW_OUTPUT_DIR}")
        
        # Get this week's language content
        categories = ['weekly_word', 'weekly_phrase', 'weekly_insult']
        review_paths = []
        
        for category in categories:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {category}")
            logger.info(f"{'='*60}")
            
            # Get item for this week
            item = resolve_item_for_week(category, current_year, current_week)
            if not item:
                logger.warning(f"No item found for {category} in week {current_year}-W{current_week:02d}")
                continue
            
            idea_id = item.get('id')
            logger.info(f"Found item ID: {idea_id}, Title: {item.get('idea_title')}")
            
            # Extract data
            try:
                data = extract_weekly_content_data(idea_id, category)
                logger.info(f"Extracted data: scots_text='{data['scots_text']}', translation='{data['translation']}'")
            except Exception as e:
                logger.error(f"Error extracting data: {e}")
                continue
            
            # Generate review output path (NOT production path)
            review_output_dir = os.path.join(REVIEW_OUTPUT_DIR, category)
            os.makedirs(review_output_dir, exist_ok=True)
            review_output_path = os.path.join(review_output_dir, f"{idea_id}_review.png")
            
            # Generate image using corrected renderer
            logger.info(f"Generating image with corrected approach...")
            result = render_weekly_content_image(
                category=data['category'],
                title=data['title'],
                scots_text=data['scots_text'],
                translation=data['translation'],
                series_footer=data['series_footer'],
                logo_path=data['logo_path'],
                output_path=review_output_path,
                usage_examples=data.get('usage_examples', []),
                notes=data.get('notes')
            )
            
            if result['success']:
                logger.info(f"✅ Successfully generated: {review_output_path}")
                review_paths.append({
                    'category': category,
                    'idea_id': idea_id,
                    'scots_text': data['scots_text'],
                    'path': review_output_path
                })
            else:
                logger.error(f"❌ Failed to generate image: {result.get('error')}")
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Generated {len(review_paths)} test images:")
        for item in review_paths:
            logger.info(f"  {item['category']}: {item['scots_text']}")
            logger.info(f"    → {item['path']}")
        
        return review_paths

if __name__ == '__main__':
    review_paths = main()
    print("\n" + "="*60)
    print("REVIEW FILEPATHS:")
    print("="*60)
    for item in review_paths:
        print(f"\n{item['category']}: {item['scots_text']}")
        print(f"  {item['path']}")
