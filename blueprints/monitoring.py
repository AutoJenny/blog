"""
Monitoring Blueprint
Provides status and control for automation monitoring system
"""

from flask import Blueprint, render_template, jsonify, request
import os
import logging
import subprocess
from datetime import datetime, timedelta
from config.database import db_manager

bp = Blueprint('monitoring', __name__)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PID_FILE = os.path.join(SCRIPT_DIR, 'logs', 'background_posting.pid')
MONITOR_SCRIPT = os.path.join(SCRIPT_DIR, 'scripts', 'background_posting_monitor.sh')

@bp.route('/monitoring/status')
def monitoring_status():
    """Get current monitoring status"""
    try:
        is_running = False
        pid = None
        
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is actually running
                result = subprocess.run(['ps', '-p', str(pid)], 
                                      capture_output=True, text=True)
                is_running = result.returncode == 0
            except (ValueError, FileNotFoundError):
                pass
        
        return jsonify({
            'success': True,
            'is_running': is_running,
            'pid': pid
        })
    except Exception as e:
        logger.error(f"Error checking monitoring status: {e}")
        return jsonify({
            'success': False,
            'is_running': False,
            'error': str(e)
        }), 500

@bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start the monitoring script"""
    try:
        # Check if already running
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                result = subprocess.run(['ps', '-p', str(pid)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return jsonify({
                        'success': False,
                        'error': 'Monitoring is already running',
                        'pid': pid
                    }), 400
            except (ValueError, FileNotFoundError):
                pass
        
        # Start the monitor
        log_file = os.path.join(SCRIPT_DIR, 'logs', 'background_posting.log')
        with open(log_file, 'a') as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Started via web interface\n")
        
        # Start in background
        subprocess.Popen(
            ['/bin/bash', MONITOR_SCRIPT],
            cwd=SCRIPT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait a moment and check if it started
        import time
        time.sleep(1)
        
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            return jsonify({
                'success': True,
                'message': 'Monitoring started successfully',
                'pid': pid
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start monitoring (PID file not created)'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop the monitoring script"""
    try:
        if not os.path.exists(PID_FILE):
            return jsonify({
                'success': False,
                'error': 'Monitoring is not running'
            }), 400
        
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # Kill the process
        try:
            subprocess.run(['kill', str(pid)], check=True)
            os.remove(PID_FILE)
            
            return jsonify({
                'success': True,
                'message': 'Monitoring stopped successfully'
            })
        except subprocess.CalledProcessError:
            # Process might already be dead
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            return jsonify({
                'success': False,
                'error': 'Process not found (may have already stopped)'
            }), 400
            
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/monitoring/report')
def monitoring_report():
    """Show monitoring report page with all automation events"""
    return render_template('monitoring/report.html')

