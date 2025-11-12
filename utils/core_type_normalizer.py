"""
LLM-Based Core Type Normalizer

Reviews and normalizes core_type values considering:
1. Product Form context (core_type must be appropriate for its product_form)
2. Synonym unification (tam/bobble → headwear, vest/waistcoat)
3. Mis-assignment correction (core_type doesn't match product name/description)
4. Hierarchical relationships (subtypes should be unified to parent types)

Uses semantic LLM analysis to understand context and make intelligent corrections.
"""

import json
import logging
import re
from typing import Dict, Optional, List, Tuple
from blueprints.llm_actions import LLMService

logger = logging.getLogger(__name__)

# Known synonym mappings (will be expanded by LLM)
SYNONYM_MAPPINGS = {
    'tam': 'headwear',
    'bobble': 'headwear',
    'vest': 'waistcoat',
    'waistcoat': 'waistcoat',  # Keep as canonical
}

# Core type hierarchy (parent → children)
TYPE_HIERARCHY = {
    'headwear': ['tam', 'bobble', 'hat', 'cap', 'beret'],
    'waistcoat': ['vest', 'waistcoat'],
    'footwear': ['brogues', 'shoes', 'boots', 'slippers'],
    'top': ['shirt', 'sweater', 'cardigan', 'tank_top', 'crop_top'],
    'bag': ['backpack', 'tote_bag', 'purse', 'clutch', 'wallet'],
    'jewellery': ['ring', 'necklace', 'bracelet', 'earrings', 'brooch', 'charm', 'pendant', 'cufflinks'],
    'accessory': ['kilt_pin', 'tie', 'scarf', 'belt', 'buckle', 'sporran'],
}

# Product Form → Valid Core Types (examples, not exhaustive)
FORM_CORE_TYPE_EXAMPLES = {
    'clothing': ['kilt', 'shirt', 'jacket', 'waistcoat', 'sporran', 'tie', 'scarf', 'headwear', 'footwear', 'trousers', 'skirt', 'dress'],
    'jewellery': ['ring', 'necklace', 'bracelet', 'earrings', 'brooch', 'charm', 'pendant', 'cufflinks'],
    'bags': ['backpack', 'tote_bag', 'purse', 'clutch', 'wallet', 'bag'],
    'homeware': ['flask', 'quaich', 'mug', 'glass', 'drink_coaster', 'letter_opener', 'cushion', 'rug'],
    'pets': ['pet_bowl', 'bandana', 'treat_bag', 'collar', 'lead'],
    'recreation': ['embroidery_kit', 'jigsaw', 'toy', 'bear'],
    'artwork': ['painting', 'print', 'plaque', 'poster'],
    'stationery': ['notebook', 'pencil_case', 'journal'],
    'haberdashery': ['button', 'ribbon', 'thread', 'fabric', 'swatch'],
    'voucher': ['voucher'],
}


