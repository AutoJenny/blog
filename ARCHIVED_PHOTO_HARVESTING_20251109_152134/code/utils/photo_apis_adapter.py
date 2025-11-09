"""
Photo APIs Adapter

Minimal adapter that wraps individual provider searches and result merging
to keep blueprints lean. This module does not contain any network logic; it
delegates to the existing utils.photo_apis helpers.
"""

from typing import List, Dict

# Re-use existing helpers (keep single source of truth)
from utils.photo_apis import search_pexels as _search_pexels
from utils.photo_apis import search_unsplash as _search_unsplash
from utils.photo_apis import merge_search_results as _merge_search_results


def run_photo_search(provider: str, pexels_key: str | None, unsplash_key: str | None,
                     search_term: str, per_page: int, orientation: str | None = None) -> List[Dict]:
    """
    Execute provider-specific search(es) and return a combined list of results.

    provider: 'pexels' | 'unsplash' | 'both'
    orientation: Optional filter: 'landscape', 'portrait', 'square' (Pexels) or 'squarish' (Unsplash)
                 Note: 'square' maps to 'squarish' for Unsplash, and vice versa
    """
    results: List[Dict] = []
    pexels_results: List[Dict] = []
    unsplash_results: List[Dict] = []
    
    # Normalize orientation for each provider
    pexels_orientation = orientation
    unsplash_orientation = orientation
    if orientation == "square":
        unsplash_orientation = "squarish"
    elif orientation == "squarish":
        pexels_orientation = "square"

    if provider in ("pexels", "both") and pexels_key:
        pexels_results = _search_pexels(pexels_key, search_term, per_page, pexels_orientation)

    if provider in ("unsplash", "both") and unsplash_key:
        unsplash_results = _search_unsplash(unsplash_key, search_term, per_page, unsplash_orientation)
        # Ensure Unsplash attribution and hotlink fields are present
        for item in unsplash_results or []:
            item.setdefault('provider', 'unsplash')
            api = item.get('api_response') or {}
            user = api.get('user') or {}
            name = user.get('name') or item.get('photographer') or 'Unknown'
            # Hotlink original URL if provided
            links = api.get('links') or {}
            raw_url = (api.get('urls') or {}).get('raw') or links.get('download') or item.get('url')
            if raw_url:
                item.setdefault('url', raw_url)
                item.setdefault('thumbnail_url', (api.get('urls') or {}).get('small') or raw_url)
            # Credits line
            if not item.get('credits'):
                item['credits'] = f"Photo by {name} on Unsplash"
            # Store download_location for later download trigger
            if links.get('download_location'):
                item.setdefault('download_location', links['download_location'])

    if provider == "both":
        results = _merge_search_results(pexels_results, unsplash_results)
    elif provider == "pexels":
        results = pexels_results
    else:  # 'unsplash'
        results = unsplash_results

    return results


