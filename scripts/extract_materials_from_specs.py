"""
Extract materials from additional_data specification fields.

Re-fetches products with missing materials from CLAN API to get their
specification data, then extracts materials from fields like:
- "Material" → material value
- "Stone or Enamel" → stone_or_enamel value
- Other specification fields that might contain materials
"""

import sys
import os
sys.path.insert(0, '.')
# Add blog-clan-api to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))

import json
import logging
import time
from config.database import db_manager
from scripts.rationalize_materials import normalize_material, VALID_MATERIALS
from clan_client import ClanAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fields in additional_data that might contain materials
MATERIAL_FIELDS = [
    'material',
    'stone_or_enamel',
    'stone',
    'enamel',
    'metal',
    'fabric',
    'composition',
    'fiber',
    'fibre',
    'content',
    'materials',  # Plural form
]

def extract_materials_from_additional_data(additional_data):
    """
    Extract materials from additional_data JSONB field.
    
    Args:
        additional_data: JSONB dict with specification fields
        
    Returns:
        List of extracted material values
    """
    if not additional_data or not isinstance(additional_data, dict):
        return []
    
    extracted = []
    
    for field_name in MATERIAL_FIELDS:
        # Check if field exists (case-insensitive)
        field_key = None
        for key in additional_data.keys():
            if key.lower() == field_name.lower():
                field_key = key
                break
        
        if field_key:
            field_data = additional_data[field_key]
            
            # Handle different structures:
            # 1. Direct value: {"material": "Silver"}
            # 2. Object with value: {"material": {"value": "Silver", "label": "Material"}}
            # 3. Array: {"materials": ["wool", "cotton"]}
            
            if isinstance(field_data, dict):
                # Object structure - get 'value' field
                value = field_data.get('value') or field_data.get('label')
                if value:
                    # Normalize the material
                    normalized = normalize_material(str(value))
                    if normalized:
                        if isinstance(normalized, list):
                            extracted.extend(normalized)
                        else:
                            extracted.append(normalized)
            elif isinstance(field_data, list):
                # Array structure
                for item in field_data:
                    if item:
                        normalized = normalize_material(str(item))
                        if normalized:
                            if isinstance(normalized, list):
                                extracted.extend(normalized)
                            else:
                                extracted.append(normalized)
            elif field_data:
                # Direct value
                normalized = normalize_material(str(field_data))
                if normalized:
                    if isinstance(normalized, list):
                        extracted.extend(normalized)
                    else:
                        extracted.append(normalized)
    
    # Remove duplicates and sort
    return sorted(list(set(extracted)))

