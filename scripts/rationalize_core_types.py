"""
Rationalize Core Type Tags

Identifies and fixes:
1. Duplicates/variations (quaich/quaichs, water_bottle/water bottle)
2. Misclassifications (sash/shawl in homeware when they're clothing)
3. Product form tags used as core types (jewellery, homeware)
4. Descriptive strings that should be normalized
5. Synonyms that should be unified
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Normalization mappings - what should be changed to what
CORE_TYPE_NORMALIZATIONS = {
    # Quaich variations
    'quaichs': 'quaich',
    'quaichs (similar to a small bowl)': 'quaich',
    
    # Water bottle variations
    'water bottle': 'water_bottle',
    
    # Flask variations
    'hip_flask': 'flask',
    
    # Comb variations
    'dress_comb': 'comb',
    'wallet/purse comb': 'comb',
    
    # Belt/buckle variations
    'kilt_belt_buckle': 'belt_buckle',
    
    # Kilt accessory variations
    'kilt hanger': 'kilt_accessory',
    
    # Napkin variations
    'napkins (set_of_4)': 'napkins',
    
    # Car mat variations
    'tartan car mats': 'car_mats',
    
    # Top variations
    'crop_tee': 'crop_top',
    
    # Sweater/jumper - unify to sweater
    'jumper': 'sweater',
    
    # Headwear variations
    'bobble': 'headwear',
    
    # Product form tags that shouldn't be core types
    'jewellery': None,  # Should be removed - product_form is jewellery
    'homeware': None,  # Should be removed - product_form is homeware
    
    # Descriptive strings that need normalization
    'Handmade Tartan Dog Accessories': 'pet_accessory',
    'Oxhorn Bugle': 'ornament',
    'oddments bag': 'bag',
    'tea towel': 'towel',
    
    # Toy -> recreation (based on earlier work)
    'toy': 'recreation',
}

# Core types that should be in clothing form (not homeware)
CLOTHING_CORE_TYPES = {
    'sash', 'shawl', 'scarf', 'poncho', 'serape', 'cape', 'stole', 'bandana', 'dog_bandana'
}

def analyze_core_types():
    """Analyze all core types and identify issues."""
    with db_manager.get_cursor() as cursor:
        # Get all core types with their product forms
        cursor.execute("""
            SELECT 
                product_type_data->>'core_type' as core_type,
                product_type_data->'disambiguation'->>'product_form' as product_form,
                COUNT(*) as count,
                array_agg(id ORDER BY id) as product_ids
            FROM clan_products
            WHERE product_type_data->>'core_type' IS NOT NULL
            GROUP BY 
                product_type_data->>'core_type',
                product_type_data->'disambiguation'->>'product_form'
            ORDER BY core_type, product_form
        """)
        
        results = cursor.fetchall()
    
    issues = {
        'normalizations_needed': [],
        'form_corrections': [],
        'product_form_as_core_type': [],
        'descriptive_strings': [],
    }
    
    for row in results:
        core_type = row['core_type']
        product_form = row['product_form']
        count = row['count']
        
        # Check for normalizations
        if core_type in CORE_TYPE_NORMALIZATIONS:
            normalized = CORE_TYPE_NORMALIZATIONS[core_type]
            if normalized is None:
                issues['product_form_as_core_type'].append({
                    'core_type': core_type,
                    'product_form': product_form,
                    'count': count,
                    'product_ids': row['product_ids'][:5]  # Sample
                })
            else:
                issues['normalizations_needed'].append({
                    'from': core_type,
                    'to': normalized,
                    'product_form': product_form,
                    'count': count,
                    'product_ids': row['product_ids'][:5]
                })
        
        # Check for clothing items in wrong form
        if core_type in CLOTHING_CORE_TYPES and product_form != 'clothing':
            issues['form_corrections'].append({
                'core_type': core_type,
                'current_form': product_form,
                'should_be': 'clothing',
                'count': count,
                'product_ids': row['product_ids'][:5]
            })
        
        # Check for descriptive strings (contain spaces, parentheses, or capitals in middle)
        if ' ' in core_type or '(' in core_type or (core_type and core_type[0].isupper() and not core_type.isupper()):
            if core_type not in CORE_TYPE_NORMALIZATIONS:
                issues['descriptive_strings'].append({
                    'core_type': core_type,
                    'product_form': product_form,
                    'count': count,
                    'product_ids': row['product_ids'][:5]
                })
    
    return issues

def apply_normalizations(dry_run=False):
    """Apply core type normalizations."""
    with db_manager.get_cursor() as cursor:
        updates = []
        
        for from_type, to_type in CORE_TYPE_NORMALIZATIONS.items():
            if to_type is None:
                # Remove core_type (it's a product_form tag)
                cursor.execute("""
                    SELECT id, name, product_type_data
                    FROM clan_products
                    WHERE product_type_data->>'core_type' = %s
                """, (from_type,))
                
                products = cursor.fetchall()
                for product in products:
                    type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                    old_core_type = type_data.get('core_type')
                    
                    if old_core_type == from_type:
                        type_data.pop('core_type', None)
                        type_data['core_type_removed'] = True
                        type_data['core_type_removed_reason'] = 'product_form_tag_used_as_core_type'
                        
                        if not dry_run:
                            cursor.execute("""
                                UPDATE clan_products
                                SET product_type_data = %s
                                WHERE id = %s
                            """, (json.dumps(type_data), product['id']))
                        
                        updates.append({
                            'id': product['id'],
                            'name': product['name'],
                            'action': 'removed',
                            'old': from_type,
                            'new': None
                        })
            else:
                # Normalize to new type
                cursor.execute("""
                    SELECT id, name, product_type_data
                    FROM clan_products
                    WHERE product_type_data->>'core_type' = %s
                """, (from_type,))
                
                products = cursor.fetchall()
                for product in products:
                    type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                    old_core_type = type_data.get('core_type')
                    
                    if old_core_type == from_type:
                        type_data['core_type'] = to_type
                        type_data['core_type_normalized'] = True
                        type_data['core_type_normalized_from'] = from_type
                        
                        if not dry_run:
                            cursor.execute("""
                                UPDATE clan_products
                                SET product_type_data = %s
                                WHERE id = %s
                            """, (json.dumps(type_data), product['id']))
                        
                        updates.append({
                            'id': product['id'],
                            'name': product['name'],
                            'action': 'normalized',
                            'old': from_type,
                            'new': to_type
                        })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

def fix_form_misclassifications(dry_run=False):
    """Fix clothing items that are in wrong product_form."""
    with db_manager.get_cursor() as cursor:
        updates = []
        
        for core_type in CLOTHING_CORE_TYPES:
            cursor.execute("""
                SELECT id, name, product_type_data
                FROM clan_products
                WHERE product_type_data->>'core_type' = %s
                  AND product_type_data->'disambiguation'->>'product_form' != 'clothing'
            """, (core_type,))
            
            products = cursor.fetchall()
            for product in products:
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_form = type_data.get('disambiguation', {}).get('product_form')
                
                if current_form != 'clothing':
                    if 'disambiguation' not in type_data:
                        type_data['disambiguation'] = {}
                    type_data['disambiguation']['product_form'] = 'clothing'
                    type_data['product_form_corrected'] = True
                    type_data['product_form_corrected_from'] = current_form
                    
                    if not dry_run:
                        cursor.execute("""
                            UPDATE clan_products
                            SET product_type_data = %s
                            WHERE id = %s
                        """, (json.dumps(type_data), product['id']))
                    
                    updates.append({
                        'id': product['id'],
                        'name': product['name'],
                        'core_type': core_type,
                        'old_form': current_form,
                        'new_form': 'clothing'
                    })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Rationalize core type tags')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, don\'t apply fixes')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("ANALYZING CORE TYPE TAGS")
        print("="*80)
        issues = analyze_core_types()
        
        print(f"\nNormalizations needed: {len(issues['normalizations_needed'])}")
        print(f"Form corrections needed: {len(issues['form_corrections'])}")
        print(f"Product form tags used as core types: {len(issues['product_form_as_core_type'])}")
        print(f"Descriptive strings: {len(issues['descriptive_strings'])}")
        
        if issues['normalizations_needed']:
            print("\n" + "="*80)
            print("NORMALIZATIONS NEEDED:")
            print("="*80)
            for item in issues['normalizations_needed'][:20]:
                print(f"  {item['from']} → {item['to']} ({item['count']} products, form: {item['product_form']})")
        
        if issues['form_corrections']:
            print("\n" + "="*80)
            print("FORM CORRECTIONS NEEDED:")
            print("="*80)
            for item in issues['form_corrections'][:20]:
                print(f"  {item['core_type']}: {item['current_form']} → {item['should_be']} ({item['count']} products)")
        
        if issues['product_form_as_core_type']:
            print("\n" + "="*80)
            print("PRODUCT FORM TAGS USED AS CORE TYPES:")
            print("="*80)
            for item in issues['product_form_as_core_type'][:20]:
                print(f"  {item['core_type']} (form: {item['product_form']}, {item['count']} products)")
        
        if issues['descriptive_strings']:
            print("\n" + "="*80)
            print("DESCRIPTIVE STRINGS (need normalization):")
            print("="*80)
            for item in issues['descriptive_strings'][:20]:
                print(f"  {item['core_type']} (form: {item['product_form']}, {item['count']} products)")
        
        if not args.analyze_only:
            print("\n" + "="*80)
            print("APPLYING FIXES")
            print("="*80)
            print(f"Dry run: {args.dry_run}")
            
            # Apply normalizations
            norm_updates = apply_normalizations(dry_run=args.dry_run)
            print(f"\n✅ Normalizations: {len(norm_updates)} products updated")
            
            # Fix form misclassifications
            form_updates = fix_form_misclassifications(dry_run=args.dry_run)
            print(f"✅ Form corrections: {len(form_updates)} products updated")
            
            print(f"\n✅ Rationalization complete!")
            if args.dry_run:
                print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

