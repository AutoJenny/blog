#!/usr/bin/env python3
"""
Test script to compare Mistral 7B vs Llama 3.2 for product type parsing.
Tests on a subset of products that already have product_type_data.
"""

import sys
import os
import json
import logging
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.product_type_parser import ProductTypeParser
from blueprints.llm_actions import LLMService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelComparisonTester:
    """Test different models on the same products."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.llm_service = LLMService()
        # Override the model in ProductTypeParser
        self.parser = ProductTypeParser(llm_service=self.llm_service)
        # Monkey patch to use our model
        self._original_llm_parse = self.parser._llm_parse
        self.parser._llm_parse = self._patched_llm_parse
    
    def _patched_llm_parse(self, name: str, category_ids: List[int], 
                          description: str = None) -> Dict:
        """Patched version that uses our specified model."""
        if not self.parser.llm_service:
            return None
        
        try:
            from config.database import db_manager
            
            # Get category names
            category_names = []
            if category_ids:
                with db_manager.get_cursor() as cursor:
                    placeholders = ','.join(['%s'] * len(category_ids))
                    cursor.execute(f"""
                        SELECT name FROM clan_categories
                        WHERE id IN ({placeholders})
                    """, tuple(category_ids))
                    category_names = [row['name'] for row in cursor.fetchall()]
            
            category_context = ' > '.join(category_names) if category_names else 'Unknown'
            desc_snippet = (description[:200] if description else '') or 'No description available'
            
            prompt = f"""Parse this product title into structured identifiers:

Product: {name}
Categories: {category_context}
Description: {desc_snippet}

Context: We need to distinguish between:
- A kilt (garment) vs kilt pin (accessory) vs painting of a kilt (artwork)
- A ring (jewelry) vs keyring (accessory)
- A shirt (garment) vs shirt pin (accessory)

Extract and return JSON only with these fields:
{{
  "core_type": "string (e.g., kilt, shirt, sporran, ring, kilt_pin)",
  "subtype": "string or null (e.g., jacobite, dress, wedding)",
  "materials": ["array of materials"],
  "patterns": ["array of patterns"],
  "decorations": ["array of decorative elements"],
  "occasions": ["array of occasions/uses"],
  "styles": ["array of style identifiers"],
  "attributes": ["array of other attributes"],
  "disambiguation": {{
    "is_accessory": boolean,
    "is_artwork": boolean,
    "is_jewelry": boolean,
    "is_clothing": boolean,
    "product_form": "garment|accessory|jewelry|artwork|homeware|other"
  }},
  "confidence": 0.0-1.0
}}

Return only valid JSON, no markdown formatting."""
            
            messages = [
                {'role': 'system', 'content': 'You are a product classification expert. Parse product titles into structured identifiers. Return only valid JSON.'},
                {'role': 'user', 'content': prompt}
            ]
            
            # Use specified model
            result = self.parser.llm_service.execute_llm_request(
                provider='ollama',
                model=self.model_name,
                messages=messages
            )
            
            if result and 'error' in result:
                logger.warning(f"{self.model_name} parsing failed: {result.get('error')}, skipping LLM parsing for this product")
                return None
            
            if result and result.get('content'):
                content = result['content'].strip()
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                try:
                    llm_data = json.loads(content)
                    llm_data['parsing_method'] = f'llm_{self.model_name}'
                    return llm_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse {self.model_name} JSON response: {e}")
                    logger.debug(f"{self.model_name} response: {content}")
                    return None
            
        except Exception as e:
            logger.error(f"Error in {self.model_name} parsing: {e}")
            return None
        
        return None
    
    def parse_product(self, product: Dict) -> Dict:
        """Parse a single product using the configured model."""
        return self.parser.parse_product(
            product_name=product['name'],
            category_ids=product.get('category_ids', []),
            description=product.get('description')
        )


def fetch_test_products(limit: int = 20) -> List[Dict]:
    """Fetch products that already have product_type_data for comparison."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, category_ids, description, product_type_data
            FROM clan_products
            WHERE product_type_data IS NOT NULL 
              AND product_type_data != '{}'::jsonb
            ORDER BY id
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()


