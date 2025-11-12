#!/usr/bin/env python3
"""
Backfill embedded_images for existing KB articles
Extracts image URLs from HTML content and stores in embedded_images JSONB field
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
import json
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def extract_embedded_images(html_content: str) -> list:
    """Extract image URLs from HTML content."""
    if not html_content:
        return []
    
    image_urls = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        images = soup.find_all('img')
        
        for img in images:
            src = img.get('src', '')
            if src and src.startswith('http'):
                image_urls.append(src)
        
        # Also check for image URLs in text
        url_pattern_full = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp|svg)'
        text_urls = re.findall(url_pattern_full, html_content, re.IGNORECASE)
        
        # Combine and deduplicate
        all_urls = list(set(image_urls + text_urls))
        
        return all_urls
        
    except Exception as e:
        logger.warning(f"Error extracting images: {e}")
        return []

def main():
    conn = psycopg.connect(
        host='localhost',
        dbname='blog',
        user='autojenny',
        password=''
    )
    
    cursor = conn.cursor()
    
    # Get all articles with text content
    cursor.execute("""
        SELECT id, name, text
        FROM clan_kb_articles
        WHERE text IS NOT NULL
    """)
    
    articles = cursor.fetchall()
    logger.info(f"Processing {len(articles)} articles...")
    
    updated_count = 0
    images_found = 0
    
    for article_id, name, html_content in articles:
        embedded_images = extract_embedded_images(html_content)
        
        if embedded_images:
            images_found += len(embedded_images)
            embedded_images_json = json.dumps(embedded_images)
            
            cursor.execute("""
                UPDATE clan_kb_articles
                SET embedded_images = %s
                WHERE id = %s
            """, (embedded_images_json, article_id))
            
            updated_count += 1
            logger.info(f"Article {article_id}: {name[:50]} - Found {len(embedded_images)} images")
    
    conn.commit()
    conn.close()
    
    logger.info(f"\nComplete!")
    logger.info(f"  Articles updated: {updated_count}")
    logger.info(f"  Total images found: {images_found}")

if __name__ == '__main__':
    main()

