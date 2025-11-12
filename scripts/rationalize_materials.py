"""
Rationalize Materials Tags

Cleans up materials tags to only include actual materials:
- Removes patterns (tartan, tweed, barathea)
- Removes marketing terms (finest quality, natural, british made)
- Splits composite materials (85% wool, 15% polyester → wool, polyester)
- Normalizes variations (pure new wool → wool, genuine leather → leather)
- Flags products with no materials
"""

import sys
sys.path.insert(0, '.')
import json
import re
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valid actual materials (not patterns, not marketing terms)
VALID_MATERIALS = {
    # Natural fibers
    'wool', 'cashmere', 'cotton', 'silk', 'linen', 'hemp', 'bamboo', 'alpaca', 'mohair',
    'lambswool', 'merino', 'merino_wool', 'new_wool', 'pure_wool', 'british_wool', 'scottish_wool',
    
    # Synthetic fibers
    'polyester', 'nylon', 'spandex', 'elastane', 'acrylic', 'polyviscose', 'microfibre', 'viscose',
    'recycled_polyester', 'polyester_spandex', 'polyester_elastane',
    
    # Leather & hides
    'leather', 'genuine_leather', 'bovine_leather', 'suede', 'fur', 'rabbit',
    
    # Metals
    'silver', 'sterling_silver', 'gold', 'brass', 'chrome', 'stainless_steel', 'metal', 'pewter',
    
    # Natural materials
    'antler', 'stag', 'horn', 'oxhorn', 'wood', 'cork', 'stone', 'slate',
    
    # Other materials
    'glass', 'ceramic', 'enamel', 'resin', 'rubber', 'paper', 'fabric', 'canvas'
}

# Patterns (should NOT be in materials - these are patterns, not materials)
PATTERNS_TO_REMOVE = {
    'tartan', 'plaid', 'check', 'checked', 'striped', 'plain', 'barathea', 'tweed'
}

# Marketing terms to remove
MARKETING_TERMS = {
    'finest quality', 'finest quality materials', 'quality', 'premium', 'luxury',
    'natural', 'natural materials', 'british made', 'scottish made', 'handmade',
    'traditional', 'authentic', 'genuine', 'pure', 'new'
}

# Material normalization mappings
MATERIAL_NORMALIZATIONS = {
    # Wool variations
    '100% pure new wool': 'wool',
    'pure new wool': 'wool',
    'new wool': 'wool',
    'pure wool': 'wool',
    'british wool': 'wool',
    'scottish wool': 'wool',
    'barathea wool': 'wool',  # barathea is a weave pattern, not a material
    'merino wool': 'merino_wool',
    'lambswool': 'wool',
    
    # Leather variations
    'genuine leather': 'leather',
    'bovine leather': 'leather',
    
    # Silver variations
    'sterling silver': 'silver',
    
    # Polyester variations
    '100% recycled polyester': 'recycled_polyester',
    'recycled polyester': 'recycled_polyester',
    'polyester spandex blend': 'polyester',  # Will be split separately
    'polyester spandex': 'polyester',  # Will be split separately
    
    # Horn variations
    'oxhorn': 'horn',
    'stag': 'antler',
    
    # Metal variations
    'stainless steel': 'stainless_steel',
}

def extract_percentage_materials(material_str):
    """
    Extract materials from percentage strings like "85% wool, 15% polyester"
    Returns list of material names.
    """
    materials = []
    
    # Pattern: "85% wool" or "26% elastane"
    percentage_pattern = r'(\d+)%\s+([a-z\s]+)'
    matches = re.findall(percentage_pattern, material_str.lower())
    
    for percentage, material in matches:
        material_clean = material.strip()
        # Normalize material name
        if material_clean in VALID_MATERIALS:
            materials.append(material_clean)
        elif material_clean in MATERIAL_NORMALIZATIONS:
            materials.append(MATERIAL_NORMALIZATIONS[material_clean])
        elif material_clean.replace(' ', '_') in VALID_MATERIALS:
            materials.append(material_clean.replace(' ', '_'))
    
    return materials

