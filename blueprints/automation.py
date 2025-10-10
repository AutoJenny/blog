"""
One-Click Blog Automation API Endpoints
Mock implementation for UI development
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('automation', __name__, url_prefix='/launchpad/one-click-blog/api')

@bp.route('/next-up', methods=['GET'])
def get_next_up():
    """Get next scheduled week and selected idea"""
    try:
        from config.database import db_manager
        
        # Get current week
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT week_number, start_date, end_date, month_name, year
                FROM calendar_weeks 
                WHERE is_current_week = TRUE
                ORDER BY year DESC, week_number DESC
                LIMIT 1
            """)
            current_week = cursor.fetchone()
            
            if not current_week:
                return jsonify({
                    "success": False,
                    "error": "No current week found"
                }), 404
            
            # Get ideas for current week
            cursor.execute("""
                SELECT ci.id, ci.idea_title, ci.idea_description, ci.priority,
                       ci.seasonal_context, ci.content_type, ci.tags,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'::json
                       ) as categories
                FROM calendar_ideas ci
                LEFT JOIN calendar_idea_categories cic ON ci.id = cic.idea_id
                LEFT JOIN calendar_categories cc ON cic.category_id = cc.id
                WHERE ci.week_number = %s
                GROUP BY ci.id, ci.idea_title, ci.idea_description, ci.priority,
                         ci.seasonal_context, ci.content_type, ci.tags
                ORDER BY 
                    CASE ci.priority 
                        WHEN 'mandatory' THEN 1 
                        WHEN 'random' THEN 2 
                        ELSE 3 
                    END,
                    ci.id
            """, (current_week['week_number'],))
            
            ideas = cursor.fetchall()
            
            if not ideas:
                return jsonify({
                    "success": False,
                    "error": f"No ideas found for week {current_week['week_number']}"
                }), 404
            
            # Determine selected idea: use idea_id from schedule if exists, otherwise first idea
            selected_idea = None
            alternative_ideas = []
            
            # Get schedule data for current week
            cursor.execute("""
                SELECT scheduled_date, scheduled_time, publish_time, status, post_id, idea_id
                FROM calendar_schedule 
                WHERE year = %s AND week_number = %s
                ORDER BY scheduled_date ASC
                LIMIT 1
            """, (current_week['year'], current_week['week_number']))
            
            schedule_data = cursor.fetchone()
            
            # Determine selected idea based on schedule or default to first idea
            if schedule_data and schedule_data['idea_id']:
                # Find the selected idea by ID
                for idea in ideas:
                    if idea['id'] == schedule_data['idea_id']:
                        selected_idea = idea
                        break
                # All other ideas are alternatives
                alternative_ideas = [idea for idea in ideas if idea['id'] != schedule_data['idea_id']]
            else:
                # No idea selected yet - use first idea as default
                selected_idea = ideas[0]
                alternative_ideas = ideas[1:] if len(ideas) > 1 else []
            
            # If no schedule exists, create one dynamically for this week
            if not schedule_data:
                from datetime import datetime, date, timedelta
                
                # Calculate appropriate publish date within the current week
                week_start = current_week['start_date']
                week_end = current_week['end_date']
                today = date.today()
                
                # Default to Wednesday of the week (middle of week) at 14:00
                # If today is past Wednesday, schedule for next available day
                if week_start and week_end:
                    # Calculate Wednesday of this week
                    days_since_monday = (week_start.weekday()) % 7  # Monday = 0
                    wednesday = week_start + timedelta(days=(2 - days_since_monday))
                    
                    # If today is past Wednesday, schedule for Friday
                    if today > wednesday:
                        friday = wednesday + timedelta(days=2)
                        publish_date = min(friday, week_end)
                    else:
                        publish_date = wednesday
                    
                    # Check if there's already a post for the selected idea
                    existing_post_id = None
                    cursor.execute("""
                        SELECT p.id FROM post p
                        JOIN post_development pd ON p.id = pd.post_id
                        WHERE pd.idea_seed ILIKE %s AND p.status != 'deleted'
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """, (f'%{selected_idea["idea_title"]}%',))
                    
                    existing_post = cursor.fetchone()
                    if existing_post:
                        existing_post_id = existing_post['id']
                        logger.info(f"Found existing post {existing_post_id} for idea '{selected_idea['idea_title']}'")
                    
                    # Insert the schedule with the selected idea
                    cursor.execute("""
                        INSERT INTO calendar_schedule 
                        (year, week_number, scheduled_date, scheduled_time, publish_time, status, requires_approval, automation_enabled, idea_id, post_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING scheduled_date, scheduled_time, publish_time, status, post_id, idea_id
                    """, (
                        current_week['year'], 
                        current_week['week_number'],
                        publish_date,
                        '14:00:00',
                        '14:00:00', 
                        'planned',
                        True,
                        True,
                        selected_idea['id'],
                        existing_post_id
                    ))
                    
                    schedule_data = cursor.fetchone()
            
            # Determine production status based on post existence and schedule
            production_status = "not_started"
            scheduled_date = "Not scheduled"
            scheduled_relative = ""
            
            if schedule_data:
                if schedule_data['post_id']:
                    # Post exists - check if it's published
                    cursor.execute("SELECT status FROM post WHERE id = %s", (schedule_data['post_id'],))
                    post_data = cursor.fetchone()
                    if post_data and post_data['status'] == 'published':
                        production_status = "completed"
                    else:
                        production_status = "in_progress"
                else:
                    production_status = "not_started"
                
                # Format schedule date
                if schedule_data['scheduled_date']:
                    from datetime import datetime, date
                    scheduled_date_obj = schedule_data['scheduled_date']
                    scheduled_date = scheduled_date_obj.strftime('%b %d, %Y')
                    
                    # Calculate relative time
                    today = date.today()
                    days_diff = (scheduled_date_obj - today).days
                    
                    if days_diff == 0:
                        scheduled_relative = "Today"
                    elif days_diff == 1:
                        scheduled_relative = "Tomorrow"
                    elif days_diff > 1:
                        scheduled_relative = f"In {days_diff} days"
                    elif days_diff == -1:
                        scheduled_relative = "Yesterday"
                    else:
                        scheduled_relative = f"{abs(days_diff)} days ago"
            
            data = {
                        "success": True,
                        "data": {
                            "current_week": {
                                "week_number": current_week['week_number'],
                                "year": current_week['year'],
                                "start_date": current_week['start_date'].strftime('%Y-%m-%d') if current_week['start_date'] else None,
                                "end_date": current_week['end_date'].strftime('%Y-%m-%d') if current_week['end_date'] else None,
                                "month_name": current_week['month_name']
                            },
                            "selected_idea": {
                                "id": selected_idea['id'],
                                "title": selected_idea['idea_title'],
                                "description": selected_idea['idea_description'],
                                "categories": [cat['name'] for cat in selected_idea['categories']] if selected_idea['categories'] else [],
                                "priority": selected_idea['priority'],
                                "seasonal_context": selected_idea['seasonal_context'],
                                "content_type": selected_idea['content_type'],
                                "tags": selected_idea['tags'] if selected_idea['tags'] else []
                            },
                            "alternative_ideas": [
                                {
                                    "id": idea['id'],
                                    "title": idea['idea_title'],
                                    "description": idea['idea_description'],
                                    "categories": [cat['name'] for cat in idea['categories']] if idea['categories'] else [],
                                    "priority": idea['priority'],
                                    "seasonal_context": idea['seasonal_context'],
                                    "content_type": idea['content_type'],
                                    "tags": idea['tags'] if idea['tags'] else []
                                }
                                for idea in alternative_ideas
                            ],
                            "production_status": production_status,
                            "scheduled_date": scheduled_date,
                            "scheduled_relative": scheduled_relative,
                            "post_id": schedule_data['post_id'] if schedule_data and schedule_data['post_id'] else None,
                            "can_start_automation": True,
                            "next_available_slot": "2025-10-15T09:00:00Z"  # Keep mock for now
                        }
                    }
            
            return jsonify(data)
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/select-idea', methods=['POST'])
def select_idea():
    """Select an idea for the current week"""
    try:
        data = request.get_json()
        idea_id = data.get('idea_id')
        
        if not idea_id:
            return jsonify({'success': False, 'error': 'Idea ID is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current week
            cursor.execute("""
                SELECT year, week_number FROM calendar_weeks 
                WHERE is_current_week = TRUE
            """)
            current_week = cursor.fetchone()
            
            if not current_week:
                return jsonify({'success': False, 'error': 'No current week found'}), 404
            
            # Verify the idea exists and belongs to this week, and get idea details
            cursor.execute("""
                SELECT id, idea_title, idea_description FROM calendar_ideas 
                WHERE id = %s AND week_number = %s
            """, (idea_id, current_week['week_number']))
            
            idea_data = cursor.fetchone()
            if not idea_data:
                return jsonify({'success': False, 'error': 'Idea not found for this week'}), 404
            
            # Check if there's already a post for this idea
            existing_post_id = None
            cursor.execute("""
                SELECT p.id FROM post p
                JOIN post_development pd ON p.id = pd.post_id
                WHERE pd.idea_seed ILIKE %s AND p.status != 'deleted'
                ORDER BY p.created_at DESC
                LIMIT 1
            """, (f'%{idea_data["idea_title"]}%',))
            
            existing_post = cursor.fetchone()
            if existing_post:
                existing_post_id = existing_post['id']
                logger.info(f"Found existing post {existing_post_id} for idea '{idea_data['idea_title']}'")
            
            # Update or create schedule with selected idea
            cursor.execute("""
                SELECT id FROM calendar_schedule 
                WHERE year = %s AND week_number = %s
            """, (current_week['year'], current_week['week_number']))
            
            existing_schedule = cursor.fetchone()
            
            if existing_schedule:
                # Update existing schedule
                cursor.execute("""
                    UPDATE calendar_schedule 
                    SET idea_id = %s, post_id = %s, updated_at = NOW()
                    WHERE year = %s AND week_number = %s
                """, (idea_id, existing_post_id, current_week['year'], current_week['week_number']))
            else:
                # Create new schedule with selected idea
                from datetime import datetime, date, timedelta
                
                # Calculate appropriate publish date within the current week
                cursor.execute("""
                    SELECT start_date, end_date FROM calendar_weeks 
                    WHERE year = %s AND week_number = %s
                """, (current_week['year'], current_week['week_number']))
                
                week_data = cursor.fetchone()
                if week_data and week_data['start_date'] and week_data['end_date']:
                    week_start = week_data['start_date']
                    week_end = week_data['end_date']
                    today = date.today()
                    
                    # Default to Wednesday of the week
                    days_since_monday = (week_start.weekday()) % 7
                    wednesday = week_start + timedelta(days=(2 - days_since_monday))
                    
                    # If today is past Wednesday, schedule for Friday
                    if today > wednesday:
                        friday = wednesday + timedelta(days=2)
                        publish_date = min(friday, week_end)
                    else:
                        publish_date = wednesday
                    
                    cursor.execute("""
                        INSERT INTO calendar_schedule 
                        (year, week_number, scheduled_date, scheduled_time, publish_time, status, requires_approval, automation_enabled, idea_id, post_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        current_week['year'], 
                        current_week['week_number'],
                        publish_date,
                        '14:00:00',
                        '14:00:00', 
                        'planned',
                        True,
                        True,
                        idea_id,
                        existing_post_id
                    ))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Idea selected successfully'
            })
            
    except Exception as e:
        logger.error(f"Error selecting idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/update-schedule', methods=['POST'])
def update_schedule():
    """Update the schedule for the current week's post"""
    try:
        from config.database import db_manager
        import json
        
        data = request.get_json()
        
        # Accept both field names for compatibility
        scheduled_date = data.get('scheduled_date') or data.get('publish_date')
        scheduled_time = data.get('scheduled_time') or data.get('publish_time', '14:00:00')
        requires_approval = data.get('requires_approval', True)
        auto_publish = data.get('auto_publish', False)
        
        if not scheduled_date:
            return jsonify({"success": False, "error": "Scheduled date is required"}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current week
            cursor.execute("""
                SELECT week_number, year
                FROM calendar_weeks 
                WHERE is_current_week = TRUE
                ORDER BY year DESC, week_number DESC
                LIMIT 1
            """)
            current_week = cursor.fetchone()
            
            if not current_week:
                return jsonify({"success": False, "error": "No current week found"}), 404
            
            # Check if schedule already exists for this week
            cursor.execute("""
                SELECT id FROM calendar_schedule 
                WHERE year = %s AND week_number = %s
            """, (current_week['year'], current_week['week_number']))
            
            existing_schedule = cursor.fetchone()
            
            if existing_schedule:
                # Update existing schedule
                cursor.execute("""
                    UPDATE calendar_schedule 
                    SET scheduled_date = %s,
                        scheduled_time = %s,
                        publish_time = %s,
                        requires_approval = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    scheduled_date,
                    scheduled_time,
                    scheduled_time,
                    requires_approval,
                    existing_schedule['id']
                ))
                schedule_id = existing_schedule['id']
            else:
                # Insert new schedule
                cursor.execute("""
                    INSERT INTO calendar_schedule 
                    (year, week_number, scheduled_date, scheduled_time, publish_time, status, requires_approval, automation_enabled)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    current_week['year'],
                    current_week['week_number'],
                    scheduled_date,
                    scheduled_time,
                    scheduled_time,
                    'planned',
                    requires_approval,
                    True
                ))
                schedule_id = cursor.fetchone()['id']
            
            return jsonify({
                "success": True,
                "message": "Schedule updated successfully",
                "schedule_id": schedule_id
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/pipeline-status/<int:post_id>', methods=['GET'])
def get_pipeline_status(post_id):
    """Get current pipeline state for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post basic info with timestamps
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.updated_at,
                       pd.sections, pd.topic_allocation, pd.section_structure,
                       pd.idea_scope, pd.structure_design_at, pd.allocation_completed_at,
                       pd.refinement_completed_at, pd.updated_at as sections_updated_at
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
            # Get section completion status
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted
                FROM post_section
                WHERE post_id = %s
            """, (post_id,))
            
            section_stats = cursor.fetchone()
            
            # Calculate stage statuses
            planning_complete = bool(post['topic_allocation'] and post['section_structure'])
            authoring_progress = 0
            if section_stats and section_stats['total'] > 0:
                authoring_progress = int((section_stats['drafted'] / section_stats['total']) * 100)
            
            # Determine overall progress
            overall_progress = 0
            if planning_complete:
                overall_progress += 40
            overall_progress += int(authoring_progress * 0.6)
            
            # Extract topic brainstorming timestamp from idea_scope
            topic_brainstorming_at = None
            if post['idea_scope']:
                try:
                    idea_scope_data = json.loads(post['idea_scope']) if isinstance(post['idea_scope'], str) else post['idea_scope']
                    topic_brainstorming_at = idea_scope_data.get('generated_at')
                except:
                    pass
            
            # Build response with actual timestamps
            data = {
                "success": True,
                "post_id": post_id,
                "overall_progress": overall_progress,
                "stages": {
                    "planning": {
                        "status": "complete" if planning_complete else "in_progress",
                        "progress": 100 if planning_complete else 50,
                        "substages": [
                            {
                                "name": "Topic Brainstorming", 
                                "status": "complete" if post['idea_scope'] else "pending",
                                "completed_at": topic_brainstorming_at
                            },
                            {
                                "name": "Section Structure", 
                                "status": "complete" if post['section_structure'] else "pending",
                                "completed_at": post['structure_design_at'].isoformat() if post['structure_design_at'] else None
                            },
                            {
                                "name": "Topic Allocation", 
                                "status": "complete" if post['topic_allocation'] else "pending",
                                "completed_at": post['allocation_completed_at'].isoformat() if post['allocation_completed_at'] else None
                            },
                            {
                                "name": "Section Titling", 
                                "status": "complete" if post['sections'] else "pending",
                                "completed_at": post['sections_updated_at'].isoformat() if post['sections'] and post['sections_updated_at'] else None
                            },
                            {
                                "name": "Content Outline", 
                                "status": "complete" if planning_complete else "pending",
                                "completed_at": None  # No specific timestamp field for outline
                            }
                        ]
                    },
                    "authoring": {
                        "status": "in_progress" if authoring_progress > 0 and authoring_progress < 100 else ("complete" if authoring_progress == 100 else "pending"),
                        "progress": authoring_progress,
                        "substages": [
                            {"name": "Author First Drafts", "status": "in_progress" if authoring_progress > 0 else "pending", "progress": authoring_progress},
                            {"name": "Fix Language", "status": "pending"},
                            {"name": "Image Concepts", "status": "pending"},
                            {"name": "Image Prompts", "status": "pending"}
                        ]
                    },
                    "imaging": {
                        "status": "pending",
                        "progress": 0,
                        "substages": [
                            {"name": "Image Generation", "status": "pending"},
                            {"name": "Optimize Images", "status": "pending"}
                        ]
                    }
                }
            }
            
            return jsonify(data)
            
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/posts-in-development', methods=['GET'])
def get_posts_in_development():
    """Get list of posts currently in development"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.updated_at,
                       pd.topic_allocation, pd.section_structure
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status IN ('draft', 'in_process')
                ORDER BY p.updated_at DESC
                LIMIT 50
            """)
            
            posts = cursor.fetchall()
            
            posts_list = []
            for post in posts:
                # Determine current stage based on what's completed
                stage = "planning"
                progress = 0
                
                if post['topic_allocation'] and post['section_structure']:
                    stage = "authoring"
                    progress = 40
                    
                    # Check authoring progress
                    cursor.execute("""
                        SELECT COUNT(*) as total,
                               SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted
                        FROM post_section
                        WHERE post_id = %s
                    """, (post['id'],))
                    
                    section_stats = cursor.fetchone()
                    if section_stats and section_stats['total'] > 0:
                        authoring_progress = int((section_stats['drafted'] / section_stats['total']) * 100)
                        progress += int(authoring_progress * 0.6)
                
                posts_list.append({
                    "id": post['id'],
                    "title": post['title'],
                    "stage": stage,
                    "progress": progress,
                    "updated_at": post['updated_at'].isoformat() if post['updated_at'] else None
                })
            
            return jsonify({
                "success": True,
                "posts": posts_list
            })
            
    except Exception as e:
        logger.error(f"Error getting posts in development: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/blog-queue', methods=['GET'])
def get_blog_queue():
    """Get list of all posts with status (filterable)"""
    filter_type = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'week')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    mock_posts = [
        {
            "post_id": 77,
            "title": "Welsh Myths and Legends",
            "week_number": 41,
            "week_dates": "Oct 7-13, 2025",
            "status": "in_progress",
            "current_stage": "authoring",
            "current_substage": "author-first-drafts",
            "progress": 67,
            "last_updated": "2025-10-10T15:30:00Z",
            "automation_mode": "manual",
            "can_resume": True,
            "can_pause": True
        },
        {
            "post_id": 78,
            "title": "Halloween Traditions in Scottish Castles",
            "week_number": 42,
            "week_dates": "Oct 14-20, 2025",
            "status": "pending",
            "current_stage": "calendar",
            "current_substage": "view",
            "progress": 0,
            "last_updated": "2025-10-10T16:00:00Z",
            "automation_mode": "auto",
            "can_resume": False,
            "can_pause": False
        },
        {
            "post_id": 76,
            "title": "Scottish Highland Wildlife in Autumn",
            "week_number": 40,
            "week_dates": "Sep 30 - Oct 6, 2025",
            "status": "published",
            "current_stage": "published",
            "current_substage": "clan.com",
            "progress": 100,
            "last_updated": "2025-10-07T14:00:00Z",
            "automation_mode": "completed",
            "can_resume": False,
            "can_pause": False
        }
    ]
    
    # Apply filters
    if filter_type != 'all':
        mock_posts = [post for post in mock_posts if post['status'] == filter_type]
    
    # Apply sorting
    if sort_by == 'week':
        mock_posts.sort(key=lambda x: x['week_number'], reverse=True)
    elif sort_by == 'status':
        mock_posts.sort(key=lambda x: x['status'])
    elif sort_by == 'progress':
        mock_posts.sort(key=lambda x: x['progress'], reverse=True)
    elif sort_by == 'updated':
        mock_posts.sort(key=lambda x: x['last_updated'], reverse=True)
    
    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_posts = mock_posts[start_idx:end_idx]
    
    mock_data = {
        "success": True,
        "data": {
            "posts": paginated_posts,
            "pagination": {
                "current_page": page,
                "total_pages": (len(mock_posts) + limit - 1) // limit,
                "total_posts": len(mock_posts),
                "has_next": end_idx < len(mock_posts),
                "has_prev": page > 1
            },
            "filters": {
                "available": ["all", "draft", "in_progress", "scheduled", "published", "failed"],
                "current": filter_type
            },
            "sort_options": {
                "available": ["week", "status", "progress", "updated"],
                "current": sort_by
            }
        }
    }
    return jsonify(mock_data)

@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get unread alerts for header"""
    unread_only = request.args.get('unread_only', 'true').lower() == 'true'
    
    mock_alerts = [
        {
            "id": 1,
            "alert_type": "stuck_post",
            "severity": "warning",
            "post_id": 76,
            "title": "Post #76 Stuck at Image Generation",
            "message": "Failed 3 times - needs manual attention",
            "action_url": "/launchpad/one-click-blog?post=76",
            "action_text": "View Post",
            "created_at": "2025-10-10T14:30:00Z",
            "is_read": False
        },
        {
            "id": 2,
            "alert_type": "ready_publish",
            "severity": "info",
            "post_id": 75,
            "title": "Post #75 Ready for Publication",
            "message": "Scheduled for today at 2:00 PM",
            "action_url": "/launchpad/one-click-blog?post=75&action=publish",
            "action_text": "Publish Now",
            "created_at": "2025-10-10T13:00:00Z",
            "is_read": False
        },
        {
            "id": 3,
            "alert_type": "completion",
            "severity": "success",
            "post_id": 74,
            "title": "Post #74 Published Successfully",
            "message": "Automation completed and published to Clan.com",
            "action_url": "/launchpad/one-click-blog?post=74",
            "action_text": "View Post",
            "created_at": "2025-10-10T12:00:00Z",
            "is_read": True
        }
    ]
    
    if unread_only:
        mock_alerts = [alert for alert in mock_alerts if not alert['is_read']]
    
    mock_data = {
        "success": True,
        "data": {
            "alerts": mock_alerts,
            "unread_count": len([alert for alert in mock_alerts if not alert['is_read']])
        }
    }
    return jsonify(mock_data)

@bp.route('/start-automation', methods=['POST'])
def start_automation():
    """Initiate automation for a post (mock initially)"""
    data = request.get_json()
    
    post_id = data.get('post_id')
    idea_id = data.get('idea_id')
    publish_time = data.get('publish_time')
    require_approval = data.get('require_approval', True)
    
    mock_data = {
        "success": True,
        "data": {
            "automation_id": f"auto_{post_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "started",
            "estimated_completion": (datetime.now() + timedelta(hours=2)).isoformat() + "Z",
            "current_stage": "calendar",
            "message": "Automation started successfully"
        }
    }
    return jsonify(mock_data)

@bp.route('/toggle-mode', methods=['POST'])
def toggle_mode():
    """Toggle manual/auto mode for a stage"""
    data = request.get_json()
    
    post_id = data.get('post_id')
    stage = data.get('stage')
    mode = data.get('mode')
    
    mock_data = {
        "success": True,
        "data": {
            "stage": stage,
            "mode": mode,
            "message": "Mode updated successfully"
        }
    }
    return jsonify(mock_data)

@bp.route('/alert/dismiss/<int:alert_id>', methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    mock_data = {
        "success": True,
        "data": {
            "alert_id": alert_id,
            "message": "Alert dismissed successfully"
        }
    }
    return jsonify(mock_data)

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
                    updated_at = CURRENT_TIMESTAMP
                RETURNING automation_mode, updated_at
            """, (stage, substage, automation_mode))
            
            result = cursor.fetchone()
            
            return jsonify({
                "success": True,
                "stage": stage,
                "substage": substage,
                "automation_mode": result['automation_mode'],
                "updated_at": result['updated_at'].isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error updating substage setting: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/substage-execute/<stage>/<substage>', methods=['POST'])
def execute_substage(stage, substage):
    """Execute a specific substage (for automation)"""
    try:
        data = request.get_json()
        logger.info(f"execute_substage called with stage={stage}, substage={substage}, data={data}, data type={type(data)}")
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({"success": False, "error": "Post ID is required"}), 400
        
        # Check automation setting for this substage
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT automation_mode
                FROM substage_automation_settings
                WHERE stage = %s AND substage = %s
            """, (stage, substage))
            
            setting = cursor.fetchone()
            logger.info(f"Setting for {stage}/{substage}: {setting}, type: {type(setting)}")
            automation_mode = setting['automation_mode'] if setting else 'manual'
            
            # If mode is 'hold', return error to trigger alert
            if automation_mode == 'hold':
                return jsonify({
                    "success": False,
                    "error": f"Automation blocked: {substage} is set to 'Hold' mode",
                    "automation_mode": "hold"
                }), 403
            
            # Execute the substage based on stage/substage
            if stage == 'planning' and substage == 'topic_brainstorming':
                return execute_topic_brainstorming(post_id, data)
            elif stage == 'planning' and substage == 'section_structure':
                return execute_section_structure(post_id, data)
            elif stage == 'planning' and substage == 'topic_allocation':
                return execute_topic_allocation(post_id, data)
            elif stage == 'planning' and substage == 'section_titling':
                logger.info(f"About to call execute_section_titling with post_id={post_id}, data={data}")
                return execute_section_titling(post_id, data)
            else:
                return jsonify({
                    "success": False,
                    "error": f"Substage execution not implemented: {stage}/{substage}"
                }), 501
                
    except Exception as e:
        logger.error(f"Error executing substage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def execute_topic_allocation(post_id, data):
    """Execute topic allocation for a post using the same logic as template page"""
    try:
        # Get post data - need section structure for generating section-specific topics
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.section_structure, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
        if not post['section_structure']:
            return jsonify({"success": False, "error": "No section structure found. Please run Section Structure first."}), 400
            
        # Call the unified section-specific topic generation API
        from blueprints.planning_api_topic_allocation import api_generate_section_specific_topics
        
        # Create a mock request object with the required data
        class MockRequest:
            def get_json(self):
                return {'post_id': post_id}
        
        # Temporarily replace the global request object
        import flask
        original_request = flask.request
        flask.request = MockRequest()
        
        try:
            # Call the unified section-specific topic generation API
            result = api_generate_section_specific_topics()
            
            # Handle Flask response
            if isinstance(result, tuple):
                status_code, result_data = result
                if status_code != 200:
                    return jsonify({
                        'success': False,
                        'error': result_data.get('error', 'Failed to generate section-specific topics')
                    }), status_code
                # If status is 200, result_data is the Flask response object
                result_data = result_data.get_json() if hasattr(result_data, 'get_json') else result_data
            else:
                if hasattr(result, 'get_json'):
                    result_data = result.get_json()
                else:
                    result_data = result
            
            if result_data.get('success'):
                # Update the allocation_completed_at timestamp
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE post_development 
                        SET allocation_completed_at = NOW()
                        WHERE post_id = %s
                    """, (post_id,))
                
                logger.info(f"Section-specific topic allocation completed successfully for post {post_id}")
                return jsonify({
                    'success': True,
                    'allocations': result_data.get('allocations'),
                    'saved_to_database': True
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result_data.get('error', 'Failed to generate section-specific topics')
                }), 500
                
        finally:
            # Restore original request object
            flask.request = original_request
            
    except Exception as e:
        logger.error(f"Error executing topic allocation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def execute_section_titling(post_id, data):
    """Execute section titling for a post using the same logic as template page"""
    try:
        logger.info(f"Starting section titling for post {post_id}, data type: {type(data)}")
        
        # Get post data - need topic allocation for generating section titles
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.topic_allocation, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                logger.error(f"Post {post_id} not found")
                return jsonify({"success": False, "error": "Post not found"}), 404
            
        logger.info(f"Post data retrieved: title={post['title']}, topic_allocation type={type(post['topic_allocation'])}, expanded_idea={post['expanded_idea']}")
        
        if not post['topic_allocation']:
            logger.error(f"No topic allocation found for post {post_id}")
            return jsonify({"success": False, "error": "No topic allocation found. Please run Topic Allocation first."}), 400
            
        # Instead of using mock request, create a direct function call
        # Prepare the data for the API call
        topic_allocation = post['topic_allocation']
        if isinstance(topic_allocation, str):
            try:
                topic_allocation = json.loads(topic_allocation)
            except json.JSONDecodeError:
                topic_allocation = []
        elif topic_allocation is None:
            topic_allocation = []
        
        # Extract the allocations array from the topic allocation data
        if isinstance(topic_allocation, dict) and 'allocations' in topic_allocation:
            topic_allocation = topic_allocation['allocations']
        
        # Import the core logic from planning_sections
        from blueprints.planning_sections import LLMService
        import json
        
        # Call the core section titling logic directly
        try:
            # Load Section Titling prompt from database
            logger.info("Loading Section Titling prompt from database")
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name = 'Section Titling'
                    ORDER BY id DESC
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if prompt_data and prompt_data['system_prompt']:
                    system_prompt = prompt_data['system_prompt']
                    logger.info("Loaded system prompt from database")
                else:
                    logger.warning("Section Titling system prompt not found in database, using fallback")
                    system_prompt = """You are a titling specialist. Your job is to craft short, poetic, evocative section titles that fit the supplied sections and their bullet topics."""
                
                if prompt_data and prompt_data['prompt_text']:
                    prompt_text = prompt_data['prompt_text']
                else:
                    prompt_text = """Generate creative section titles for this post. Follow all constraints and output format exactly."""
            
            # Format the prompt with actual data
            sections_text = ""
            for i, allocation in enumerate(topic_allocation):
                section_theme = allocation.get('section_theme', f'Section {i+1}')
                sections_text += f"{i+1}. {section_theme}\n"
            
            formatted_prompt = f"""Generate creative section titles for this blog post.

BLOG POST TOPIC: {post['expanded_idea']}

SECTIONS TO TITLE:
{sections_text.strip()}

REQUIREMENTS:
- Generate exactly {len(topic_allocation)} titles
- Each title should be 2-4 words
- Make titles poetic and evocative
- Do not include the blog post topic in your titles

OUTPUT FORMAT (JSON only):
{{
  "post_title": "{post['expanded_idea']}",
  "sections": [
    {", ".join([f'{{ "index": {i+1}, "original": "{allocation.get("section_theme", f"Section {i+1}")}", "title": "Your Creative Title Here" }}' for i, allocation in enumerate(topic_allocation)])}
  ]
}}"""
            
            # Call LLM service
            llm_service = LLMService()
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': formatted_prompt}
            ]
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=4000)
            
            if response and 'content' in response:
                # Parse the JSON response
                content = response['content'].strip()
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                try:
                    result = json.loads(json_content)
                    sections = result.get('sections', [])
                    
                    if not sections:
                        return jsonify({
                            'success': False,
                            'error': 'No sections generated'
                        }), 500
                    
                    # Save the generated sections to database
                    sections_json = json.dumps({'sections': sections})
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            UPDATE post_development 
                            SET sections = %s, updated_at = %s
                            WHERE post_id = %s
                        """, (sections_json, datetime.now(), post_id))
                    
                    logger.info(f"Section titling completed successfully for post {post_id}")
                    return jsonify({
                        'success': True,
                        'sections': sections,
                        'saved_to_database': True
                    })
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid JSON response from LLM'
                    }), 500
            else:
                logger.error("No content in LLM response")
                return jsonify({
                    'success': False,
                    'error': 'No content in LLM response'
                }), 500
                
        except Exception as e:
            logger.error(f"Error in direct section titling: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to generate section titles: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error executing section titling: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

def execute_topic_brainstorming(post_id, data):
    """Execute topic brainstorming for a post using the same logic as template page"""
    try:
        # Get post data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
            expanded_idea = post['expanded_idea'] or post['title']
            
        if not expanded_idea:
            return jsonify({"success": False, "error": "Expanded idea is required"}), 400
            
        # Use the same logic as the template page API
        from blueprints.planning_llm import LLMService, parse_brainstorm_topics
        
        brainstorm_type = data.get('brainstorm_type', 'comprehensive')
        
        # Load prompt from database (same as template page)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT system_prompt, prompt_text
                FROM llm_prompt 
                WHERE name = 'brainstorm_topics'
                ORDER BY id DESC
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({
                    "success": False,
                    "error": "No brainstorm_topics prompt found in database. Please add a proper prompt with JSON format specification."
                }), 500
            
            system_prompt = prompt_data['system_prompt']
            prompt_text = prompt_data['prompt_text']
        
        # Generate topics using LLM (same as template page)
        llm_service = LLMService()
        
        user_content = prompt_text.format(
            brainstorm_type=brainstorm_type,
            expanded_idea=expanded_idea
        )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ]
        
        response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=6000)
        
        if response and 'content' in response:
            topics = parse_brainstorm_topics(response['content'])
            
            # Save topics using the same logic as template page (api_posts_idea_scope)
            with db_manager.get_cursor() as cursor:
                # Get existing idea_scope if it exists
                cursor.execute("""
                    SELECT idea_scope FROM post_development WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                idea_scope = {}
                if result and result['idea_scope']:
                    try:
                        idea_scope = json.loads(result['idea_scope']) if isinstance(result['idea_scope'], str) else result['idea_scope']
                    except:
                        idea_scope = {}
                
                # Update idea_scope with new topics (same as template page)
                idea_scope['generated_topics'] = topics
                idea_scope['generated_at'] = datetime.now().isoformat()
                idea_scope['total_count'] = len(topics)
                
                # Save back to database (same as template page)
                cursor.execute("""
                    UPDATE post_development
                    SET idea_scope = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s
                """, (json.dumps(idea_scope), post_id))
                
                logger.info(f"Saved {len(topics)} brainstorm topics to database for post {post_id}")
            
            return jsonify({
                'success': True,
                'topics': topics,
                'raw_content': response['content'],
                'saved_to_database': True
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate topics'}), 500
            
    except Exception as e:
        logger.error(f"Error executing topic brainstorming: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get automation settings"""
    mock_data = {
        "success": True,
        "data": {
            "default_automation_mode": {
                "calendar": "auto",
                "concept": "auto",
                "authoring": "manual",
                "imaging": "auto"
            },
            "retry_settings": {
                "max_retries": 3,
                "retry_delay_minutes": 5,
                "exponential_backoff": True
            },
            "notification_preferences": {
                "email": False,
                "browser": True,
                "sound": False
            },
            "publication_timing": {
                "default_publish_time": "14:00",
                "require_approval": True,
                "auto_publish": False
            },
            "llm_providers": {
                "calendar": "ollama",
                "concept": "ollama",
                "authoring": "ollama",
                "imaging": "ollama"
            }
        }
    }
    return jsonify(mock_data)

@bp.route('/settings', methods=['POST'])
def save_settings():
    """Save automation settings"""
    data = request.get_json()
    
    mock_data = {
        "success": True,
        "data": {
            "message": "Settings saved successfully",
            "settings": data
        }
    }
    return jsonify(mock_data)

@bp.route('/post/<int:post_id>/pause', methods=['POST'])
def pause_post(post_id):
    """Pause automation for a post"""
    mock_data = {
        "success": True,
        "data": {
            "post_id": post_id,
            "status": "paused",
            "message": "Automation paused successfully"
        }
    }
    return jsonify(mock_data)

@bp.route('/post/<int:post_id>/resume', methods=['POST'])
def resume_post(post_id):
    """Resume automation for a post"""
    mock_data = {
        "success": True,
        "data": {
            "post_id": post_id,
            "status": "resumed",
            "message": "Automation resumed successfully"
        }
    }
    return jsonify(mock_data)

@bp.route('/post/<int:post_id>/delete', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post"""
    mock_data = {
        "success": True,
        "data": {
            "post_id": post_id,
            "message": "Post deleted successfully"
        }
    }
    return jsonify(mock_data)

@bp.route('/create-post', methods=['POST'])
def create_post():
    """Create a new post"""
    data = request.get_json()
    
    mock_data = {
        "success": True,
        "data": {
            "post_id": 79,
            "title": data.get('title', 'New Post'),
            "status": "pending",
            "message": "Post created successfully"
        }
    }
    return jsonify(mock_data)

def execute_section_structure(post_id, data):
    """Execute section structure design for a post"""
    try:
        # Get post data and topics
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.expanded_idea, pd.idea_scope
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
            expanded_idea = post['expanded_idea'] or post['title']
            
            # Get topics from idea_scope
            topics = []
            if post['idea_scope']:
                try:
                    idea_scope_data = json.loads(post['idea_scope']) if isinstance(post['idea_scope'], str) else post['idea_scope']
                    topics = idea_scope_data.get('generated_topics', [])
                except:
                    pass
            
        if not topics:
            return jsonify({"success": False, "error": "No topics found. Please run topic brainstorming first."}), 400
            
        if not expanded_idea:
            return jsonify({"success": False, "error": "Expanded idea is required"}), 400
            
        # Call the section structure API logic directly
        from blueprints.planning_sections import api_design_section_structure
        
        # Create a mock request object with the required data
        class MockRequest:
            def get_json(self):
                return {
                    'topics': topics,
                    'post_id': post_id,
                    'expanded_idea': expanded_idea
                }
        
        # Temporarily replace the global request object
        import flask
        original_request = flask.request
        flask.request = MockRequest()
        
        try:
            # Call the section structure API
            result = api_design_section_structure()
            
            # Convert Flask response to dict if needed
            if hasattr(result, 'get_json'):
                result_data = result.get_json()
            else:
                result_data = result
            
            if result_data.get('success'):
                # Update the structure_design_at timestamp
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE post_development 
                        SET structure_design_at = NOW()
                        WHERE post_id = %s
                    """, (post_id,))
                
                logger.info(f"Section structure generated successfully for post {post_id}")
                return jsonify({
                    'success': True,
                    'section_structure': result_data.get('section_structure'),
                    'raw_response': result_data.get('raw_response'),
                    'saved_to_database': True
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result_data.get('error', 'Failed to generate section structure')
                }), 500
                
        finally:
            # Restore original request object
            flask.request = original_request
            
    except Exception as e:
        logger.error(f"Error executing section structure: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/analytics/<int:post_id>', methods=['GET'])
def get_post_analytics(post_id):
    """Get analytics for a published post"""
    mock_data = {
        "success": True,
        "data": {
            "post_id": post_id,
            "views": 1250,
            "clicks": 45,
            "engagement_rate": 3.6,
            "published_at": "2025-10-07T14:00:00Z",
            "analytics_url": f"/analytics/posts/{post_id}"
        }
    }
    return jsonify(mock_data)
