"""
Extract patterns and decorations using string matching.

Primary approach: String matching on product names, descriptions, and specifications.
Only extracts patterns/decorations that are explicitly mentioned.
"""

import sys
sys.path.insert(0, '.')
import json
import logging
import re
from typing import Dict, Optional, List, Set
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valid patterns (repeating designs)
VALID_PATTERNS = {
    'tartan',
    'harris_tweed',
    'celtic_knotwork',
    'check',
    'argyle',
    'herringbone',
    'fairisle',
    'striped',
    'polka_dot',
    'paisley',
}

# Valid decorations (specific motifs)
VALID_DECORATIONS = {
    'clan_crest',
    'lion_rampant',
    'thistle',
    'stag',
    'shamrock',
    'sword',
    'rose',
    'dragon',
    'knot',
    'celtic_knotwork',
    'masonic',
    'viking',
    'highland_cow',
}

# Pattern matching rules - what text indicates which pattern
PATTERN_MATCHES = {
    'tartan': [
        r'\btartan\b',
        r'\btartans\b',
        r'\bplaid\b',
        r'\bplaids\b',
    ],
    'harris_tweed': [
        r'\bharris\s+tweed\b',
        r'\bharris\s+tweeds\b',
        r'\btweed\b',  # Only if not already matched as tartan
    ],
    'celtic_knotwork': [
        r'\bceltic\s+knot\b',
        r'\bceltic\s+knotwork\b',
        r'\bceltic\s+knots\b',
        r'\bknotwork\b',
        r'\bceltic\s+interlace\b',
        r'\bceltic\s+interlaced\b',
        r'\bkells\b',  # Book of Kells has celtic knotwork
        r'\bnever\s+ending\s+knot\b',
        r'\bviking\s+knotwork\b',
    ],
    'check': [
        r'\bcheck\b',
        r'\bchecked\b',
        r'\bchecks\b',
        r'\btattersall\b',
    ],
    'argyle': [
        r'\bargyle\b',
        r'\bargyll\b',
    ],
    'herringbone': [
        r'\bherringbone\b',
    ],
    'fairisle': [
        r'\bfairisle\b',
        r'\bfair\s+isle\b',
    ],
    'striped': [
        r'\bstriped\b',
        r'\bstripe\b',
        r'\bstripes\b',
    ],
    'polka_dot': [
        r'\bpolka\s+dot\b',
        r'\bpolkadot\b',
        r'\bpolka\s+dots\b',
    ],
    'paisley': [
        r'\bpaisley\b',
    ],
}

# Decoration matching rules
DECORATION_MATCHES = {
    'clan_crest': [
        r'\bclan\s+crest\b',
        r'\bclan\s+crests\b',
        r'\bfamily\s+crest\b',
        r'\bfamily\s+crests\b',
        r'\bcrest\b',  # Only if context suggests clan/family
    ],
    'lion_rampant': [
        r'\blion\s+rampant\b',
        r'\blions\s+rampant\b',
    ],
    'thistle': [
        r'\bthistle\b',
        r'\bthistles\b',
    ],
    'stag': [
        r'\bstag\b',
        r'\bstags\b',
        r'\bdeer\b',
    ],
    'shamrock': [
        r'\bshamrock\b',
        r'\bshamrocks\b',
    ],
    'sword': [
        r'\bsword\b',
        r'\bswords\b',
    ],
    'rose': [
        r'\brose\b',
        r'\broses\b',
    ],
    'dragon': [
        r'\bdragon\b',
        r'\bdragons\b',
    ],
    'knot': [
        r'\bknot\b',  # Only if not already matched as celtic_knotwork
        r'\bknots\b',
    ],
    # Note: celtic_knotwork is a PATTERN, not a decoration, so it's not in this list
    'masonic': [
        r'\bmasonic\b',
    ],
    'viking': [
        r'\bviking\b',
        r'\bvikings\b',
    ],
    'highland_cow': [
        r'\bhighland\s+cow\b',
        r'\bhighland\s+cows\b',
    ],
}

def clean_text(text: Optional[str]) -> str:
    """Clean HTML tags and normalize text."""
    if not text:
        return ''
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.lower()

def extract_patterns_from_text(text: str) -> Set[str]:
    """Extract patterns from text using string matching."""
    patterns = set()
    
    # Check each pattern
    for pattern_name, regexes in PATTERN_MATCHES.items():
        for regex in regexes:
            if re.search(regex, text, re.IGNORECASE):
                patterns.add(pattern_name)
                break  # Found this pattern, move to next
    
    # Special handling: if "tweed" matches but we already have tartan, don't add harris_tweed
    # (tartan is more specific)
    if 'tartan' in patterns and 'harris_tweed' in patterns:
        patterns.discard('harris_tweed')
    
    # Special handling: if celtic_knotwork matches, don't also add knot
    if 'celtic_knotwork' in patterns:
        patterns.discard('knot')
    
    return patterns

def extract_decorations_from_text(text: str) -> Set[str]:
    """Extract decorations from text using string matching."""
    decorations = set()
    
    # Check each decoration
    for decoration_name, regexes in DECORATION_MATCHES.items():
        for regex in regexes:
            if re.search(regex, text, re.IGNORECASE):
                decorations.add(decoration_name)
                break  # Found this decoration, move to next
    
    # Special handling: celtic_knotwork should never be in decorations (it's a pattern only)
    decorations.discard('celtic_knotwork')
    
    # Special handling: if celtic_knotwork matches, don't also add knot
    if 'celtic_knotwork' in decorations:
        decorations.discard('knot')
    
    # Special handling: "crest" alone should only match if context suggests clan crest
    # (e.g., "clan crest", "family crest", but not just "crest" in isolation)
    if 'clan_crest' in decorations:
        # Already matched with context, keep it
        pass
    elif re.search(r'\bcrest\b', text, re.IGNORECASE):
        # Check if there's clan/family context nearby
        # Look for "clan" or "family" within 5 words of "crest"
        crest_positions = [m.start() for m in re.finditer(r'\bcrest\b', text, re.IGNORECASE)]
        for pos in crest_positions:
            # Check context around this position
            start = max(0, pos - 30)
            end = min(len(text), pos + 30)
            context = text[start:end]
            if re.search(r'\b(clan|family)\b', context, re.IGNORECASE):
                decorations.add('clan_crest')
                break
    
    return decorations

