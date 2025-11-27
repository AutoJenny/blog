"""Heuristic pre-filtering for quirky news articles.

This service scores articles based on keywords and section preferences
before expensive LLM classification, helping narrow the candidate pool.
"""

from __future__ import annotations

from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


# Positive keywords that suggest quirky/local interest stories
POSITIVE_KEYWORDS = [
    'gala', 'fete', 'ceilidh', 'parade', 'village hall', 'school fair',
    'fundraiser', 'charity', 'duck race', 'pipe band', 'festival', 'pet show',
    'community', 'local hero', 'village', 'town', 'celebration', 'gathering',
    'highland games', 'tartan', 'bagpipes', 'haggis', 'burns night',
    'st andrew', 'scottish', 'scotland', 'highlands', 'islands',
    'whisky', 'whiskey', 'distillery', 'castle', 'heritage',
    'tradition', 'custom', 'folklore', 'storytelling', 'music',
    'dancing', 'dance', 'concert', 'performance', 'exhibition',
    'museum', 'gallery', 'art', 'craft', 'handmade', 'local produce',
    'farmer', 'market', 'shop', 'business', 'award', 'prize',
    'competition', 'contest', 'winner', 'champion', 'achievement',
    'milestone', 'anniversary', 'opening', 'launch', 'unveiling',
]

# Negative keywords that suggest serious/not-quirky content
NEGATIVE_KEYWORDS = [
    'court', 'sentenced', 'murder', 'crash', 'budget', 'tax', 'crime',
    'stabbing', 'assault', 'robbery', 'theft', 'arrest', 'police',
    'investigation', 'trial', 'verdict', 'jail', 'prison', 'sentence',
    'death', 'died', 'killed', 'fatal', 'accident', 'emergency',
    'crisis', 'disaster', 'flood', 'fire', 'storm', 'warning',
    'alert', 'danger', 'risk', 'threat', 'violence', 'attack',
    'protest', 'strike', 'dispute', 'conflict', 'war', 'battle',
    'politics', 'election', 'vote', 'campaign', 'party', 'mps',
    'parliament', 'government', 'council', 'councillor', 'mayor',
    'budget', 'cuts', 'funding', 'finance', 'money', 'cost',
    'price', 'fee', 'charge', 'payment', 'debt', 'loan',
]

# Section names that are preferred for quirky content
PREFERRED_SECTIONS = [
    'community', 'lifestyle', 'what\'s on', 'events', 'entertainment',
    'culture', 'heritage', 'local', 'features', 'people', 'society',
    'leisure', 'arts', 'music', 'food', 'drink', 'tourism',
]

# Section names to exclude
EXCLUDED_SECTIONS = [
    'crime', 'court', 'breaking', 'politics', 'business', 'finance',
    'sport', 'sports', 'weather', 'obituaries', 'death notices',
]


def calculate_heuristic_score(item: Dict[str, Any], source_config: Dict[str, Any] = None) -> tuple[float, List[str]]:
    """Calculate heuristic score for an article.
    
    Args:
        item: Article item with title, snippet, category, etc.
        source_config: Optional source configuration with preferred/excluded sections
    
    Returns:
        Tuple of (score, flags) where score is numeric and flags is list of matched keywords
    """
    score = 0.0
    flags = []
    
    # Get text to analyze
    title = item.get('title', '').lower()
    snippet = item.get('raw_data', {}).get('description', '') or item.get('raw_data', {}).get('summary', '')
    snippet = snippet.lower() if snippet else ''
    text = f"{title} {snippet}"
    
    # Section-based weighting
    section = item.get('category', '').lower()
    source_preferred = source_config.get('preferred_sections', []) if source_config else []
    source_excluded = source_config.get('excluded_sections', []) if source_config else []
    
    # Check against source-specific preferred sections
    if source_preferred:
        for pref_section in source_preferred:
            if pref_section.lower() in section or section in pref_section.lower():
                score += 2.0
                flags.append(f"preferred_section:{pref_section}")
                break
    
    # Check against source-specific excluded sections
    if source_excluded:
        for excl_section in source_excluded:
            if excl_section.lower() in section or section in excl_section.lower():
                score -= 5.0
                flags.append(f"excluded_section:{excl_section}")
                break
    
    # Check against global preferred sections
    for pref_section in PREFERRED_SECTIONS:
        if pref_section in section or section in pref_section:
            score += 1.5
            flags.append(f"section:{pref_section}")
            break
    
    # Check against global excluded sections
    for excl_section in EXCLUDED_SECTIONS:
        if excl_section in section or section in excl_section:
            score -= 4.0
            flags.append(f"excluded:{excl_section}")
            break
    
    # Keyword-based weighting
    positive_matches = []
    for keyword in POSITIVE_KEYWORDS:
        if keyword in text:
            score += 0.5
            positive_matches.append(keyword)
    
    if positive_matches:
        flags.append(f"positive_keywords:{','.join(positive_matches[:5])}")  # Limit flags
    
    negative_matches = []
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in text:
            score -= 1.0
            negative_matches.append(keyword)
    
    if negative_matches:
        flags.append(f"negative_keywords:{','.join(negative_matches[:5])}")
    
    # Boost for local/community indicators
    local_indicators = ['local', 'community', 'village', 'town', 'area', 'region']
    local_count = sum(1 for ind in local_indicators if ind in text)
    if local_count >= 2:
        score += 1.0
        flags.append("local_focus")
    
    # Boost for event/celebration indicators
    event_indicators = ['event', 'celebration', 'festival', 'gathering', 'meeting']
    event_count = sum(1 for ind in event_indicators if ind in text)
    if event_count >= 2:
        score += 0.5
        flags.append("event_focus")
    
    return (score, flags)


def score_quirky_items(items: List[Dict[str, Any]], source_configs: Dict[str, Dict[str, Any]] = None,
                       threshold: float = 3.0) -> List[Dict[str, Any]]:
    """Score a list of items and filter by threshold.
    
    Args:
        items: List of article items
        source_configs: Dict mapping source_name to source config
        threshold: Minimum heuristic score to include
    
    Returns:
        List of items with heuristic_score and heuristic_flags added, filtered by threshold
    """
    if source_configs is None:
        source_configs = {}
    
    scored = []
    for item in items:
        source_name = item.get('source_name', '')
        source_config = source_configs.get(source_name, {})
        
        score, flags = calculate_heuristic_score(item, source_config)
        
        item['heuristic_score'] = score
        item['heuristic_flags'] = flags
        
        if score >= threshold:
            scored.append(item)
    
    # Sort by heuristic score descending
    scored.sort(key=lambda x: x.get('heuristic_score', 0), reverse=True)
    
    return scored

