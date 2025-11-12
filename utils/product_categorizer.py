"""
LLM-Based Product Categorizer

Uses semantic understanding via LLM to categorize products into product_form categories.
More reliable than pattern matching - understands context and handles edge cases.
"""

import json
import logging
import re
from typing import Dict, Optional, List
# Import LLMService from blueprints.llm_actions (same as product_type_parser)
from blueprints.llm_actions import LLMService

logger = logging.getLogger(__name__)

# Category definitions for LLM
CATEGORY_DEFINITIONS = {
    'clothing': 'Items worn on the body. Includes garments (kilts, shirts, jackets, sweaters, skirts, dresses) and accessories worn with clothing (ties, belts, sporrans, kilt pins, scarves, waistcoats, cufflinks).',
    'jewellery': 'Items worn as jewellery. Includes rings, necklaces, bracelets, brooches, charms, pendants, earrings, watches. Note: Charms are jewellery items (e.g., "teddy bear charm" is jewellery, not a toy).',
    'bags': 'Items for carrying or storing things. Includes backpacks, purses, wallets, totes, shopping bags, pencil cases, clutches, crossbody bags, gym bags, duffle bags.',
    'homeware': 'Items for home use. Includes flasks, quaichs, glasses, mugs, coasters, letter openers, decorative items, keyrings, laptop sleeves, shoehorns, napkin rings.',
    'pets': 'Items specifically for pets (dogs, cats). Includes dog bandanas, pet bowls, treat bags, collars, leads. Must be clearly for pets - not just items with "dog" or "cat" in the name.',
    'recreation': 'Leisure activities and games. Includes toys (teddy bears, cuddly toys), jigsaws, puzzles, embroidery kits, cross stitch kits, board games. Note: Embroidery kits are recreation, but embroidery decorations on clothing are clothing.',
    'artwork': 'Items that hang on walls for decoration. Includes paintings, prints, plaques, maps, pictures, posters, canvas art. Must be wall art - not functional items.',
    'stationery': 'Writing and office supplies. Includes notebooks, pencil cases, journals, diaries, writing supplies.',
    'haberdashery': 'Sewing and craft supplies. Includes buttons, ribbons, thread, needles, fabric swatches.',
    'voucher': 'Gift vouchers and certificates.'
}

# Examples for each category
CATEGORY_EXAMPLES = {
    'clothing': [
        'Balmoral Kilt',
        'Jacobite Shirt',
        'Antique Thistle Kilt Pin',
        'Tartan Tie',
        'Leather Sporran'
    ],
    'jewellery': [
        'Silver Celtic Knot Ring',
        'Teddy Bear Charm - C114',
        'Clan Crest Brooch',
        'Celtic Pendant Necklace'
    ],
    'bags': [
        'Tartan Classic Backpack',
        'Clan Crest Tote Bag',
        'Small Tartan Coin Purse',
        'Tartan Pencil Case'
    ],
    'homeware': [
        'Clan Crest Quaich',
        'Lion of Scotland Hip Flask',
        'Tartan Drink Coasters',
        'Celtic Knot Letter Opener'
    ],
    'pets': [
        'Handmade Tartan Dog Bandana',
        'Clan Crest Pet Bowl',
        'Handmade Tartan Dog Treat Bag'
    ],
    'recreation': [
        'Angus the Highland Bear',
        'Cross Stitch Celtic Cross Kit',
        'Scottish Thistle Jigsaw Puzzle'
    ],
    'artwork': [
        'Clan Crest Wall Plaque',
        'Clan Map Of Scotland',
        'Childhood - Set of 2 Prints'
    ],
    'stationery': [
        'Tartan Spiral Notebook',
        'Clan Crest Pencil Case'
    ],
    'haberdashery': [
        'Oxhorn Buttons (Set of Six)',
        'Tartan Ribbon, 10mm wide'
    ],
    'voucher': [
        'CLAN Gift Voucher'
    ]
}


