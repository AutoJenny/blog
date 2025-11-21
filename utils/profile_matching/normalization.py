"""
Normalization and Selection Module

Provides weighted random selection for choosing best match type
(product, supplier, category) based on similarity scores.
"""

import random
import logging

logger = logging.getLogger(__name__)


def normalize_and_select_best(products: list, suppliers: list, categories: list) -> dict:
    """
    Normalize scores and randomly select type with weighted probability.
    
    Process:
    1. Get top score from each type (or 0 if empty)
    2. Normalize each to 0-1 range (min-max within available scores)
    3. Apply exponential weighting (score^2) to favor higher scores
    4. Normalize weights to probabilities
    5. Randomly select type based on probabilities
    6. Return selected type with its top match
    
    This ensures variety while preferring better matches.
    
    Args:
        products: List of product match dicts with 'score' key
        suppliers: List of supplier match dicts with 'score' key
        categories: List of category match dicts with 'score' key
        
    Returns:
        Dictionary with:
        - 'type': 'product'|'supplier'|'category'
        - 'match': Selected match dict
        - 'normalized_score': float (0-1)
        - 'probabilities': dict with probabilities for each type
        Or None if no matches available
    """
    # Get top scores
    product_score = products[0]['score'] if products else 0.0
    supplier_score = suppliers[0]['score'] if suppliers else 0.0
    category_score = categories[0]['score'] if categories else 0.0
    
    # Collect non-zero scores for normalization
    scores = [s for s in [product_score, supplier_score, category_score] if s > 0]
    if not scores:
        logger.warning("No matches with scores > 0 available")
        return None
    
    # Min-max normalize
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        # All same - equal probability
        normed = [1.0, 1.0, 1.0]
    else:
        normed = [
            (product_score - min_score) / (max_score - min_score) if product_score > 0 else 0,
            (supplier_score - min_score) / (max_score - min_score) if supplier_score > 0 else 0,
            (category_score - min_score) / (max_score - min_score) if category_score > 0 else 0
        ]
    
    # Apply exponential weighting (favor higher scores but keep randomness)
    weights = [s**2 for s in normed]
    
    # Normalize to probabilities
    total = sum(weights)
    if total == 0:
        # All zero - equal probability
        probs = [1/3, 1/3, 1/3]
    else:
        probs = [w / total for w in weights]
    
    # Random selection based on probabilities
    rand = random.random()
    if rand < probs[0] and products:
        selected_type = 'product'
        selected_match = products[0]
        normalized_score = normed[0]
    elif rand < probs[0] + probs[1] and suppliers:
        selected_type = 'supplier'
        selected_match = suppliers[0]
        normalized_score = normed[1]
    elif categories:
        selected_type = 'category'
        selected_match = categories[0]
        normalized_score = normed[2]
    else:
        # Fallback: return highest score regardless of type
        all_matches = []
        if products:
            all_matches.append(('product', products[0], normed[0]))
        if suppliers:
            all_matches.append(('supplier', suppliers[0], normed[1]))
        if categories:
            all_matches.append(('category', categories[0], normed[2]))
        
        if not all_matches:
            return None
        
        all_matches.sort(key=lambda x: x[2], reverse=True)
        selected_type, selected_match, normalized_score = all_matches[0]
    
    return {
        'type': selected_type,
        'match': selected_match,
        'normalized_score': normalized_score,
        'probabilities': {
            'product': probs[0],
            'supplier': probs[1],
            'category': probs[2]
        }
    }

