"""
Normalize core_type values - unify duplicates and variations
- Case variations (e.g., "Kilt" -> "kilt")
- Plural/singular (e.g., "kilts" -> "kilt")
- Underscore variations (e.g., "kilt_pin" vs "kiltpin")
- Common abbreviations
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import re
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of variations to canonical form
CORE_TYPE_NORMALIZATION = {
    # Case variations
    'Kilt': 'kilt',
    'Shirt': 'shirt',
    'Sporran': 'sporran',
    'Tie': 'tie',
    'Belt': 'belt',
    'Scarf': 'scarf',
    'Hat': 'hat',
    'Jacket': 'jacket',
    'Sweater': 'sweater',
    'Ring': 'ring',
    'Necklace': 'necklace',
    'Bracelet': 'bracelet',
    'Earring': 'earring',
    'Pendant': 'pendant',
    'Brooch': 'brooch',
    'Charm': 'charm',
    'Pin': 'pin',
    'Bag': 'bag',
    'Backpack': 'backpack',
    'Purse': 'purse',
    'Wallet': 'wallet',
    'Flask': 'flask',
    'Quaich': 'quaich',
    'Glass': 'glass',
    'Mug': 'mug',
    'Plaque': 'plaque',
    'Print': 'print',
    'Painting': 'painting',
    'Picture': 'picture',
    'Map': 'map',
    'Poster': 'poster',
    'Canvas': 'canvas',
    
    # Plural variations (convert to singular)
    'kilts': 'kilt',
    'shirts': 'shirt',
    'sporrans': 'sporran',
    'ties': 'tie',
    'belts': 'belt',
    'scarves': 'scarf',
    'hats': 'hat',
    'jackets': 'jacket',
    'sweaters': 'sweater',
    'rings': 'ring',
    'necklaces': 'necklace',
    'bracelets': 'bracelet',
    'earrings': 'earring',
    'pendants': 'pendant',
    'brooches': 'brooch',
    'charms': 'charm',
    'pins': 'pin',
    'bags': 'bag',
    'backpacks': 'backpack',
    'purses': 'purse',
    'wallets': 'wallet',
    'flasks': 'flask',
    'quaichs': 'quaich',
    'glasses': 'glass',
    'mugs': 'mug',
    'plaques': 'plaque',
    'prints': 'print',
    'paintings': 'painting',
    'pictures': 'picture',
    'maps': 'map',
    'posters': 'poster',
    'canvases': 'canvas',
    
    # Underscore/hyphen variations
    'kiltpin': 'kilt_pin',
    'kilt-pin': 'kilt_pin',
    'kilts_pin': 'kilt_pin',
    'tiepin': 'tie_pin',
    'tie-pin': 'tie_pin',
    'tie_slide': 'tie_slide',
    'tieslide': 'tie_slide',
    'tie-slide': 'tie_slide',
    'bowtie': 'bow_tie',
    'bow-tie': 'bow_tie',
    'bow_ties': 'bow_tie',
    'pocket_square': 'pocket_square',
    'pocketsquare': 'pocket_square',
    'pocket-square': 'pocket_square',
    'drink_coaster': 'drink_coaster',
    'drinkcoaster': 'drink_coaster',
    'drink-coaster': 'drink_coaster',
    'letter_opener': 'letter_opener',
    'letteropener': 'letter_opener',
    'letter-opener': 'letter_opener',
    'pencil_case': 'pencil_case',
    'pencilcase': 'pencil_case',
    'pencil-case': 'pencil_case',
    'pet_bowl': 'pet_bowl',
    'petbowl': 'pet_bowl',
    'pet-bowl': 'pet_bowl',
    'tote_bag': 'tote_bag',
    'totebag': 'tote_bag',
    'tote-bag': 'tote_bag',
    'shopping_bag': 'shopping_bag',
    'shoppingbag': 'shopping_bag',
    'shopping-bag': 'shopping_bag',
    'gym_bag': 'gym_bag',
    'gymbag': 'gym_bag',
    'gym-bag': 'gym_bag',
    'duffle_bag': 'duffle_bag',
    'dufflebag': 'duffle_bag',
    'duffle-bag': 'duffle_bag',
    'crossbody_bag': 'crossbody_bag',
    'crossbodybag': 'crossbody_bag',
    'crossbody-bag': 'crossbody_bag',
    'bum_bag': 'bum_bag',
    'bumbag': 'bum_bag',
    'bum-bag': 'bum_bag',
    'clutch_bag': 'clutch_bag',
    'clutchbag': 'clutch_bag',
    'clutch-bag': 'clutch_bag',
    'drawstring_bag': 'drawstring_bag',
    'drawstringbag': 'drawstring_bag',
    'drawstring-bag': 'drawstring_bag',
    'handbag': 'handbag',
    'hand_bag': 'handbag',
    'hand-bag': 'handbag',
    'embroidery_kit': 'embroidery_kit',
    'embroiderykit': 'embroidery_kit',
    'embroidery-kit': 'embroidery_kit',
    'treat_bag': 'treat_bag',
    'treatbag': 'treat_bag',
    'treat-bag': 'treat_bag',
    
    # Common abbreviations
    'sgian_dubh': 'sgian_dubh',
    'sgian_dubhs': 'sgian_dubh',
    'sgian-dubh': 'sgian_dubh',
    'sgian dubh': 'sgian_dubh',
}

def normalize_core_type(core_type):
    """
    Normalize a core_type to its canonical form.
    """
    if not core_type:
        return None
    
    # Check direct mapping first
    if core_type in CORE_TYPE_NORMALIZATION:
        return CORE_TYPE_NORMALIZATION[core_type]
    
    # Check lowercase
    core_type_lower = core_type.lower()
    if core_type_lower in CORE_TYPE_NORMALIZATION:
        return CORE_TYPE_NORMALIZATION[core_type_lower]
    
    # Check normalized (no underscores, hyphens)
    normalized = core_type_lower.replace('_', '').replace('-', '').replace(' ', '')
    if normalized in CORE_TYPE_NORMALIZATION:
        return CORE_TYPE_NORMALIZATION[normalized]
    
    # Default: lowercase and replace spaces/hyphens with underscores
    normalized = re.sub(r'[\s-]+', '_', core_type_lower.strip())
    return normalized

def normalize_all_core_types():
    """
    Normalize all core_type values in the database.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all products with core_type
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    product_type_data
                FROM clan_products
                WHERE product_type_data->>'core_type' IS NOT NULL
            """)
            
            products = cursor.fetchall()
            logger.info(f"Processing {len(products)} products with core_type")
            
            updated_count = 0
            changes = defaultdict(int)
            
            for product in products:
                product_id = product['id']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                
                if not current_core_type:
                    continue
                
                # Normalize
                normalized = normalize_core_type(current_core_type)
                
                # Update if changed
                if normalized != current_core_type:
                    type_data['core_type'] = normalized
                    changes[f"{current_core_type} -> {normalized}"] += 1
                    
                    cursor.execute("""
                        UPDATE clan_products
                        SET product_type_data = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(type_data), product_id))
                    
                    updated_count += 1
                    if updated_count % 100 == 0:
                        logger.info(f"Updated {updated_count} products...")
            
            conn.commit()
            logger.info(f"Normalization complete. Updated {updated_count} products.")
            
            # Show summary of changes
            print(f"\n✅ Normalization Summary:")
            print(f"   Total products updated: {updated_count}")
            print(f"\n   Top changes:")
            for change, count in sorted(changes.items(), key=lambda x: x[1], reverse=True)[:20]:
                print(f"     {change}: {count} products")
            
            # Verify final unique count
            cursor.execute("""
                SELECT COUNT(DISTINCT product_type_data->>'core_type') as count
                FROM clan_products
                WHERE product_type_data->>'core_type' IS NOT NULL
            """)
            final_unique = cursor.fetchone()['count']
            
            print(f"\n✅ Final unique core_types: {final_unique}")
            
            return updated_count

if __name__ == '__main__':
    try:
        count = normalize_all_core_types()
        print(f"\n✅ Successfully normalized {count} core_type values")
    except Exception as e:
        logger.error(f"Error normalizing core_types: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

