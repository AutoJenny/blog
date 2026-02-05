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

from blueprints.launchpad_utils import resolve_current_posting_queue_id

bp = Blueprint('launchpad_scheduling', __name__)
logger = logging.getLogger(__name__)

# Phase H-5.1: No current output -> 400 (no silent fallback)
_NO_CURRENT_OUTPUT = {
    'success': False,
    'error': 'NO_CURRENT_OUTPUT',
    'message': 'No current output selected for this item. Select an output in the workbench before publishing.',
}

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
            # Detect optional columns to keep compatibility if migrations not applied yet
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'daily_posts_schedule'
            """)
            cols_result = cursor.fetchall()
            cols = {row['column_name'] for row in cols_result}
            
            logger.debug(f"Found columns in daily_posts_schedule: {cols}")

            # Build SELECT with explicit columns
            # Always include platform and content_type - they exist in the schema
            select_cols = ['id', 'name', 'time', 'timezone', 'days', 'is_active', 'created_at', 'updated_at', 'platform', 'content_type']
            if 'page_id' in cols:
                select_cols.append('page_id')
            if 'page_name' in cols:
                select_cols.append('page_name')
            
            query = f"SELECT {', '.join(select_cols)} FROM daily_posts_schedule WHERE 1=1"
            params = []

            # Only show active schedules
            if 'is_active' in cols:
                query += " AND is_active = true"

            if platform and 'platform' in cols:
                query += " AND platform = %s"
                params.append(platform)

            if content_type and 'content_type' in cols:
                query += " AND content_type = %s"
                params.append(content_type)

            query += " ORDER BY time ASC"

            logger.info(f"Executing query: {query}")
            logger.info(f"With params: {params}")
            cursor.execute(query, params)
            schedules = cursor.fetchall()
            
            logger.info(f"Found {len(schedules)} schedules")
            if schedules:
                logger.info(f"First schedule keys: {list(schedules[0].keys())}")
                logger.info(f"First schedule platform: {schedules[0].get('platform')}")
                logger.info(f"First schedule content_type: {schedules[0].get('content_type')}")
            
            # Convert to list of dicts and ensure all fields are included
            schedules_list = []
            for sched in schedules:
                sched_dict = dict(sched)  # Ensure it's a dict
                # Explicitly check and add platform/content_type
                if 'platform' not in sched_dict or sched_dict.get('platform') is None:
                    # Try to get it from the raw row
                    platform_val = getattr(sched, 'platform', None) if hasattr(sched, 'platform') else None
                    if platform_val is None:
                        platform_val = sched.get('platform') if isinstance(sched, dict) else None
                    sched_dict['platform'] = platform_val
                if 'content_type' not in sched_dict or sched_dict.get('content_type') is None:
                    content_type_val = getattr(sched, 'content_type', None) if hasattr(sched, 'content_type') else None
                    if content_type_val is None:
                        content_type_val = sched.get('content_type') if isinstance(sched, dict) else None
                    sched_dict['content_type'] = content_type_val
                schedules_list.append(sched_dict)
            
            return jsonify({
                'success': True,
                'schedules': schedules_list
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
                # Check columns; if missing, apply migration inline (user approved)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'daily_posts_schedule'
                """)
                existing_cols = {row['column_name'] for row in cursor.fetchall()}

                required_adds = []
                if 'name' not in existing_cols:
                    required_adds.append("ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'Schedule'")
                if 'platform' not in existing_cols:
                    required_adds.append("ADD COLUMN IF NOT EXISTS platform VARCHAR(50)")
                if 'content_type' not in existing_cols:
                    required_adds.append("ADD COLUMN IF NOT EXISTS content_type VARCHAR(50)")
                if 'page_id' not in existing_cols:
                    required_adds.append("ADD COLUMN IF NOT EXISTS page_id VARCHAR(100)")
                if 'page_name' not in existing_cols:
                    required_adds.append("ADD COLUMN IF NOT EXISTS page_name VARCHAR(200)")

                if required_adds:
                    alter_sql = "ALTER TABLE daily_posts_schedule\n" + ",\n".join(required_adds) + ";"
                    cursor.execute(alter_sql)
                    # Backfill sensible defaults for platform/content_type
                    cursor.execute("""
                        UPDATE daily_posts_schedule
                        SET platform = COALESCE(platform, 'facebook'),
                            content_type = COALESCE(content_type, 'product')
                        WHERE platform IS NULL OR content_type IS NULL
                    """)

                # Now perform insert with full column set
                # Ensure JSONB-compatible value for days
                days_value = data['days']
                try:
                    import json as _json
                    if not isinstance(days_value, str):
                        days_value = _json.dumps(days_value)
                except Exception:
                    pass

                if 'name' in existing_cols or required_adds:
                    cursor.execute("""
                        INSERT INTO daily_posts_schedule (name, time, platform, content_type, days, timezone, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data.get('name') or 'Schedule',
                        data['time'],
                        data['platform'],
                        data['content_type'],
                        days_value,
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

@bp.route('/api/syndication/schedules/purge-legacy', methods=['POST'])
def purge_legacy_schedules():
    """Hard-delete legacy or inactive schedules to eliminate duplicates in UI."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Ensure optional columns exist checks
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'daily_posts_schedule'
                """)
                cols = {row['column_name'] for row in cursor.fetchall()}

                # Build deletion criteria for legacy rows
                delete_clauses = ["is_active = false"] if 'is_active' in cols else []
                if 'platform' in cols:
                    delete_clauses.append("platform IS NULL")
                if 'content_type' in cols:
                    delete_clauses.append("content_type IS NULL")

                if delete_clauses:
                    delete_sql = "DELETE FROM daily_posts_schedule WHERE " + " OR ".join(delete_clauses)
                    cursor.execute(delete_sql)
                    deleted_count = cursor.rowcount
                else:
                    deleted_count = 0

                conn.commit()

        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        logger.error(f"Error purging legacy schedules: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/syndication/schedules/backfill', methods=['POST'])
def backfill_schedules_platform_content_type():
    """Backfill platform/content_type (and optional page fields) for legacy rows."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Ensure columns exist (safe if already applied)
                cursor.execute("""
                    ALTER TABLE daily_posts_schedule
                    ADD COLUMN IF NOT EXISTS platform VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS content_type VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS page_id VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS page_name VARCHAR(200)
                """)

                # Backfill sensible defaults
                cursor.execute("""
                    UPDATE daily_posts_schedule
                    SET platform = COALESCE(platform, 'facebook'),
                        content_type = COALESCE(content_type, 'product')
                    WHERE platform IS NULL OR content_type IS NULL
                """)

                conn.commit()

        return jsonify({'success': True, 'message': 'Backfill complete'})
    except Exception as e:
        logger.error(f"Error in schedules backfill: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    """Post content immediately. Phase H-5.1: For blog_post, only the current workbench output is allowed."""
    try:
        data = request.get_json() or {}
        platform = data.get('platform', 'facebook')
        channel_type = data.get('channel_type') or data.get('content_type', 'blog_post')
        item_id = data.get('item_id')
        content_ref = data.get('content_ref')

        if content_ref is not None and (platform or channel_type):
            resolved_id = resolve_current_posting_queue_id(
                int(content_ref), platform, channel_type, 'primary'
            )
            if resolved_id is None:
                return jsonify(_NO_CURRENT_OUTPUT), 400
            item_id = resolved_id
        elif item_id:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, post_id, platform, channel_type, content_type
                    FROM posting_queue WHERE id = %s
                """, (item_id,))
                row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Queue item not found'}), 404
            ct = (row.get('content_type') or '').strip().lower()
            if ct == 'blog_post' and row.get('post_id') is not None:
                resolved_id = resolve_current_posting_queue_id(
                    row['post_id'],
                    row.get('platform') or platform,
                    row.get('channel_type') or channel_type,
                    'primary',
                )
                if resolved_id is None:
                    return jsonify(_NO_CURRENT_OUTPUT), 400
                if resolved_id != item_id:
                    return jsonify({
                        'success': False,
                        'error': 'NO_CURRENT_OUTPUT',
                        'message': 'Selected item is not the current output. Select this output in the workbench first.',
                    }), 400
        else:
            return jsonify({'success': False, 'error': 'Item ID or (content_ref, platform, channel_type) is required'}), 400

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE posting_queue
                    SET status = 'posted', updated_at = NOW()
                    WHERE id = %s
                """, (item_id,))
                conn.commit()
        return jsonify({'success': True, 'message': 'Content posted successfully'})
    except Exception as e:
        logger.error(f"Error posting now: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/syndication/schedule-tomorrow', methods=['POST'])
def schedule_tomorrow():
    """Schedule content for tomorrow. Phase H-5.1: For blog_post, only the current workbench output is allowed."""
    try:
        data = request.get_json() or {}
        platform = data.get('platform', 'facebook')
        channel_type = data.get('channel_type') or data.get('content_type', 'blog_post')
        item_id = data.get('item_id')
        content_ref = data.get('content_ref')

        if content_ref is not None and (platform or channel_type):
            resolved_id = resolve_current_posting_queue_id(
                int(content_ref), platform, channel_type, 'primary'
            )
            if resolved_id is None:
                return jsonify(_NO_CURRENT_OUTPUT), 400
            item_id = resolved_id
        elif item_id:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, post_id, platform, channel_type, content_type
                    FROM posting_queue WHERE id = %s
                """, (item_id,))
                row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Queue item not found'}), 404
            ct = (row.get('content_type') or '').strip().lower()
            if ct == 'blog_post' and row.get('post_id') is not None:
                resolved_id = resolve_current_posting_queue_id(
                    row['post_id'],
                    row.get('platform') or platform,
                    row.get('channel_type') or channel_type,
                    'primary',
                )
                if resolved_id is None:
                    return jsonify(_NO_CURRENT_OUTPUT), 400
                if resolved_id != item_id:
                    return jsonify({
                        'success': False,
                        'error': 'NO_CURRENT_OUTPUT',
                        'message': 'Selected item is not the current output. Select this output in the workbench first.',
                    }), 400
        else:
            return jsonify({'success': False, 'error': 'Item ID or (content_ref, platform, channel_type) is required'}), 400

        tomorrow = date.today() + timedelta(days=1)
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE posting_queue
                    SET scheduled_date = %s, scheduled_time = '09:00:00',
                        scheduled_timestamp = %s, status = 'ready', updated_at = NOW()
                    WHERE id = %s
                """, (tomorrow, datetime.combine(tomorrow, time(9, 0)), item_id))
                conn.commit()
        return jsonify({'success': True, 'message': 'Content scheduled for tomorrow'})
    except Exception as e:
        logger.error(f"Error scheduling tomorrow: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
