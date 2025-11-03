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
                     search_term: str, per_page: int) -> List[Dict]:
    """
    Execute provider-specific search(es) and return a combined list of results.

    provider: 'pexels' | 'unsplash' | 'both'
    """
    results: List[Dict] = []
    pexels_results: List[Dict] = []
    unsplash_results: List[Dict] = []

    if provider in ("pexels", "both") and pexels_key:
        pexels_results = _search_pexels(pexels_key, search_term, per_page)

    if provider in ("unsplash", "both") and unsplash_key:
        unsplash_results = _search_unsplash(unsplash_key, search_term, per_page)

    if provider == "both":
        results = _merge_search_results(pexels_results, unsplash_results)
    elif provider == "pexels":
        results = pexels_results
    else:  # 'unsplash'
        results = unsplash_results

    return results


