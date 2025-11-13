"""
Rationalize existing patterns and decorations.

Unifies obvious duplicates and removes items that shouldn't be there.
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pattern normalizations - unify duplicates
PATTERN_NORMALIZATIONS = {
    # Tartan variations
    'tartans': 'tartan',
    'tartan design': 'tartan',
    'tartan pattern (not specified)': 'tartan',
    'classic tartan': 'tartan',
    'irish tartan': 'tartan',
    'any tartan': 'tartan',
    'choice of tartans': 'tartan',
    'various popular tartans': 'tartan',
    
    # Plaid variations
    'plaid': 'tartan',  # Plaid is a type of tartan
    
    # Celtic variations
    'celtic knot': 'celtic_knotwork',
    'celtic knot work': 'celtic_knotwork',
    'celtic knotwork': 'celtic_knotwork',
    'celtic-inspired': 'celtic_knotwork',
    'celtic inspired knotwork': 'celtic_knotwork',
    'celtic pattern': 'celtic_knotwork',
    'celtic design': 'celtic_knotwork',
    'celtic motifs': 'celtic_knotwork',
    'celtic tooled': 'celtic_knotwork',
    'celtic': 'celtic_knotwork',
    
    # Check variations
    'check': 'check',
    'checked': 'check',
    'tattersall check': 'check',
    
    # Tweed variations
    'tweed': 'harris_tweed',  # Most tweed is Harris Tweed
    
    # Argyle variations
    'argyll': 'argyle',
    'argyle': 'argyle',
    
    # Other patterns
    'herringbone': 'herringbone',
    'fairisle': 'fairisle',
    'plain': None,  # Remove - plain is not a pattern
    'prince charlie': None,  # Remove - this is a style, not a pattern
    'masonic': None,  # Remove - this is a decoration/motif, not a pattern
    'book of kells': 'celtic_knotwork',
    'viking knotwork': 'celtic_knotwork',
    'never ending knot design': 'celtic_knotwork',
    
    # Remove non-patterns
    'clan crest': None,  # This is a decoration, not a pattern
    'thistle': None,  # This is a decoration, not a pattern
    'thistle design': None,  # This is a decoration, not a pattern
    'lion rampant': None,  # This is a decoration, not a pattern
    'shamrock': None,  # This is a decoration, not a pattern
    'celtic thistle': None,  # This is a decoration, not a pattern
    'celtic dog': None,  # This is a decoration, not a pattern
    'celtic bird': None,  # This is a decoration, not a pattern
    'celtic stag': None,  # This is a decoration, not a pattern
    'stag and thistle': None,  # This is a decoration, not a pattern
    'highland cow': None,  # This is a decoration, not a pattern
    'archibald knox enamelled design': None,  # This is a decoration/style, not a pattern
    'clan crest design': None,  # This is a decoration, not a pattern
    'irish clan crest': None,  # This is a decoration, not a pattern
    'variety of crests and tartans': 'tartan',  # Just tartan, not a variety
}

# Decoration normalizations - unify duplicates
DECORATION_NORMALIZATIONS = {
    # Clan crest variations
    'clan crest': 'clan_crest',
    'clan_crest': 'clan_crest',
    'clan crest badge': 'clan_crest',
    'clan crest design': 'clan_crest',
    'irish clan crest': 'clan_crest',
    
    # Lion rampant variations
    'lion_rampant': 'lion_rampant',
    'lion rampant': 'lion_rampant',
    
    # Thistle variations
    'thistle': 'thistle',
    'thistle emblem': 'thistle',
    'thistle design': 'thistle',
    
    # Stag variations
    'stag': 'stag',
    'stag design': 'stag',
    'stag head badge': 'stag',
    
    # Celtic variations
    'celtic': 'celtic_knotwork',
    'knot': 'celtic_knotwork',
    
    # Remove non-decorations (these are functional features, not decorative motifs)
    'none': None,
    'engraved': None,  # Engraving is a technique, not a motif
    'engraving': None,
    'tooled': None,  # Tooling is a technique
    'embossed': None,  # Embossing is a technique
    'printed': None,  # Printing is a technique
    'print': None,
    'full cover print': None,
    'studded': None,  # Studding is a technique
    'studded targe': None,
    'studded flap': None,
    'fringing': None,  # Fringing is a feature
    'fringed ends': None,
    'fringe': None,
    'tassels': None,  # Tassels are functional features
    'chrome ball tassels': None,
    '3 chrome ball tassels': None,
    'flashes': None,  # Flashes are functional items
    'collar': None,  # Collar is a functional feature
    'ribbed collar': None,
    'four button cuff': None,
    'kilt belt loops': None,
    'hidden zipper': None,
    'military fishtail': None,
    'steel quarter tip on heel': None,
    'bottle opener': None,  # Functional feature
    'decorative sheath': None,  # Functional feature
    'chrome finish cantles': None,  # Functional feature
    'chrome cantle': None,  # Functional feature
    'tooled flap': None,  # Technique
    'detailed design on lid': None,  # Too vague
    'enhanced with hot glass enamel': None,  # Technique
    'imitation bone buttons': None,  # Material/feature, not decoration
    'brooch': None,  # This is a product type, not a decoration
}

def normalize_patterns_decorations(dry_run=False):
    """Normalize patterns and decorations across all products."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE (
                product_type_data->'patterns' IS NOT NULL
                AND jsonb_array_length(product_type_data->'patterns') > 0
            ) OR (
                product_type_data->'decorations' IS NOT NULL
                AND jsonb_array_length(product_type_data->'decorations') > 0
            )
        """)
        
        products = cursor.fetchall()
        
        pattern_updates = 0
        decoration_updates = 0
        
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            needs_update = False
            
            # Normalize patterns
            if type_data.get('patterns'):
                original_patterns = type_data['patterns'].copy()
                normalized_patterns = []
                for pattern in original_patterns:
                    normalized = PATTERN_NORMALIZATIONS.get(pattern)
                    if normalized is None:
                        # Remove this pattern
                        continue
                    elif normalized not in normalized_patterns:
                        normalized_patterns.append(normalized)
                
                if set(normalized_patterns) != set(original_patterns):
                    type_data['patterns'] = sorted(normalized_patterns) if normalized_patterns else None
                    if not normalized_patterns:
                        type_data.pop('patterns', None)
                    type_data['patterns_normalized'] = True
                    needs_update = True
                    pattern_updates += 1
            
            # Normalize decorations
            if type_data.get('decorations'):
                original_decorations = type_data['decorations'].copy()
                normalized_decorations = []
                for decoration in original_decorations:
                    normalized = DECORATION_NORMALIZATIONS.get(decoration)
                    if normalized is None:
                        # Remove this decoration
                        continue
                    elif normalized not in normalized_decorations:
                        normalized_decorations.append(normalized)
                
                if set(normalized_decorations) != set(original_decorations):
                    type_data['decorations'] = sorted(normalized_decorations) if normalized_decorations else None
                    if not normalized_decorations:
                        type_data.pop('decorations', None)
                    type_data['decorations_normalized'] = True
                    needs_update = True
                    decoration_updates += 1
            
            if needs_update and not dry_run:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(type_data), product['id']))
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return {
            'pattern_updates': pattern_updates,
            'decoration_updates': decoration_updates,
            'total_products': len(products)
        }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Rationalize patterns and decorations')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("RATIONALIZING PATTERNS AND DECORATIONS")
        print("="*80)
        print(f"Dry run: {args.dry_run}\n")
        
        results = normalize_patterns_decorations(dry_run=args.dry_run)
        
        print(f"✅ Processed {results['total_products']} products")
        print(f"✅ Updated patterns in {results['pattern_updates']} products")
        print(f"✅ Updated decorations in {results['decoration_updates']} products")
        
        print(f"\n✅ Rationalization complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

