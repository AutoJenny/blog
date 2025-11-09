"""
Photo Harvesting Storage Utilities

Handles file-based persistence for Photo-harvesting route:
- Normalizes photo metadata from Pexels/Unsplash
- Stores search results as JSON in raw/ directory
- Stores selected photos (landscape and portrait) as JSON in optimized/ directory
"""

import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def normalize_photo_metadata(photo: Dict) -> Dict:
    """
    Normalize photo metadata from Pexels or Unsplash into a common format.
    
    Args:
        photo: Photo object from either provider (already partially standardized)
    
    Returns:
        Normalized photo metadata dictionary
    """
    provider = photo.get('provider', 'unknown')
    
    # Extract dimensions
    width = photo.get('width', 0)
    height = photo.get('height', 0)
    
    # Determine orientation
    if width > height:
        orientation = 'landscape'
    elif height > width:
        orientation = 'portrait'
    else:
        orientation = 'square'
    
    # Normalized structure
    normalized = {
        'provider': provider,
        'image_id': str(photo.get('image_id', '')),
        'url': photo.get('url', ''),
        'thumbnail_url': photo.get('thumbnail_url', photo.get('url', '')),
        'width': width,
        'height': height,
        'orientation': orientation,
        'photographer': photo.get('photographer', 'Unknown'),
        'photographer_url': photo.get('photographer_url', ''),
        'credits': photo.get('credits', ''),
        'search_term': photo.get('search_term', ''),
        'selected': photo.get('selected', False),
        'selected_at': photo.get('selected_at'),
    }
    
    # Provider-specific metadata
    if provider == 'pexels':
        api_response = photo.get('api_response', {})
        normalized.update({
            'provider_data': {
                'pexels_id': str(photo.get('image_id', '')),
                'pexels_url': api_response.get('url', ''),
                'photographer_id': api_response.get('photographer_id', ''),
            }
        })
    elif provider == 'unsplash':
        api_response = photo.get('api_response', {})
        user = api_response.get('user', {})
        links = api_response.get('links', {})
        urls = api_response.get('urls', {})
        normalized.update({
            'provider_data': {
                'unsplash_id': photo.get('image_id', ''),
                'unsplash_url': links.get('html', ''),
                'download_location': links.get('download_location', photo.get('download_location', '')),
                'user_id': user.get('id', ''),
                'user_username': user.get('username', ''),
                'color': api_response.get('color', ''),
                'description': api_response.get('description', api_response.get('alt_description', '')),
                'raw_url': urls.get('raw', ''),
                'full_url': urls.get('full', ''),
            }
        })
    
    return normalized


def store_search_results(post_id: int, section_id: int, results: List[Dict], search_term: str) -> str:
    """
    Store normalized photo search results as JSON file in raw/ directory.
    
    Args:
        post_id: Post ID
        section_id: Section ID
        results: List of photo objects from search
        search_term: Search term used
    
    Returns:
        Path to stored JSON file
    """
    # Create directory structure
    raw_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
    os.makedirs(raw_dir, exist_ok=True)
    
    # Normalize all photos
    normalized_results = [normalize_photo_metadata(photo) for photo in results]
    
    # Create metadata object
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'post_id': post_id,
        'section_id': section_id,
        'search_term': search_term,
        'count': len(normalized_results),
        'results': normalized_results
    }
    
    # Write JSON file
    filename = f"photo_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(raw_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Stored {len(normalized_results)} photo search results to {filepath}")
    
    # Also store a "latest" file for easy access
    latest_filepath = os.path.join(raw_dir, "photo_search_results_latest.json")
    with open(latest_filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return filepath


def load_search_results(post_id: int, section_id: int) -> Optional[Dict]:
    """
    Load the latest photo search results from raw/ directory.
    
    Args:
        post_id: Post ID
        section_id: Section ID
    
    Returns:
        Metadata dictionary with results, or None if not found
    """
    latest_filepath = f"static/content/posts/{post_id}/sections/{section_id}/raw/photo_search_results_latest.json"
    
    if not os.path.exists(latest_filepath):
        return None
    
    try:
        with open(latest_filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading search results: {e}")
        return None


def store_selected_photo(post_id: int, section_id: int, photo: Dict, orientation: str) -> str:
    """
    Store selected photo metadata as JSON in optimized/ directory.
    
    Args:
        post_id: Post ID
        section_id: Section ID
        photo: Normalized photo metadata
        orientation: 'landscape' or 'portrait'
    
    Returns:
        Path to stored JSON file
    """
    if orientation not in ('landscape', 'portrait'):
        raise ValueError(f"Invalid orientation: {orientation}. Must be 'landscape' or 'portrait'")
    
    # Create directory structure
    optimized_dir = f"static/content/posts/{post_id}/sections/{section_id}/optimized"
    os.makedirs(optimized_dir, exist_ok=True)
    
    # Normalize photo if not already normalized
    if 'orientation' not in photo:
        photo = normalize_photo_metadata(photo)
    
    # Add selection metadata
    photo['selected_at'] = datetime.now().isoformat()
    photo['selection_orientation'] = orientation
    
    # Create metadata object
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'post_id': post_id,
        'section_id': section_id,
        'orientation': orientation,
        'photo': photo
    }
    
    # Write JSON file (overwrite previous selection for this orientation)
    filename = f"selected_{orientation}.json"
    filepath = os.path.join(optimized_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Stored selected {orientation} photo to {filepath}")
    
    return filepath


def load_selected_photos(post_id: int, section_id: int) -> Dict[str, Optional[Dict]]:
    """
    Load selected landscape and portrait photos from optimized/ directory.
    
    Args:
        post_id: Post ID
        section_id: Section ID
    
    Returns:
        Dictionary with 'landscape' and 'portrait' keys, values are metadata dicts or None
    """
    optimized_dir = f"static/content/posts/{post_id}/sections/{section_id}/optimized"
    
    result = {
        'landscape': None,
        'portrait': None
    }
    
    for orientation in ('landscape', 'portrait'):
        filepath = os.path.join(optimized_dir, f"selected_{orientation}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    result[orientation] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading selected {orientation} photo: {e}")
    
    return result

