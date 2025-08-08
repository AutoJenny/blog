#!/usr/bin/env python3
"""
Clan.com API Microservice
Provides access to clan.com product and category data
"""

from flask import Flask, jsonify, request
from clan_client import ClanAPIClient
from transformers import flatten_category_tree, transform_product_for_ui
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
clan_api = ClanAPIClient()

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'service': 'clan-api',
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({'message': 'Test endpoint working'})

@app.route('/api/categories')
def get_categories():
    """Get all categories from clan.com"""
    try:
        logger.info("Fetching categories from clan.com API")
        
        result = clan_api.get_category_tree()
        
        if result.get('success', True):
            categories = result.get('data', [])
            flat_categories = flatten_category_tree(categories)
            logger.info(f"Successfully fetched {len(flat_categories)} categories")
            return jsonify(flat_categories)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching categories: {str(e)}")
        return jsonify([]), 500

@app.route('/api/products')
def get_products():
    """Get products from clan.com with optional search"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50)
        
        logger.info(f"Fetching products from clan.com API (limit: {limit}, query: '{query}')")
        
        # Use real clan.com API data
        # Get ALL products with real images
        actual_limit = int(limit) if limit and limit != 'None' else None
        result = clan_api.get_products(limit=actual_limit, include_images=True)
        
        if result.get('success', True):
            products = result.get('data', [])
            
            # Filter by query if provided
            if query:
                products = [p for p in products if query.lower() in p[0].lower()]
            
            # Transform products for UI
            transformed_products = [transform_product_for_ui(p) for p in products]
            logger.info(f"Successfully fetched {len(transformed_products)} products")
            return jsonify(transformed_products)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching products: {str(e)}")
        return jsonify([]), 500

@app.route('/api/products/incremental-download', methods=['POST'])
def incremental_product_download():
    """Download all products incrementally, saving to database as we go"""
    try:
        from clan_client import ClanAPIClient
        import time
        
        client = ClanAPIClient()
        
        # Get basic product list first
        all_basic_products = []
        offset = 0
        batch_size = 100
        
        logger.info("Starting incremental product download...")
        
        # Get ALL basic products first
        while True:
            params = {'limit': batch_size, 'offset': offset}
            basic_result = client.make_api_request('/getProducts', params)
            
            if not basic_result.get('success', True):
                break
            
            batch_products = basic_result.get('data', [])
            if not batch_products:
                break
            
            all_basic_products.extend(batch_products)
            offset += batch_size
            
            logger.info(f"Fetched {len(all_basic_products)} basic products so far...")
            
            # Small delay between batches
            time.sleep(0.1)
        
        logger.info(f"Total basic products to process: {len(all_basic_products)}")
        
        # Now process each product individually and save immediately
        successful_products = 0
        failed_products = 0
        
        for i, product in enumerate(all_basic_products):
            try:
                if isinstance(product, list) and len(product) > 1:
                    sku = product[1]
                    detailed_result = client.get_product_data(sku, all_images=True)
                    
                    if detailed_result.get('success', True):
                        product_data = detailed_result.get('data')
                        if product_data:
                            # Transform the product for storage
                            from transformers import transform_product_for_ui
                            transformed_product = transform_product_for_ui(product_data)
                            
                            # Save to database immediately
                            # We'll need to call the blog-launchpad's clan_cache to save
                            import requests
                            save_response = requests.post(
                                'http://localhost:5001/api/clan/cache/save-product',
                                json=transformed_product,
                                timeout=10
                            )
                            
                            if save_response.status_code == 200:
                                successful_products += 1
                                if successful_products % 10 == 0:
                                    logger.info(f"Saved {successful_products} products to database...")
                            else:
                                failed_products += 1
                                logger.error(f"Failed to save product {sku}: {save_response.status_code}")
                        else:
                            failed_products += 1
                    else:
                        failed_products += 1
                        logger.warning(f"Failed to get detailed data for product {sku}")
                else:
                    failed_products += 1
                
                # Delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                failed_products += 1
                logger.error(f"Error processing product {i}: {str(e)}")
                continue
        
        logger.info(f"Incremental download complete: {successful_products} successful, {failed_products} failed")
        
        return jsonify({
            'success': True,
            'message': f'Incremental download complete: {successful_products} products saved, {failed_products} failed',
            'stats': {
                'total_processed': len(all_basic_products),
                'successful': successful_products,
                'failed': failed_products
            }
        })
        
    except Exception as e:
        logger.error(f"Error in incremental download: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/products/download-all-basic', methods=['POST'])
def download_all_basic_products():
    """Download all basic products (SKUs) first, then populate details incrementally"""
    try:
        from clan_client import ClanAPIClient
        import time
        
        client = ClanAPIClient()
        
        logger.info("Starting download of all basic products...")
        
        # Get ALL basic products by making multiple calls
        all_basic_products = []
        successful_basic = 0
        failed_basic = 0
        
        # Get all products in one call
        params = {'limit': 1200}
        basic_result = client.make_api_request('/getProducts', params)
        
        if basic_result.get('success', True):
            batch1 = basic_result.get('data', [])
            all_basic_products.extend(batch1)
            logger.info(f"Fetched first batch: {len(batch1)} products")
        

        
        logger.info(f"Total products fetched: {len(all_basic_products)}")
        
        # Store all basic products immediately
        for product in all_basic_products:
            try:
                if isinstance(product, list) and len(product) > 1:
                    # Create basic product data
                    basic_product_data = {
                        'id': hash(product[1]) % 100000,  # Generate ID from SKU
                        'name': product[0],
                        'sku': product[1],
                        'url': product[2],
                        'description': product[3] if len(product) > 3 else '',
                        'image_url': '',  # Will be populated later
                        'price': '',  # Will be populated later
                        'has_detailed_data': False  # Flag to track what's been populated
                    }
                    
                    # Save to database immediately
                    import requests
                    save_response = requests.post(
                        'http://localhost:5001/api/clan/cache/save-product',
                        json=basic_product_data,
                        timeout=10
                    )
                    
                    if save_response.status_code == 200:
                        successful_basic += 1
                        if successful_basic % 100 == 0:
                            logger.info(f"Saved {successful_basic} basic products...")
                    else:
                        failed_basic += 1
                        logger.error(f"Failed to save basic product {product[1]}: {save_response.status_code}")
                else:
                    failed_basic += 1
                    
            except Exception as e:
                failed_basic += 1
                logger.error(f"Error processing basic product: {str(e)}")
                continue
        
        logger.info(f"Basic download complete: {successful_basic} successful, {failed_basic} failed")
        
        return jsonify({
            'success': True,
            'message': f'Downloaded {successful_basic} basic products. Ready for incremental detail population.',
            'stats': {
                'total_products': len(all_basic_products),
                'basic_saved': successful_basic,
                'basic_failed': failed_basic,
                'ready_for_details': True
            }
        })
        
    except Exception as e:
        logger.error(f"Error in basic download: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/products/populate-details', methods=['POST'])
def populate_product_details():
    """Populate detailed data for all products that don't have has_detailed_data=True"""
    try:
        from clan_client import ClanAPIClient
        import time
        import requests
        
        client = ClanAPIClient()
        
        logger.info("Starting detailed data population for products...")
        
        # Get products that need detailed data from blog-launchpad
        try:
            response = requests.get('http://localhost:5001/api/clan/products?limit=2000', timeout=30)
            if response.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'Failed to get products from blog-launchpad: {response.status_code}'
                }), 500
            
            all_products = response.json()
            # Check for products missing price or image_url (indicating they need detailed data)
            products_needing_details = [p for p in all_products if not p.get('price') or not p.get('image_url')]
            
            logger.info(f"Found {len(products_needing_details)} products needing detailed data out of {len(all_products)} total")
            
        except Exception as e:
            logger.error(f"Error getting products from blog-launchpad: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to get products: {str(e)}'
            }), 500
        
        if not products_needing_details:
            return jsonify({
                'success': True,
                'message': 'All products already have price and image data',
                'stats': {
                    'total_products': len(all_products),
                    'products_processed': 0,
                    'products_failed': 0,
                    'products_updated': 0
                }
            })
        
        # Process products in batches
        batch_size = 10
        successful_updates = 0
        failed_updates = 0
        total_processed = 0
        
        for i in range(0, len(products_needing_details), batch_size):
            batch = products_needing_details[i:i + batch_size]
            batch_start = i + 1
            batch_end = min(i + batch_size, len(products_needing_details))
            
            logger.info(f"Processing batch {batch_start}-{batch_end} of {len(products_needing_details)} products...")
            
            for product in batch:
                try:
                    sku = product.get('sku')
                    if not sku:
                        logger.warning(f"Product {product.get('id')} has no SKU, skipping")
                        failed_updates += 1
                        continue
                    
                    # Get detailed product data from external API
                    detailed_result = client.get_product_data(sku, all_images=False)
                    
                    if not detailed_result.get('success', True):
                        logger.warning(f"Failed to get detailed data for SKU {sku}")
                        failed_updates += 1
                        continue
                    
                    detailed_data = detailed_result.get('data', {})
                    
                    # Prepare updated product data with ALL available fields
                    updated_product = {
                        'id': product.get('id'),
                        'name': detailed_data.get('title', product.get('name', '')),
                        'sku': sku,
                        'url': detailed_data.get('product_url', product.get('url', '')),
                        'image_url': detailed_data.get('image', ''),
                        'price': str(detailed_data.get('price', '')) if detailed_data.get('price') else '',
                        'description': detailed_data.get('description', product.get('description', '')),
                        'has_detailed_data': True
                    }
                    
                    # Send updated product to blog-launchpad
                    save_response = requests.post(
                        'http://localhost:5001/api/clan/cache/save-product',
                        json=updated_product,
                        timeout=10
                    )
                    
                    if save_response.status_code == 200:
                        successful_updates += 1
                        if successful_updates % 50 == 0:
                            logger.info(f"Successfully updated {successful_updates} products...")
                    else:
                        failed_updates += 1
                        logger.error(f"Failed to save updated product {sku}: {save_response.status_code}")
                    
                    total_processed += 1
                    
                    # Rate limiting - delay between individual products
                    time.sleep(0.5)
                    
                except Exception as e:
                    failed_updates += 1
                    logger.error(f"Error processing product {product.get('sku', 'unknown')}: {str(e)}")
                    continue
            
            # Progress report after each batch
            logger.info(f"Batch {batch_start}-{batch_end} complete. Progress: {total_processed}/{len(products_needing_details)} products processed")
            
            # Rate limiting - delay between batches
            time.sleep(1)
        
        logger.info(f"Detailed data population complete: {successful_updates} successful, {failed_updates} failed")
        
        return jsonify({
            'success': True,
            'message': f'Detailed data population complete. {successful_updates} products updated successfully.',
            'stats': {
                'total_products': len(all_products),
                'products_needing_details': len(products_needing_details),
                'products_processed': total_processed,
                'products_updated': successful_updates,
                'products_failed': failed_updates
            }
        })
        
    except Exception as e:
        logger.error(f"Error in detailed data population: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories/<int:category_id>/products')
def get_category_products(category_id):
    """Get products from a specific category"""
    try:
        logger.info(f"Fetching products for category {category_id}")
        
        # Get ALL products with real images
        result = clan_api.get_products(limit=None, include_images=True)
        if result.get('success', True):
            products = result.get('data', [])
            
            # For now, return random products since category filtering isn't available
            import random
            if len(products) > 6:
                products = random.sample(products, 6)
            
            transformed_products = [transform_product_for_ui(p) for p in products]
            
            logger.info(f"Found {len(transformed_products)} products for category {category_id}")
            return jsonify(transformed_products)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching category products: {str(e)}")
        return jsonify([]), 500

@app.route('/api/products/<int:product_id>/related')
def get_related_products(product_id):
    """Get related products for a specific product"""
    try:
        logger.info(f"Fetching related products for product {product_id}")
        
        # Get ALL products with real images and return random selection as related
        result = clan_api.get_products(limit=None, include_images=True)
        if result.get('success', True):
            products = result.get('data', [])
            
            # Return random products as related
            import random
            if len(products) > 6:
                products = random.sample(products, 6)
            
            transformed_products = [transform_product_for_ui(p) for p in products]
            logger.info(f"Found {len(transformed_products)} related products")
            return jsonify(transformed_products)
        
        logger.error("Failed to fetch related products")
        return jsonify([]), 500
        
    except Exception as e:
        logger.error(f"Exception fetching related products: {str(e)}")
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=False)
