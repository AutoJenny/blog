"""
Parsing Services module
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from config.database import db_manager
import logging
from datetime import datetime, date
import json
import requests

logger = logging.getLogger(__name__)

# Create parsing_bp blueprint
parsing_bp = Blueprint('parsing_bp', __name__, url_prefix='/api/parsing')

"""

# Auto-generated from blueprints/planning.py
# Module: services/parsing.py

@parsing_bp.route('/parse-brainstorm-topics')
def parse_brainstorm_topics(content):
    """Enhanced topic parsing with validation and categorization"""
    topics = []
    
    # Step 1: Try JSON parsing (expected format)
    try:
        # Clean up the content to extract JSON
        content_clean = content.strip()
        
        # Find JSON array boundaries
        start_idx = content_clean.find('[')
        end_idx = content_clean.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content_clean[start_idx:end_idx + 1]
            topic_list = json.loads(json_str)
            
            if isinstance(topic_list, list):
                for topic_item in topic_list:
                    if isinstance(topic_item, dict):
                        # Handle object format with title, description, category, word_count
                        if 'title' in topic_item:
                            topics.append({
                                'title': topic_item['title'].strip(),
                                'description': topic_item.get('description', topic_item['title']).strip(),
                                'category': topic_item.get('category', 'general'),
                                'word_count': topic_item.get('word_count', len(topic_item['title'].split()))
                            })
                    elif isinstance(topic_item, str) and validate_topic(topic_item):
                        # Handle string format (legacy)
                        topics.append({
                            'title': topic_item.strip(),
                            'description': topic_item.strip(),
                            'category': categorize_topic(topic_item),
                            'word_count': len(topic_item.split())
                        })
                
                if topics:
                    logger.info(f"Successfully parsed {len(topics)} topics from JSON format")
                    return topics[:50]  # Limit to 50 topics
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"JSON parsing failed: {e}, falling back to text parsing")
        pass  # Fall back to text parsing
    
    # Fallback: Parse as text format (numbered, bulleted, or short lines)
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this looks like a topic (numbered, bulleted, or short line)
        if (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.', '16.', '17.', '18.', '19.', '20.', '21.', '22.', '23.', '24.', '25.', '26.', '27.', '28.', '29.', '30.', '31.', '32.', '33.', '34.', '35.', '36.', '37.', '38.', '39.', '40.', '41.', '42.', '43.', '44.', '45.', '46.', '47.', '48.', '49.', '50.')) or 
            line.startswith(('-', '*', '•')) or
            (len(line) < 100 and not line.endswith('.') and not line.startswith('SERIOUS') and not line.startswith('BALANCED') and not line.startswith('QUIRKY') and not line.startswith('Format') and not line.startswith('Ensure'))):
            
            # Clean up the line and add as topic
            clean_line = line.lstrip('1234567890.-*• ').strip()
            if clean_line and validate_topic(clean_line):
                topics.append({
                    'title': clean_line,
                    'description': clean_line,  # Same as title since it's a short summary
                    'category': categorize_topic(clean_line),
                    'word_count': len(clean_line.split())
                })
    
    # If no structured topics found, try to split by lines that look like topics
    if not topics:
        for line in lines:
            line = line.strip()
            if line and validate_topic(line):
                topics.append({
                    'title': line,
                    'description': line,
                    'category': categorize_topic(line),
                    'word_count': len(line.split())
                })
    
    return topics[:50]  # Limit to 50 topics


@parsing_bp.route('/validate-topic')
def validate_topic(topic):
    """Validate individual topic for length and content"""
    if not topic or not isinstance(topic, str):
        return False
    
    words = topic.strip().split()
    # Check word count (5-8 words)
    if not (5 <= len(words) <= 8):
        return False
    
    # Check minimum length
    if len(topic.strip()) < 10:
        return False
    
    # Check for common invalid patterns
    invalid_patterns = ['SERIOUS', 'BALANCED', 'QUIRKY', 'Format', 'Ensure', 'Generate', 'Here are', 'The following']
    topic_lower = topic.lower()
    if any(pattern.lower() in topic_lower for pattern in invalid_patterns):
        return False
    
    return True


