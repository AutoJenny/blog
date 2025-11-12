"""
Product Type Parser

Systematically parses product titles into structured identifiers using a hybrid approach:
1. Strict pattern matching (fast, reliable)
2. Category context analysis (uses existing category data)
3. LLM disambiguation (for ambiguous cases)
4. Validation & normalization (ensures consistency)
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ProductTypeParser:
    """Parses product titles into structured type identifiers."""
    
    # Strict pattern dictionaries
    ACCESSORY_SUFFIXES = ['pin', 'keyring', 'key fob', 'slide', 'brooch', 'charm', 'key chain']
    ARTWORK_SUFFIXES = ['painting', 'print', 'artwork', 'poster', 'plaque']
    JEWELRY_TYPES = ['ring', 'earrings', 'bracelet', 'necklace', 'pendant']
    
    SUBTYPES = {
        'jacobite', 'jacobean', 'ghillie', 'argyll', 'prince charlie', 'prince charles',
        'dress', 'casual', 'daywear', 'wedding', 'formal', 'semi dress', 'semi-dress',
        'mini', 'full', 'box pleat', 'knife pleat', 'plain top', 'studded'
    }
    
    MATERIALS = {
        'tweed', 'cashmere', 'wool', 'leather', 'silk', 'cotton', 'polyester',
        'poly', 'linen', 'suede', 'antler', 'horn', 'oxhorn', 'stag', 'rabbit', 'fur',
        'glass', 'wood', 'metal', 'silver', 'gold', 'brass', 'chrome',
        'fabric', 'slate', 'ceramic', 'tartan'
    }
    
    PATTERNS = {
        'tartan', 'plaid', 'check', 'plain', 'striped', 'checked'
    }
    
    DECORATIONS = {
        'clan crest', 'celtic', 'thistle', 'stag', 'studded', 'lion rampant',
        'sword', 'knot', 'rose', 'shamrock', 'dragon',
        'rust-proof eyelets', 'rust proof eyelets', 'eyelets',
        'thick leather tie', 'leather tie'
    }
    
    OCCASIONS = {
        'wedding', 'formal', 'casual', 'daywear', 'evening', 'day', 'night'
    }
    
    STYLES = {
        'box pleat', 'knife pleat', 'prince charlie', 'prince charles', 'argyll',
        'jacobite', 'ghillie', 'plain top', 'studded'
    }
    
    ATTRIBUTES = {
        'mini', 'full', 'adjustable', 'made to measure', 'custom', 'antique',
        'vintage', 'traditional', 'modern', 'contemporary'
    }
    
    # Master core type list
    CORE_TYPES = {
        # Garments
        'kilt', 'shirt', 'jacket', 'waistcoat', 'sporran', 'tie', 'bow_tie',
        'cummerbund', 'scarf', 'tam', 'hat', 'brogues', 'shoes', 'boots',
        'trews', 'skirt', 'dress', 'trousers', 'sweater', 'cardigan',
        'hoodie', 'shorts', 'sports_bra', 'poncho', 'crop_top', 'tank_top',
        'flip_flops', 'rash_guard', 'swimsuit', 'swim_trunks',
        # Accessories
        'kilt_pin', 'tie_slide', 'keyring', 'key_fob', 'flask', 'bag',
        'belt', 'buckle', 'comb', 'sporran_chain', 'hose', 'garters', 'garter',
        'pin', 'duffle_bag', 'tote_bag', 'shopping_bag', 'backpack',
        # Jewelry
        'ring', 'earrings', 'bracelet', 'necklace', 'brooch', 'charm',
        'cufflinks', 'pendant',
        # Artwork/Homeware
        'painting', 'print', 'artwork', 'poster', 'plaque', 'cushion',
        'blanket', 'rug', 'tartan_fabric', 'chopping_board', 'board',
        'fabric', 'swatch', 'glasses', 'mouse_mat', 'drink_coaster',
        'pet_bowl', 'door_mat', 'bath_mat', 'laptop_sleeve', 'notebook',
        'mug', 'magnet', 'flag', 'ornament', 'place_mat', 'bar_runner',
        'pencil_case', 'tea_towel', 'towel', 'sash', 'ribbon', 'cup',
        'cups', 'tankard', 'decanter', 'quaich', 'hip_flask', 'flask',
        'shot_glass', 'dram_glass', 'whisky_glass', 'tumbler', 'buttons',
        'button', 'zip_pull', 'letter_opener', 'drinking_horn', 'throw',
        'stole', 'pocket_watch', 'watch', 'socks', 'hose', 'braces',
        'serape', 'gloves', 'jumper', 'sweater', 'hair_bobble', 'bobble',
        'hair_tie', 'hair_accessory', 'glass', 'candlestick', 'trinket_box',
        'knitwear', 'voucher', 'gift', 'necklace', 'bangle', 'pocket_square',
        'handbag_accessory', 'drinking_vessels', 'fabrics', 'suit', 'cutlery',
        'utensil', 'face_mask', 'book', 'slipover', 'wallet', 'purse',
        'cufflinks', 'picture', 'embroidery_kit', 'sewing_kit', 'crafts_kit',
        'headband', 'bandana', 'jersey', 'top', 'leggings', 'bikini',
        'gym_bag', 'egg_spoon', 'spoon', 'utensils', 'jewelry', 'artwork',
        'peeler', 'mustard_dab', 'cheese_knife', 'knife', 'coin', 'sixpence',
        'boxer_briefs', 'briefs', 'underwear',
        'shoehorn', 'shoe_horn',
        # Other
        'bear', 'toy', 'gift_set', 'outfit'
    }
    
    def __init__(self, llm_service=None):
        """
        Initialize parser.
        
        Args:
            llm_service: LLM service instance (optional)
        """
        if llm_service is None:
            try:
                from blueprints.llm_actions import LLMService
                self.llm_service = LLMService()
            except ImportError:
                logger.warning("LLM service not available, LLM parsing will be disabled")
                self.llm_service = None
        else:
            self.llm_service = llm_service
    
    def parse_product(self, product_name: str, category_ids: List[int], 
                     description: Optional[str] = None) -> Dict:
        """
        Main parsing method - hybrid approach.
        
        Args:
            product_name: Product title
            category_ids: List of category IDs (can be None)
            description: Product description (optional, first 200 chars used)
            
        Returns:
            Dictionary with parsed type data including confidence score
        """
        if not product_name:
            return self._empty_result()
        
        # Normalize category_ids - handle None
        if category_ids is None:
            category_ids = []
        elif not isinstance(category_ids, list):
            category_ids = []
        
        # Phase 1: Strict pattern matching
        strict_result = self._strict_parse(product_name, category_ids)
        
        # Phase 2: Category context
        category_result = self._apply_category_context(strict_result, category_ids, product_name)
        
        # Phase 3: LLM if needed
        if category_result['confidence'] < 0.8:
            llm_result = self._llm_parse(product_name, category_ids, description)
            if llm_result:
                # Merge results, preferring LLM for ambiguous fields
                final_result = self._merge_results(category_result, llm_result)
            else:
                final_result = category_result
        else:
            final_result = category_result
        
        # Phase 4: Validation & normalization
        final_result = self._validate_and_normalize(final_result, category_ids, product_name)
        
        return final_result
    
    def _strict_parse(self, name: str, category_ids: List[int]) -> Dict:
        """Phase 1: Pattern matching."""
        name_lower = name.lower()
        result = {
            'core_type': None,
            'subtype': None,
            'level': self._parse_level(name),
            'materials': [],
            'patterns': [],
            'decorations': [],
            'occasions': [],
            'styles': [],
            'attributes': [],
            'disambiguation': {
                'is_accessory': False,
                'is_artwork': False,
                'is_jewelry': False,
                'is_clothing': False,
                'product_form': None
            },
            'confidence': 0.5,
            'parsing_method': 'strict'
        }
        
        # Check for accessory indicators
        # Use word boundaries to avoid false matches (e.g., "pin" in "pinafore")
        for suffix in self.ACCESSORY_SUFFIXES:
            # Check if suffix appears as a complete word
            suffix_pattern = r'\b' + re.escape(suffix) + r'\b'
            if name_lower.endswith(suffix) or re.search(suffix_pattern, name_lower):
                # Additional check: exclude "pin" if it's part of "pinafore"
                if suffix == 'pin' and 'pinafore' in name_lower:
                    continue
                result['disambiguation']['is_accessory'] = True
                result['disambiguation']['product_form'] = 'accessory'
                # Extract core type from context
                if 'kilt' in name_lower and re.search(r'\bpin\b', name_lower):
                    result['core_type'] = 'kilt_pin'
                elif 'tie' in name_lower and 'slide' in name_lower:
                    result['core_type'] = 'tie_slide'
                elif 'keyring' in name_lower or 'key fob' in name_lower:
                    result['core_type'] = 'keyring' if 'keyring' in name_lower else 'key_fob'
                else:
                    result['core_type'] = suffix.replace(' ', '_')
                result['confidence'] = 0.85
                break
        
        # Check for artwork indicators
        if not result['disambiguation']['is_accessory']:
            for suffix in self.ARTWORK_SUFFIXES:
                if name_lower.endswith(suffix) or f' {suffix}' in name_lower:
                    result['disambiguation']['is_artwork'] = True
                    result['disambiguation']['product_form'] = 'artwork'
                    result['core_type'] = suffix.replace(' ', '_')
                    result['confidence'] = 0.85
                    break
        
        # Check for jewelry (but not keyring)
        if not result['disambiguation']['is_accessory'] and not result['disambiguation']['is_artwork']:
            for jewelry_type in self.JEWELRY_TYPES:
                if jewelry_type in name_lower and 'keyring' not in name_lower:
                    result['disambiguation']['is_jewelry'] = True
                    result['disambiguation']['product_form'] = 'jewelry'
                    result['core_type'] = jewelry_type.replace(' ', '_')
                    result['confidence'] = 0.85
                    break
        
        # Extract materials, patterns, decorations, etc.
        result['materials'] = [m for m in self._extract_keywords(name_lower, self.MATERIALS) if m != 'unknown']
        
        # Special handling: if "oxhorn" appears in name, ensure it's in materials
        if 'oxhorn' in name_lower and 'oxhorn' not in result['materials']:
            result['materials'].append('oxhorn')
        
        result['patterns'] = [p for p in self._extract_keywords(name_lower, self.PATTERNS) if p != 'unknown']
        result['decorations'] = [d for d in self._extract_keywords(name_lower, self.DECORATIONS) if d != 'unknown']
        result['occasions'] = [o for o in self._extract_keywords(name_lower, self.OCCASIONS) if o != 'unknown']
        result['styles'] = [s for s in self._extract_keywords(name_lower, self.STYLES) if s != 'unknown']
        result['attributes'] = [a for a in self._extract_keywords(name_lower, self.ATTRIBUTES) if a != 'unknown']
        
        # Extract subtype
        for subtype in self.SUBTYPES:
            if subtype in name_lower:
                result['subtype'] = subtype.replace(' ', '_')
                break
        
        # If no core_type determined yet, try to infer from name
        if not result['core_type']:
            # First check compound names (multi-word core types)
            # Order matters: longer/more specific matches first
            # Handle both singular and plural forms
            compound_names = [
                ('athletic long shorts', 'shorts'),
                ('long sleeve crop top', 'crop_top'),
                ('chopping board', 'chopping_board'),
                ('chopping boards', 'chopping_board'),
                ('drink coaster', 'drink_coaster'),
                ('drink coasters', 'drink_coaster'),
                ('drinks coaster', 'drink_coaster'),
                ('drinks coasters', 'drink_coaster'),
                ('mouse mat', 'mouse_mat'),
                ('mouse mats', 'mouse_mat'),
                ('laptop sleeve', 'laptop_sleeve'),
                ('laptop sleeves', 'laptop_sleeve'),
                ('pet bowl', 'pet_bowl'),
                ('pet bowls', 'pet_bowl'),
                ('door mat', 'door_mat'),
                ('door mats', 'door_mat'),
                ('bath mat', 'bath_mat'),
                ('bath mats', 'bath_mat'),
                ('crop top', 'crop_top'),
                ('crop tops', 'crop_top'),
                ('sports bra', 'sports_bra'),
                ('sports bras', 'sports_bra'),
                ('tank top', 'tank_top'),
                ('tank tops', 'tank_top'),
                ('flip flops', 'flip_flops'),
                ('flip-flops', 'flip_flops'),
                ('rash guard', 'rash_guard'),
                ('rash guards', 'rash_guard'),
                ('swim trunks', 'swim_trunks'),
                ('swimsuit', 'swimsuit'),
                ('swimsuits', 'swimsuit'),
                ('place mat', 'place_mat'),
                ('place mats', 'place_mat'),
                ('bar runner', 'bar_runner'),
                ('bar runners', 'bar_runner'),
                ('pencil case', 'pencil_case'),
                ('pencil cases', 'pencil_case'),
                ('tote bag', 'tote_bag'),
                ('tote bags', 'tote_bag'),
                ('shopping bag', 'shopping_bag'),
                ('shopping bags', 'shopping_bag'),
                ('duffle bag', 'duffle_bag'),
                ('duffle bags', 'duffle_bag'),
                ('long shorts', 'shorts'),
                ('large mouse mat', 'mouse_mat'),
                ('yoga leggings', 'leggings'),
                ('plus size leggings', 'leggings'),
                ('letter opener', 'letter_opener'),
                ('handled letter opener', 'letter_opener'),
                ('orange peeler', 'peeler'),
                ('cheese knife', 'knife'),
                ('boxer briefs', 'boxer_briefs'),
                ('cross stitch', 'embroidery_kit'),
                ('cross stitch kit', 'embroidery_kit'),
                ('shoehorn', 'shoehorn'),
                ('shoe horn', 'shoehorn'),
                ('shoehorns', 'shoehorn'),
                ('shoe horns', 'shoehorn'),
            ]
            
            for compound, core_type in compound_names:
                if compound in name_lower:
                    if core_type in self.CORE_TYPES:
                        result['core_type'] = core_type
                        # Determine product form
                        if core_type in ['hoodie', 'shorts', 'sports_bra', 'crop_top', 'tank_top', 'shirt', 'dress']:
                            result['disambiguation']['is_clothing'] = True
                            result['disambiguation']['product_form'] = 'garment'
                        elif core_type in ['mouse_mat', 'drink_coaster', 'pet_bowl', 'door_mat', 'bath_mat', 
                                          'laptop_sleeve', 'notebook', 'mug', 'magnet', 'flag', 'ornament', 
                                          'place_mat', 'bar_runner', 'pencil_case', 'chopping_board', 'shoehorn']:
                            result['disambiguation']['product_form'] = 'homeware'
                        elif core_type in ['pin', 'duffle_bag', 'tote_bag', 'shopping_bag', 'backpack']:
                            result['disambiguation']['is_accessory'] = True
                            result['disambiguation']['product_form'] = 'accessory'
                        result['confidence'] = 0.75
                        break
            
            # Then check single-word core types (garments and others)
            if not result['core_type']:
                garment_keywords = {
                    'kilt': 'kilt', 'shirt': 'shirt', 'jacket': 'jacket',
                    'waistcoat': 'waistcoat', 'sporran': 'sporran', 'tie': 'tie',
                    'scarf': 'scarf', 'tam': 'tam', 'hat': 'hat', 'skirt': 'skirt',
                    'dress': 'dress', 'trousers': 'trousers', 'sweater': 'sweater',
                    'cardigan': 'cardigan', 'cummerbund': 'cummerbund',
                    'hoodie': 'hoodie', 'shorts': 'shorts', 'poncho': 'poncho',
                    'swatch': 'swatch', 'mug': 'mug', 'magnet': 'magnet',
                    'flag': 'flag', 'ornament': 'ornament', 'notebook': 'notebook',
                    'backpack': 'backpack', 'garter': 'garter',
                    'jumper': 'jumper', 'socks': 'socks', 'hose': 'hose',
                    'braces': 'braces', 'gloves': 'gloves', 'sash': 'sash',
                    'ribbon': 'ribbon', 'towel': 'towel', 'tea_towel': 'tea_towel',
                    'cup': 'cup', 'cups': 'cup', 'tankard': 'tankard',
                    'decanter': 'decanter', 'quaich': 'quaich', 'flask': 'flask',
                    'hip_flask': 'hip_flask', 'throw': 'throw', 'blanket': 'blanket',
                    'stole': 'stole', 'serape': 'serape', 'pocket_watch': 'pocket_watch',
                    'watch': 'watch', 'buttons': 'buttons', 'button': 'button',
                    'letter_opener': 'letter_opener', 'drinking_horn': 'drinking_horn',
                    'hair_bobble': 'hair_bobble', 'bobble': 'bobble',
                    'glass': 'glass', 'glasses': 'glasses', 'candlestick': 'candlestick',
                    'trinket_box': 'trinket_box', 'knitwear': 'knitwear', 'voucher': 'voucher',
                    'gift': 'gift', 'necklace': 'necklace', 'bangle': 'bangle',
                    'pocket_square': 'pocket_square', 'handbag_accessory': 'handbag_accessory',
                    'cufflinks': 'cufflinks', 'picture': 'picture', 'book': 'book',
                    'slipover': 'slipover', 'wallet': 'wallet', 'purse': 'purse',
                    'headband': 'headband', 'bandana': 'bandana', 'jersey': 'jersey',
                    'top': 'top', 'leggings': 'leggings', 'bikini': 'bikini',
                    'gym_bag': 'gym_bag', 'cushion': 'cushion', 'face_mask': 'face_mask',
                    'spoon': 'spoon', 'egg_spoon': 'egg_spoon', 'comb': 'comb',
                    'peeler': 'peeler', 'mustard dab': 'utensil', 'mustard_dab': 'utensil',
                    'cheese knife': 'knife', 'cheese_knife': 'knife', 'knife': 'knife',
                    'sixpence': 'coin', 'coin': 'coin', 'boxer briefs': 'boxer_briefs',
                    'boxer_briefs': 'boxer_briefs', 'briefs': 'briefs', 'underwear': 'underwear',
                    'cross stitch': 'embroidery_kit', 'cross_stitch': 'embroidery_kit',
                    'shoehorn': 'shoehorn', 'shoe horn': 'shoehorn'
                }
                
                # Check other keywords first (before pins to avoid false matches)
                for keyword, core_type in garment_keywords.items():
                    if keyword in name_lower:
                        result['core_type'] = core_type
                        if core_type in ['kilt', 'shirt', 'jacket', 'waistcoat', 'sporran', 'tie', 
                                       'scarf', 'tam', 'hat', 'skirt', 'dress', 'trousers', 
                                       'sweater', 'cardigan', 'cummerbund', 'hoodie', 'shorts', 
                                       'poncho', 'crop_top', 'tank_top']:
                            result['disambiguation']['is_clothing'] = True
                            result['disambiguation']['product_form'] = 'garment'
                        elif core_type in ['swatch', 'mug', 'magnet', 'flag', 'ornament', 'notebook', 'shoehorn']:
                            result['disambiguation']['product_form'] = 'homeware'
                        elif core_type == 'garter':
                            result['disambiguation']['is_accessory'] = True
                            result['disambiguation']['product_form'] = 'accessory'
                        result['confidence'] = 0.70
                        break
                
                # Check for pins (handle various pin types) - AFTER garment keywords
                # Be careful: "pin" in "pinafore" should not match
                if not result.get('core_type'):
                    if re.search(r'\bpin\b', name_lower) and 'pinafore' not in name_lower:
                        # Check for specific pin types first
                        if 'kilt' in name_lower and re.search(r'\bpin\b', name_lower):
                            result['core_type'] = 'kilt_pin'
                            result['disambiguation']['is_accessory'] = True
                            result['disambiguation']['product_form'] = 'accessory'
                            result['confidence'] = 0.80
                        elif (('tie' in name_lower or 'lapel' in name_lower) and 
                              re.search(r'\bpin\b', name_lower)):
                            result['core_type'] = 'pin'
                            result['disambiguation']['is_accessory'] = True
                            result['disambiguation']['product_form'] = 'accessory'
                            result['confidence'] = 0.80
                        elif (name_lower.endswith(' pin') or ' pin ' in name_lower or 
                              name_lower.startswith('pin ') or name_lower.endswith(' pins')):
                            result['core_type'] = 'pin'
                            result['disambiguation']['is_accessory'] = True
                            result['disambiguation']['product_form'] = 'accessory'
                            result['confidence'] = 0.80
        
        return result
    
    def _apply_category_context(self, result: Dict, category_ids: List[int], 
                               product_name: str) -> Dict:
        """Phase 2: Use category to refine parsing."""
        if not category_ids:
            return result
        
        try:
            from config.database import db_manager
            
            with db_manager.get_cursor() as cursor:
                placeholders = ','.join(['%s'] * len(category_ids))
                cursor.execute(f"""
                    SELECT id, name, parent_id, level
                    FROM clan_categories
                    WHERE id IN ({placeholders})
                    ORDER BY level DESC
                """, tuple(category_ids))
                
                categories = cursor.fetchall()
                category_names = [cat['name'].lower() for cat in categories]
                category_path = ' > '.join([cat['name'] for cat in categories])
                
                # Use category to determine core_type if not set
                if not result['core_type']:
                    # Map category names to core types
                    # Use exact matches first, then word-boundary matches for precision
                    category_to_type = {
                        'kilt': 'kilt', 'kilts': 'kilt',
                        'shirt': 'shirt', 'shirts': 'shirt',
                        'sporran': 'sporran', 'sporrans': 'sporran',
                        'ring': 'ring', 'rings': 'ring',
                        'jacket': 'jacket', 'jackets': 'jacket',
                        'waistcoat': 'waistcoat', 'waistcoats': 'waistcoat',
                        'tie': 'tie', 'ties': 'tie',
                        'scarf': 'scarf', 'scarves': 'scarf',
                        'hat': 'hat', 'hats': 'hat',
                        'skirt': 'skirt', 'skirts': 'skirt',
                        'dress': 'dress', 'dresses': 'dress'
                    }
                    
                    cat_name_lower = ' '.join(category_names).lower()
                    
                    # First, try exact category name matches (highest confidence)
                    for cat_name in category_names:
                        cat_lower = cat_name.lower()
                        for keyword, core_type in category_to_type.items():
                            # Exact match (category name IS the keyword)
                            if cat_lower == keyword or cat_lower == keyword + 's':
                                result['core_type'] = core_type
                                if not result['disambiguation']['product_form']:
                                    result['disambiguation']['is_clothing'] = True
                                    result['disambiguation']['product_form'] = 'garment'
                                result['confidence'] = min(result['confidence'] + 0.2, 0.9)
                                break
                        if result['core_type']:
                            break
                    
                    # If no exact match, try word-boundary matching (lower confidence)
                    # This prevents "kilt" matching "Kilts & Highlandwear"
                    if not result['core_type']:
                        for cat_name in category_names:
                            cat_lower = cat_name.lower()
                            for keyword, core_type in category_to_type.items():
                                # Use word boundaries to match whole words only
                                pattern = r'\b' + re.escape(keyword) + r'\b'
                                if re.search(pattern, cat_lower):
                                    # Check if category is too broad (contains "&" or multiple words)
                                    # Broad categories get lower confidence
                                    is_broad = '&' in cat_name or len(cat_name.split()) > 2
                                    
                                    result['core_type'] = core_type
                                    if not result['disambiguation']['product_form']:
                                        result['disambiguation']['is_clothing'] = True
                                        result['disambiguation']['product_form'] = 'garment'
                                    
                                    # Lower confidence for broad categories
                                    if is_broad:
                                        result['confidence'] = min(result['confidence'] + 0.05, 0.7)
                                    else:
                                        result['confidence'] = min(result['confidence'] + 0.1, 0.8)
                                    break
                            if result['core_type']:
                                break
                
                # Refine disambiguation based on category
                if 'accessor' in ' '.join(category_names) or 'pin' in ' '.join(category_names):
                    if 'kilt' in ' '.join(category_names) and 'pin' in ' '.join(category_names):
                        result['disambiguation']['is_accessory'] = True
                        result['disambiguation']['product_form'] = 'accessory'
                        result['core_type'] = 'kilt_pin'
                        result['confidence'] = min(result['confidence'] + 0.1, 0.95)
                
                if 'jeweller' in ' '.join(category_names) or 'jewelry' in ' '.join(category_names):
                    if not result['disambiguation']['is_accessory']:
                        result['disambiguation']['is_jewelry'] = True
                        result['disambiguation']['product_form'] = 'jewelry'
                        result['confidence'] = min(result['confidence'] + 0.1, 0.95)
                
                if 'artwork' in ' '.join(category_names) or 'homeware' in ' '.join(category_names):
                    result['disambiguation']['is_artwork'] = True
                    result['disambiguation']['product_form'] = 'artwork'
                    result['confidence'] = min(result['confidence'] + 0.1, 0.95)
                
                result['parsing_method'] = 'hybrid'
                
        except Exception as e:
            logger.error(f"Error applying category context: {e}")
        
        return result
    
    def _llm_parse(self, name: str, category_ids: List[int], 
                   description: Optional[str] = None) -> Optional[Dict]:
        """Phase 3: LLM disambiguation for ambiguous cases."""
        if not self.llm_service:
            return None
        
        try:
            from config.database import db_manager
            
            # Get category names
            category_names = []
            if category_ids:
                with db_manager.get_cursor() as cursor:
                    placeholders = ','.join(['%s'] * len(category_ids))
                    cursor.execute(f"""
                        SELECT name FROM clan_categories
                        WHERE id IN ({placeholders})
                    """, tuple(category_ids))
                    category_names = [row['name'] for row in cursor.fetchall()]
            
            category_context = ' > '.join(category_names) if category_names else 'Unknown'
            desc_snippet = (description[:200] if description else '') or 'No description available'
            
            prompt = f"""Parse this product title into structured identifiers:

