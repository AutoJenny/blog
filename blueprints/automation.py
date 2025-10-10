"""
One-Click Blog Automation API Endpoints
Mock implementation for UI development
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta

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
            
            # Select the first idea as the selected one (highest priority)
            selected_idea = ideas[0]
            alternative_ideas = ideas[1:] if len(ideas) > 1 else []
            
            # Get schedule data for current week
            cursor.execute("""
                SELECT scheduled_date, scheduled_time, publish_time, status, post_id
                FROM calendar_schedule 
                WHERE year = %s AND week_number = %s
                ORDER BY scheduled_date ASC
                LIMIT 1
            """, (current_week['year'], current_week['week_number']))
            
            schedule_data = cursor.fetchone()
            
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
                    
                    # Insert the schedule
                    cursor.execute("""
                        INSERT INTO calendar_schedule 
                        (year, week_number, scheduled_date, scheduled_time, publish_time, status, requires_approval, automation_enabled)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING scheduled_date, scheduled_time, publish_time, status, post_id
                    """, (
                        current_week['year'], 
                        current_week['week_number'],
                        publish_date,
                        '14:00:00',
                        '14:00:00', 
                        'planned',
                        True,
                        True
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
    mock_data = {
        "success": True,
        "data": {
            "post_id": post_id,
            "title": "Welsh Myths and Legends",
            "current_stage": "authoring",
            "current_substage": "author-first-drafts",
            "overall_progress": 67,
            "stages": {
                "calendar": {
                    "status": "complete",
                    "progress": 100,
                    "substages": {
                        "view": {"status": "complete", "completed_at": "2025-10-10T10:00:00Z"},
                        "ideas": {"status": "complete", "completed_at": "2025-10-10T10:15:00Z"}
                    }
                },
                "concept": {
                    "status": "complete",
                    "progress": 100,
                    "substages": {
                        "brainstorm": {"status": "complete", "completed_at": "2025-10-10T11:00:00Z"},
                        "section-structure": {"status": "complete", "completed_at": "2025-10-10T12:00:00Z"},
                        "topic-allocation": {"status": "complete", "completed_at": "2025-10-10T13:00:00Z"},
                        "titling": {"status": "complete", "completed_at": "2025-10-10T14:00:00Z"},
                        "outline": {"status": "complete", "completed_at": "2025-10-10T15:00:00Z"}
                    }
                },
                "authoring": {
                    "status": "in_progress",
                    "progress": 60,
                    "automation_mode": "manual",
                    "substages": {
                        "author-first-drafts": {"status": "in_progress", "progress": 80},
                        "fix-language": {"status": "pending"},
                        "image-concepts": {"status": "pending"},
                        "image-prompts": {"status": "pending"},
                        "image-captions": {"status": "pending"}
                    }
                },
                "imaging": {
                    "status": "pending",
                    "progress": 0,
                    "automation_mode": "auto",
                    "substages": {
                        "image-generation": {"status": "pending"},
                        "optimise": {"status": "pending"}
                    }
                }
            },
            "estimated_completion": "2025-10-12T16:00:00Z",
            "last_action_at": "2025-10-10T15:30:00Z",
            "error_count": 0
        }
    }
    return jsonify(mock_data)

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