def extract_from_product(product: Dict) -> Dict:
    """Extract patterns and decorations from a product."""
    # Build text from all sources
    text_parts = []
    
    if product.get('name'):
        text_parts.append(product['name'])
    
    if product.get('short_description'):
        text_parts.append(clean_text(product['short_description']))
    
    if product.get('description'):
        text_parts.append(clean_text(product['description']))
    
    # Extract from specifications
    additional_data = product.get('additional_data')
    if additional_data and isinstance(additional_data, dict):
        for key, value in additional_data.items():
            if isinstance(value, dict):
                label = value.get('label', '')
                val = value.get('value', '')
                if label and val:
                    text_parts.append(f"{label}: {val}")
            elif value:
                text_parts.append(str(value))
    
    # Combine all text
    full_text = ' '.join(text_parts)
    
    # Extract patterns and decorations
    patterns = extract_patterns_from_text(full_text)
    decorations = extract_decorations_from_text(full_text)
    
    return {
        'patterns': sorted(list(patterns)),
        'decorations': sorted(list(decorations))
    }

def clear_all_patterns_decorations(dry_run=False):
    """Clear all existing patterns and decorations."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, product_type_data
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
        
        cleared = 0
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            
            if type_data.get('patterns') or type_data.get('decorations'):
                type_data.pop('patterns', None)
                type_data.pop('decorations', None)
                type_data['patterns_decorations_cleared'] = True
                
                if not dry_run:
                    cursor.execute("""
                        UPDATE clan_products
                        SET product_type_data = %s
                        WHERE id = %s
                    """, (json.dumps(type_data), product['id']))
                
                cleared += 1
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return cleared

def extract_all_products(dry_run=False, limit=None):
    """Extract patterns and decorations for all products using string matching."""
    # Fetch all products
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT 
                id,
                name,
                description,
                short_description,
                additional_data,
                product_type_data
            FROM clan_products
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        products = cursor.fetchall()
    
    logger.info(f"Processing {len(products)} products")
    logger.info(f"Dry run: {dry_run}")
    
    updated_count = 0
    patterns_found = 0
    decorations_found = 0
    empty_count = 0
    
    for i, product in enumerate(products, 1):
        if i % 100 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        product_id = product['id']
        product_name = product['name']
        type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
        
        try:
            # Extract patterns and decorations
            result = extract_from_product(product)
            
            patterns = result['patterns']
            decorations = result['decorations']
            
            # Only update if we found something or if there were previous entries
            if patterns or decorations or type_data.get('patterns') or type_data.get('decorations'):
                if patterns:
                    type_data['patterns'] = patterns
                    patterns_found += len(patterns)
                elif 'patterns' in type_data:
                    type_data.pop('patterns')
                
                if decorations:
                    type_data['decorations'] = decorations
                    decorations_found += len(decorations)
                elif 'decorations' in type_data:
                    type_data.pop('decorations')
                
                type_data['patterns_decorations_extracted'] = True
                type_data['patterns_decorations_method'] = 'string_matching'
                
                if not dry_run:
                    with db_manager.get_cursor() as update_cursor:
                        update_cursor.execute("""
                            UPDATE clan_products
                            SET product_type_data = %s
                            WHERE id = %s
                        """, (json.dumps(type_data), product_id))
                        db_manager.get_connection().commit()
                
                updated_count += 1
            else:
                empty_count += 1
            
        except Exception as e:
            logger.error(f"Error processing product {product_id} ({product_name}): {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("PATTERNS AND DECORATIONS EXTRACTION SUMMARY (STRING MATCHING)")
    print("="*80)
    print(f"Total products processed: {len(products)}")
    print(f"Products updated: {updated_count} ({100*updated_count/len(products):.1f}%)")
    print(f"Products with no patterns/decorations: {empty_count} ({100*empty_count/len(products):.1f}%)")
    print(f"\nTotal patterns found: {patterns_found}")
    print(f"Total decorations found: {decorations_found}")
    
    return {
        'updated': updated_count,
        'patterns_found': patterns_found,
        'decorations_found': decorations_found,
        'empty': empty_count
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract patterns and decorations using string matching')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    parser.add_argument('--limit', type=int, help='Limit number of products to process')
    parser.add_argument('--skip-clear', action='store_true', help='Skip clearing existing patterns/decorations')
    
    args = parser.parse_args()
    
    try:
        if not args.skip_clear:
            print("="*80)
            print("CLEARING EXISTING PATTERNS AND DECORATIONS")
            print("="*80)
            print(f"Dry run: {args.dry_run}\n")
            
            cleared = clear_all_patterns_decorations(dry_run=args.dry_run)
            print(f"✅ Cleared patterns/decorations from {cleared} products\n")
        
        print("="*80)
        print("EXTRACTING PATTERNS AND DECORATIONS (STRING MATCHING)")
        print("="*80)
        print(f"Dry run: {args.dry_run}")
        if args.limit:
            print(f"Limit: {args.limit} products")
        print()
        
        results = extract_all_products(dry_run=args.dry_run, limit=args.limit)
        
        print(f"\n✅ Extraction complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