def compare_models(test_products: List[Dict], models: List[str] = ['llama3.2', 'mistral']):
    """Compare results from different models."""
    results = {}
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"Testing with {model}")
        print(f"{'='*60}\n")
        
        tester = ModelComparisonTester(model)
        model_results = []
        
        for product in test_products:
            try:
                new_result = tester.parse_product(product)
                old_result = product.get('product_type_data', {})
                
                comparison = {
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'old_core_type': old_result.get('core_type'),
                    'new_core_type': new_result.get('core_type'),
                    'old_confidence': old_result.get('confidence', 0.0),
                    'new_confidence': new_result.get('confidence', 0.0),
                    'old_method': old_result.get('parsing_method'),
                    'new_method': new_result.get('parsing_method'),
                    'changed': old_result.get('core_type') != new_result.get('core_type'),
                    'confidence_delta': new_result.get('confidence', 0.0) - old_result.get('confidence', 0.0),
                    'json_valid': True,
                    'full_result': new_result
                }
                
                model_results.append(comparison)
                
                # Print summary
                status = "✓" if not comparison['changed'] else "⚠"
                print(f"{status} ID {product['id']:3d}: {product['name'][:45]:<45} | "
                      f"Old: {str(comparison['old_core_type']):<15} ({comparison['old_confidence']:.2f}) | "
                      f"New: {str(comparison['new_core_type']):<15} ({comparison['new_confidence']:.2f})")
                
            except Exception as e:
                logger.error(f"Error processing product {product['id']}: {e}")
                model_results.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'error': str(e),
                    'json_valid': False
                })
        
        results[model] = model_results
    
    return results


def print_comparison_summary(results: Dict):
    """Print summary comparison of results."""
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}\n")
    
    for model, model_results in results.items():
        valid_results = [r for r in model_results if r.get('json_valid', False)]
        changed = sum(1 for r in valid_results if r.get('changed', False))
        avg_confidence = sum(r.get('new_confidence', 0.0) for r in valid_results) / len(valid_results) if valid_results else 0.0
        avg_confidence_delta = sum(r.get('confidence_delta', 0.0) for r in valid_results) / len(valid_results) if valid_results else 0.0
        
        print(f"{model}:")
        print(f"  Total tested: {len(model_results)}")
        print(f"  Valid JSON: {len(valid_results)}")
        print(f"  Changed classifications: {changed}")
        print(f"  Average confidence: {avg_confidence:.2f}")
        print(f"  Average confidence change: {avg_confidence_delta:+.2f}")
        print()
    
    # Detailed differences
    if 'llama3.2' in results and 'mistral' in results:
        llama_results = {r['product_id']: r for r in results['llama3.2'] if r.get('json_valid')}
        mistral_results = {r['product_id']: r for r in results['mistral'] if r.get('json_valid')}
        
        print(f"\n{'='*60}")
        print("DETAILED DIFFERENCES")
        print(f"{'='*60}\n")
        
        differences = []
        for pid in llama_results.keys():
            if pid in mistral_results:
                llama = llama_results[pid]
                mistral = mistral_results[pid]
                
                if llama['new_core_type'] != mistral['new_core_type']:
                    differences.append({
                        'id': pid,
                        'name': llama['product_name'],
                        'llama3.2': llama['new_core_type'],
                        'mistral': mistral['new_core_type'],
                        'llama_conf': llama['new_confidence'],
                        'mistral_conf': mistral['new_confidence']
                    })
        
        if differences:
            print(f"Found {len(differences)} products with different classifications:\n")
            for diff in differences:
                llama_type = str(diff['llama3.2']) if diff['llama3.2'] else 'None'
                mistral_type = str(diff['mistral']) if diff['mistral'] else 'None'
                print(f"ID {diff['id']:3d}: {diff['name'][:45]:<45}")
                print(f"  Llama 3.2: {llama_type:<20} (confidence: {diff['llama_conf']:.2f})")
                print(f"  Mistral:   {mistral_type:<20} (confidence: {diff['mistral_conf']:.2f})")
                print()
        else:
            print("No differences found - both models produced identical classifications!")


def main():
    print("="*60)
    print("MODEL COMPARISON TEST: Mistral 7B vs Llama 3.2")
    print("="*60)
    print("\nFetching test products...")
    
    test_products = fetch_test_products(limit=20)
    print(f"Found {len(test_products)} products with existing classifications\n")
    
    results = compare_models(test_products, models=['llama3.2', 'mistral'])
    
    print_comparison_summary(results)
    
    # Save detailed results to file
    output_file = '/tmp/model_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()

