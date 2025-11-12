"""
Batch normalize all core_type values using LLM-based semantic analysis.
Considers product form context, unifies synonyms, fixes mis-assignments.
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager
from utils.core_type_normalizer import CoreTypeNormalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_all_core_types(confidence_threshold=0.8, dry_run=False, limit=None):
    """
    Normalize all core_type values using LLM.
    
    Args:
        confidence_threshold: Minimum confidence for auto-apply (default 0.8)
        dry_run: If True, don't update database, just report
        limit: Limit number of products to process (for testing)
    """
    normalizer = CoreTypeNormalizer()
    
    # Get all products with core_type
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT 
                id,
                name,
                short_description,
                product_type_data->>'core_type' as current_core_type,
                product_type_data->'disambiguation'->>'product_form' as product_form
            FROM clan_products
            WHERE product_type_data->>'core_type' IS NOT NULL
              AND product_type_data->'disambiguation'->>'product_form' IS NOT NULL
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        products = cursor.fetchall()
    
    logger.info(f"Processing {len(products)} products with core_type...")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Dry run: {dry_run}")
    
    high_confidence = []
    review_queue = []
    errors = []
    unchanged = []
    
    for i, product in enumerate(products, 1):
        if i % 10 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        result = normalizer.normalize_core_type(
            product_name=product['name'],
            current_core_type=product['current_core_type'],
            product_form=product['product_form'],
            description=product['short_description']
        )
        
        if result.get('error'):
            errors.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'error': result['error']
            })
        else:
            new_core_type = result.get('core_type')
            confidence = result.get('confidence', 0.0)
            reasoning = result.get('reasoning', '')
            change_type = result.get('change_type', 'none')
            
            # Check if unchanged
            if new_core_type == product['current_core_type']:
                unchanged.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'core_type': new_core_type
                })
            elif confidence > confidence_threshold:
                high_confidence.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'current_core_type': product['current_core_type'],
                    'new_core_type': new_core_type,
                    'product_form': product['product_form'],
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'change_type': change_type
                })
            else:
                review_queue.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'current_core_type': product['current_core_type'],
                    'new_core_type': new_core_type,
                    'product_form': product['product_form'],
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'change_type': change_type
                })
    
    # Print summary
    print("\n" + "="*80)
    print("CORE TYPE NORMALIZATION SUMMARY")
    print("="*80)
    print(f"Total products: {len(products)}")
    print(f"Unchanged: {len(unchanged)} ({100*len(unchanged)/len(products):.1f}%)")
    print(f"High confidence (auto-apply): {len(high_confidence)} ({100*len(high_confidence)/len(products):.1f}%)")
    print(f"Review queue: {len(review_queue)} ({100*len(review_queue)/len(products):.1f}%)")
    print(f"Errors: {len(errors)} ({100*len(errors)/len(products):.1f}%)")
    
    # Group changes by type
    if high_confidence:
        change_types = {}
        for item in high_confidence:
            ct = item['change_type']
            change_types[ct] = change_types.get(ct, 0) + 1
        
        print("\nChange types (high confidence):")
        for ct, count in sorted(change_types.items(), key=lambda x: -x[1]):
            print(f"  {ct}: {count}")
    
    # Apply high-confidence changes
    if not dry_run and high_confidence:
        logger.info(f"\nApplying {len(high_confidence)} high-confidence normalizations...")
        with db_manager.get_cursor() as cursor:
            for item in high_confidence:
                # Get current product_type_data
                cursor.execute("""
                    SELECT product_type_data
                    FROM clan_products
                    WHERE id = %s
                """, (item['product_id'],))
                
                row = cursor.fetchone()
                if row and row['product_type_data']:
                    product_type_data = row['product_type_data']
                else:
                    product_type_data = {}
                
                # Update core_type
                product_type_data['core_type'] = item['new_core_type']
                
                # Track normalization
                product_type_data['core_type_normalized_at'] = '2025-11-12T00:00:00'  # Will be updated
                product_type_data['core_type_normalization_method'] = 'llm'
                product_type_data['core_type_normalization_confidence'] = item['confidence']
                product_type_data['core_type_change_type'] = item['change_type']
                
                # Save back to database
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(product_type_data), item['product_id']))
        
        logger.info(f"Applied {len(high_confidence)} normalizations")
    
    # Save review queue to file
    if review_queue:
        review_file = 'data/core_type_normalization_review_queue.json'
        with open(review_file, 'w') as f:
            json.dump(review_queue, f, indent=2)
        logger.info(f"\nReview queue saved to: {review_file}")
        logger.info(f"Review {len(review_queue)} products with confidence <= {confidence_threshold}")
    
    # Save errors to file
    if errors:
        error_file = 'data/core_type_normalization_errors.json'
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
        logger.info(f"\nErrors saved to: {error_file}")
    
    # Show sample of high-confidence changes
    if high_confidence:
        print("\n" + "="*80)
        print("SAMPLE HIGH-CONFIDENCE CHANGES (first 20):")
        print("="*80)
        for item in high_confidence[:20]:
            print(f"\n{item['product_name']}")
            print(f"  {item['current_core_type']} → {item['new_core_type']} ({item['change_type']})")
            print(f"  Form: {item['product_form']}, Confidence: {item['confidence']:.2f}")
            print(f"  Reasoning: {item['reasoning'][:100]}...")
    
    # Show sample of review queue
    if review_queue:
        print("\n" + "="*80)
        print("SAMPLE REVIEW QUEUE (first 10):")
        print("="*80)
        for item in review_queue[:10]:
            print(f"\n{item['product_name']}")
            print(f"  {item['current_core_type']} → {item['new_core_type']} ({item['change_type']})")
            print(f"  Form: {item['product_form']}, Confidence: {item['confidence']:.2f}")
            print(f"  Reasoning: {item['reasoning'][:100]}...")
    
    return {
        'unchanged': len(unchanged),
        'high_confidence': len(high_confidence),
        'review_queue': len(review_queue),
        'errors': len(errors)
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize all core_type values using LLM')
    parser.add_argument('--threshold', type=float, default=0.8, help='Confidence threshold (default: 0.8)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    parser.add_argument('--limit', type=int, help='Limit number of products (for testing)')
    
    args = parser.parse_args()
    
    try:
        results = normalize_all_core_types(
            confidence_threshold=args.threshold,
            dry_run=args.dry_run,
            limit=args.limit
        )
        print(f"\n✅ Normalization complete!")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

