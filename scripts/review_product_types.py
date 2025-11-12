#!/usr/bin/env python3
"""
Review Product Type Parsing Results

Displays products that need review:
1. Low confidence products (< threshold)
2. Products with errors (no product_type_data or parsing failures)
3. Products with None core_type

Usage:
    python scripts/review_product_types.py --threshold 0.7
    python scripts/review_product_types.py --threshold 0.7 --export-csv review_queue.csv
"""

import sys
import os
import argparse
import csv
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager


def get_low_confidence_products(threshold: float = 0.7, limit: int = None):
    """Get products with low confidence."""
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data IS NOT NULL
              AND product_type_data != '{}'::jsonb
              AND (
                  (product_type_data->>'confidence')::float < %s
                  OR product_type_data->>'needs_review' = 'true'
              )
            ORDER BY 
              COALESCE((product_type_data->>'confidence')::float, 0) ASC,
              id ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, (threshold,))
        return cursor.fetchall()


def get_error_products(limit: int = None):
    """Get products with no product_type_data (errors)."""
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data IS NULL 
               OR product_type_data = '{}'::jsonb
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        return cursor.fetchall()


def get_no_core_type_products(limit: int = None):
    """Get products with product_type_data but no core_type."""
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data IS NOT NULL
              AND product_type_data != '{}'::jsonb
              AND (
                  product_type_data->>'core_type' IS NULL
                  OR product_type_data->>'core_type' = 'null'
              )
            ORDER BY 
              COALESCE((product_type_data->>'confidence')::float, 0) ASC,
              id ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        return cursor.fetchall()


def display_review_queue(threshold: float = 0.7, limit: int = None, export_csv: str = None):
    """Display comprehensive review queue."""
    
    low_confidence = get_low_confidence_products(threshold, limit)
    errors = get_error_products(limit)
    no_core_type = get_no_core_type_products(limit)
    
    all_products = []
    
    print("=" * 100)
    print("PRODUCT TYPE PARSING REVIEW QUEUE")
    print("=" * 100)
    print(f"\nReview Threshold: {threshold}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Section 1: Low Confidence Products
    print("=" * 100)
    print(f"SECTION 1: LOW CONFIDENCE PRODUCTS (< {threshold})")
    print("=" * 100)
    print(f"\nFound {len(low_confidence)} products with low confidence:\n")
    
    if low_confidence:
        print(f"{'ID':<8} {'Product Name':<50} {'Core Type':<20} {'Confidence':<12} {'Method':<10}")
        print("-" * 100)
        
        for product in low_confidence:
            type_data = product.get('product_type_data') or {}
            core_type = type_data.get('core_type', 'None')
            confidence = type_data.get('confidence', 0.0)
            method = type_data.get('parsing_method', 'N/A')
            
            print(f"{product['id']:<8} {product['name'][:48]:<50} {str(core_type)[:18]:<20} {confidence:<12.2f} {method:<10}")
            
            all_products.append({
                'id': product['id'],
                'name': product['name'],
                'issue': 'low_confidence',
                'core_type': core_type,
                'confidence': confidence,
                'method': method,
                'details': f"Confidence {confidence:.2f} < {threshold}"
            })
    else:
        print("No low confidence products found.\n")
    
    # Section 2: Error Products (No product_type_data)
    print("\n" + "=" * 100)
    print("SECTION 2: ERROR PRODUCTS (No product_type_data)")
    print("=" * 100)
    print(f"\nFound {len(errors)} products with no product_type_data:\n")
    
    if errors:
        print(f"{'ID':<8} {'Product Name':<60}")
        print("-" * 100)
        
        for product in errors:
            print(f"{product['id']:<8} {product['name'][:58]:<60}")
            
            all_products.append({
                'id': product['id'],
                'name': product['name'],
                'issue': 'no_data',
                'core_type': 'N/A',
                'confidence': 0.0,
                'method': 'N/A',
                'details': 'No product_type_data in database'
            })
    else:
        print("No error products found.\n")
    
    # Section 3: Products with No Core Type
    print("\n" + "=" * 100)
    print("SECTION 3: PRODUCTS WITH NO CORE TYPE")
    print("=" * 100)
    print(f"\nFound {len(no_core_type)} products with product_type_data but no core_type:\n")
    
    if no_core_type:
        print(f"{'ID':<8} {'Product Name':<50} {'Confidence':<12} {'Method':<10}")
        print("-" * 100)
        
        for product in no_core_type:
            type_data = product.get('product_type_data') or {}
            confidence = type_data.get('confidence', 0.0)
            method = type_data.get('parsing_method', 'N/A')
            
            print(f"{product['id']:<8} {product['name'][:48]:<50} {confidence:<12.2f} {method:<10}")
            
            all_products.append({
                'id': product['id'],
                'name': product['name'],
                'issue': 'no_core_type',
                'core_type': 'None',
                'confidence': confidence,
                'method': method,
                'details': 'Has product_type_data but core_type is None'
            })
    else:
        print("No products with missing core_type found.\n")
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total products needing review: {len(all_products)}")
    print(f"  - Low confidence: {len(low_confidence)}")
    print(f"  - No product_type_data: {len(errors)}")
    print(f"  - No core_type: {len(no_core_type)}")
    
    # Export to CSV if requested
    if export_csv and all_products:
        with open(export_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'issue', 'core_type', 'confidence', 'method', 'details'])
            writer.writeheader()
            writer.writerows(all_products)
        print(f"\n✓ Exported {len(all_products)} products to {export_csv}")
    
    return all_products


def main():
    parser = argparse.ArgumentParser(description='Review product type parsing results')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Confidence threshold (default: 0.7)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of products per section (default: no limit)')
    parser.add_argument('--export-csv', type=str, default=None,
                       help='Export results to CSV file')
    
    args = parser.parse_args()
    
    display_review_queue(args.threshold, args.limit, args.export_csv)


if __name__ == '__main__':
    main()

