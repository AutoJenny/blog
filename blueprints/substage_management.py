"""
Substage Management Blueprint
Provides UI and API endpoints for managing substage configurations.
"""

from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
from utils.substage_config import (
    get_substages_for_post_type,
    get_substages_with_metadata,
    get_substage_metadata,
    invalidate_cache,
    get_all_post_types,
    get_all_stages
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('substage_management', __name__, url_prefix='/settings')


@bp.route('/substage-management', methods=['GET'])
def substage_management_page():
    """Render the substage management UI with optional context from query parameters"""
    post_id = request.args.get('post_id', type=int)
    post_type = request.args.get('post_type')
    output_channel = request.args.get('output', 'blog')  # Default to 'blog'
    
    # If post_id provided but post_type not, look it up
    if post_id and not post_type:
        try:
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
        except Exception as e:
            logger.warning(f"Could not determine post_type for post_id {post_id}: {e}")
            post_type = None
    
    return render_template('settings/substage_management.html',
                         post_id=post_id,
                         post_type=post_type,
                         output_channel=output_channel)


@bp.route('/api/substage-management/overview', methods=['GET'])
def get_overview():
    """Get comprehensive overview of all substage configurations"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all substages with their metadata
            cursor.execute("""
                SELECT substage_key, label, route_function, display_order, stage, is_active
                FROM substage_metadata
                ORDER BY stage, display_order
            """)
            substages_data = cursor.fetchall()
            
            # Get post_type configurations
            cursor.execute("""
                SELECT post_type, stage, substage_key, display_order, is_active
                FROM post_type_substages
                ORDER BY post_type, stage, display_order
            """)
            post_type_configs = cursor.fetchall()
            
            # Get output_channel configurations
            cursor.execute("""
                SELECT post_type, output_channel, stage, substage_key, display_order, use_post_type_config, is_active
                FROM output_channel_substages
                ORDER BY post_type, output_channel, stage, display_order
            """)
            channel_configs = cursor.fetchall()
            
            # Build response structure
            result = {
                'substages': [],
                'post_types': {},
                'output_channels': {}
            }
            
            # Process substages
            for sub in substages_data:
                substage_key = sub['substage_key']
                
                # Find post_type usage
                post_type_usage = {}
                for pt_config in post_type_configs:
                    if pt_config['substage_key'] == substage_key:
                        pt = pt_config['post_type']
                        stage = pt_config['stage']
                        if pt not in post_type_usage:
                            post_type_usage[pt] = {}
                        post_type_usage[pt][stage] = {
                            'active': pt_config['is_active'],
                            'order': pt_config['display_order']
                        }
                
                # Find output_channel usage
                channel_usage = {}
                for ch_config in channel_configs:
                    if ch_config['substage_key'] == substage_key:
                        key = f"{ch_config['post_type']}_{ch_config['output_channel']}"
                        stage = ch_config['stage']
                        if key not in channel_usage:
                            channel_usage[key] = {}
                        channel_usage[key][stage] = {
                            'active': ch_config['is_active'],
                            'order': ch_config['display_order'],
                            'inherited': ch_config['use_post_type_config']
                        }
                
                result['substages'].append({
                    'key': substage_key,
                    'label': sub['label'],
                    'stage': sub['stage'],
                    'route_function': sub['route_function'],
                    'order': sub['display_order'],
                    'is_active': sub['is_active'],
                    'post_types': post_type_usage,
                    'output_channels': channel_usage
                })
            
            return jsonify({
                'success': True,
                'data': result
            })
            
    except Exception as e:
        logger.error(f"Error getting substage overview: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/post-types/<post_type>', methods=['GET'])
def get_post_type_config(post_type):
    """Get configuration for a specific post type"""
    try:
        substages = get_substages_with_metadata(post_type)
        return jsonify({
            'success': True,
            'post_type': post_type,
            'substages': substages
        })
    except Exception as e:
        logger.error(f"Error getting post type config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/output-channels/<post_type>/<output_channel>', methods=['GET'])
def get_output_channel_config(post_type, output_channel):
    """Get configuration for a specific (post_type, output_channel) combination"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT stage, substage_key, display_order, use_post_type_config, is_active
                FROM output_channel_substages
                WHERE post_type = %s AND output_channel = %s
                ORDER BY stage, display_order
            """, (post_type, output_channel))
            
            configs = cursor.fetchall()
            
            # Also check if we should use post_type config
            cursor.execute("""
                SELECT use_post_type_config
                FROM output_channel_substages
                WHERE post_type = %s AND output_channel = %s
                LIMIT 1
            """, (post_type, output_channel))
            use_post_type = cursor.fetchone()
            use_post_type_config = use_post_type['use_post_type_config'] if use_post_type else False
            
            result = {}
            for config in configs:
                stage = config['stage']
                if stage not in result:
                    result[stage] = []
                result[stage].append({
                    'key': config['substage_key'],
                    'order': config['display_order'],
                    'active': config['is_active']
                })
            
            return jsonify({
                'success': True,
                'post_type': post_type,
                'output_channel': output_channel,
                'use_post_type_config': use_post_type_config,
                'substages': result
            })
    except Exception as e:
        logger.error(f"Error getting output channel config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/substage/toggle', methods=['POST'])
def toggle_substage():
    """Toggle substage active status for a post type or output channel"""
    try:
        data = request.get_json()
        substage_key = data.get('substage_key')
        post_type = data.get('post_type')
        stage = data.get('stage')
        output_channel = data.get('output_channel')  # null for post_type config
        is_active = data.get('is_active', True)
        
        if not all([substage_key, post_type, stage]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        with db_manager.get_cursor() as cursor:
            if output_channel:
                # Update output_channel_substages
                cursor.execute("""
                    UPDATE output_channel_substages
                    SET is_active = %s, updated_at = NOW()
                    WHERE post_type = %s AND output_channel = %s AND stage = %s AND substage_key = %s
                """, (is_active, post_type, output_channel, stage, substage_key))
            else:
                # Update post_type_substages
                cursor.execute("""
                    UPDATE post_type_substages
                    SET is_active = %s, updated_at = NOW()
                    WHERE post_type = %s AND stage = %s AND substage_key = %s
                """, (is_active, post_type, stage, substage_key))
            
            # Invalidate cache
            invalidate_cache()
            
            return jsonify({
                'success': True,
                'message': 'Substage toggled successfully'
            })
    except Exception as e:
        logger.error(f"Error toggling substage: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/substage/reorder', methods=['POST'])
def reorder_substages():
    """Reorder substages within a stage"""
    try:
        data = request.get_json()
        post_type = data.get('post_type')
        stage = data.get('stage')
        output_channel = data.get('output_channel')  # null for post_type config
        substage_keys = data.get('substage_keys', [])
        
        if not all([post_type, stage, substage_keys]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        with db_manager.get_cursor() as cursor:
            if output_channel:
                # Update output_channel_substages
                for order, substage_key in enumerate(substage_keys, start=1):
                    cursor.execute("""
                        UPDATE output_channel_substages
                        SET display_order = %s, updated_at = NOW()
                        WHERE post_type = %s AND output_channel = %s AND stage = %s AND substage_key = %s
                    """, (order, post_type, output_channel, stage, substage_key))
            else:
                # Update post_type_substages
                for order, substage_key in enumerate(substage_keys, start=1):
                    cursor.execute("""
                        UPDATE post_type_substages
                        SET display_order = %s, updated_at = NOW()
                        WHERE post_type = %s AND stage = %s AND substage_key = %s
                    """, (order, post_type, stage, substage_key))
            
            # Invalidate cache
            invalidate_cache()
            
            return jsonify({
                'success': True,
                'message': 'Substages reordered successfully'
            })
    except Exception as e:
        logger.error(f"Error reordering substages: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/substage-metadata/<substage_key>', methods=['PUT'])
def update_substage_metadata(substage_key):
    """Update substage metadata"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE substage_metadata
                SET label = %s, route_function = %s, display_order = %s, stage = %s,
                    description = %s, updated_at = NOW()
                WHERE substage_key = %s
            """, (
                data.get('label'),
                data.get('route_function'),
                data.get('display_order', 999),
                data.get('stage'),
                data.get('description'),
                substage_key
            ))
            
            # Invalidate cache
            invalidate_cache()
            
            return jsonify({
                'success': True,
                'message': 'Substage metadata updated successfully'
            })
    except Exception as e:
        logger.error(f"Error updating substage metadata: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/substage-metadata', methods=['POST'])
def create_substage():
    """Create new substage"""
    try:
        data = request.get_json()
        
        required_fields = ['substage_key', 'label', 'stage']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO substage_metadata 
                (substage_key, label, route_function, display_order, stage, description, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (substage_key) DO UPDATE SET
                    label = EXCLUDED.label,
                    route_function = EXCLUDED.route_function,
                    display_order = EXCLUDED.display_order,
                    stage = EXCLUDED.stage,
                    description = EXCLUDED.description,
                    updated_at = NOW()
            """, (
                data['substage_key'],
                data['label'],
                data.get('route_function'),
                data.get('display_order', 999),
                data['stage'],
                data.get('description'),
                data.get('is_active', True)
            ))
            
            # Invalidate cache
            invalidate_cache()
            
            return jsonify({
                'success': True,
                'message': 'Substage created successfully'
            })
    except Exception as e:
        logger.error(f"Error creating substage: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/substage-management/bulk-copy', methods=['POST'])
def bulk_copy():
    """Copy configuration from one post type to another"""
    try:
        data = request.get_json()
        source_post_type = data.get('source_post_type')
        target_post_type = data.get('target_post_type')
        stages = data.get('stages')  # Optional: specific stages, or null for all
        
        if not all([source_post_type, target_post_type]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get source configurations
            query = """
                SELECT stage, substage_key, display_order, is_active
                FROM post_type_substages
                WHERE post_type = %s
            """
            params = [source_post_type]
            
            if stages:
                query += " AND stage = ANY(%s)"
                params.append(stages)
            
            cursor.execute(query, params)
            source_configs = cursor.fetchall()
            
            # Insert into target
            inserted = 0
            for config in source_configs:
                cursor.execute("""
                    INSERT INTO post_type_substages 
                    (post_type, stage, substage_key, display_order, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (post_type, stage, substage_key) DO UPDATE SET
                        display_order = EXCLUDED.display_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                """, (
                    target_post_type,
                    config['stage'],
                    config['substage_key'],
                    config['display_order'],
                    config['is_active']
                ))
                inserted += 1
            
            # Invalidate cache
            invalidate_cache()
            
            return jsonify({
                'success': True,
                'message': f'Copied {inserted} substage configurations',
                'count': inserted
            })
    except Exception as e:
        logger.error(f"Error bulk copying: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

