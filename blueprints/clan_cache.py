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