def enrich_all_products(dry_run=False, limit=None):
    """
    Re-fetch ALL products from CLAN API to get their additional_data.
    """
    api_client = ClanAPIClient()
    
    with db_manager.get_cursor() as cursor:
        # Get all products that don't have additional_data
        query = """
            SELECT id, sku, name, product_type_data, additional_data
            FROM clan_products
            WHERE additional_data IS NULL
               OR additional_data = '{}'::jsonb
               OR additional_data = 'null'::jsonb
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        products = cursor.fetchall()
    
    logger.info(f"Found {len(products)} products without additional_data")
    logger.info(f"Dry run: {dry_run}")
    
    updated_count = 0
    no_additional_data = []
    errors = []
    
    for i, product in enumerate(products, 1):
        if i % 50 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        product_id = product['id']
        sku = product['sku']
        product_name = product['name']
        
        try:
            # Fetch product data from API
            result = api_client.get_product_data(sku, all_images=False)
            
            if not result.get('success', True):
                errors.append({
                    'id': product_id,
                    'name': product_name,
                    'error': result.get('message', 'Unknown API error')
                })
                continue
            
            product_data = result.get('data', {})
            additional_data = product_data.get('additional_data')
            
            if additional_data:
                # Update additional_data in the database
                if not dry_run:
                    cursor.execute("""
                        UPDATE clan_products
                        SET additional_data = %s
                        WHERE id = %s
                    """, (
                        json.dumps(additional_data),
                        product_id
                    ))
                updated_count += 1
            else:
                no_additional_data.append({
                    'id': product_id,
                    'name': product_name,
                    'reason': 'No additional_data in API response'
                })
            
            # Rate limiting - increased to avoid 429 errors
            time.sleep(1.0)
            
        except Exception as e:
            logger.error(f"Error processing product {product_id} ({product_name}): {e}")
            errors.append({
                'id': product_id,
                'name': product_name,
                'error': str(e)
            })
    
    if not dry_run:
        db_manager.get_connection().commit()
    
    logger.info(f"Enriched {updated_count} products with additional_data")
    return updated_count

def extract_materials_for_missing(dry_run=False):
    """
    Extract materials from additional_data for products with missing materials.
    """
    with db_manager.get_cursor() as cursor:
        # Get products with missing materials that now have additional_data
        cursor.execute("""
            SELECT id, name, additional_data, product_type_data
            FROM clan_products
            WHERE (
                product_type_data->'materials' IS NULL
                OR product_type_data->'materials' = '[]'::jsonb
                OR jsonb_array_length(product_type_data->'materials') = 0
            )
            AND additional_data IS NOT NULL
            AND additional_data != '{}'::jsonb
            AND additional_data != 'null'::jsonb
            ORDER BY id
        """)
        products = cursor.fetchall()
    
    logger.info(f"Found {len(products)} products with missing materials that have additional_data")
    logger.info(f"Dry run: {dry_run}")
    
    updated_count = 0
    no_materials_found = []
    changes_summary = {}
    
    for i, product in enumerate(products, 1):
        if i % 50 == 0:
            logger.info(f"Processed {i}/{len(products)} products...")
        
        product_id = product['id']
        product_name = product['name']
        additional_data = product['additional_data']
        type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
        
        # Extract materials from additional_data
        extracted_materials = extract_materials_from_additional_data(additional_data)
        
        if extracted_materials:
            # Update product_type_data
            if not dry_run:
                type_data['materials'] = extracted_materials
                
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (
                    json.dumps(type_data),
                    product_id
                ))
            
            change_key = f"[] → {sorted(extracted_materials)}"
            changes_summary[change_key] = changes_summary.get(change_key, 0) + 1
            updated_count += 1
        else:
            no_materials_found.append({
                'id': product_id,
                'name': product_name,
                'reason': 'No materials found in additional_data',
                'additional_data': additional_data
            })
    
    if not dry_run:
        db_manager.get_connection().commit()
    
    # Print summary
    print("\n" + "="*80)
    print("MATERIALS EXTRACTION FROM SPECIFICATIONS SUMMARY")
    print("="*80)
    print(f"Total products checked: {len(products)}")
    if len(products) > 0:
        print(f"Materials extracted: {updated_count} ({100*updated_count/len(products):.1f}%)")
        print(f"No materials found: {len(no_materials_found)} ({100*len(no_materials_found)/len(products):.1f}%)")
    else:
        print(f"Materials extracted: {updated_count}")
        print(f"No materials found: {len(no_materials_found)}")
    
    # Show sample changes
    if changes_summary:
        print("\n" + "="*80)
        print("SAMPLE EXTRACTIONS (first 20):")
        print("="*80)
        for change, count in list(changes_summary.items())[:20]:
            print(f"  {change} ({count} products)")
    
    # Show sample products with no materials found
    if no_materials_found:
        print("\n" + "="*80)
        print("PRODUCTS WITH NO MATERIALS IN SPECIFICATIONS (first 10):")
        print("="*80)
        for item in no_materials_found[:10]:
            print(f"  [{item['id']}] {item['name']}")
            print(f"      Reason: {item['reason']}")
            if 'additional_data' in item:
                print(f"      Additional Data: {json.dumps(item['additional_data'], indent=2)[:200]}...")
    
    return {
        'extracted': updated_count,
        'no_materials': len(no_materials_found)
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract materials from specification fields')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    parser.add_argument('--limit', type=int, help='Limit number of products to process')
    parser.add_argument('--skip-enrichment', action='store_true', help='Skip enrichment step (assume additional_data already exists)')
    
    args = parser.parse_args()
    
    try:
        if not args.skip_enrichment:
            print("="*80)
            print("STEP 1: Enriching all products with additional_data from CLAN API")
            print("="*80)
            enriched = enrich_all_products(dry_run=args.dry_run, limit=args.limit)
            print(f"\n✅ Enriched {enriched} products with additional_data\n")
        
        print("="*80)
        print("STEP 2: Extracting materials from additional_data for products with missing materials")
        print("="*80)
        results = extract_materials_for_missing(dry_run=args.dry_run)
        print(f"\n✅ Extraction complete!")
        print(f"   Materials extracted: {results['extracted']}")
        print(f"   No materials found: {results['no_materials']}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
