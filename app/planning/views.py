"""

# Auto-generated from blueprints/planning.py
# Module: planning/views.py

def planning_dashboard():
    """Main planning dashboard"""
    return render_template('planning/dashboard.html', blueprint_name='planning')


def planning_post_overview(post_id):
    """Planning overview for a specific post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get planning progress
            cursor.execute("""
                SELECT stage_id, sub_stage_id, status, updated_at
                FROM post_workflow_stage 
                WHERE post_id = %s AND stage_id IN (
                    SELECT id FROM workflow_stage_entity WHERE name = 'planning'
                )
                ORDER BY stage_id, sub_stage_id
            """, (post_id,))
            progress = cursor.fetchall()
            
            return render_template('planning/post_overview.html', 
                                 post=post, progress=progress, blueprint_name='planning')
            
    except Exception as e:
        logger.error(f"Error in planning_post_overview: {e}")
        return f"Error: {e}", 500


def planning_idea(post_id):
    """Idea planning phase"""
    return render_template('planning/idea.html', post_id=post_id, blueprint_name='planning')


def planning_research(post_id):
    """Research planning phase"""
    return render_template('planning/research.html', post_id=post_id, blueprint_name='planning')


def planning_structure(post_id):
    """Structure planning phase"""
    return render_template('planning/structure.html', post_id=post_id, blueprint_name='planning')


def planning_calendar(post_id):
    """Content Calendar main stage"""
    return render_template('planning/calendar.html', 
                         post_id=post_id, 
                         page_title='Content Calendar',
                         blueprint_name='planning')


def planning_calendar_view(post_id):
    """Calendar View sub-stage"""
    return render_template('planning/calendar/view.html', 
                         post_id=post_id, 
                         page_title='Calendar View',
                         blueprint_name='planning')


def categories_manage():
    """Category management page"""
    return render_template('planning/categories/manage.html', blueprint_name='planning')


def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    try:
        # Use the same week calculation as the calendar system
        from datetime import datetime
        current_date = datetime.now()
        week_number = current_date.isocalendar()[1]  # Use ISO week standard
        
        # Get week dates for display
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT start_date, end_date, month_name
                FROM calendar_weeks 
                WHERE year = %s AND week_number = %s
            """, (current_date.year, week_number))
            week_data = cursor.fetchone()
            
            if week_data:
                week_dates = f"{week_data['start_date'].strftime('%b %d')} - {week_data['end_date'].strftime('%b %d, %Y')}"
            else:
                week_dates = f"Week {week_number}, {current_date.year}"
        
        return render_template('planning/calendar/ideas.html', 
                             post_id=post_id, 
                             week_number=week_number,
                             week_dates=week_dates,
                             page_title='Idea Generation',
                             blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        # Fallback with basic week number
        from datetime import datetime
        current_date = datetime.now()
        week_number = current_date.isocalendar()[1]
        return render_template('planning/calendar/ideas.html', 
                             post_id=post_id, 
                             week_number=week_number,
                             week_dates=f"Week {week_number}, {current_date.year}",
                             page_title='Idea Generation',
                             blueprint_name='planning')



def planning_concept(post_id):
    """Concept Development main stage - redirects to Topic Brainstorming by default"""
    return redirect(url_for('planning.planning_concept_brainstorm', post_id=post_id))



def planning_concept_brainstorm(post_id):
    """Topic Brainstorming sub-stage"""
    return render_template('planning/concept/brainstorm.html', 
                         post_id=post_id, 
                         page_title='Topic Brainstorming',
                         blueprint_name='planning')


def planning_concept_section_structure(post_id):
    """Section Structure Design - Step 1 of topic allocation"""
    return render_template('planning/concept/section_structure.html', 
                         post_id=post_id, 
                         page_title='Section Structure Design',
                         blueprint_name='planning')


def planning_concept_topic_allocation(post_id):
    """Topic Allocation - Step 2 of topic allocation"""
    return render_template('planning/concept/topic_allocation.html', 
                         post_id=post_id, 
                         page_title='Topic Allocation',
                         blueprint_name='planning')


def planning_concept_topic_refinement(post_id):
    """Topic Refinement - Step 3 of topic allocation"""
    return render_template('planning/concept/topic_refinement.html', 
                         post_id=post_id, 
                         page_title='Topic Refinement',
                         blueprint_name='planning')


def planning_concept_grouping(post_id):
    """Section Grouping sub-stage - groups topics into thematic clusters (DEPRECATED - use individual substages)"""
    return render_template('planning/concept/grouping.html', 
                         post_id=post_id, 
                         page_title='Section Grouping',
                         blueprint_name='planning')


def planning_concept_titling(post_id):
    """Section Titling sub-stage - creates titles and descriptions for grouped sections"""
    return render_template('planning/concept/titling.html', 
                         post_id=post_id, 
                         page_title='Section Titling',
                         blueprint_name='planning')


def planning_concept_sections(post_id):
    """Section Planning sub-stage"""
    return render_template('planning/concept/sections.html', 
                         post_id=post_id, 
                         page_title='Section Planning',
                         blueprint_name='planning')


def planning_concept_outline(post_id):
    """Content Outline sub-stage"""
    return render_template('planning/concept/outline.html', 
                         post_id=post_id, 
                         page_title='Content Outline',
                         blueprint_name='planning')


def test_authoring_preview(post_id):
    """Temporary route to preview the Authoring template"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/drafting.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Authoring Preview")
            
    except Exception as e:
        logger.error(f"Error in test_authoring_preview: {e}")
        return f"Error: {e}", 500


def planning_research_sources(post_id):
    """Source Research sub-stage"""
    return render_template('planning/research/sources.html', post_id=post_id, blueprint_name='planning')


def planning_research_visuals(post_id):
    """Visual Planning sub-stage"""
    return render_template('planning/research/visuals.html', post_id=post_id, blueprint_name='planning')


def planning_research_prompts(post_id):
    """Image Prompts sub-stage"""
    return render_template('planning/research/prompts.html', post_id=post_id, blueprint_name='planning')


def planning_research_verification(post_id):
    """Fact Verification sub-stage"""
    return render_template('planning/research/verification.html', post_id=post_id, blueprint_name='planning')


def planning_old_interface(post_id):
    """Access to old workflow interface"""
    return render_template('planning/old_interface.html', post_id=post_id, blueprint_name='planning')