@bp.route('/monitoring/api/events')
def monitoring_events():
    """Get automation events from logs"""
    try:
        # Get filter parameter
        event_type = request.args.get('type', 'all')  # 'all', 'posting', 'admin'
        
        events = []
        
        # Define log files with their categories
        log_files = [
            # Automated posting processes (actual social media posts)
            ('automated_weekly_content_creator', 'logs/automated_weekly_content_creator.log', 'posting'),
            ('automated_weekly_content_workflow', 'logs/automated_weekly_content_workflow.log', 'posting'),
            ('posting_executor', 'logs/posting_executor.log', 'posting'),
            ('scheduled_posting_executor', 'logs/scheduled_posting_executor.log', 'posting'),
            ('automated_posting', 'logs/automated_posting.log', 'posting'),
            # Administrative processes (infrastructure, monitoring, maintenance)
            ('background_posting_monitor', 'logs/background_posting.log', 'admin'),
        ]
        
        for script_name, log_path, category in log_files:
            # Apply filter
            if event_type != 'all' and category != event_type:
                continue
                
            full_path = os.path.join(SCRIPT_DIR, log_path)
            if os.path.exists(full_path):
                try:
                    # Read last 1000 lines
                    with open(full_path, 'r') as f:
                        lines = f.readlines()
                        # Get last 200 lines for each script
                        for line in lines[-200:]:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Special handling for background_posting.log (admin category)
                            # It contains both monitor messages and script outputs
                            # Only show monitor's own messages (format: "YYYY-MM-DD HH:MM:SS - message")
                            # Skip Python logging format (has comma and log level like "INFO", "DEBUG")
                            if category == 'admin' and script_name == 'background_posting_monitor':
                                # Only parse lines that match monitor's own format (no comma in timestamp, no log level)
                                if ' - ' in line:
                                    # Check if it's monitor format (no comma in timestamp part)
                                    first_part = line.split(' - ')[0]
                                    if ',' not in first_part and len(first_part.split()) == 2:
                                        parts = line.split(' - ', 1)
                                        if len(parts) == 2:
                                            timestamp_str = parts[0].strip()
                                            message = parts[1].strip()
                                            
                                            # Skip if it looks like Python logging output (has log level keywords at start)
                                            # Monitor messages are simple like "Starting background posting monitor"
                                            # Script outputs start with "INFO -", "DEBUG -", etc.
                                            if message.startswith(('INFO', 'DEBUG', 'ERROR', 'WARNING')):
                                                continue
                                            
                                            try:
                                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                                
                                                # Determine result icon
                                                result_icon = 'success'
                                                if 'error' in message.lower() or 'failed' in message.lower() or 'stopped' in message.lower():
                                                    result_icon = 'error'
                                                elif 'warning' in message.lower():
                                                    result_icon = 'warning'
                                                
                                                events.append({
                                                    'timestamp': timestamp.isoformat(),
                                                    'script': script_name,
                                                    'level': 'INFO',
                                                    'message': message,
                                                    'result': result_icon,
                                                    'category': category
                                                })
                                            except ValueError:
                                                continue
                                continue
                            
                            # Standard parsing for posting scripts (Python logging format)
                            # Format: 2026-01-17 20:01:19,484 - INFO - ...
                            # For posting category, only show ACTUAL publication events, not internal processing
                            if ' - ' in line:
                                parts = line.split(' - ', 2)
                                if len(parts) >= 3:
                                    timestamp_str = parts[0]
                                    level = parts[1]
                                    message = parts[2]
                                    
                                    # For posting category, filter to only actual publication events
                                    if category == 'posting':
                                        # Only include messages that indicate actual posting/publication
                                        # Exclude all internal processing, debug, and status messages
                                        is_publication_event = False
                                        
                                        # Actual publication success messages
                                        # Exclude intermediate "Facebook API response" messages (too granular, shows per-page)
                                        # Only show final completion messages with context
                                        if any(phrase in message for phrase in [
                                            'Successfully posted to',
                                            'Posted to',
                                            'Published to Facebook',
                                            'Posting execution complete:',
                                            'Published successfully'
                                        ]):
                                            is_publication_event = True
                                        
                                        # New enhanced completion message format
                                        if 'Published to Facebook' in message and 'queue_id' in message:
                                            is_publication_event = True
                                        
                                        # Explicitly exclude intermediate API response messages and old generic completion
                                        if 'Facebook API response - Status:' in message:
                                            is_publication_event = False
                                        
                                        # Exclude old generic "publish_to_facebook completed" (replaced with detailed message)
                                        if message.strip() == '✅ publish_to_facebook completed' or message.endswith('publish_to_facebook completed'):
                                            is_publication_event = False
                                        
                                        # Actual publication attempts (when a post is being executed to a platform)
                                        # Format: "Executing post X to platform"
                                        if 'Executing post' in message and ' to ' in message:
                                            is_publication_event = True
                                        
                                        # Show completion stats only if there were actual publications
                                        if 'Posting execution complete:' in message:
                                            # Only show if it mentions successful publications or failures
                                            if 'successfully_published' in message or 'failed' in message.lower():
                                                is_publication_event = True
                                        
                                        # Publication failures
                                        if any(phrase in message.lower() for phrase in [
                                            'failed to post',
                                            'posting failed',
                                            'facebook api error',
                                            'error posting to',
                                            'publish_to_facebook failed',
                                            'failed on'
                                        ]):
                                            is_publication_event = True
                                        
                                        # Skip all other messages (debug, info about processing, etc.)
                                        if not is_publication_event:
                                            continue
                                    
                                    # Parse timestamp
                                    try:
                                        # Handle both formats: "2026-01-17 20:01:19,484" and "2026-01-17 20:01:19"
                                        if ',' in timestamp_str:
                                            timestamp_str = timestamp_str.split(',')[0]
                                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        
                                        # Determine result icon
                                        result_icon = 'success'
                                        if 'ERROR' in level or 'error' in message.lower() or 'failed' in message.lower():
                                            result_icon = 'error'
                                        elif 'WARNING' in level or 'warning' in message.lower():
                                            result_icon = 'warning'
                                        elif '✅' in message or 'success' in message.lower() or 'completed' in message.lower() or '200' in message:
                                            result_icon = 'success'
                                        
                                        events.append({
                                            'timestamp': timestamp.isoformat(),
                                            'script': script_name,
                                            'level': level,
                                            'message': message,
                                            'result': result_icon,
                                            'category': category
                                        })
                                    except ValueError:
                                        continue
                except Exception as e:
                    logger.warning(f"Error reading log file {log_path}: {e}")
                    continue
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to most recent 500 events
        events = events[:500]
        
        return jsonify({
            'success': True,
            'events': events,
            'total': len(events),
            'filter': event_type
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring events: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'events': []
        }), 500
