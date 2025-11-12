"""
Test LLM-based categorization on a sample of products
Compare with current categories to measure accuracy
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
from utils.product_categorizer import ProductCategorizer
import json

def test_llm_categorization():
    """
    Test LLM categorization on a sample of products.
    """
    categorizer = ProductCategorizer()
    
    # Get sample products from different categories
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                name,
                short_description,
                product_type_data->'disambiguation'->>'product_form' as current_form,
                product_type_data->>'core_type' as current_core_type
            FROM clan_products
            WHERE product_type_data IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 30
        """)
        
        products = cursor.fetchall()
    
    print("Testing LLM categorization on 30 random products:")
    print("="*80)
    
    correct = 0
    incorrect = 0
    errors = 0
    
    results = []
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] {product['name']}")
        print(f"  Current: {product['current_form']} / {product['current_core_type']}")
        
        result = categorizer.categorize_product(
            product_name=product['name'],
            description=product['short_description'],
            current_category=product['current_form'],
            current_core_type=product['current_core_type']
        )
        
        if result.get('error'):
            print(f"  ❌ Error: {result['error']}")
            errors += 1
        else:
            llm_form = result.get('product_form')
            llm_core_type = result.get('core_type')
            confidence = result.get('confidence', 0.0)
            reasoning = result.get('reasoning', '')
            
            print(f"  LLM: {llm_form} / {llm_core_type} (confidence: {confidence:.2f})")
            print(f"  Reasoning: {reasoning[:100]}")
            
            # Compare with current
            if llm_form == product['current_form']:
                print(f"  ✅ Match!")
                correct += 1
            else:
                print(f"  ⚠️  Different: {product['current_form']} → {llm_form}")
                incorrect += 1
            
            results.append({
                'product': product['name'],
                'current': product['current_form'],
                'llm': llm_form,
                'confidence': confidence,
                'match': llm_form == product['current_form']
            })
    
    print("\n" + "="*80)
    print("Summary:")
    print(f"  Total tested: {len(products)}")
    print(f"  Correct matches: {correct} ({100*correct/len(products):.1f}%)")
    print(f"  Different: {incorrect} ({100*incorrect/len(products):.1f}%)")
    print(f"  Errors: {errors} ({100*errors/len(products):.1f}%)")
    
    # Show differences
    if incorrect > 0:
        print("\nDifferences (LLM suggests different category):")
        for r in results:
            if not r['match']:
                print(f"  {r['product']}: {r['current']} → {r['llm']} (confidence: {r['confidence']:.2f})")
    
    return results

if __name__ == '__main__':
    try:
        results = test_llm_categorization()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

