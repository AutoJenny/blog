"""
Families & Clans Browser Blueprint
Browse and filter Scottish families and clans
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('families', __name__, url_prefix='/families')


@bp.route('/')
def browser():
    """Main families browser page with filters."""
    return render_template('families/browser.html')


@bp.route('/<int:family_id>/narrative')
@bp.route('/<int:family_id>/narrative/')
def family_narrative(family_id):
    """Shareable narrative page for a family."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family
                cur.execute("SELECT id, name, research_data FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                
                if not family:
                    return render_template('families/not_found.html', family_id=family_id), 404
                
                family_dict = dict(family)
                
                # Parse research_data from JSONB if present
                if family_dict.get('research_data'):
                    if isinstance(family_dict['research_data'], str):
                        family_dict['research_data'] = json.loads(family_dict['research_data'])
                
                # Check if narrative exists
                narrative = None
                if (family_dict.get('research_data') and 
                    family_dict['research_data'].get('metadata') and 
                    family_dict['research_data']['metadata'].get('narrative')):
                    narrative = family_dict['research_data']['metadata']['narrative']
                    last_updated = family_dict['research_data']['metadata'].get('last_updated', 'Unknown')
                    word_count = family_dict['research_data']['metadata'].get('narrative_word_count', 0)
                else:
                    return render_template('families/narrative_not_found.html', 
                                         family_name=family_dict['name'], 
                                         family_id=family_id), 404
                
                return render_template('families/narrative.html', 
                                     family_name=family_dict['name'],
                                     family_id=family_id,
                                     narrative=narrative,
                                     last_updated=last_updated,
                                     word_count=word_count)
    
    except Exception as e:
        logger.error(f"Error loading narrative: {e}", exc_info=True)
        return render_template('families/error.html', error=str(e)), 500


@bp.route('/<int:family_id>')
@bp.route('/<int:family_id>/')
def family_detail(family_id):
    """Family detail page."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family
                cur.execute("SELECT * FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                
                if not family:
                    return render_template('families/not_found.html', family_id=family_id), 404
                
                family_dict = dict(family)
                
                # Parse research_data from JSONB if present
                if family_dict.get('research_data'):
                    import json
                    if isinstance(family_dict['research_data'], str):
                        family_dict['research_data'] = json.loads(family_dict['research_data'])
                    # If it's already a dict (psycopg parsed it), keep it as is
                
                # Get relationships
                cur.execute("""
                    SELECT alias_name FROM family_aliases 
                    WHERE family_id = %s ORDER BY alias_name
                """, (family_id,))
                family_dict['aliases'] = [row['alias_name'] for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.spelling_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['variants'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.spelling_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['spelling_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.sept_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['septs'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.sept_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['sept_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT resource_type, resource_category, resource_value, resource_metadata
                    FROM family_resources
                    WHERE family_id = %s
                    ORDER BY resource_type, resource_category
                """, (family_id,))
                family_dict['resources'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT design_id, design_year, design_url, is_default
                    FROM family_designs
                    WHERE family_id = %s
                    ORDER BY is_default DESC, design_year DESC
                """, (family_id,))
                family_dict['designs'] = [dict(row) for row in cur.fetchall()]
                
                return render_template('families/detail.html', family=family_dict)
    
    except Exception as e:
        logger.error(f"Error loading family detail: {e}", exc_info=True)
        return render_template('families/error.html', error=str(e)), 500


@bp.route('/api/list')
def api_list():
    """API endpoint for listing families with filters."""
    try:
        # Get filter parameters
        search = request.args.get('search', '').strip()
        is_clan = request.args.get('is_clan')
        is_canonical = request.args.get('is_canonical')
        has_history = request.args.get('has_history')
        has_research = request.args.get('has_research')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Build WHERE clause
                conditions = []
                params = []
                
                if search:
                    conditions.append("f.name ILIKE %s")
                    params.append(f"%{search}%")
                
                if is_clan is not None:
                    conditions.append("f.is_clan = %s")
                    params.append(is_clan.lower() == 'true')
                
                if is_canonical is not None:
                    conditions.append("f.is_canonical = %s")
                    params.append(is_canonical.lower() == 'true')
                
                if has_history is not None:
                    conditions.append("f.has_history = %s")
                    params.append(has_history.lower() == 'true')
                
                if has_research is not None:
                    if has_research.lower() == 'true':
                        conditions.append("f.research_data IS NOT NULL")
                    else:
                        conditions.append("f.research_data IS NULL")
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM families f
                    WHERE {where_clause}
                """
                cur.execute(count_query, params)
                total = cur.fetchone()['total']
                
                # Get families with relationships
                query = f"""
                    SELECT 
                        f.id,
                        f.name,
                        f.is_clan,
                        f.is_canonical,
                        f.has_history,
                        f.is_virtual,
                        CASE WHEN f.research_data IS NOT NULL THEN true ELSE false END as has_research,
                        (SELECT COUNT(*) FROM family_aliases WHERE family_id = f.id) as alias_count,
                        (SELECT COUNT(*) FROM family_spellings WHERE family_id = f.id) as variant_count,
                        (SELECT COUNT(*) FROM family_spellings WHERE spelling_of_id = f.id) as has_variants_count,
                        (SELECT COUNT(*) FROM family_septs WHERE family_id = f.id) as sept_count,
                        (SELECT COUNT(*) FROM family_septs WHERE sept_of_id = f.id) as has_septs_count,
                        (SELECT COUNT(*) FROM family_resources WHERE family_id = f.id) as resource_count,
                        (SELECT COUNT(*) FROM family_designs WHERE family_id = f.id) as design_count
                    FROM families f
                    WHERE {where_clause}
                    ORDER BY f.name
                    LIMIT %s OFFSET %s
                """
                params.extend([per_page, offset])
                cur.execute(query, params)
                families = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'families': families,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page
                })
    
    except Exception as e:
        logger.error(f"Error listing families: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/<int:family_id>')
def api_family_detail(family_id):
    """Get detailed information about a specific family."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family
                cur.execute("SELECT * FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                
                if not family:
                    return jsonify({'error': 'Family not found'}), 404
                
                family_dict = dict(family)
                
                # Get relationships
                cur.execute("""
                    SELECT alias_name FROM family_aliases 
                    WHERE family_id = %s ORDER BY alias_name
                """, (family_id,))
                family_dict['aliases'] = [row['alias_name'] for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.spelling_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['variants'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.spelling_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['spelling_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.sept_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['septs'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.sept_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['sept_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT resource_type, resource_category, resource_value
                    FROM family_resources
                    WHERE family_id = %s
                    ORDER BY resource_type, resource_category
                """, (family_id,))
                family_dict['resources'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT design_id, design_year, design_url, is_default
                    FROM family_designs
                    WHERE family_id = %s
                    ORDER BY is_default DESC, design_year DESC
                """, (family_id,))
                family_dict['designs'] = [dict(row) for row in cur.fetchall()]
                
                return jsonify(family_dict)
    
    except Exception as e:
        logger.error(f"Error getting family detail: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/stats')
def api_stats():
    """Get statistics about families."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE is_clan = TRUE) as clans,
                        COUNT(*) FILTER (WHERE is_canonical = TRUE) as canonical,
                        COUNT(*) FILTER (WHERE has_history = TRUE) as with_history,
                        COUNT(*) FILTER (WHERE research_data IS NOT NULL) as with_research,
                        COUNT(*) FILTER (WHERE is_clan = TRUE AND has_history = FALSE) as clans_no_history,
                        COUNT(*) FILTER (WHERE is_clan = TRUE AND research_data IS NOT NULL) as clans_with_research
                    FROM families
                """)
                stats = dict(cur.fetchone())
                
                return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

