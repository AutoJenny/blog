# blueprints/launchpad_scheduling.py
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import logging
import json
import os
import requests
from datetime import datetime, date, time, timedelta
import pytz
from humanize import naturaltime
from config.database import db_manager
import psycopg

bp = Blueprint('launchpad_scheduling', __name__)
logger = logging.getLogger(__name__)

def get_next_posting_slot(cursor, platform='facebook', content_type='product'):
    """Calculate the next available posting slot based on schedules and existing queue."""
    try:
        # Get active schedules for the specific platform and content type
        cursor.execute("""
            SELECT id, time, timezone, days, is_active
            FROM daily_posts_schedule
            WHERE is_active = true AND platform = %s AND content_type = %s
            ORDER BY time ASC
        """, (platform, content_type))
        schedules = cursor.fetchall()
        
        if not schedules:
            return None
        
        # Get the latest scheduled post to know where to start
        cursor.execute("""
            SELECT scheduled_timestamp, scheduled_date, scheduled_time
            FROM posting_queue
            WHERE scheduled_timestamp IS NOT NULL
            ORDER BY scheduled_timestamp DESC
            LIMIT 1
        """)
        latest_scheduled = cursor.fetchone()
        
        # Start from current time or latest scheduled time + 1 day
        if latest_scheduled and latest_scheduled['scheduled_timestamp']:
            start_date = latest_scheduled['scheduled_date'] + timedelta(days=1)
        else:
            start_date = date.today()
        
        # First, try to fill existing scheduled days
        cursor.execute("""
            SELECT scheduled_date, scheduled_time, COUNT(*) as count
            FROM posting_queue
            WHERE scheduled_timestamp IS NOT NULL
            GROUP BY scheduled_date, scheduled_time
            ORDER BY scheduled_date ASC, scheduled_time ASC
        """)
        existing_slots = cursor.fetchall()
        
        # Create a set of existing slots for quick lookup
        existing_slot_set = set()
        for slot in existing_slots:
            existing_slot_set.add((slot['scheduled_date'], slot['scheduled_time']))
        
        # Try to find the next available slot
        max_posts_per_slot = 1  # Only allow 1 post per time slot
        
        # Check each schedule for available slots
        for schedule in schedules:
            schedule_time = schedule['time']
            schedule_days = schedule['days']
            
            # Check the next 30 days for available slots
            for day_offset in range(30):
                check_date = start_date + timedelta(days=day_offset)
                
                # Check if this day is in the schedule
                if schedule_days and check_date.strftime('%A').lower() not in [d.lower() for d in schedule_days]:
                    continue
                
                # Check if this slot is available
                if (check_date, schedule_time) not in existing_slot_set:
                    # Found an available slot
                    return {
                        'scheduled_date': check_date,
                        'scheduled_time': schedule_time,
                        'scheduled_timestamp': datetime.combine(check_date, schedule_time),
                        'schedule_name': f"Schedule {schedule['id']}",
                        'timezone': schedule['timezone'] or 'UTC'
                    }
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculating next posting slot: {e}")
        return None

