"""
Photo API Integration Utilities

Provides standardized functions to query Pexels and Unsplash APIs
and normalize their responses into a common format.
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def search_pexels(api_key: str, query: str, per_page: int = 10) -> List[Dict]:
    """
    Search Pexels API for photos.
    
    Args:
        api_key: Pexels API key
        query: Search query string
        per_page: Number of results per page (max 80)
    
    Returns:
        List of standardized photo objects
    """
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {
            "Authorization": api_key
        }
        params = {
            "query": query,
            "per_page": min(per_page, 80)  # Pexels max is 80
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        photos = []
        
        for photo in data.get("photos", []):
            standardized = {
                "provider": "pexels",
                "image_id": str(photo.get("id", "")),
                "url": photo.get("src", {}).get("original", ""),
                "thumbnail_url": photo.get("src", {}).get("large", ""),
                "width": photo.get("width", 0),
                "height": photo.get("height", 0),
                "photographer": photo.get("photographer", ""),
                "photographer_url": photo.get("photographer_url", ""),
                "api_response": photo  # Store raw response for debugging
            }
            
            # Parse credits
            credits_data = parse_pexels_credits(photo)
            standardized.update(credits_data)
            standardized["search_term"] = query
            
            photos.append(standardized)
        
        logger.info(f"Pexels search returned {len(photos)} results for query: {query}")
        return photos
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Pexels API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error processing Pexels results: {e}")
        return []


def search_unsplash(api_key: str, query: str, per_page: int = 10) -> List[Dict]:
    """
    Search Unsplash API for photos.
    
    Args:
        api_key: Unsplash Access Key
        query: Search query string
        per_page: Number of results per page (max 30)
    
    Returns:
        List of standardized photo objects
    """
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {api_key}"
        }
        params = {
            "query": query,
            "per_page": min(per_page, 30)  # Unsplash max is 30
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        photos = []
        
        for photo in data.get("results", []):
            standardized = {
                "provider": "unsplash",
                "image_id": photo.get("id", ""),
                "url": photo.get("urls", {}).get("full", ""),
                "thumbnail_url": photo.get("urls", {}).get("regular", ""),
                "width": photo.get("width", 0),
                "height": photo.get("height", 0),
                "photographer": photo.get("user", {}).get("name", ""),
                "photographer_url": photo.get("user", {}).get("links", {}).get("html", ""),
                "api_response": photo  # Store raw response for debugging
            }
            
            # Parse credits
            credits_data = parse_unsplash_credits(photo)
            standardized.update(credits_data)
            standardized["search_term"] = query
            
            photos.append(standardized)
        
        logger.info(f"Unsplash search returned {len(photos)} results for query: {query}")
        return photos
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Unsplash API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error processing Unsplash results: {e}")
        return []


def parse_pexels_credits(photo_data: Dict) -> Dict:
    """
    Parse photographer credits from Pexels photo data.
    
    Args:
        photo_data: Raw photo object from Pexels API
    
    Returns:
        Dict with photographer, photographer_url, and credits fields
    """
    photographer = photo_data.get("photographer", "Unknown Photographer")
    photographer_url = photo_data.get("photographer_url", "")
    
    if photographer_url:
        credits = f"Photo by {photographer} on Pexels"
    else:
        credits = f"Photo by {photographer} on Pexels"
    
    return {
        "photographer": photographer,
        "photographer_url": photographer_url,
        "credits": credits
    }


def parse_unsplash_credits(photo_data: Dict) -> Dict:
    """
    Parse photographer credits from Unsplash photo data.
    
    Args:
        photo_data: Raw photo object from Unsplash API
    
    Returns:
        Dict with photographer, photographer_url, and credits fields
    """
    user = photo_data.get("user", {})
    photographer = user.get("name", "Unknown Photographer")
    photographer_url = user.get("links", {}).get("html", "")
    
    if photographer_url:
        credits = f"Photo by {photographer} on Unsplash"
    else:
        credits = f"Photo by {photographer} on Unsplash"
    
    return {
        "photographer": photographer,
        "photographer_url": photographer_url,
        "credits": credits
    }


def merge_search_results(pexels_results: List[Dict], unsplash_results: List[Dict]) -> List[Dict]:
    """
    Combine results from both providers, deduplicating by URL.
    
    Args:
        pexels_results: List of standardized Pexels photo objects
        unsplash_results: List of standardized Unsplash photo objects
    
    Returns:
        Combined list with deduplicated photos (maintains provider attribution)
    """
    merged = []
    seen_urls = set()
    
    # Add Pexels results first
    for photo in pexels_results:
        url = photo.get("url", "")
        if url and url not in seen_urls:
            merged.append(photo)
            seen_urls.add(url)
    
    # Add Unsplash results (skip if URL already seen)
    for photo in unsplash_results:
        url = photo.get("url", "")
        if url and url not in seen_urls:
            merged.append(photo)
            seen_urls.add(url)
    
    logger.info(f"Merged {len(pexels_results)} Pexels + {len(unsplash_results)} Unsplash = {len(merged)} unique photos")
    return merged

