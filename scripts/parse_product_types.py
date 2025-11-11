#!/usr/bin/env python3
"""
Product Type Parser - Batch Processing Script

Parses product titles into structured type identifiers with confidence-based filtering.
Supports iterative refinement by re-processing only low-confidence products.

Usage:
    # Initial run (process all products)
    python scripts/parse_product_types.py --threshold 0.7
    
    # Review queue (list low-confidence products)
    python scripts/parse_product_types.py --review-queue --threshold 0.7
    
    # Re-process low-confidence only
    python scripts/parse_product_types.py --reprocess-low --threshold 0.7
    
    # Statistics
    python scripts/parse_product_types.py --stats
"""

import sys
import os
import argparse
import json
import logging
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.product_type_parser import ProductTypeParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_products_batch(offset: int, limit: int) -> List[Dict]:
    """Fetch a batch of products."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, category_ids, description
            FROM clan_products
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return cursor.fetchall()


def fetch_products_batch_low_confidence(offset: int, limit: int, threshold: float) -> List[Dict]:
    """Fetch products with low confidence or no parsing yet."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, category_ids, description
            FROM clan_products
            WHERE product_type_data->>'confidence' IS NULL
               OR (product_type_data->>'confidence')::float < %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (threshold, limit, offset))
        return cursor.fetchall()


def save_parsed_data(product_id: int, parsed_data: Dict, review_threshold: float):
    """Save parsed type data to database."""
    try:
        with db_manager.get_cursor() as cursor:
            # Set needs_review flag
            parsed_data['needs_review'] = parsed_data.get('confidence', 0.0) < review_threshold
            parsed_data['review_threshold'] = review_threshold
            
            # Convert to JSON
            json_data = json.dumps(parsed_data)
            
            cursor.execute("""
                UPDATE clan_products
                SET product_type_data = %s::jsonb
                WHERE id = %s
            """, (json_data, product_id))
            
            cursor.connection.commit()
            
    except Exception as e:
        logger.error(f"Error saving parsed data for product {product_id}: {e}")
        raise


def process_all_products(review_threshold: float = 0.7, reprocess_low_confidence: bool = False):
    """
    Process entire catalog in batches with confidence tracking.
    
    Args:
        review_threshold: Confidence below which products are flagged for review
        reprocess_low_confidence: If True, only process products with confidence < threshold
    """
    batch_size = 100
    
    # Get total count
    with db_manager.get_cursor() as cursor:
        if reprocess_low_confidence:
            cursor.execute("""
                SELECT COUNT(*) as count FROM clan_products
                WHERE product_type_data->>'confidence' IS NULL
                   OR (product_type_data->>'confidence')::float < %s
            """, (review_threshold,))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM clan_products")
        total = cursor.fetchone()['count']
    
    logger.info(f"Processing {total} products (threshold: {review_threshold})")
    
    parser = ProductTypeParser()
    stats = {
        'total': 0,
        'processed': 0,
        'high_confidence': 0,
        'low_confidence': 0,
        'errors': 0
    }
    
    for offset in range(0, total, batch_size):
        if reprocess_low_confidence:
            products = fetch_products_batch_low_confidence(offset, batch_size, review_threshold)
        else:
            products = fetch_products_batch(offset, batch_size)
        
        for product in products:
            stats['total'] += 1
            try:
                # Parse product
                parsed = parser.parse_product(
                    product['name'],
                    product.get('category_ids', []) or [],
                    product.get('description', '')[:200] if product.get('description') else None
                )
                
                # Save to database
                save_parsed_data(product['id'], parsed, review_threshold)
                
                stats['processed'] += 1
                if parsed.get('confidence', 0.0) >= review_threshold:
                    stats['high_confidence'] += 1
                else:
                    stats['low_confidence'] += 1
                
                # Log progress
                if stats['processed'] % 50 == 0:
                    logger.info(f"Processed {stats['processed']}/{total} products...")
                
            except Exception as e:
                logger.error(f"Error parsing product {product.get('id')} ({product.get('name', 'Unknown')}): {e}")
                stats['errors'] += 1
    
    logger.info(f"\nProcessing complete:")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Processed: {stats['processed']}")
    logger.info(f"  High confidence (>= {review_threshold}): {stats['high_confidence']}")
    logger.info(f"  Low confidence (< {review_threshold}): {stats['low_confidence']}")
    logger.info(f"  Errors: {stats['errors']}")
    
    return stats