class CoreTypeNormalizer:
    """Uses LLM to normalize and correct core_type values."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize core type normalizer.
        
        Args:
            llm_service: LLMService instance (creates new one if not provided)
        """
        self.llm_service = llm_service or LLMService()
    
    def normalize_core_type(self,
                           product_name: str,
                           current_core_type: str,
                           product_form: str,
                           description: Optional[str] = None) -> Dict:
        """
        Normalize a core_type considering product context.
        
        Args:
            product_name: Product name/title
            current_core_type: Current core_type value
            product_form: Product form category
            description: Product description (optional)
            
        Returns:
            Dictionary with:
            - core_type: Normalized core_type
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Brief explanation
            - change_type: 'synonym', 'misassignment', 'hierarchy', 'none'
            - error: Error message if normalization failed
        """
        try:
            # Build valid core types for this product_form
            valid_types_text = ""
            if product_form in FORM_CORE_TYPE_EXAMPLES:
                valid_types_text = f"Valid core types for {product_form}: {', '.join(FORM_CORE_TYPE_EXAMPLES[product_form][:20])}"
            
            # Build synonym examples
            synonym_examples = "\n".join([
                f"- {k} → {v}" for k, v in SYNONYM_MAPPINGS.items()
            ])
            
            # Build hierarchy examples
            hierarchy_examples = "\n".join([
                f"- {parent}: {', '.join(children)}" 
                for parent, children in TYPE_HIERARCHY.items() 
                if len(children) > 0
            ])
            
            # Clean description
            desc_snippet = ""
            if description:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(description, 'html.parser')
                clean_desc = soup.get_text().strip()[:200]
                desc_snippet = clean_desc if clean_desc else ""
            
            prompt = f"""Review and normalize this product's core_type:

Product: "{product_name}"
Current core_type: {current_core_type}
Product Form: {product_form}
Description: {desc_snippet or 'No description available'}

{valid_types_text}

Rules:
1. **Synonym Unification**: Unify synonyms to canonical forms:
{synonym_examples}

2. **Hierarchical Normalization**: If a subtype exists, consider if it should be the parent type:
{hierarchy_examples}
   - Example: "tam" or "bobble" → "headwear" (they are subtypes of headwear)
   - Example: "vest" → "waistcoat" (they are synonyms)
   - Only unify if the parent type is more appropriate

3. **Product Form Validation**: core_type must be appropriate for product_form:
   - clothing: garments, accessories worn with clothing
   - jewellery: rings, necklaces, charms, etc.
   - bags: backpacks, purses, wallets, etc.
   - If core_type doesn't match product_form, correct it

4. **Mis-assignment Detection**: If core_type doesn't match product name/description, correct it:
   - Example: Product name says "Tam" but core_type is "hat" → should be "headwear"
   - Example: Product name says "Waistcoat" but core_type is "vest" → should be "waistcoat"

Return JSON only with these fields:
{{
    "core_type": "normalized_core_type (canonical form)",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "change_type": "synonym|hierarchy|misassignment|form_correction|none"
}}

Return only valid JSON, no markdown formatting."""

            messages = [
                {
                    'role': 'system',
                    'content': 'You are a product taxonomy expert. Normalize core_type values to canonical forms, considering product context and form. Return only valid JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Use Ollama (free, local)
            result = self.llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if result and 'error' in result:
                return {
                    'core_type': current_core_type,  # Keep original on error
                    'confidence': 0.0,
                    'reasoning': None,
                    'change_type': 'none',
                    'error': result.get('error')
                }
            
            content = result.get('content', '') if result else ''
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    normalization = json.loads(json_str)
                    
                    new_core_type = normalization.get('core_type', current_core_type)
                    
                    # Determine if changed
                    change_type = 'none'
                    if new_core_type != current_core_type:
                        change_type = normalization.get('change_type', 'misassignment')
                    
                    return {
                        'core_type': new_core_type,
                        'confidence': float(normalization.get('confidence', 0.0)),
                        'reasoning': normalization.get('reasoning', ''),
                        'change_type': change_type,
                        'error': None
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM JSON response: {e}, content: {content[:200]}")
                    return {
                        'core_type': current_core_type,
                        'confidence': 0.0,
                        'reasoning': None,
                        'change_type': 'none',
                        'error': f"JSON parse error: {e}"
                    }
            else:
                logger.error(f"No JSON found in LLM response: {content[:200]}")
                return {
                    'core_type': current_core_type,
                    'confidence': 0.0,
                    'reasoning': None,
                    'change_type': 'none',
                    'error': "No JSON found in response"
                }
                
        except Exception as e:
            logger.error(f"Error normalizing core_type for {product_name}: {e}", exc_info=True)
            return {
                'core_type': current_core_type,
                'confidence': 0.0,
                'reasoning': None,
                'change_type': 'none',
                'error': str(e)
            }
    
    def normalize_batch(self,
                       products: List[Dict],
                       confidence_threshold: float = 0.8) -> Dict:
        """
        Normalize multiple products in batch.
        
        Args:
            products: List of product dicts with 'name', 'core_type', 'product_form', etc.
            confidence_threshold: Minimum confidence for auto-apply
            
        Returns:
            Dictionary with:
            - high_confidence: Products with confidence > threshold
            - review_queue: Products with confidence <= threshold
            - errors: Products that failed normalization
        """
        high_confidence = []
        review_queue = []
        errors = []
        
        for product in products:
            result = self.normalize_core_type(
                product_name=product.get('name', ''),
                current_core_type=product.get('core_type', ''),
                product_form=product.get('product_form', ''),
                description=product.get('description')
            )
            
            if result.get('error'):
                errors.append({
                    'product': product,
                    'error': result['error']
                })
            elif result.get('core_type') != product.get('core_type'):
                # Only include if changed
                if result.get('confidence', 0.0) > confidence_threshold:
                    high_confidence.append({
                        'product': product,
                        'normalization': result
                    })
                else:
                    review_queue.append({
                        'product': product,
                        'normalization': result
                    })
        
        return {
            'high_confidence': high_confidence,
            'review_queue': review_queue,
            'errors': errors
        }

