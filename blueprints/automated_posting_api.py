"""
Automated Posting API
--------------------

API endpoints for controlling automated posting:
- Get automation status (on/off)
- Toggle automation on/off
- Trigger manual publishing when automation is off
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import logging
import subprocess
import os

logger = logging.getLogger(__name__)

bp = Blueprint("automated_posting_api", __name__, url_prefix="/api")


def get_automated_posting_enabled() -> bool:
    """
    Get the current state of automated posting from system_config.
    
    Returns
    -------
    bool: True if automated posting is enabled, False otherwise.
          Defaults to True if config not found.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT config_value
                FROM system_config
                WHERE config_key = 'automated_posting_enabled'
            """)
            result = cursor.fetchone()
            
            if result:
                value = result.get('config_value', 'true').lower()
                return value == 'true' or value == '1'
            
            # Default to enabled if not found
            return True
    except Exception as e:
        logger.error(f"Error reading automated posting config: {e}")
        # Default to enabled on error (safer - allows posting)
        return True


def set_automated_posting_enabled(enabled: bool) -> bool:
    """
    Set the automated posting state in system_config.
    
    Parameters
    ----------
    enabled:
        True to enable, False to disable.
    
    Returns
    -------
    bool: True if update succeeded, False otherwise.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO system_config (config_key, config_value, description)
                VALUES ('automated_posting_enabled', %s, 'Master switch for automated posting to all channels')
                ON CONFLICT (config_key) 
                DO UPDATE SET 
                    config_value = %s,
                    updated_at = NOW()
            """, (str(enabled).lower(), str(enabled).lower()))
            
            return True
    except Exception as e:
        logger.error(f"Error updating automated posting config: {e}")
        return False


@bp.route('/automated-posting/status', methods=['GET'])
def get_automated_posting_status():
    """
    Get the current automated posting status.
    
    Returns
    -------
    JSON: {
        "success": bool,
        "enabled": bool
    }
    """
    try:
        enabled = get_automated_posting_enabled()
        return jsonify({
            "success": True,
            "enabled": enabled
        })
    except Exception as e:
        logger.error(f"Error getting automated posting status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/automated-posting/toggle', methods=['POST'])
def toggle_automated_posting():
    """
    Toggle automated posting on/off.
    
    Request Body
    ------------
    JSON: {
        "enabled": bool
    }
    
    Returns
    -------
    JSON: {
        "success": bool,
        "enabled": bool,
        "message": str
    }
    """
    try:
        data = request.get_json()
        if data is None:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        enabled = data.get('enabled')
        if enabled is None:
            return jsonify({
                "success": False,
                "error": "Missing 'enabled' field"
            }), 400
        
        # Convert to boolean
        enabled = bool(enabled)
        
        # Update config
        success = set_automated_posting_enabled(enabled)
        
        if success:
            logger.info(f"Automated posting {'enabled' if enabled else 'disabled'}")
            return jsonify({
                "success": True,
                "enabled": enabled,
                "message": f"Automated posting {'enabled' if enabled else 'disabled'}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update configuration"
            }), 500
            
    except Exception as e:
        logger.error(f"Error toggling automated posting: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/automated-posting/trigger', methods=['POST'])
def trigger_manual_publishing():
    """
    Manually trigger the scheduled posting executor.
    This bypasses the automation switch and runs publishing immediately.
    
    Returns
    -------
    JSON: {
        "success": bool,
        "message": str,
        "stats": dict (if successful)
    }
    """
    try:
        # Get script path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(script_dir, 'scripts', 'scheduled_posting_executor.py')
        
        if not os.path.exists(script_path):
            return jsonify({
                "success": False,
                "error": f"Scheduled posting executor script not found: {script_path}"
            }), 500
        
        # Run the script
        logger.info("Manual publishing triggered via API")
        
        # Set PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = script_dir
        
        result = subprocess.run(
            ['/opt/homebrew/bin/python3', script_path, '--bypass-switch'],
            cwd=script_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Manual publishing completed successfully")
            return jsonify({
                "success": True,
                "message": "Manual publishing triggered successfully",
                "output": result.stdout
            })
        else:
            logger.error(f"Manual publishing failed: {result.stderr}")
            return jsonify({
                "success": False,
                "error": f"Publishing failed: {result.stderr}",
                "output": result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Manual publishing timed out")
        return jsonify({
            "success": False,
            "error": "Publishing timed out after 5 minutes"
        }), 500
    except Exception as e:
        logger.error(f"Error triggering manual publishing: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