def normalize_material(material):
    """
    Normalize a single material tag.
    Returns normalized material name or None if invalid.
    """
    if not material:
        return None
    
    material_lower = material.lower().strip()
    
    # Check if it's a pattern (should be removed)
    if material_lower in PATTERNS_TO_REMOVE:
        return None
    
    # Check if it's a marketing term (should be removed)
    if material_lower in MARKETING_TERMS:
        return None
    
    # Check for percentage-based materials
    if '%' in material_lower:
        extracted = extract_percentage_materials(material_lower)
        return extracted if extracted else None
    
    # Normalize known variations
    if material_lower in MATERIAL_NORMALIZATIONS:
        normalized = MATERIAL_NORMALIZATIONS[material_lower]
        return normalized if normalized in VALID_MATERIALS else None
    
    # Check if it's already a valid material
    if material_lower in VALID_MATERIALS:
        return material_lower
    
    # Try with underscores
    material_underscore = material_lower.replace(' ', '_')
    if material_underscore in VALID_MATERIALS:
        return material_underscore
    
    # Check if it contains a valid material (e.g., "barathea wool" → "wool")
    for valid_material in sorted(VALID_MATERIALS, key=len, reverse=True):
        if valid_material in material_lower:
            return valid_material
    
    return None

def rationalize_materials(product_id, current_materials):
    """
    Rationalize materials for a single product.
    Returns list of normalized materials.
    """
    if not current_materials or not isinstance(current_materials, list):
        return []
    
    normalized_materials = []
    
    for material in current_materials:
        if not material:
            continue
        
        # Handle percentage strings that might contain multiple materials
        if '%' in str(material):
            extracted = extract_percentage_materials(str(material))
            normalized_materials.extend(extracted)
        else:
            normalized = normalize_material(material)
            if normalized:
                if isinstance(normalized, list):
                    normalized_materials.extend(normalized)
                else:
                    normalized_materials.append(normalized)
    
    # Remove duplicates and sort
    normalized_materials = sorted(list(set(normalized_materials)))
    
    return normalized_materials

def rationalize_all_materials(dry_run=False):
    """
    Rationalize materials for all products.
    """
    # Get all products first
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                name,
                product_type_data
            FROM clan_products
            WHERE product_type_data IS NOT NULL
            ORDER BY id
        """)
        
        products = cursor.fetchall()
    
    logger.info(f"Processing {len(products)} products...")
    logger.info(f"Dry run: {dry_run}")
    
    updated_count = 0
    missing_materials = []
    changes_summary = {}
    updates_to_apply = []
    
    for i, product in enumerate(products, 1):
        if i % 100 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        product_id = product['id']
        product_name = product['name']
        type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
        
        current_materials = type_data.get('materials', [])
        normalized_materials = rationalize_materials(product_id, current_materials)
        
        # Check if changed
        if set(current_materials or []) != set(normalized_materials):
            change_key = f"{sorted(current_materials or [])} → {sorted(normalized_materials)}"
            changes_summary[change_key] = changes_summary.get(change_key, 0) + 1
            
            if not dry_run:
                type_data['materials'] = normalized_materials
                type_data['materials_rationalized'] = True
                updates_to_apply.append((product_id, type_data))
            
            updated_count += 1
        
        # Flag products with no materials
        if not normalized_materials:
            missing_materials.append({
                'id': product_id,
                'name': product_name
            })
    
    # Apply updates in batch
    if not dry_run and updates_to_apply:
        logger.info(f"\nApplying {len(updates_to_apply)} updates...")
        with db_manager.get_cursor() as cursor:
            for product_id, type_data in updates_to_apply:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(type_data), product_id))
    
    # Print summary
    print("\n" + "="*80)
    print("MATERIALS RATIONALIZATION SUMMARY")
    print("="*80)
    print(f"Total products: {len(products)}")
    print(f"Updated: {updated_count} ({100*updated_count/len(products):.1f}%)")
    print(f"Missing materials: {len(missing_materials)} ({100*len(missing_materials)/len(products):.1f}%)")
    
    # Show sample changes
    if changes_summary:
        print("\n" + "="*80)
        print("SAMPLE CHANGES (first 20):")
        print("="*80)
        for change, count in list(changes_summary.items())[:20]:
            print(f"  {change} ({count} products)")
    
    # Show sample missing materials
    if missing_materials:
        print("\n" + "="*80)
        print("PRODUCTS WITH MISSING MATERIALS (first 20):")
        print("="*80)
        for item in missing_materials[:20]:
            print(f"  [{item['id']}] {item['name']}")
    
    # Save missing materials to file
    if missing_materials:
        missing_file = 'data/missing_materials.json'
        with open(missing_file, 'w') as f:
            json.dump(missing_materials, f, indent=2)
        logger.info(f"\nMissing materials list saved to: {missing_file}")
    
    return {
        'updated': updated_count,
        'missing': len(missing_materials)
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Rationalize materials tags')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        results = rationalize_all_materials(dry_run=args.dry_run)
        print(f"\n✅ Rationalization complete!")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

