# blueprints/clan_cache.py
from flask import Blueprint, jsonify, request
import logging
import os
import sys
import threading
import time
from datetime import datetime

bp = Blueprint('clan_cache', __name__)
logger = logging.getLogger(__name__)

# Incremental-basic refresh state
_INC_STATE = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'processed': 0,
    'inserted': 0,
    'skipped_known': 0,
    'error': None,
}

# Weekly discovery sync state
_SYNC_STATE = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'pages_scanned': 0,
    'candidates': 0,
    'inserted': 0,
    'updated': 0,
    'unchanged': 0,
    'errors': 0,
    'last_run_allowed': None,
}


@bp.route('/api/clan/cache/save-product', methods=['POST'])
def save_individual_product():
    """Save a single product to the cache database"""
    try:
        product_data = request.json
        if not product_data:
            return jsonify({'success': False, 'error': 'No product data provided'}), 400

        # Save via ClanCache (load from blog-launchpad package path)
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        cache.store_single_product(product_data)

        return jsonify({'success': True, 'message': 'Product saved successfully'})

    except Exception as e:
        logger.error(f"Error saving individual product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/clan/products')
def list_cached_products():
    """List cached products (for internal use)"""
    try:
        limit = request.args.get('limit', type=int)
        query = request.args.get('q', default='', type=str)

        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        products = cache.get_products(limit=limit, query=query)
        return jsonify(products)
    except Exception as e:
        logger.error(f"Error listing cached products: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/clan/cache/stats')
def get_clan_cache_stats():
    """Get cache statistics."""
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        stats = cache.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return jsonify({'error': f'Failed to get cache stats: {str(e)}'}), 500

@bp.route('/api/clan/cache/refresh', methods=['POST'])
def refresh_clan_cache():
    """Full incremental refresh: fetch category tree and all products.
    - Categories: fetch tree → flatten → upsert
    - Products: page basic list → per-SKU detailed fetch → transform → upsert one-by-one
    """
    try:
        # Load external API client and transformers from blog-clan-api
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        from transformers import flatten_category_tree, transform_product_for_ui  # type: ignore

        client = ClanAPIClient()

        # Fetch categories and upsert
        cat_result = client.get_category_tree()
        categories_saved = 0
        if cat_result.get('success', True):
            cats = cat_result.get('data', [])
            flat = flatten_category_tree(cats)
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
            from clan_cache import ClanCache  # type: ignore
            cache = ClanCache()
            cache.store_categories(flat)
            categories_saved = len(flat)

        # Fetch ALL basic products via paging
        products_saved = 0
        products_failed = 0
        basic_offset = 0
        page_size = 200

        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()

        while True:
            basic_result = client.make_api_request('/getProducts', {'limit': page_size, 'offset': basic_offset})
            if not basic_result.get('success', True):
                break
            batch = basic_result.get('data', [])
            if not batch:
                break

            for product in batch:
                try:
                    if isinstance(product, list) and len(product) > 1:
                        sku = product[1]
                        detailed = client.get_product_data(sku, all_images=True)
                        if detailed.get('success', True):
                            data = detailed.get('data')
                            if data:
                                transformed = transform_product_for_ui(data)
                                cache.store_single_product(transformed)
                                products_saved += 1
                            else:
                                products_failed += 1
                        else:
                            products_failed += 1
                    else:
                        products_failed += 1
                except Exception:
                    products_failed += 1

            basic_offset += page_size

        return jsonify({
            'success': True,
            'categories_upserted': categories_saved,
            'products_upserted': products_saved,
            'products_failed': products_failed
        })

    except Exception as e:
        logger.error(f"Error refreshing clan cache: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------
# Background refresh management
# -----------------------------
_REFRESH_STATE = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'categories_upserted': 0,
    'products_upserted': 0,
    'products_failed': 0,
    'error': None,
}


def _perform_full_refresh_in_background():
    """Background worker that performs the full incremental refresh and updates _REFRESH_STATE."""
    global _REFRESH_STATE
    _REFRESH_STATE.update({
        'running': True,
        'started_at': datetime.utcnow().isoformat(),
        'finished_at': None,
        'categories_upserted': 0,
        'products_upserted': 0,
        'products_failed': 0,
        'error': None,
    })
    try:
        # Load external API client and transformers from blog-clan-api
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        from transformers import flatten_category_tree, transform_product_for_ui  # type: ignore

        client = ClanAPIClient()

        # Categories
        cat_result = client.get_category_tree()
        if cat_result.get('success', True):
            cats = cat_result.get('data', [])
            flat = flatten_category_tree(cats)
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
            from clan_cache import ClanCache  # type: ignore
            cache = ClanCache()
            cache.store_categories(flat)
            _REFRESH_STATE['categories_upserted'] = len(flat)

        # Products: page through basics, then detailed per SKU
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()

        offset = 0
        page_size = 200
        while True:
            basic_result = client.make_api_request('/getProducts', {'limit': page_size, 'offset': offset})
            if not basic_result.get('success', True):
                break
            batch = basic_result.get('data', [])
            if not batch:
                break

            for product in batch:
                sku = None
                try:
                    if isinstance(product, list) and len(product) > 1:
                        sku = product[1]
                        # Always store basic product first to ensure we capture first_seen_at
                        basic_transformed = transform_product_for_ui(product)
                        basic_transformed['has_detailed_data'] = False
                        try:
                            cache.store_single_product(basic_transformed)
                            _REFRESH_STATE['products_upserted'] += 1
                        except Exception as store_e:
                            logger.error(f"Failed to store basic product {sku}: {str(store_e)}")
                            _REFRESH_STATE['products_failed'] += 1
                            continue
                        
                        # Try to enrich with detailed data, but don't fail if this doesn't work
                        try:
                            detailed = client.get_product_data(sku, all_images=False)
                            if detailed.get('success', True):
                                data = detailed.get('data')
                                if data:
                                    transformed = transform_product_for_ui(data)
                                    transformed['has_detailed_data'] = True
                                    cache.store_single_product(transformed)
                        except Exception as detail_e:
                            # Detailed fetch failed, but we already stored basic product
                            logger.debug(f"Detailed fetch failed for {sku}: {str(detail_e)}")
                    else:
                        _REFRESH_STATE['products_failed'] += 1
                except Exception as e:
                    logger.error(f"Error processing product {sku if sku else 'unknown'}: {str(e)}")
                    _REFRESH_STATE['products_failed'] += 1

            offset += page_size
            # Be polite to upstream
            time.sleep(0.2)

        _REFRESH_STATE['finished_at'] = datetime.utcnow().isoformat()
        _REFRESH_STATE['running'] = False
        logger.info(f"Refresh completed: {_REFRESH_STATE['products_upserted']} products, {_REFRESH_STATE['products_failed']} failed")

    except Exception as e:
        logger.error(f"Refresh job failed: {str(e)}", exc_info=True)
        _REFRESH_STATE['error'] = str(e)
        _REFRESH_STATE['finished_at'] = datetime.utcnow().isoformat()
        _REFRESH_STATE['running'] = False


@bp.route('/api/clan/cache/refresh/start', methods=['POST'])
def start_refresh_job():
    """Start full incremental refresh in the background."""
    if _REFRESH_STATE.get('running'):
        return jsonify({'success': False, 'message': 'Refresh already running', 'state': _REFRESH_STATE}), 409
    t = threading.Thread(target=_perform_full_refresh_in_background, daemon=True)
    t.start()
    return jsonify({'success': True, 'message': 'Refresh started', 'state': _REFRESH_STATE})


@bp.route('/api/clan/cache/refresh/status')
def refresh_status():
    """Get background refresh status and counters."""
    return jsonify({'success': True, 'state': _REFRESH_STATE})


@bp.route('/api/clan/cache/sync/status')
def weekly_sync_status():
    """Get weekly discovery sync status."""
    return jsonify({'success': True, 'state': _SYNC_STATE})

@bp.route('/api/clan/cache/sync/start', methods=['POST'])
def weekly_sync_start():
    """Start weekly discovery sync in background (idempotent)."
    """
    force = request.args.get('force', 'false').lower() == 'true'
    if _SYNC_STATE.get('running'):
        return jsonify({'success': False, 'message': 'Sync already running', 'state': _SYNC_STATE}), 409
    t = threading.Thread(target=_perform_weekly_sync, args=(force,), daemon=True)
    t.start()
    return jsonify({'success': True, 'message': 'Weekly sync started', 'state': _SYNC_STATE})

@bp.route('/api/clan/cache/enrich', methods=['POST'])
def enrich_single_sku():
    """Enrich and upsert a single SKU using getProductData."""
    try:
        data = request.get_json(force=True) or {}
        sku = data.get('sku')
        if not sku:
            return jsonify({'success': False, 'error': 'sku is required'}), 400

        # Load clients
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        from transformers import transform_product_for_ui  # type: ignore
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()

        client = ClanAPIClient()
        result = client.get_product_data(sku, all_images=False)
        if not result.get('success', True) or not result.get('data'):
            return jsonify({'success': False, 'error': 'No data returned for SKU'}), 404

        pdata = result['data']
        # Transform and map extended fields
        transformed = transform_product_for_ui(pdata)
        # Map optional extended fields directly
        transformed['short_description'] = pdata.get('short_description')
        transformed['supplier_name'] = pdata.get('supplier_name')
        transformed['supplier_description'] = pdata.get('supplier_description')
        transformed['configurable_options'] = pdata.get('configurable_options')
        transformed['clan_created_at'] = pdata.get('created_at')
        # Some APIs may include updated_at in future
        if 'updated_at' in pdata:
            transformed['clan_updated_at'] = pdata.get('updated_at')

        # Upsert
        cache.store_single_product(transformed)
        return jsonify({'success': True, 'sku': sku})

    except Exception as e:
        logger.error(f"Error enriching SKU: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/clan/products/<sku>/full')
def get_full_product(sku: str):
    """Return merged DB product plus live details from clan.com (no persistence)."""
    try:
        # Read DB record
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        conn = cache.get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, sku, price, image_url, url, short_description, description,
                   supplier_name, supplier_description, clan_created_at, clan_updated_at,
                   configurable_options, category_ids, first_seen_at, last_updated
            FROM clan_products
            WHERE sku = %s
        """, (sku,))
        row = cur.fetchone()
        cur.close(); conn.close()
        db_product = None
        if row:
            (pid, name, psku, price, image_url, url, short_desc, desc,
             supp_name, supp_desc, clan_created, clan_updated,
             options, category_ids, first_seen, last_upd) = row
            db_product = {
                'id': pid, 'name': name, 'sku': psku, 'price': str(price) if price is not None else None,
                'image_url': image_url, 'url': url, 'short_description': short_desc, 'description': desc,
                'supplier_name': supp_name, 'supplier_description': supp_desc,
                'clan_created_at': clan_created.isoformat() if clan_created else None,
                'clan_updated_at': clan_updated.isoformat() if clan_updated else None,
                'configurable_options': options, 'category_ids': category_ids,
                'first_seen_at': first_seen.isoformat() if first_seen else None,
                'last_updated': last_upd.isoformat() if last_upd else None,
            }

        # Live fetch - support all_images parameter for profile writing
        all_images = request.args.get('all_images', 'false').lower() == 'true'
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        client = ClanAPIClient()
        live = client.get_product_data(sku, all_images=all_images)
        live_data = live.get('data') if live.get('success', True) else None

        # Merge: prefer live fields when present
        merged = db_product or {}
        if live_data:
            merged.update({
                'sku': sku,
                'id': int(live_data.get('product_id')) if live_data.get('product_id') else merged.get('id'),
                'name': live_data.get('title') or merged.get('name'),
                'price': str(live_data.get('price')) if live_data.get('price') is not None else merged.get('price'),
                'image_url': live_data.get('image') or merged.get('image_url'),
                'url': live_data.get('product_url') or merged.get('url'),
                'short_description': live_data.get('short_description') or merged.get('short_description'),
                'description': live_data.get('description') or merged.get('description'),
                'supplier_name': live_data.get('supplier_name') or merged.get('supplier_name'),
                'supplier_description': live_data.get('supplier_description') or merged.get('supplier_description'),
                'configurable_options': live_data.get('configurable_options') or merged.get('configurable_options'),
            })
            
            # Include all images if requested (for profile writing)
            if all_images and live_data.get('images'):
                merged['all_images'] = live_data.get('images')

        return jsonify({'success': True, 'product': merged})

    except Exception as e:
        logger.error(f"Error fetching full product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/clan/products/<sku>/scrape-specifications', methods=['POST'])
def scrape_product_specifications(sku: str):
    """Scrape product specifications from product page and save to database."""
    try:
        # Get product from database to get URL
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        conn = cache.get_db_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, url FROM clan_products WHERE sku = %s
        """, (sku,))
        row = cur.fetchone()
        
        if not row:
            return jsonify({'success': False, 'error': f'Product with SKU {sku} not found'}), 404
        
        product_id, product_url = row[0], row[1]
        
        if not product_url:
            return jsonify({'success': False, 'error': 'Product URL not available'}), 400
        
        # Scrape specifications
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
        from product_specifications_scraper import ProductSpecificationsScraper  # type: ignore
        
        scraper = ProductSpecificationsScraper()
        specs = scraper.scrape_product_specifications(product_url)
        
        if not specs:
            return jsonify({'success': False, 'error': 'No specifications found on product page'}), 404
        
        # Save to database
        import json
        cur.execute("""
            UPDATE clan_products
            SET specifications = %s
            WHERE id = %s
            RETURNING specifications
        """, (json.dumps(specs), product_id))
        
        updated_specs = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'sku': sku,
            'specifications': updated_specs
        })
        
    except Exception as e:
        logger.error(f"Error scraping specifications for SKU {sku}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def _read_metadata_last_run(key: str):
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        conn = cache.get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT value, last_updated FROM clan_cache_metadata WHERE key = %s", (key,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row and row[1]:
            return row[1]
    except Exception as e:
        logger.error(f"Error reading metadata {key}: {e}")
    return None

def _write_metadata(key: str, value: str):
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        conn = cache.get_db_conn()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO clan_cache_metadata (key, value, last_updated)
            VALUES (%s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                last_updated = EXCLUDED.last_updated
        ''', (key, value, datetime.utcnow()))
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        logger.error(f"Error writing metadata {key}: {e}")

def _perform_weekly_sync(force: bool):
    global _SYNC_STATE
    _SYNC_STATE.update({
        'running': True,
        'started_at': datetime.utcnow().isoformat(),
        'finished_at': None,
        'pages_scanned': 0,
        'candidates': 0,
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
    })
    try:
        # Gate on last-run (7 days)
        last_run = _read_metadata_last_run('list_last_successful_sync_at')
        allow_run = True
        if last_run and not force:
            allow_run = (datetime.utcnow() - last_run).days >= 7
        _SYNC_STATE['last_run_allowed'] = allow_run
        if not allow_run:
            _SYNC_STATE['finished_at'] = datetime.utcnow().isoformat()
            _SYNC_STATE['running'] = False
            return

        # Load clients
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        from transformers import transform_product_for_ui  # type: ignore
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()

        # Build set of known SKUs (deduplication key; IDs have huge gaps for configurable products)
        db_conn = cache.get_db_conn()
        db_cur = db_conn.cursor()
        try:
            db_cur.execute("SELECT sku FROM clan_products")
            known_skus = {r[0] for r in db_cur.fetchall() if r and r[0]}
        finally:
            db_cur.close(); db_conn.close()

        client = ClanAPIClient()
        page_size = 200
        max_pages = 100
        pages_with_no_candidates = 0
        for page in range(max_pages):
            offset = page * page_size
            res = client.make_api_request('/getProducts', {'limit': page_size, 'offset': offset, 'sort': 'id_desc'})
            if not res.get('success', True):
                break
            batch = res.get('data', [])
            if not batch:
                break
            _SYNC_STATE['pages_scanned'] = page + 1

            # Identify candidates: check if SKU is new (not in known_skus)
            # Note: IDs have huge gaps (configurable variants can be 1800+ IDs per product)
            # So we use SKU-based deduplication, not ID-based
            candidates = []
            for p in batch:
                sku = None
                if isinstance(p, dict):
                    sku = p.get('sku')
                elif isinstance(p, list) and len(p) > 1:
                    sku = p[1]
                
                # If SKU is new (not in known set), it's a candidate
                if sku and sku not in known_skus:
                    candidates.append(p)
                    known_skus.add(sku)  # Track as seen to avoid duplicates in same run

            _SYNC_STATE['candidates'] += len(candidates)
            if len(candidates) == 0:
                pages_with_no_candidates += 1
            else:
                pages_with_no_candidates = 0

            # Enrich candidates with getProductData and hash-based change detection
            for c in candidates:
                try:
                    sku = c.get('sku') if isinstance(c, dict) else (c[1] if isinstance(c, list) and len(c) > 1 else None)
                    if not sku:
                        continue
                    
                    # Fetch detailed data
                    detail_result = client.get_product_data(sku, all_images=False)
                    if not detail_result.get('success', True) or not detail_result.get('data'):
                        # Fallback to basic transform if detail fetch fails
                        basic = transform_product_for_ui(c)
                        basic['has_detailed_data'] = False
                        cache.store_single_product(basic)
                        _SYNC_STATE['inserted'] += 1
                        continue
                    
                    pdata = detail_result['data']
                    # Build enriched product
                    enriched = transform_product_for_ui(pdata)
                    enriched['short_description'] = pdata.get('short_description')
                    enriched['supplier_name'] = pdata.get('supplier_name')
                    enriched['supplier_description'] = pdata.get('supplier_description')
                    enriched['configurable_options'] = pdata.get('configurable_options')
                    enriched['clan_created_at'] = pdata.get('created_at')
                    enriched['clan_updated_at'] = pdata.get('updated_at')
                    enriched['has_detailed_data'] = True
                    
                    # Check if product exists and compare hash
                    conn = cache.get_db_conn()
                    cur = conn.cursor()
                    cur.execute("SELECT product_content_hash FROM clan_products WHERE sku = %s", (sku,))
                    existing_row = cur.fetchone()
                    
                    # Build hash from enriched fields
                    content_fields = {
                        'name': enriched.get('name', ''),
                        'sku': sku,
                        'price': enriched.get('price', ''),
                        'image_url': enriched.get('image_url', ''),
                        'url': enriched.get('url', ''),
                        'short_description': enriched.get('short_description', ''),
                        'description': enriched.get('description', ''),
                        'supplier_name': enriched.get('supplier_name', ''),
                        'supplier_description': enriched.get('supplier_description', ''),
                        'configurable_options': enriched.get('configurable_options'),
                    }
                    new_hash = cache._build_product_hash(content_fields)
                    
                    if existing_row and existing_row[0]:
                        existing_hash = existing_row[0]
                        if new_hash == existing_hash:
                            _SYNC_STATE['unchanged'] += 1
                            cur.close(); conn.close()
                            continue
                        else:
                            _SYNC_STATE['updated'] += 1
                    else:
                        _SYNC_STATE['inserted'] += 1
                    
                    cur.close(); conn.close()
                    
                    # Upsert with new hash
                    enriched['product_content_hash'] = new_hash
                    cache.store_single_product(enriched)
                    
                    time.sleep(0.5)  # Rate limit detail fetches
                    
                except Exception as e:
                    _SYNC_STATE['errors'] += 1
                    logger.error(f"Error processing candidate: {e}")

            # Stop if several pages with no candidates or when IDs drop below known max for a while
            if pages_with_no_candidates >= 3:
                break

        # Update last successful sync
        _write_metadata('list_last_successful_sync_at', datetime.utcnow().isoformat())
        _SYNC_STATE['finished_at'] = datetime.utcnow().isoformat()
        _SYNC_STATE['running'] = False

    except Exception as e:
        logger.error(f"Weekly sync failed: {e}", exc_info=True)
        _SYNC_STATE['finished_at'] = datetime.utcnow().isoformat()
        _SYNC_STATE['running'] = False
        _SYNC_STATE['errors'] += 1

@bp.route('/api/clan/cache/refresh/incremental-basic/status')
def incremental_basic_status():
    """Get status of incremental basic refresh."""
    return jsonify({'success': True, 'state': _INC_STATE})


@bp.route('/api/clan/cache/refresh/incremental-basic/start', methods=['POST'])
def start_incremental_basic():
    """Start incremental basic refresh in background."""
    if _INC_STATE.get('running'):
        return jsonify({'success': False, 'message': 'Refresh already running', 'state': _INC_STATE}), 409
    t = threading.Thread(target=_perform_incremental_basic_refresh, daemon=True)
    t.start()
    return jsonify({'success': True, 'message': 'Incremental refresh started', 'state': _INC_STATE})


@bp.route('/api/clan/cache/fetch-new-by-id', methods=['POST'])
def fetch_new_products_by_id():
    """Fetch and enrich all products with IDs greater than our max ID."""
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        if _SYNC_STATE.get('running'):
            return jsonify({'success': False, 'message': 'Sync already running', 'state': _SYNC_STATE}), 409
        
        t = threading.Thread(target=_fetch_products_above_max_id, args=(force,), daemon=True)
        t.start()
        return jsonify({'success': True, 'message': 'Fetching products with IDs above max', 'state': _SYNC_STATE})
    except Exception as e:
        logger.error(f"Error starting fetch by ID: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _fetch_products_above_max_id(force: bool):
    """Fetch all products with IDs > max_id in DB."""
    global _SYNC_STATE
    _SYNC_STATE.update({
        'running': True,
        'started_at': datetime.utcnow().isoformat(),
        'finished_at': None,
        'pages_scanned': 0,
        'candidates': 0,
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
    })
    
    try:
        # Load clients
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        from transformers import transform_product_for_ui  # type: ignore
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()
        
        # Get max ID from DB
        db_conn = cache.get_db_conn()
        db_cur = db_conn.cursor()
        db_cur.execute("SELECT COALESCE(MAX(id), 0) FROM clan_products")
        max_id_row = db_cur.fetchone()
        max_id = int(max_id_row[0]) if max_id_row and max_id_row[0] is not None else 0
        db_cur.close(); db_conn.close()
        
        logger.info(f"Starting fetch for products with ID > {max_id}")
        
        client = ClanAPIClient()
        page_size = 200
        max_pages = 500  # Scan more pages since sort doesn't work
        consecutive_empty = 0
        
        for page in range(max_pages):
            offset = page * page_size
            res = client.make_api_request('/getProducts', {'limit': page_size, 'offset': offset, 'sort': 'id_desc'})
            if not res.get('success', True):
                break
            batch = res.get('data', [])
            if not batch:
                consecutive_empty += 1
                # Stop after 3 empty pages
                if consecutive_empty >= 3:
                    logger.info(f"Stopped after {consecutive_empty} empty pages")
                    break
                continue
            consecutive_empty = 0
            _SYNC_STATE['pages_scanned'] = page + 1
            
            # Find products with ID > max_id (scan all pages since sort may not work)
            candidates = []
            for p in batch:
                product_id = None
                sku = None
                if isinstance(p, dict):
                    sku = p.get('sku')
                    try:
                        pid_raw = p.get('product_id')
                        product_id = int(pid_raw) if pid_raw is not None else None
                    except Exception:
                        product_id = None
                elif isinstance(p, list) and len(p) > 5:
                    sku = p[1] if len(p) > 1 else None
                    try:
                        product_id = int(p[5]) if p[5] else None
                    except Exception:
                        product_id = None
                
                if product_id and product_id > max_id:
                    candidates.append(p)
                    _SYNC_STATE['candidates'] += 1
            
            # Log progress periodically
            if page % 10 == 0 and page > 0:
                logger.info(f"Scanned {page} pages, found {_SYNC_STATE['candidates']} candidates so far")
            
            # Enrich candidates
            for c in candidates:
                try:
                    sku = c.get('sku') if isinstance(c, dict) else (c[1] if isinstance(c, list) and len(c) > 1 else None)
                    if not sku:
                        continue
                    
                    detail_result = client.get_product_data(sku, all_images=False)
                    if not detail_result.get('success', True) or not detail_result.get('data'):
                        basic = transform_product_for_ui(c)
                        basic['has_detailed_data'] = False
                        cache.store_single_product(basic)
                        _SYNC_STATE['inserted'] += 1
                        continue
                    
                    pdata = detail_result['data']
                    enriched = transform_product_for_ui(pdata)
                    enriched['short_description'] = pdata.get('short_description')
                    enriched['supplier_name'] = pdata.get('supplier_name')
                    enriched['supplier_description'] = pdata.get('supplier_description')
                    enriched['configurable_options'] = pdata.get('configurable_options')
                    enriched['clan_created_at'] = pdata.get('created_at')
                    enriched['clan_updated_at'] = pdata.get('updated_at')
                    enriched['has_detailed_data'] = True
                    
                    # Check hash for change detection
                    conn = cache.get_db_conn()
                    cur = conn.cursor()
                    cur.execute("SELECT product_content_hash FROM clan_products WHERE sku = %s", (sku,))
                    existing_row = cur.fetchone()
                    
                    content_fields = {
                        'name': enriched.get('name', ''),
                        'sku': sku,
                        'price': str(enriched.get('price', '')),
                        'image_url': enriched.get('image_url', ''),
                        'url': enriched.get('url', ''),
                        'short_description': enriched.get('short_description', ''),
                        'description': enriched.get('description', ''),
                        'supplier_name': enriched.get('supplier_name', ''),
                        'supplier_description': enriched.get('supplier_description', ''),
                        'configurable_options': enriched.get('configurable_options'),
                    }
                    new_hash = cache._build_product_hash(content_fields)
                    
                    if existing_row and existing_row[0]:
                        existing_hash = existing_row[0]
                        if new_hash == existing_hash:
                            _SYNC_STATE['unchanged'] += 1
                            cur.close(); conn.close()
                            continue
                        else:
                            _SYNC_STATE['updated'] += 1
                    else:
                        _SYNC_STATE['inserted'] += 1
                    
                    cur.close(); conn.close()
                    
                    enriched['product_content_hash'] = new_hash
                    cache.store_single_product(enriched)
                    
                    time.sleep(0.5)  # Rate limit
                    
                except Exception as e:
                    _SYNC_STATE['errors'] += 1
                    logger.error(f"Error processing candidate: {e}")
        
        _SYNC_STATE['finished_at'] = datetime.utcnow().isoformat()
        _SYNC_STATE['running'] = False
        logger.info(f"Fetch by ID complete: {_SYNC_STATE['inserted']} inserted, {_SYNC_STATE['updated']} updated")
        
    except Exception as e:
        logger.error(f"Fetch by ID failed: {e}", exc_info=True)
        _SYNC_STATE['finished_at'] = datetime.utcnow().isoformat()
        _SYNC_STATE['running'] = False
        _SYNC_STATE['errors'] += 1


def _do_incremental_basic_refresh(limit=200, max_pages=100, known_streak_limit=2000):
    """Core logic for incremental basic refresh. Updates _INC_STATE."""
    global _INC_STATE
    try:
        # Load clan client and transformer
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))
        from clan_client import ClanAPIClient  # type: ignore
        from transformers import transform_product_for_ui  # type: ignore

        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad'))
        from clan_cache import ClanCache  # type: ignore
        cache = ClanCache()

        # Build set of known SKUs and get last update date
        import psycopg
        from datetime import datetime, timedelta
        conn = cache.get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT sku FROM clan_products")
        known = {r[0] for r in cur.fetchall() if r and r[0]}
        
        # Get last update date for filtering
        cur.execute("SELECT MAX(last_updated) FROM clan_products")
        last_update_row = cur.fetchone()
        if last_update_row and last_update_row[0]:
            last_update = last_update_row[0]
            # Use date 1 day before last update to catch anything we might have missed
            cutoff_date = last_update - timedelta(days=1)
        else:
            # Default to 2025-09-16 if no last_update found
            cutoff_date = datetime(2025, 9, 16)
        
        cur.close(); conn.close()
        logger.info(f"Loaded {len(known)} known SKUs from database")
        logger.info(f"Filtering for products created after {cutoff_date.isoformat()}")

        client = ClanAPIClient()

        _INC_STATE['processed'] = 0
        _INC_STATE['inserted'] = 0
        _INC_STATE['skipped_known'] = 0
        processed = 0
        inserted = 0
        skipped_known = 0
        known_streak = 0

        # Scan from beginning (date filtering will skip old products)
        for page in range(max_pages):
            offset = page * limit
            res = client.make_api_request('/getProducts', {'limit': limit, 'offset': offset})
            if not res.get('success', True):
                break
            batch = res.get('data', [])
            if not batch:
                break
            for p in batch:
                processed += 1
                # Handle both dict and list formats from API
                if isinstance(p, dict):
                    sku = p.get('sku')
                    created_str = p.get('created_at')
                elif isinstance(p, list) and len(p) > 1:
                    sku = p[1]
                    created_str = None  # List format may not have created_at
                else:
                    continue
                
                if not sku:
                    continue
                
                # If we have created_at, check if it's new enough
                if created_str:
                    try:
                        # Parse ISO format date (handle timezone offset)
                        # Format: '2016-07-01T10:50:06+01:00' or '2016-07-01T10:50:06Z'
                        date_part = created_str.split('T')[0]  # Get 'YYYY-MM-DD'
                        if '+' in created_str:
                            time_part = created_str.split('+')[0].split('T')[1]  # Get 'HH:MM:SS'
                        elif created_str.endswith('Z'):
                            time_part = created_str.split('T')[1].replace('Z', '')
                        else:
                            time_part = created_str.split('T')[1] if 'T' in created_str else '00:00:00'
                        product_date = datetime.fromisoformat(f"{date_part} {time_part}")
                        
                        # Skip products created before cutoff
                        if product_date < cutoff_date:
                            skipped_known += 1
                            continue
                    except Exception as date_err:
                        logger.debug(f"Could not parse date {created_str}: {date_err}")
                        # Continue processing if date parsing fails
                
                # Check if we already know this SKU
                if sku in known:
                    skipped_known += 1
                    known_streak += 1
                    if known_streak >= known_streak_limit:
                        _INC_STATE['processed'] = processed
                        _INC_STATE['inserted'] = inserted
                        _INC_STATE['skipped_known'] = skipped_known
                        _INC_STATE['finished_at'] = datetime.utcnow().isoformat()
                        _INC_STATE['running'] = False
                        return
                    continue
                known_streak = 0
                # Insert basic product record
                try:
                    basic = transform_product_for_ui(p)
                    basic['has_detailed_data'] = False
                    cache.store_single_product(basic)
                    inserted += 1
                    known.add(sku)
                    _INC_STATE['inserted'] = inserted
                    logger.info(f"Inserted new product: {sku}")
                except Exception as store_err:
                    logger.error(f"Failed to store product {sku}: {str(store_err)}")
                    continue
                
                # Update progress counters
                _INC_STATE['processed'] = processed
                _INC_STATE['skipped_known'] = skipped_known

        _INC_STATE['processed'] = processed
        _INC_STATE['inserted'] = inserted
        _INC_STATE['skipped_known'] = skipped_known
        _INC_STATE['finished_at'] = datetime.utcnow().isoformat()
        _INC_STATE['running'] = False
        logger.info(f"Incremental refresh complete: {inserted} inserted, {skipped_known} skipped")

    except Exception as e:
        logger.error(f"Incremental basic refresh failed: {str(e)}", exc_info=True)
        _INC_STATE['error'] = str(e)
        _INC_STATE['finished_at'] = datetime.utcnow().isoformat()
        _INC_STATE['running'] = False


def _perform_incremental_basic_refresh():
    """Background worker for incremental basic refresh."""
    global _INC_STATE
    _INC_STATE.update({
        'running': True,
        'started_at': datetime.utcnow().isoformat(),
        'finished_at': None,
        'processed': 0,
        'inserted': 0,
        'skipped_known': 0,
        'error': None,
    })
    _do_incremental_basic_refresh(limit=200, max_pages=100, known_streak_limit=2000)


@bp.route('/api/clan/cache/refresh/incremental-basic', methods=['POST'])
def incremental_basic_refresh():
    """Synchronous endpoint - starts background job and returns immediately."""
    if _INC_STATE.get('running'):
        return jsonify({'success': False, 'message': 'Refresh already running', 'state': _INC_STATE}), 409
    t = threading.Thread(target=_perform_incremental_basic_refresh, daemon=True)
    t.start()
    return jsonify({'success': True, 'message': 'Incremental refresh started', 'state': _INC_STATE})