Product: {name}
Categories: {category_context}
Description: {desc_snippet}

Context: We need to distinguish between:
- A kilt (garment) vs kilt pin (accessory) vs painting of a kilt (artwork)
- A ring (jewelry) vs keyring (accessory)
- A shirt (garment) vs shirt pin (accessory)

Extract and return JSON only with these fields:
{{
  "core_type": "string (e.g., kilt, shirt, sporran, ring, kilt_pin)",
  "subtype": "string or null (e.g., jacobite, dress, wedding)",
  "materials": ["array of materials"],
  "patterns": ["array of patterns"],
  "decorations": ["array of decorative elements"],
  "occasions": ["array of occasions/uses"],
  "styles": ["array of style identifiers"],
  "attributes": ["array of other attributes"],
  "disambiguation": {{
    "is_accessory": boolean,
    "is_artwork": boolean,
    "is_jewelry": boolean,
    "is_clothing": boolean,
    "product_form": "garment|accessory|jewelry|artwork|homeware|other"
  }},
  "confidence": 0.0-1.0
}}

Return only valid JSON, no markdown formatting."""
            
            messages = [
                {'role': 'system', 'content': 'You are a product classification expert. Parse product titles into structured identifiers. Return only valid JSON.'},
                {'role': 'user', 'content': prompt}
            ]
            
            # Use Ollama first for bulk processing (free, local)
            # Only use OpenAI if explicitly needed for high-priority tasks
            result = self.llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if result and 'error' in result:
                # Log error but don't fallback to OpenAI for bulk processing
                logger.warning(f"Ollama parsing failed: {result.get('error')}, skipping LLM parsing for this product")
                return None
            
            if result and result.get('content'):
                content = result['content'].strip()
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                try:
                    llm_data = json.loads(content)
                    llm_data['parsing_method'] = 'llm'
                    return llm_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM JSON response: {e}")
                    logger.debug(f"LLM response: {content}")
                    return None
            
        except Exception as e:
            logger.error(f"Error in LLM parsing: {e}")
            return None
        
        return None
    
    def _merge_results(self, strict_result: Dict, llm_result: Dict) -> Dict:
        """Merge strict and LLM results, preferring LLM for ambiguous fields."""
        merged = strict_result.copy()
        
        # Prefer LLM for core_type if it's more confident
        if llm_result.get('core_type') and not merged.get('core_type'):
            merged['core_type'] = llm_result['core_type']
        
        # Merge arrays (union)
        for field in ['materials', 'patterns', 'decorations', 'occasions', 'styles', 'attributes']:
            merged[field] = list(set(merged.get(field, []) + llm_result.get(field, [])))
        
        # Prefer LLM disambiguation if it's more specific
        if llm_result.get('disambiguation'):
            llm_disambig = llm_result['disambiguation']
            for key in ['is_accessory', 'is_artwork', 'is_jewelry', 'is_clothing']:
                if llm_disambig.get(key):
                    merged['disambiguation'][key] = llm_disambig[key]
            if llm_disambig.get('product_form'):
                merged['disambiguation']['product_form'] = llm_disambig['product_form']
        
        # Use higher confidence
        merged['confidence'] = max(merged.get('confidence', 0.5), llm_result.get('confidence', 0.5))
        merged['parsing_method'] = 'hybrid'
        
        return merged
    
    def _validate_and_normalize(self, result: Dict, category_ids: List[int], product_name: str = None) -> Dict:
        """Phase 4: Validation and normalization."""
        # Validate core_type with normalization
        if result.get('core_type'):
            core_type = result['core_type']
            
            # Normalize: lowercase, replace spaces with underscores
            core_type_normalized = core_type.lower().strip().replace(' ', '_')
            
            # Validation: Check if product name suggests a different core type
            # This helps catch cases where category-based inference overrides product name
            if product_name:
                name_lower = product_name.lower()
                
                # List of product name keywords that should take precedence over category
                name_priority_keywords = {
                    'shoehorn': 'shoehorn', 'shoe horn': 'shoehorn',
                    'letter opener': 'letter_opener', 'letter_opener': 'letter_opener',
                    'peeler': 'peeler', 'orange peeler': 'peeler',
                    'cheese knife': 'knife', 'cheese_knife': 'knife',
                    'drink coaster': 'drink_coaster', 'drink_coaster': 'drink_coaster',
                    'mouse mat': 'mouse_mat', 'mouse_mat': 'mouse_mat',
                    'laptop sleeve': 'laptop_sleeve', 'laptop_sleeve': 'laptop_sleeve',
                    'pet bowl': 'pet_bowl', 'pet_bowl': 'pet_bowl',
                    'door mat': 'door_mat', 'door_mat': 'door_mat',
                    'bath mat': 'bath_mat', 'bath_mat': 'bath_mat',
                    'place mat': 'place_mat', 'place_mat': 'place_mat',
                    'bar runner': 'bar_runner', 'bar_runner': 'bar_runner',
                    'pencil case': 'pencil_case', 'pencil_case': 'pencil_case',
                    'chopping board': 'chopping_board', 'chopping_board': 'chopping_board',
                }
                
                # Check if product name contains a priority keyword
                for keyword, expected_type in name_priority_keywords.items():
                    if keyword in name_lower:
                        # If category-based inference conflicts with product name, prefer product name
                        if core_type_normalized != expected_type and expected_type in self.CORE_TYPES:
                            logger.warning(
                                f"Product name '{product_name}' suggests '{expected_type}' but "
                                f"category inference gave '{core_type_normalized}'. Preferring product name."
                            )
                            core_type_normalized = expected_type
                            result['confidence'] = max(0.6, result.get('confidence', 0.5) - 0.1)
                        break
            
            # Handle common variations and synonyms
            type_mappings = {
                'homeware': None,  # Too generic
                'home_accessories': None,  # Too generic
                'drinking_horn': 'drinking_horn',
                'drinking_vessel': 'cup',  # Map to generic cup
                'drinking_vessels': 'cup',
                'letter_opener': 'letter_opener',
                'trinket_box': 'trinket_box',
                'gift': None,  # Too generic
                'necklace': 'necklace',
                'pocket_square': 'pocket_square',
                'fabrics': 'fabric',
                'suits': 'suit',
                'face_mask': 'face_mask',
                'picture': 'artwork',  # Map to artwork
                'embroidery_kit': 'embroidery_kit',
                'sewing_kit': 'sewing_kit',
                'crafts_kit': 'sewing_kit',
                'jewellery': 'jewelry',  # British spelling
                'garment': None,  # Too generic
                'gym_bag': 'gym_bag',
                'zip_pull': 'zip_pull',
                'zip_pulls': 'zip_pull',
                'letter_opener': 'letter_opener',
                'peeler': 'peeler',
                'mustard_dab': 'utensil',
                'cheese_knife': 'knife',
                'knife': 'knife',
                'sixpence': 'coin',
                'coin': 'coin',
                'boxer_briefs': 'boxer_briefs',
                'briefs': 'briefs',
                'underwear': 'underwear',
                'cross_stitch': 'embroidery_kit',
            }
            
            # Check normalized form first
            if core_type_normalized in self.CORE_TYPES:
                result['core_type'] = core_type_normalized
            elif core_type_normalized in type_mappings:
                mapped = type_mappings[core_type_normalized]
                if mapped and mapped in self.CORE_TYPES:
                    result['core_type'] = mapped
                elif mapped is None:
                    # Generic type - set to None
                    logger.warning(f"Generic core_type: {core_type}, setting to None")
                    result['core_type'] = None
                    result['confidence'] = max(0.0, result.get('confidence', 0.5) - 0.2)
                else:
                    logger.warning(f"Unknown core_type: {core_type}, setting to None")
                    result['core_type'] = None
                    result['confidence'] = max(0.0, result.get('confidence', 0.5) - 0.2)
            elif core_type not in self.CORE_TYPES:
                logger.warning(f"Unknown core_type: {core_type}, setting to None")
                result['core_type'] = None
                result['confidence'] = max(0.0, result.get('confidence', 0.5) - 0.2)
        
        # Normalize: lowercase, remove duplicates, sort
        for field in ['materials', 'patterns', 'decorations', 'occasions', 'styles', 'attributes']:
            if result.get(field):
                result[field] = sorted(list(set([item.lower().strip() for item in result[field] if item])))
        
        # Normalize subtype
        if result.get('subtype'):
            result['subtype'] = result['subtype'].lower().strip().replace(' ', '_')
        
        # Normalize core_type
        if result.get('core_type'):
            result['core_type'] = result['core_type'].lower().strip().replace(' ', '_')
        
        # Build type_hierarchy
        hierarchy = []
        if result.get('disambiguation', {}).get('product_form'):
            hierarchy.append(result['disambiguation']['product_form'])
        if result.get('core_type'):
            hierarchy.append(result['core_type'])
        if result.get('subtype'):
            hierarchy.append(f"{result['core_type']}_{result['subtype']}")
        result['type_hierarchy'] = hierarchy
        
        # Build type_keywords
        keywords = []
        if result.get('core_type'):
            keywords.append(result['core_type'])
        if result.get('subtype'):
            keywords.append(result['subtype'])
        keywords.extend(result.get('materials', []))
        keywords.extend(result.get('patterns', []))
        keywords.extend(result.get('decorations', []))
        result['type_keywords'] = sorted(list(set(keywords)))
        
        # Add metadata
        result['parsed_at'] = datetime.utcnow().isoformat()
        
        return result
    
    def _parse_level(self, name: str) -> str:
        """Parse product level (already implemented in product_level.py)."""
        from utils.product_level import parse_product_level
        return parse_product_level(name)
    
    def _extract_keywords(self, text: str, keyword_set: set) -> List[str]:
        """Extract keywords from text that match keyword_set."""
        found = []
        text_lower = text.lower()
        for keyword in keyword_set:
            if keyword in text_lower:
                found.append(keyword.replace(' ', '_'))
        return found
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'core_type': None,
            'subtype': None,
            'level': 'classic',
            'materials': [],
            'patterns': [],
            'decorations': [],
            'occasions': [],
            'styles': [],
            'attributes': [],
            'disambiguation': {
                'is_accessory': False,
                'is_artwork': False,
                'is_jewelry': False,
                'is_clothing': False,
                'product_form': None
            },
            'type_hierarchy': [],
            'type_keywords': [],
            'parsed_at': datetime.utcnow().isoformat(),
            'parsing_method': 'none',
            'confidence': 0.0
        }