def get_review_queue(threshold: float = 0.7, limit: int = 50):
    """Get products flagged for review."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'needs_review' = 'true'
               OR (product_type_data->>'confidence')::float < %s
            ORDER BY (product_type_data->>'confidence')::float ASC NULLS LAST
            LIMIT %s
        """, (threshold, limit))
        return cursor.fetchall()


def show_review_queue(threshold: float = 0.7, limit: int = 50):
    """Display products needing review."""
    products = get_review_queue(threshold, limit)
    
    if not products:
        print(f"No products found with confidence < {threshold}")
        return
    
    print(f"\nProducts needing review (confidence < {threshold}):\n")
    print(f"{'ID':<8} {'Name':<50} {'Core Type':<20} {'Confidence':<12} {'Method':<10}")
    print("-" * 100)
    
    for product in products:
        type_data = product.get('product_type_data') or {}
        core_type = type_data.get('core_type', 'N/A')
        confidence = type_data.get('confidence', 0.0)
        method = type_data.get('parsing_method', 'N/A')
        
        print(f"{product['id']:<8} {product['name'][:48]:<50} {str(core_type)[:18]:<20} {confidence:<12.2f} {method:<10}")
    
    print(f"\nTotal: {len(products)} products")


def show_statistics():
    """Show parsing statistics."""
    with db_manager.get_cursor() as cursor:
        # Overall stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(product_type_data->>'core_type') as parsed,
                AVG((product_type_data->>'confidence')::float) as avg_confidence,
                COUNT(*) FILTER (WHERE (product_type_data->>'confidence')::float < 0.7) as low_confidence
            FROM clan_products
        """)
        overall = cursor.fetchone()
        
        # By core_type
        cursor.execute("""
            SELECT 
                product_type_data->>'core_type' as core_type,
                COUNT(*) as count,
                AVG((product_type_data->>'confidence')::float) as avg_confidence
            FROM clan_products
            WHERE product_type_data->>'core_type' IS NOT NULL
            GROUP BY product_type_data->>'core_type'
            ORDER BY count DESC
            LIMIT 20
        """)
        by_type = cursor.fetchall()
        
        # By parsing method
        cursor.execute("""
            SELECT 
                product_type_data->>'parsing_method' as method,
                COUNT(*) as count,
                AVG((product_type_data->>'confidence')::float) as avg_confidence
            FROM clan_products
            WHERE product_type_data->>'parsing_method' IS NOT NULL
            GROUP BY product_type_data->>'parsing_method'
            ORDER BY count DESC
        """)
        by_method = cursor.fetchall()
    
    print("\n=== Product Type Parsing Statistics ===\n")
    
    print("Overall:")
    print(f"  Total products: {overall['total']}")
    print(f"  Parsed: {overall['parsed']}")
    print(f"  Average confidence: {overall['avg_confidence']:.2f}" if overall['avg_confidence'] else "  Average confidence: N/A")
    print(f"  Low confidence (< 0.7): {overall['low_confidence']}")
    
    print("\nTop 20 Core Types:")
    print(f"{'Core Type':<25} {'Count':<10} {'Avg Confidence':<15}")
    print("-" * 50)
    for row in by_type:
        print(f"{str(row['core_type'])[:23]:<25} {row['count']:<10} {row['avg_confidence']:.2f}" if row['avg_confidence'] else f"{str(row['core_type'])[:23]:<25} {row['count']:<10} N/A")
    
    print("\nBy Parsing Method:")
    print(f"{'Method':<15} {'Count':<10} {'Avg Confidence':<15}")
    print("-" * 40)
    for row in by_method:
        print(f"{str(row['method'])[:13]:<15} {row['count']:<10} {row['avg_confidence']:.2f}" if row['avg_confidence'] else f"{str(row['method'])[:13]:<15} {row['count']:<10} N/A")
    
    print()


def main():
    parser = argparse.ArgumentParser(description='Parse product types with confidence-based filtering')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Confidence threshold for review flagging (default: 0.7)')
    parser.add_argument('--reprocess-low', action='store_true',
                       help='Only process products with confidence < threshold')
    parser.add_argument('--review-queue', action='store_true',
                       help='Show products needing review')
    parser.add_argument('--stats', action='store_true',
                       help='Show parsing statistics')
    parser.add_argument('--limit', type=int, default=50,
                       help='Limit for review queue display (default: 50)')
    
    args = parser.parse_args()
    
    if args.stats:
        show_statistics()
    elif args.review_queue:
        show_review_queue(args.threshold, args.limit)
    else:
        process_all_products(args.threshold, args.reprocess_low)


if __name__ == '__main__':
    main()

