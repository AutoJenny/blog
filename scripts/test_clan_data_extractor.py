#!/usr/bin/env python3
"""
Test script for ClanDataExtractor module

Tests data extraction, validation, formatting, and alternative product discovery.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.content_generation.clan_data_extractor import ClanDataExtractor
from config.database import db_manager
import json

def test_extract_product_data(extractor, product_id):
    """Test product data extraction."""
    print(f"\n{'='*60}")
    print(f"TEST 1: Extract Product Data (ID: {product_id})")
    print(f"{'='*60}")
    
    try:
        product_data = extractor.extract_product_data(product_id)
        
        print(f"✅ Product extracted successfully")
        print(f"   Name: {product_data.get('name', 'N/A')}")
        print(f"   SKU: {product_data.get('sku', 'N/A')}")
        print(f"   Price: {product_data.get('price', 'N/A')}")
        print(f"   Has Description: {product_data.get('has_description')}")
        print(f"   Has Supplier: {product_data.get('has_supplier')}")
        print(f"   Has Heritage Data: {product_data.get('has_heritage_data')}")
        print(f"   Categories: {len(product_data.get('categories', []))}")
        print(f"   Category IDs: {product_data.get('category_ids', [])}")
        
        return product_data
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_validate_data_completeness(extractor, product_data):
    """Test data validation."""
    print(f"\n{'='*60}")
    print(f"TEST 2: Validate Data Completeness")
    print(f"{'='*60}")
    
    try:
        validation = extractor.validate_data_completeness(product_data)
        
        print(f"✅ Validation completed")
        print(f"   Has Minimum Requirements: {validation.get('has_minimum_requirements')}")
        print(f"   Core Completeness: {validation.get('core_completeness', 0):.1%}")
        print(f"   Optional Completeness: {validation.get('optional_completeness', 0):.1%}")
        print(f"   Threshold: {validation.get('threshold')} words")
        print(f"\n   Word Counts:")
        word_counts = validation.get('word_counts', {})
        print(f"     Description: {word_counts.get('description', 0)} words")
        print(f"     Supplier Description: {word_counts.get('supplier_description', 0)} words")
        if word_counts.get('heritage_data'):
            for key, count in word_counts['heritage_data'].items():
                print(f"     Heritage {key}: {count} words")
        
        print(f"\n   Needs LLM Supplement:")
        needs = validation.get('needs_llm_supplement', {})
        print(f"     Description: {needs.get('description', False)}")
        print(f"     Supplier Description: {needs.get('supplier_description', False)}")
        if needs.get('heritage_data'):
            for key, needs_supp in needs['heritage_data'].items():
                print(f"     Heritage {key}: {needs_supp}")
        
        if validation.get('missing_fields'):
            print(f"\n   ⚠️  Missing Fields: {', '.join(validation['missing_fields'])}")
        
        return validation
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_format_for_prompt(extractor, product_data, validation):
    """Test prompt formatting."""
    print(f"\n{'='*60}")
    print(f"TEST 3: Format for Prompt")
    print(f"{'='*60}")
    
    try:
        formatted = extractor.format_for_prompt(product_data, validation)
        
        print(f"✅ Prompt formatted successfully")
        print(f"   Length: {len(formatted)} characters")
        print(f"   Lines: {len(formatted.split(chr(10)))}")
        
        # Show first 500 characters
        print(f"\n   Preview (first 500 chars):")
        print(f"   {'-'*60}")
        print(f"   {formatted[:500]}...")
        print(f"   {'-'*60}")
        
        # Check for key sections
        has_clan_data = "=== CLAN DATA" in formatted
        has_llm_supplement = "=== LLM SUPPLEMENTATION" in formatted
        print(f"\n   Contains CLAN DATA section: {has_clan_data}")
        print(f"   Contains LLM SUPPLEMENTATION section: {has_llm_supplement}")
        
        return formatted
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_find_alternative_products(extractor, product_id, product_data):
    """Test alternative product discovery."""
    print(f"\n{'='*60}")
    print(f"TEST 4: Find Alternative Products")
    print(f"{'='*60}")
    
    try:
        alternatives = extractor.find_alternative_products(product_id, limit=5)
        
        print(f"✅ Found {len(alternatives)} alternative products")
        
        for i, alt in enumerate(alternatives, 1):
            print(f"\n   Alternative {i}:")
            print(f"     ID: {alt.get('id')}")
            print(f"     Name: {alt.get('name', 'N/A')[:50]}")
            print(f"     Strategy: {alt.get('discovery_strategy', 'unknown')}")
            if alt.get('price_comparison'):
                print(f"     Price: {alt.get('price_comparison')}")
            if alt.get('similarity_score'):
                print(f"     Similarity: {alt.get('similarity_score', 0):.3f}")
        
        # Count by strategy
        strategies = {}
        for alt in alternatives:
            strategy = alt.get('discovery_strategy', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        print(f"\n   Discovery Strategies:")
        for strategy, count in strategies.items():
            print(f"     {strategy}: {count}")
        
        return alternatives
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests."""
    print("="*60)
    print("CLAN Data Extractor - Test Suite")
    print("="*60)
    
    # Get a test product ID
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, sku 
            FROM clan_products 
            WHERE name IS NOT NULL 
              AND (description IS NOT NULL OR short_description IS NOT NULL)
              AND supplier_name IS NOT NULL
            LIMIT 1
        """)
        product = cursor.fetchone()
        
        if not product:
            print("❌ No products found with required fields for testing")
            return
        
        test_product_id = product['id']
        print(f"\n📦 Testing with Product ID: {test_product_id}")
        print(f"   Name: {product.get('name', 'N/A')[:60]}")
        print(f"   SKU: {product.get('sku', 'N/A')}")
    
    # Initialize extractor
    extractor = ClanDataExtractor()
    print(f"\n✅ ClanDataExtractor initialized")
    print(f"   LLM Threshold: {extractor.llm_threshold} words")
    print(f"   FAISS Index Available: {extractor.retriever is not None}")
    
    # Run tests
    product_data = test_extract_product_data(extractor, test_product_id)
    if not product_data:
        print("\n❌ Test 1 failed - cannot continue")
        return
    
    validation = test_validate_data_completeness(extractor, product_data)
    if not validation:
        print("\n❌ Test 2 failed - cannot continue")
        return
    
    formatted = test_format_for_prompt(extractor, product_data, validation)
    if not formatted:
        print("\n❌ Test 3 failed")
    
    alternatives = test_find_alternative_products(extractor, test_product_id, product_data)
    if alternatives is None:
        print("\n❌ Test 4 failed")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Test 1: Extract Product Data - {'PASSED' if product_data else 'FAILED'}")
    print(f"✅ Test 2: Validate Data Completeness - {'PASSED' if validation else 'FAILED'}")
    print(f"✅ Test 3: Format for Prompt - {'PASSED' if formatted else 'FAILED'}")
    print(f"✅ Test 4: Find Alternative Products - {'PASSED' if alternatives is not None else 'FAILED'}")
    
    if all([product_data, validation, formatted, alternatives is not None]):
        print(f"\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  Some tests failed")

if __name__ == '__main__':
    main()

