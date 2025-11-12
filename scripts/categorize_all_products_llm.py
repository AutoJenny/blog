"""
Batch categorize all products using LLM-based semantic analysis.
Uses confidence thresholds to auto-apply high-confidence categorizations
and create a review queue for manual verification.
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager
from utils.product_categorizer import ProductCategorizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def categorize_all_products(confidence_threshold=0.8, dry_run=False, limit=None):
    """
    Categorize all products using LLM.
    
    Args:
        confidence_threshold: Minimum confidence for auto-apply (default 0.8)
        dry_run: If True, don't update database, just report
        limit: Limit number of products to process (for testing)
    """
    categorizer = ProductCategorizer()
    
    # Get all products
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT 
                id,
                name,
                short_description,
                product_type_data->'disambiguation'->>'product_form' as current_form,
                product_type_data->>'core_type' as current_core_type
            FROM clan_products
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        products = cursor.fetchall()
    
    logger.info(f"Processing {len(products)} products...")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Dry run: {dry_run}")
    
    high_confidence = []
    review_queue = []
    errors = []
    unchanged = []
    
    for i, product in enumerate(products, 1):
        if i % 10 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        result = categorizer.categorize_product(
            product_name=product['name'],
            description=product['short_description'],
            current_category=product['current_form'],
            current_core_type=product['current_core_type']
        )
        
        if result.get('error'):
            errors.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'error': result['error']
            })
        else:
            llm_form = result.get('product_form')
            llm_core_type = result.get('core_type')
            confidence = result.get('confidence', 0.0)
            reasoning = result.get('reasoning', '')
            
            # Check if unchanged
            if llm_form == product['current_form'] and llm_core_type == product['current_core_type']:
                unchanged.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'form': llm_form,
                    'core_type': llm_core_type
                })
            elif confidence > confidence_threshold:
                high_confidence.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'current_form': product['current_form'],
                    'current_core_type': product['current_core_type'],
                    'new_form': llm_form,
                    'new_core_type': llm_core_type,
                    'confidence': confidence,
                    'reasoning': reasoning
                })
            else:
                review_queue.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'current_form': product['current_form'],
                    'current_core_type': product['current_core_type'],
                    'new_form': llm_form,
                    'new_core_type': llm_core_type,
                    'confidence': confidence,
                    'reasoning': reasoning
                })
    
    # Print summary
    print("\n" + "="*80)
    print("CATEGORIZATION SUMMARY")
    print("="*80)
    print(f"Total products: {len(products)}")
    print(f"Unchanged: {len(unchanged)} ({100*len(unchanged)/len(products):.1f}%)")
    print(f"High confidence (auto-apply): {len(high_confidence)} ({100*len(high_confidence)/len(products):.1f}%)")
    print(f"Review queue: {len(review_queue)} ({100*len(review_queue)/len(products):.1f}%)")
    print(f"Errors: {len(errors)} ({100*len(errors)/len(products):.1f}%)")
    
    # Apply high-confidence changes
    if not dry_run and high_confidence:
        logger.info(f"\nApplying {len(high_confidence)} high-confidence categorizations...")
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
                
                # Update disambiguation.product_form
                if 'disambiguation' not in product_type_data:
                    product_type_data['disambiguation'] = {}
                
                product_type_data['disambiguation']['product_form'] = item['new_form']
                
                # Update core_type
                if item['new_core_type']:
                    product_type_data['core_type'] = item['new_core_type']
                
                # Update confidence
                product_type_data['categorization_confidence'] = item['confidence']
                product_type_data['categorization_method'] = 'llm'
                
                # Save back to database
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(product_type_data), item['product_id']))
        
        logger.info(f"Applied {len(high_confidence)} categorizations")
    
    # Save review queue to file
    if review_queue:
        review_file = 'data/llm_categorization_review_queue.json'
        with open(review_file, 'w') as f:
            json.dump(review_queue, f, indent=2)
        logger.info(f"\nReview queue saved to: {review_file}")
        logger.info(f"Review {len(review_queue)} products with confidence <= {confidence_threshold}")
    
    # Save errors to file
    if errors:
        error_file = 'data/llm_categorization_errors.json'
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
        logger.info(f"\nErrors saved to: {error_file}")
    
    # Show sample of high-confidence changes
    if high_confidence:
        print("\n" + "="*80)
        print("SAMPLE HIGH-CONFIDENCE CHANGES (first 10):")
        print("="*80)
        for item in high_confidence[:10]:
            print(f"\n{item['product_name']}")
            print(f"  {item['current_form']} / {item['current_core_type']} → {item['new_form']} / {item['new_core_type']}")
            print(f"  Confidence: {item['confidence']:.2f}")
            print(f"  Reasoning: {item['reasoning'][:100]}...")
    
    # Show sample of review queue
    if review_queue:
        print("\n" + "="*80)
        print("SAMPLE REVIEW QUEUE (first 10):")
        print("="*80)
        for item in review_queue[:10]:
            print(f"\n{item['product_name']}")
            print(f"  {item['current_form']} / {item['current_core_type']} → {item['new_form']} / {item['new_core_type']}")
            print(f"  Confidence: {item['confidence']:.2f}")
            print(f"  Reasoning: {item['reasoning'][:100]}...")
    
    return {
        'unchanged': len(unchanged),
        'high_confidence': len(high_confidence),
        'review_queue': len(review_queue),
        'errors': len(errors)
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Categorize all products using LLM')
    parser.add_argument('--threshold', type=float, default=0.8, help='Confidence threshold (default: 0.8)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    parser.add_argument('--limit', type=int, help='Limit number of products (for testing)')
    
    args = parser.parse_args()
    
    try:
        results = categorize_all_products(
            confidence_threshold=args.threshold,
            dry_run=args.dry_run,
            limit=args.limit
        )
        print(f"\n✅ Categorization complete!")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

