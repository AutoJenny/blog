"""Newsletter Content Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_content', __name__)


@bp.route('/newsletter/weather/summary')
def weather_summary():
    """Get weather summary for past week and forecast."""
    try:
        from newsletter.services.weather_summary_service import generate_weather_summary
        
        days_back = request.args.get('days_back', 7, type=int)
        days_ahead = request.args.get('days_ahead', 7, type=int)
        
        summary = generate_weather_summary(days_back=days_back, days_ahead=days_ahead)
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/weather_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating weather summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/weather_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500



@bp.route('/newsletter/weather')
def weather_summary_page():
    """Weather summary page UI."""
    return render_template('newsletter/weather_summary.html')



@bp.route('/newsletter/news/summary')
def news_summary():
    """Get news summary from synopses."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.news_synopsis_service import generate_news_summary
        
        days_back = request.args.get('days_back', 7, type=int)
        limit = request.args.get('limit', 100, type=int)  # Default to 100, allow override
        sort_by = request.args.get('sort_by', 'combined_score')  # combined_score, suitability_score, published_at
        
        summary = generate_news_summary(days_back=days_back, limit=limit, sort_by=sort_by)
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/news_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating news summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/news_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500



@bp.route('/newsletter/news')
def news_summary_page():
    """News summary page UI."""
    return render_template('newsletter/news_summary.html')



@bp.route('/newsletter/events/summary')
def events_summary():
    """Get events summary."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.events_summary_service import generate_events_summary
        
        days_back = request.args.get('days_back', 365, type=int)  # Default to 1 year back
        days_ahead = request.args.get('days_ahead', 365, type=int)  # Default to 1 year ahead
        source_name = request.args.get('source', None, type=str)
        location = request.args.get('location', None, type=str)
        
        recurrence_type = request.args.get('recurrence_type', None, type=str)
        
        summary = generate_events_summary(
            days_back=days_back,
            days_ahead=days_ahead,
            source_name=source_name,
            location=location,
            recurrence_type=recurrence_type
        )
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/events_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating events summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/events_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500



@bp.route('/newsletter/events')
def events_summary_page():
    """Events summary page UI."""
    return render_template('newsletter/events_summary.html')