class ProductCategorizer:
    """Uses LLM to categorize products semantically."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize product categorizer.
        
        Args:
            llm_service: LLMService instance (creates new one if not provided)
        """
        self.llm_service = llm_service or LLMService()
    
    def categorize_product(self, 
                          product_name: str,
                          description: Optional[str] = None,
                          current_category: Optional[str] = None,
                          current_core_type: Optional[str] = None) -> Dict:
        """
        Categorize a product using LLM semantic analysis.
        
        Args:
            product_name: Product name/title
            description: Product description (first 200 chars)
            current_category: Current product_form (if any)
            current_core_type: Current core_type (if any)
            
        Returns:
            Dictionary with:
            - product_form: Recommended category
            - core_type: Recommended core_type
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Brief explanation
            - error: Error message if categorization failed
        """
        try:
            # Build category definitions text
            categories_text = "\n".join([
                f"- {cat}: {desc}"
                for cat, desc in CATEGORY_DEFINITIONS.items()
            ])
            
            # Build examples text
            examples_text = "\n".join([
                f"- {cat}: {', '.join(examples[:3])}"
                for cat, examples in CATEGORY_EXAMPLES.items()
            ])
            
            # Clean description
            desc_snippet = ""
            if description:
                # Remove HTML tags
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(description, 'html.parser')
                clean_desc = soup.get_text().strip()[:200]
                desc_snippet = clean_desc if clean_desc else ""
            
            prompt = f"""Categorize this product into one of these categories:

Categories:
{categories_text}

Product: "{product_name}"
Description: {desc_snippet or 'No description available'}
Current category: {current_category or 'None'}
Current core_type: {current_core_type or 'None'}

Examples of correctly categorized products:
{examples_text}

Important distinctions:
- "Teddy bear charm" is jewellery (it's a charm), not recreation (not a toy)
- "Embroidery kit" is recreation (activity), but "embroidery decoration" on clothing is clothing
- "Dog bandana" is pets, but "tartan bandana" (for humans) is clothing
- "Framed handbag" is bags (functional item), not artwork (not wall art)
- Charms are jewellery, not toys, even if they depict toys

Return JSON only with these fields:
{{
    "product_form": "category_name (one of: clothing, jewellery, bags, homeware, pets, recreation, artwork, stationery, haberdashery, voucher)",
    "core_type": "specific_type (e.g., kilt, ring, backpack, teddy_bear, embroidery_kit)",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this category"
}}

Return only valid JSON, no markdown formatting, no code blocks."""

            messages = [
                {
                    'role': 'system',
                    'content': 'You are a product categorization expert. Categorize products accurately based on their function and use. Return only valid JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Use Ollama (free, local)
            # Same approach as product_type_parser - no intercept_context needed
            result = self.llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if result and 'error' in result:
                return {
                    'product_form': None,
                    'core_type': None,
                    'confidence': 0.0,
                    'reasoning': None,
                    'error': result.get('error')
                }
            
            content = result.get('content', '') if result else ''
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    categorization = json.loads(json_str)
                    
                    # Validate and clean product_form
                    valid_forms = list(CATEGORY_DEFINITIONS.keys())
                    product_form = categorization.get('product_form', '').strip()
                    
                    # Handle cases where LLM returns description instead of category name
                    # Extract category name if it's in parentheses or after colon
                    if product_form and product_form not in valid_forms:
                        # Try to extract category from common patterns
                        for form in valid_forms:
                            if form in product_form.lower():
                                product_form = form
                                break
                    
                    if product_form not in valid_forms:
                        logger.warning(f"Invalid product_form: {categorization.get('product_form')}")
                        return {
                            'product_form': None,
                            'core_type': None,
                            'confidence': 0.0,
                            'reasoning': None,
                            'error': f"Invalid product_form: {categorization.get('product_form')}"
                        }
                    
                    return {
                        'product_form': product_form,
                        'core_type': categorization.get('core_type'),
                        'confidence': float(categorization.get('confidence', 0.0)),
                        'reasoning': categorization.get('reasoning', ''),
                        'error': None
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM JSON response: {e}, content: {content[:200]}")
                    return {
                        'product_form': None,
                        'core_type': None,
                        'confidence': 0.0,
                        'reasoning': None,
                        'error': f"JSON parse error: {e}"
                    }
            else:
                logger.error(f"No JSON found in LLM response: {content[:200]}")
                return {
                    'product_form': None,
                    'core_type': None,
                    'confidence': 0.0,
                    'reasoning': None,
                    'error': "No JSON found in response"
                }
                
        except Exception as e:
            logger.error(f"Error categorizing product {product_name}: {e}", exc_info=True)
            return {
                'product_form': None,
                'core_type': None,
                'confidence': 0.0,
                'reasoning': None,
                'error': str(e)
            }
    
    def categorize_batch(self, 
                         products: List[Dict],
                         confidence_threshold: float = 0.8) -> Dict:
        """
        Categorize multiple products in batch.
        
        Args:
            products: List of product dicts with 'name', 'description', etc.
            confidence_threshold: Minimum confidence for auto-apply
            
        Returns:
            Dictionary with:
            - high_confidence: Products with confidence > threshold
            - review_queue: Products with confidence <= threshold
            - errors: Products that failed categorization
        """
        high_confidence = []
        review_queue = []
        errors = []
        
        for product in products:
            result = self.categorize_product(
                product_name=product.get('name', ''),
                description=product.get('description'),
                current_category=product.get('product_form'),
                current_core_type=product.get('core_type')
            )
            
            if result.get('error'):
                errors.append({
                    'product': product,
                    'error': result['error']
                })
            elif result.get('confidence', 0.0) > confidence_threshold:
                high_confidence.append({
                    'product': product,
                    'categorization': result
                })
            else:
                review_queue.append({
                    'product': product,
                    'categorization': result
                })
        
        return {
            'high_confidence': high_confidence,
            'review_queue': review_queue,
            'errors': errors
        }

