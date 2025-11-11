#!/usr/bin/env python3
"""
Bulk Product Enrichment Script

Enriches ALL products in the database with full data from CLAN API:
- Full description (with bullet points)
- Short description
- Supplier information
- Configurable options
- Specifications (if available in API)
- Sets has_detailed_data = true

Usage:
    python3 scripts/enrich_all_products.py [--limit N] [--skip-existing] [--delay SECONDS]
"""

import sys
import os
import time
import logging
import argparse
from datetime import datetime

# Add paths for imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)  # Add project root to path first
sys.path.append(os.path.join(project_root, 'blog-clan-api'))
sys.path.append(os.path.join(project_root, 'blog-launchpad'))

from config.database import db_manager

# Import from blog-clan-api (need to import module, not function directly)
import importlib.util
clan_api_path = os.path.join(project_root, 'blog-clan-api', 'clan_client.py')
spec = importlib.util.spec_from_file_location("clan_client", clan_api_path)
clan_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clan_client_module)
ClanAPIClient = clan_client_module.ClanAPIClient

transformers_path = os.path.join(project_root, 'blog-clan-api', 'transformers.py')
spec = importlib.util.spec_from_file_location("transformers_local", transformers_path)
transformers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transformers_module)
transform_product_for_ui = transformers_module.transform_product_for_ui

launchpad_path = os.path.join(project_root, 'blog-launchpad', 'clan_cache.py')
spec = importlib.util.spec_from_file_location("clan_cache", launchpad_path)
clan_cache_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clan_cache_module)
ClanCache = clan_cache_module.ClanCache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def enrich_all_products(limit=None, skip_existing=False, delay=0.5):
    """
    Enrich all products in the database with full data from CLAN API.
    
    Args:
        limit: Maximum number of products to enrich (None = all)
        skip_existing: Skip products that already have has_detailed_data = true
        delay: Delay between API calls (seconds) to be polite to upstream
    """
    client = ClanAPIClient()
    cache = ClanCache()
    
    # Get all products from database
    with db_manager.get_cursor() as cursor:
        query = """
            SELECT id, sku, name, has_detailed_data
            FROM clan_products
            ORDER BY id
        """
        
        if skip_existing:
            query = """
                SELECT id, sku, name, has_detailed_data
                FROM clan_products
                WHERE has_detailed_data = false OR has_detailed_data IS NULL
                ORDER BY id
            """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        products = cursor.fetchall()
    
    total = len(products)
    logger.info(f"Found {total} products to enrich")
    
    if total == 0:
        logger.info("No products to enrich")
        return
    
    # Statistics
    enriched = 0
    failed = 0
    skipped = 0
    
    start_time = time.time()
    
    for i, product in enumerate(products, 1):
        product_id = product['id']
        sku = product['sku']
        name = product['name']
        already_enriched = product.get('has_detailed_data', False)
        
        if skip_existing and already_enriched:
            skipped += 1
            logger.info(f"[{i}/{total}] SKIPPED: {name} (SKU: {sku}) - already enriched")
            continue
        
        try:
            logger.info(f"[{i}/{total}] Enriching: {name} (SKU: {sku})")
            
            # Fetch full product data from CLAN API
            api_result = client.get_product_data(sku, all_images=False)
            
            if not api_result.get('success', True):
                error_msg = api_result.get('message', 'Unknown error')
                logger.warning(f"  ❌ API error: {error_msg}")
                failed += 1
                continue
            
            api_data = api_result.get('data')
            if not api_data:
                logger.warning(f"  ❌ No data returned from API")
                failed += 1
                continue
            
            # Transform API data to our format
            transformed = transform_product_for_ui(api_data)
            
            # Ensure we have the product ID
            if not transformed.get('id'):
                transformed['id'] = product_id
            
            # Extract additional fields that transformer might not handle
            # These come directly from the API response
            if 'short_description' in api_data:
                transformed['short_description'] = api_data.get('short_description', '')
            if 'supplier_name' in api_data:
                transformed['supplier_name'] = api_data.get('supplier_name', '')
            if 'supplier_description' in api_data:
                transformed['supplier_description'] = api_data.get('supplier_description', '')
            if 'configurable_options' in api_data:
                transformed['configurable_options'] = api_data.get('configurable_options', None)
            if 'created_at' in api_data:
                transformed['created_at'] = api_data.get('created_at')
            if 'updated_at' in api_data:
                transformed['updated_at'] = api_data.get('updated_at')
            
            # Mark as enriched
            transformed['has_detailed_data'] = True
            
            # Store enriched product data
            success = cache.store_single_product(transformed)
            
            if success:
                enriched += 1
                logger.info(f"  ✅ Enriched successfully")
            else:
                failed += 1
                logger.warning(f"  ❌ Failed to store in database")
            
            # Be polite to upstream API
            if delay > 0 and i < total:
                time.sleep(delay)
                
        except Exception as e:
            failed += 1
            logger.error(f"  ❌ Error enriching {sku}: {str(e)}", exc_info=True)
        
        # Progress update every 10 products
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (total - i) / rate if rate > 0 else 0
            logger.info(f"Progress: {i}/{total} ({i*100//total}%) | "
                       f"Enriched: {enriched} | Failed: {failed} | "
                       f"Rate: {rate:.1f}/sec | ETA: {remaining:.0f}s")
    
    # Final summary
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("ENRICHMENT COMPLETE")
    logger.info(f"Total products: {total}")
    logger.info(f"Successfully enriched: {enriched}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Average rate: {total/elapsed:.2f} products/second" if elapsed > 0 else "N/A")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Enrich all products with full CLAN API data')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of products to enrich (default: all)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip products that already have has_detailed_data = true')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between API calls in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    logger.info("Starting bulk product enrichment...")
    logger.info(f"Options: limit={args.limit}, skip_existing={args.skip_existing}, delay={args.delay}")
    
    enrich_all_products(
        limit=args.limit,
        skip_existing=args.skip_existing,
        delay=args.delay
    )


if __name__ == '__main__':
    main()

