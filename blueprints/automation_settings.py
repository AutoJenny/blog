"""
Automation Settings API Endpoints
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('automation_settings', __name__)

@bp.route('/start-automation', methods=['POST'])
def start_automation():
    """
    Start automation for a post (Mark Ready semantics). W2-FIX-7 Part C.
    Requires: automation.enabled, workflow_stage >= essentials_complete, preflight ok.
    Override: ?override=1 or { "override": true } bypasses checks.
    """
    try:
        data = request.get_json() or {}
        post_id = data.get('post_id')

        if not post_id:
            return jsonify({'success': False, 'error': 'Post ID is required'}), 400

        override = (
            request.args.get('override') == '1' or
            data.get('override') is True
        )

        if not override:
            from utils.posts.automation_helpers import is_automation_enabled
            if not is_automation_enabled(post_id):
                return jsonify({
                    'success': False,
                    'error': 'Automation is disabled for this post.',
                    'automation_blocked': True,
                }), 403

            from utils.posts.early_stage import get_canonical_stage
            from utils.posts.stage_order import stage_index

            current = get_canonical_stage(post_id)
            min_stage = "imaging"
            if stage_index(current) < stage_index(min_stage):
                return jsonify({
                    'success': False,
                    'error': f'Stage {min_stage.upper()} required to run this operation.',
                    'required_stage': min_stage,
                    'current_stage': current,
                    'stage_blocked': True,
                }), 403

            # W2-FIX-8: Output readiness check before preflight
            from utils.posts.output_readiness import get_output_readiness
            readiness = get_output_readiness(post_id, output_channel='blog')
            if not readiness.get('ok'):
                return jsonify({
                    'success': False,
                    'error': 'Output not ready for automation. Complete required substage first.',
                    'output_blocked': True,
                    'current_substage': readiness.get('current_substage', ''),
                    'required_substage': readiness.get('required_substage', ''),
                    'errors': readiness.get('errors', []),
                }), 409

            from utils.publishing.validators import validate_post_for_clan_publish
            preflight = validate_post_for_clan_publish(post_id)
            if not preflight.get('ok'):
                return jsonify({
                    'success': False,
                    'error': 'Preflight validation failed.',
                    'errors': preflight.get('errors', []),
                    'warnings': preflight.get('warnings', []),
                    'required_fields_snapshot': preflight.get('required_fields_snapshot', {}),
                }), 400

        from utils.posts.status_transitions import transition_post_status
        ok, err = transition_post_status(post_id, 'in_process', actor='automation')
        if not ok:
            return jsonify({'success': False, 'error': err or 'Failed to start'}), (
                404 if err and 'not found' in (err or '').lower() else 400
            )
        return jsonify({
            'success': True,
            'message': 'Automation started successfully'
        })
    except Exception as e:
        logger.error(f"Error starting automation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/toggle-mode', methods=['POST'])
def toggle_mode():
    """Toggle automation mode for a substage"""
    try:
        data = request.get_json()
        stage = data.get('stage')
        substage = data.get('substage')
        
        if not stage or not substage:
            return jsonify({'success': False, 'error': 'Stage and substage are required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current mode
            cursor.execute("""
                SELECT automation_mode FROM substage_automation_settings
                WHERE stage = %s AND substage = %s
            """, (stage, substage))
            
            current_setting = cursor.fetchone()
            
            if current_setting:
                current_mode = current_setting['automation_mode']
                # Cycle through modes: manual -> automatic -> hold -> manual
                if current_mode == 'manual':
                    new_mode = 'automatic'
                elif current_mode == 'automatic':
                    new_mode = 'hold'
                else:
                    new_mode = 'manual'
            else:
                # Default to automatic if no setting exists
                new_mode = 'automatic'
            
            # Update or insert the setting
            cursor.execute("""
                INSERT INTO substage_automation_settings (stage, substage, automation_mode)
                VALUES (%s, %s, %s)
                ON CONFLICT (stage, substage) 
                DO UPDATE SET 
                    automation_mode = EXCLUDED.automation_mode,
                    updated_at = NOW()
            """, (stage, substage, new_mode))
            
            return jsonify({
                'success': True,
                'mode': new_mode,
                'message': f'Mode changed to {new_mode}'
            })
            
    except Exception as e:
        logger.error(f"Error toggling mode: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/substage-settings', methods=['GET'])
def get_substage_settings():
    """Get all substage automation settings"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT stage, substage, automation_mode, updated_at
                FROM substage_automation_settings
                ORDER BY stage, substage
            """)
            
            settings = cursor.fetchall()
            
            # Convert to dictionary format for easier frontend use
            settings_dict = {}
            for setting in settings:
                stage = setting['stage']
                if stage not in settings_dict:
                    settings_dict[stage] = {}
                settings_dict[stage][setting['substage']] = {
                    'mode': setting['automation_mode'],
                    'updated_at': setting['updated_at'].isoformat() if setting['updated_at'] else None
                }
            
            return jsonify({
                "success": True,
                "settings": settings_dict
            })
            
    except Exception as e:
        logger.error(f"Error getting substage settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/substage-settings/<stage>/<substage>', methods=['PUT'])
def update_substage_setting(stage, substage):
    """Update automation setting for a specific substage"""
    try:
        data = request.get_json()
        automation_mode = data.get('automation_mode')
        
        if automation_mode not in ['manual', 'automatic', 'hold']:
            return jsonify({"success": False, "error": "Invalid automation mode"}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO substage_automation_settings (stage, substage, automation_mode)
                VALUES (%s, %s, %s)
                ON CONFLICT (stage, substage) 
                DO UPDATE SET 
                    automation_mode = EXCLUDED.automation_mode,
                    updated_at = NOW()
            """, (stage, substage, automation_mode))
            
            return jsonify({
                "success": True,
                "message": f"Setting updated for {stage}/{substage}",
                "automation_mode": automation_mode
            })
            
    except Exception as e:
        logger.error(f"Error updating substage setting: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
