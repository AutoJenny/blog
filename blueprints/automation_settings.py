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
    """Start automation for a post"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({'success': False, 'error': 'Post ID is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Check if post exists
            cursor.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            # Update post status to in_progress
            cursor.execute("""
                UPDATE post 
                SET status = 'in_progress', updated_at = NOW()
                WHERE id = %s
            """, (post_id,))
            
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