@bp.route('/api/syndication/schedules')
def get_schedules():
    """Get posting schedules."""
    try:
        platform = request.args.get('platform')
        content_type = request.args.get('content_type')
        
        with db_manager.get_cursor() as cursor:
            query = "SELECT * FROM daily_posts_schedule WHERE 1=1"
            params = []
            
            if platform:
                query += " AND platform = %s"
                params.append(platform)
            
            if content_type:
                query += " AND content_type = %s"
                params.append(content_type)
            
            query += " ORDER BY time ASC"
            
            cursor.execute(query, params)
            schedules = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'schedules': schedules
            })
    except Exception as e:
        logger.error(f"Error getting schedules: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/schedules', methods=['POST'])
def add_schedule():
    """Add a new posting schedule."""
    try:
        data = request.get_json()
        
        required_fields = ['time', 'platform', 'content_type', 'days']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO daily_posts_schedule (time, platform, content_type, days, timezone, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    data['time'],
                    data['platform'],
                    data['content_type'],
                    data['days'],
                    data.get('timezone', 'UTC'),
                    data.get('is_active', True)
                ))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule added successfully'
                })
    except Exception as e:
        logger.error(f"Error adding schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a posting schedule."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM daily_posts_schedule WHERE id = %s", (schedule_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule deleted successfully'
                })
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/schedules/test')
def test_schedules():
    """Test schedule functionality."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all active schedules
            cursor.execute("""
                SELECT id, time, platform, content_type, days, timezone
                FROM daily_posts_schedule
                WHERE is_active = true
                ORDER BY platform, content_type, time
            """)
            schedules = cursor.fetchall()
            
            # Get current queue status
            cursor.execute("""
                SELECT COUNT(*) as total_items,
                       COUNT(CASE WHEN scheduled_timestamp IS NOT NULL THEN 1 END) as scheduled_items,
                       COUNT(CASE WHEN scheduled_timestamp IS NULL THEN 1 END) as unscheduled_items
                FROM posting_queue
            """)
            queue_status = cursor.fetchone()
            
            # Get next available slots for each platform/content_type combination
            next_slots = {}
            cursor.execute("""
                SELECT DISTINCT platform, content_type
                FROM daily_posts_schedule
                WHERE is_active = true
            """)
            platform_content_types = cursor.fetchall()
            
            for pct in platform_content_types:
                next_slot = get_next_posting_slot(cursor, pct['platform'], pct['content_type'])
                if next_slot:
                    next_slots[f"{pct['platform']}_{pct['content_type']}"] = next_slot
            
            return jsonify({
                'success': True,
                'schedules': schedules,
                'queue_status': queue_status,
                'next_slots': next_slots
            })
    except Exception as e:
        logger.error(f"Error testing schedules: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/schedules/clear', methods=['POST'])
def clear_schedules():
    """Clear all schedules."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM daily_posts_schedule")
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'All schedules cleared successfully'
                })
    except Exception as e:
        logger.error(f"Error clearing schedules: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/today-status')
def get_today_status():
    """Get today's posting status."""
    try:
        today = date.today()
        
        with db_manager.get_cursor() as cursor:
            # Get today's scheduled posts
            cursor.execute("""
                SELECT COUNT(*) as scheduled_today
                FROM posting_queue
                WHERE scheduled_date = %s AND scheduled_timestamp IS NOT NULL
            """, (today,))
            today_scheduled = cursor.fetchone()
            
            # Get today's completed posts
            cursor.execute("""
                SELECT COUNT(*) as completed_today
                FROM posting_queue
                WHERE scheduled_date = %s AND status = 'posted'
            """, (today,))
            today_completed = cursor.fetchone()
            
            # Get pending posts for today
            cursor.execute("""
                SELECT COUNT(*) as pending_today
                FROM posting_queue
                WHERE scheduled_date = %s AND status IN ('ready', 'pending')
            """, (today,))
            today_pending = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'today': {
                    'date': today.isoformat(),
                    'scheduled': today_scheduled['scheduled_today'],
                    'completed': today_completed['completed_today'],
                    'pending': today_pending['pending_today']
                }
            })
    except Exception as e:
        logger.error(f"Error getting today status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/post-now', methods=['POST'])
def post_now():
    """Post content immediately."""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({
                'success': False,
                'error': 'Item ID is required'
            }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update the item status to posted
                cursor.execute("""
                    UPDATE posting_queue
                    SET status = 'posted', updated_at = NOW()
                    WHERE id = %s
                """, (item_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Content posted successfully'
                })
    except Exception as e:
        logger.error(f"Error posting now: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/schedule-tomorrow', methods=['POST'])
def schedule_tomorrow():
    """Schedule content for tomorrow."""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({
                'success': False,
                'error': 'Item ID is required'
            }), 400
        
        tomorrow = date.today() + timedelta(days=1)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update the item to schedule for tomorrow
                cursor.execute("""
                    UPDATE posting_queue
                    SET scheduled_date = %s, scheduled_time = '09:00:00',
                        scheduled_timestamp = %s, status = 'ready', updated_at = NOW()
                    WHERE id = %s
                """, (tomorrow, datetime.combine(tomorrow, time(9, 0)), item_id))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Content scheduled for tomorrow'
                })
    except Exception as e:
        logger.error(f"Error scheduling tomorrow: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
