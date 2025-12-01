"""
Families & Clans Browser Blueprint
Browse and filter Scottish families and clans
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)

# In-memory store for filtered ID sets for navigation between families.
# Maps a short key to {'ids': [int], 'created_at': datetime}
FILTERED_ID_SETS = {}
FILTERED_ID_SETS_MAX_AGE_SECONDS = 3600  # 1 hour

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
                
                # Get filtered family IDs from server-side filter key (if present)
                # Otherwise, fall back to previous behaviour.
                filter_key = request.args.get('filter_key')
                filtered_ids_param = request.args.get('filtered_ids')
                if filter_key:
                    from datetime import datetime, timedelta
                    # Clean up expired keys
                    now = datetime.utcnow()
                    expired_keys = [
                        k for k, v in FILTERED_ID_SETS.items()
                        if (now - v.get('created_at', now)) > timedelta(seconds=FILTERED_ID_SETS_MAX_AGE_SECONDS)
                    ]
                    for k in expired_keys:
                        FILTERED_ID_SETS.pop(k, None)
                    
                    id_set = FILTERED_ID_SETS.get(filter_key)
                    filtered_ids = id_set.get('ids', []) if id_set else []
                    if filtered_ids and family_id in filtered_ids:
                        current_index = filtered_ids.index(family_id)
                        if current_index > 0:
                            prev_id = filtered_ids[current_index - 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (prev_id,))
                            prev_family = cur.fetchone()
                            family_dict['prev_family'] = dict(prev_family) if prev_family else None
                        else:
                            family_dict['prev_family'] = None
                        
                        if current_index < len(filtered_ids) - 1:
                            next_id = filtered_ids[current_index + 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (next_id,))
                            next_family = cur.fetchone()
                            family_dict['next_family'] = dict(next_family) if next_family else None
                        else:
                            family_dict['next_family'] = None
                    else:
                        family_dict['prev_family'] = None
                        family_dict['next_family'] = None
                elif filtered_ids_param:
                    try:
                        filtered_ids = [int(id) for id in filtered_ids_param.split(',')]
                        current_index = filtered_ids.index(family_id) if family_id in filtered_ids else -1
                        
                        if current_index > 0:
                            prev_id = filtered_ids[current_index - 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (prev_id,))
                            prev_family = cur.fetchone()
                            family_dict['prev_family'] = dict(prev_family) if prev_family else None
                        else:
                            family_dict['prev_family'] = None
                        
                        if current_index >= 0 and current_index < len(filtered_ids) - 1:
                            next_id = filtered_ids[current_index + 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (next_id,))
                            next_family = cur.fetchone()
                            family_dict['next_family'] = dict(next_family) if next_family else None
                        else:
                            family_dict['next_family'] = None
                    except (ValueError, IndexError):
                        # Fallback to ID-based navigation if parsing fails
                        cur.execute("SELECT id, name FROM families WHERE id < %s ORDER BY id DESC LIMIT 1", (family_id,))
                        prev_family = cur.fetchone()
                        cur.execute("SELECT id, name FROM families WHERE id > %s ORDER BY id ASC LIMIT 1", (family_id,))
                        next_family = cur.fetchone()
                        family_dict['prev_family'] = dict(prev_family) if prev_family else None
                        family_dict['next_family'] = dict(next_family) if next_family else None
                else:
                    # Default: get previous and next by ID order
                    cur.execute("SELECT id, name FROM families WHERE id < %s ORDER BY id DESC LIMIT 1", (family_id,))
                    prev_family = cur.fetchone()
                    cur.execute("SELECT id, name FROM families WHERE id > %s ORDER BY id ASC LIMIT 1", (family_id,))
                    next_family = cur.fetchone()
                    family_dict['prev_family'] = dict(prev_family) if prev_family else None
                    family_dict['next_family'] = dict(next_family) if next_family else None
                
                # Pass current filters to template for navigation links
                family_dict['current_filters'] = dict(request.args)
                
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
        popularity_min = request.args.get('popularity_min')
        popularity_max = request.args.get('popularity_max')
        sort_by = request.args.get('sort_by', 'name')  # name, popularity
        sort_order = request.args.get('sort_order', 'asc')  # asc, desc
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
                    # Use spelling_of IS NULL to identify canonical names
                    if is_canonical.lower() == 'true':
                        conditions.append("f.spelling_of IS NULL")
                    else:
                        conditions.append("f.spelling_of IS NOT NULL")
                
                if has_history is not None:
                    conditions.append("f.has_history = %s")
                    params.append(has_history.lower() == 'true')
                
                if has_research is not None:
                    if has_research.lower() == 'true':
                        conditions.append("f.research_data IS NOT NULL")
                    else:
                        conditions.append("f.research_data IS NULL")
                
                if popularity_min is not None:
                    try:
                        conditions.append("f.popularity_rating >= %s")
                        params.append(int(popularity_min))
                    except ValueError:
                        pass
                
                if popularity_max is not None:
                    try:
                        conditions.append("f.popularity_rating <= %s")
                        params.append(int(popularity_max))
                    except ValueError:
                        pass
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Build ORDER BY clause
                valid_sort_fields = {'name': 'f.name', 'popularity': 'f.popularity_rating'}
                sort_field = valid_sort_fields.get(sort_by, 'f.name')
                sort_dir = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
                
                # Handle NULL values in popularity sorting
                if sort_by == 'popularity':
                    # Put NULLs last regardless of sort order
                    order_clause = f"f.popularity_rating {sort_dir} NULLS LAST, f.name ASC"
                else:
                    order_clause = f"{sort_field} {sort_dir}"
                
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
                        (f.spelling_of IS NULL) as is_canonical,
                        f.has_history,
                        f.is_virtual,
                        f.popularity_rating,
                        CASE WHEN f.research_data IS NOT NULL THEN true ELSE false END as has_research,
                        CASE WHEN f.research_data IS NOT NULL AND jsonb_typeof(f.research_data) = 'object' AND (f.research_data::text != '{{}}'::text) THEN true ELSE false END as has_json,
                        CASE WHEN f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative' THEN true ELSE false END as has_compiled,
                        CASE WHEN f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked' THEN true ELSE false END as has_openai,
                        (
                            SELECT COUNT(*) 
                            FROM family_resources fr 
                            WHERE fr.family_id = f.id 
                              AND fr.resource_type = 'text'
                              AND fr.resource_category = 'history_legacy'
                              AND fr.resource_value IS NOT NULL
                              AND array_length(
                                    string_to_array(
                                        regexp_replace(fr.resource_value, '\\s+', ' ', 'g'),
                                        ' '
                                    ),
                                    1
                                  ) > 50
                        ) as legacy_history_count,
                        CASE WHEN EXISTS (
                            SELECT 1 
                            FROM family_resources fr2
                            WHERE fr2.family_id = f.id
                              AND fr2.resource_type = 'text'
                              AND fr2.resource_category = 'history_legacy_generated'
                        ) THEN true ELSE false END as has_legacy_generated,
                        (SELECT COUNT(*) FROM family_aliases WHERE family_id = f.id) as alias_count,
                        (SELECT COUNT(*) FROM family_spellings WHERE family_id = f.id) as variant_count,
                        (SELECT COUNT(*) FROM family_spellings WHERE spelling_of_id = f.id) as has_variants_count,
                        (SELECT COUNT(*) FROM family_septs WHERE family_id = f.id) as sept_count,
                        (SELECT COUNT(*) FROM family_septs WHERE sept_of_id = f.id) as has_septs_count,
                        (SELECT COUNT(*) FROM family_resources WHERE family_id = f.id) as resource_count,
                        (SELECT COUNT(*) FROM family_designs WHERE family_id = f.id) as design_count
                    FROM families f
                    WHERE {where_clause}
                    ORDER BY {order_clause}
                    LIMIT %s OFFSET %s
                """
                # Get filtered stats for the current filter set (before adding pagination params)
                stats_query = f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE f.is_clan = TRUE) as clans,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL) as canonical,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE) as with_history,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL) as with_research,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND jsonb_typeof(f.research_data) = 'object' AND (f.research_data::text != '{{}}'::text)) as with_json,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative') as with_compiled,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_openai,
                        COUNT(*) FILTER (
                            WHERE EXISTS (
                                SELECT 1 
                                FROM family_resources frg
                                WHERE frg.family_id = f.id
                                  AND frg.resource_type = 'text'
                                  AND frg.resource_category = 'history_legacy_generated'
                            )
                        ) as with_legacy_generated,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE AND f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_both,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL AND f.has_history = FALSE AND (f.research_data IS NULL OR NOT (f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked'))) as canonical_no_content
                    FROM families f
                    WHERE {where_clause}
                """
                cur.execute(stats_query, params)
                filtered_stats = dict(cur.fetchone())
                
                # Now add pagination params for the main query
                params.extend([per_page, offset])
                cur.execute(query, params)
                families = [dict(row) for row in cur.fetchall()]

                return jsonify({
                    'families': families,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page,
                    'filtered_stats': filtered_stats
                })
    
    except Exception as e:
        logger.error(f"Error listing families: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/store_filter_ids', methods=['POST'])
def api_store_filter_ids():
    """Store filtered family IDs server-side and return a short key."""
    try:
        data = request.get_json(silent=True) or {}
        ids = data.get('ids') or []
        # Normalise to list of ints
        try:
            ids = [int(i) for i in ids]
        except (TypeError, ValueError):
            ids = []
        
        if not ids:
            return jsonify({'error': 'No ids provided'}), 400
        
        from uuid import uuid4
        from datetime import datetime, timedelta

        # Prune expired keys
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in FILTERED_ID_SETS.items()
            if (now - v.get('created_at', now)) > timedelta(seconds=FILTERED_ID_SETS_MAX_AGE_SECONDS)
        ]
        for k in expired_keys:
            FILTERED_ID_SETS.pop(k, None)
        
        key = uuid4().hex[:12]
        FILTERED_ID_SETS[key] = {
            'ids': ids,
            'created_at': now,
        }
        
        return jsonify({'key': key})
    except Exception as e:
        logger.error(f"Error storing filter ids: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/<int:family_id>/approve', methods=['POST', 'PUT'])
def api_family_approve(family_id):
    """Update the research_approved status for a family."""
    try:
        data = request.get_json()
        approved = data.get('approved', False)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE families 
                    SET research_approved = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (approved, family_id))
                conn.commit()
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Family not found'}), 404
                
                return jsonify({'success': True, 'approved': approved})
    
    except Exception as e:
        logger.error(f"Error updating approval status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/<int:family_id>/feedback', methods=['POST'])
def api_family_feedback(family_id):
    """Submit feedback for a family's research data and trigger regeneration."""
    try:
        data = request.get_json()
        feedback = data.get('feedback', '').strip()
        
        if not feedback:
            return jsonify({'error': 'Feedback is required'}), 400
        
        # Get family info
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                if not family:
                    return jsonify({'error': 'Family not found'}), 404
        
        # Run regeneration script
        import subprocess
        import sys
        from pathlib import Path
        
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'regenerate_with_feedback.py'), 
             str(family_id), feedback],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Parse report from stdout
        import re
        import json
        report = None
        report_match = re.search(
            r'FEEDBACK_PROCESSING_REPORT_START\s*(.*?)\s*FEEDBACK_PROCESSING_REPORT_END',
            result.stdout,
            re.DOTALL
        )
        if report_match:
            try:
                report = json.loads(report_match.group(1))
            except json.JSONDecodeError:
                logger.warning(f"Could not parse report JSON for family {family_id}")
        
        if result.returncode != 0:
            logger.error(f"Error regenerating family {family_id}: {result.stderr}")
            logger.error(f"Script stdout: {result.stdout}")
            return jsonify({
                'error': 'Failed to process feedback',
                'details': result.stderr[:500] if result.stderr else 'Unknown error',
                'stdout': result.stdout[:500] if result.stdout else '',
                'report': report
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Feedback processed successfully',
            'output': result.stdout,
            'report': report
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Processing timed out'}), 500
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
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
    """Get statistics about families, optionally filtered."""
    try:
        # Get filter parameters (same as api_list)
        search = request.args.get('search', '').strip()
        is_clan = request.args.get('is_clan')
        is_canonical = request.args.get('is_canonical')
        has_history = request.args.get('has_history')
        has_research = request.args.get('has_research')
        popularity_min = request.args.get('popularity_min')
        popularity_max = request.args.get('popularity_max')
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Build WHERE clause (same logic as api_list)
                conditions = []
                params = []
                
                if search:
                    conditions.append("f.name ILIKE %s")
                    params.append(f"%{search}%")
                
                if is_clan is not None:
                    conditions.append("f.is_clan = %s")
                    params.append(is_clan.lower() == 'true')
                
                if is_canonical is not None:
                    if is_canonical.lower() == 'true':
                        conditions.append("f.spelling_of IS NULL")
                    else:
                        conditions.append("f.spelling_of IS NOT NULL")
                
                if has_history is not None:
                    conditions.append("f.has_history = %s")
                    params.append(has_history.lower() == 'true')
                
                if has_research is not None:
                    if has_research.lower() == 'true':
                        conditions.append("f.research_data IS NOT NULL")
                    else:
                        conditions.append("f.research_data IS NULL")
                
                if popularity_min is not None:
                    try:
                        conditions.append("f.popularity_rating >= %s")
                        params.append(int(popularity_min))
                    except ValueError:
                        pass
                
                if popularity_max is not None:
                    try:
                        conditions.append("f.popularity_rating <= %s")
                        params.append(int(popularity_max))
                    except ValueError:
                        pass
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Get stats with breakdown of research data
                query = f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE f.is_clan = TRUE) as clans,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL) as canonical,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE) as with_history,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL) as with_research,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND jsonb_typeof(f.research_data) = 'object' AND (f.research_data::text != '{{}}'::text)) as with_json,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative') as with_compiled,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_openai,
                        COUNT(*) FILTER (
                            WHERE EXISTS (
                                SELECT 1 
                                FROM family_resources frg
                                WHERE frg.family_id = f.id
                                  AND frg.resource_type = 'text'
                                  AND frg.resource_category = 'history_legacy_generated'
                            )
                        ) as with_legacy_generated,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE AND f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_both,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL AND f.has_history = FALSE AND (f.research_data IS NULL OR NOT (f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked'))) as canonical_no_content
                    FROM families f
                    WHERE {where_clause}
                """
                cur.execute(query, params)
                stats = dict(cur.fetchone())
                
                return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

