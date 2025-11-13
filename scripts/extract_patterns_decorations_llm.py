"""
Extract patterns and decorations from all products using LLM.

Processes all products to extract:
- Patterns: repeating designs (tartan, harris_tweed, celtic_knotwork, etc.)
- Decorations: specific motifs (clan_crest, lion_rampant, thistle, etc.)
"""

import sys
sys.path.insert(0, '.')
import json
import logging
import time
from config.database import db_manager
from utils.pattern_decoration_extractor import PatternDecorationExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_all_products(confidence_threshold=0.7, dry_run=False, limit=None):
    """
    Extract patterns and decorations for all products.
    
    Args:
        confidence_threshold: Minimum confidence to apply changes
        dry_run: If True, don't update database
        limit: Limit number of products to process (for testing)
    """
    extractor = PatternDecorationExtractor()
    
    # Fetch all products first
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
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Dry run: {dry_run}")
    
    updated_count = 0
    skipped_low_confidence = 0
    errors = []
    changes_summary = {
        'patterns_added': 0,
        'patterns_removed': 0,
        'decorations_added': 0,
        'decorations_removed': 0,
    }
    
    for i, product in enumerate(products, 1):
        if i % 50 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        product_id = product['id']
        product_name = product['name']
        description = product.get('description')
        short_description = product.get('short_description')
        additional_data = product.get('additional_data')
        type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
        
        try:
            # Extract patterns and decorations
            result = extractor.extract_patterns_decorations(
                product_name=product_name,
                description=description,
                short_description=short_description,
                additional_data=additional_data
            )
            
            if result.get('error'):
                errors.append({
                    'id': product_id,
                    'name': product_name,
                    'error': result['error']
                })
                continue
            
            confidence = result.get('confidence', 0.0)
            if confidence < confidence_threshold:
                skipped_low_confidence += 1
                continue
            
            extracted_patterns = result.get('patterns', [])
            extracted_decorations = result.get('decorations', [])
            
            current_patterns = set(type_data.get('patterns', []))
            current_decorations = set(type_data.get('decorations', []))
            new_patterns = set(extracted_patterns)
            new_decorations = set(extracted_decorations)
            
            # Only update if there are changes
            if current_patterns != new_patterns or current_decorations != new_decorations:
                if new_patterns:
                    type_data['patterns'] = sorted(list(new_patterns))
                elif 'patterns' in type_data:
                    type_data.pop('patterns')
                
                if new_decorations:
                    type_data['decorations'] = sorted(list(new_decorations))
                elif 'decorations' in type_data:
                    type_data.pop('decorations')
                
                type_data['patterns_decorations_extracted'] = True
                type_data['patterns_decorations_extracted_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
                type_data['patterns_decorations_confidence'] = confidence
                
                if not dry_run:
                    # Use a new cursor for updates
                    with db_manager.get_cursor() as update_cursor:
                        update_cursor.execute("""
                            UPDATE clan_products
                            SET product_type_data = %s
                            WHERE id = %s
                        """, (json.dumps(type_data), product_id))
                        db_manager.get_connection().commit()
                
                # Track changes
                if new_patterns != current_patterns:
                    if new_patterns - current_patterns:
                        changes_summary['patterns_added'] += len(new_patterns - current_patterns)
                    if current_patterns - new_patterns:
                        changes_summary['patterns_removed'] += len(current_patterns - new_patterns)
                
                if new_decorations != current_decorations:
                    if new_decorations - current_decorations:
                        changes_summary['decorations_added'] += len(new_decorations - current_decorations)
                    if current_decorations - new_decorations:
                        changes_summary['decorations_removed'] += len(current_decorations - new_decorations)
                
                updated_count += 1
            
            # Rate limiting
            time.sleep(0.3)
            
        except Exception as e:
            logger.error(f"Error processing product {product_id} ({product_name}): {e}")
            errors.append({
                'id': product_id,
                'name': product_name,
                'error': str(e)
            })
    
    # All updates are committed individually above
    
    # Print summary
    print("\n" + "="*80)
    print("PATTERNS AND DECORATIONS EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total products processed: {len(products)}")
    print(f"Products updated: {updated_count} ({100*updated_count/len(products):.1f}%)")
    print(f"Skipped (low confidence): {skipped_low_confidence} ({100*skipped_low_confidence/len(products):.1f}%)")
    print(f"Errors: {len(errors)} ({100*len(errors)/len(products):.1f}%)")
    print(f"\nChanges:")
    print(f"  Patterns added: {changes_summary['patterns_added']}")
    print(f"  Patterns removed: {changes_summary['patterns_removed']}")
    print(f"  Decorations added: {changes_summary['decorations_added']}")
    print(f"  Decorations removed: {changes_summary['decorations_removed']}")
    
    if errors:
        print("\n" + "="*80)
        print("ERRORS (first 10):")
        print("="*80)
        for item in errors[:10]:
            print(f"  [{item['id']}] {item['name']}")
            print(f"      Error: {item['error']}")
    
    return {
        'updated': updated_count,
        'skipped': skipped_low_confidence,
        'errors': len(errors)
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract patterns and decorations using LLM')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    parser.add_argument('--threshold', type=float, default=0.7, help='Confidence threshold (default: 0.7)')
    parser.add_argument('--limit', type=int, help='Limit number of products to process')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("EXTRACTING PATTERNS AND DECORATIONS USING LLM")
        print("="*80)
        print(f"Confidence threshold: {args.threshold}")
        print(f"Dry run: {args.dry_run}")
        if args.limit:
            print(f"Limit: {args.limit} products")
        print()
        
        results = extract_all_products(
            confidence_threshold=args.threshold,
            dry_run=args.dry_run,
            limit=args.limit
        )
        
        print(f"\n✅ Extraction complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

