"""Photo-harvesting API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .llm_service import LLMService
import logging
import os
import json as _json
from datetime import datetime as _dt
from urllib import request as urlrequest, parse as urlparse

logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMService()


def register_routes(bp):
    """Register photo-harvesting API routes"""
    
    @bp.route('/api/llm/prompts/header-image-search', methods=['GET', 'PUT'])
    def header_api_image_search_prompt():
        """Get or update Header Image Search prompt (Photo-harvesting).
        
        Supports illustration_method query parameter:
        - 'Photo-harvesting' → 'Header Image Search Prompt (Photo-harvesting)' (for photo search)
        - 'LLM-creation' or default → returns 404 (header uses LLM-creation via different flow)
        No fallbacks: 404 if prompt missing.
        """
        try:
            with db_manager.get_cursor() as cursor:
                illustration_method = request.args.get('illustration_method', 'LLM-creation')
                if illustration_method != 'Photo-harvesting':
                    return jsonify({'error': 'Header Image Search prompt only available for Photo-harvesting route'}), 404
                
                prompt_name = 'Header Image Search Prompt (Photo-harvesting)'
                
                if request.method == 'PUT':
                    data = request.get_json()
                    system_prompt_template = data.get('system_prompt', '')
                    prompt_text = data.get('prompt_text', '')
                    
                    system_prompt_complete = system_prompt_template
                    if system_prompt_template and not system_prompt_template.endswith('JSON object'):
                        system_prompt_complete += '\n\nIMPORTANT: Respond ONLY with the final search query text (no quotes, no markdown). No commentary.'
                    
                    cursor.execute("""
                        UPDATE llm_prompt 
                        SET system_prompt_template = %s, system_prompt = %s, prompt_text = %s
                        WHERE name = %s
                    """, (system_prompt_template, system_prompt_complete, prompt_text, prompt_name))
                    
                    cursor.connection.commit()
                    return jsonify({'success': True, 'message': f'Prompt "{prompt_name}" updated successfully'})
                else:
                    cursor.execute("""
                        SELECT name, prompt_text, system_prompt, system_prompt_template, updated_at
                        FROM llm_prompt 
                        WHERE name = %s
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """, (prompt_name,))
                    prompt_data = cursor.fetchone()
                    
                    if not prompt_data:
                        return jsonify({'error': f'Header Image Search prompt "{prompt_name}" not found'}), 404
                    
                    system_prompt_for_display = prompt_data['system_prompt_template'] or prompt_data['system_prompt']
                    
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'name': prompt_data['name'],
                            'prompt_text': prompt_data['prompt_text'],
                            'system_prompt': system_prompt_for_display,
                            'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                        }
                    })
                        
        except Exception as e:
            logger.error(f"Error with header image search prompt: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/photo-search/posts/<int:post_id>/header/generate-search-term', methods=['POST'])
    def header_api_generate_search_term(post_id: int):
        """Generate header image search term using LLM from theme name and expanded_idea.
        Uses Header Image Search Prompt (Photo-harvesting). No fallbacks.
        """
        try:
            # Get week context from request
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            # Resolve target_post_id (use provided post_id as fallback, but prefer resolved one)
            target_post_id = post_id
            if year and week:
                try:
                    from utils.week_post_resolver import resolve_post_for_week
                    resolved = resolve_post_for_week(year, week)
                    if resolved:
                        target_post_id = resolved
                    else:
                        # If no resolved post, use provided post_id (may be from URL)
                        logger.info(f"No resolved post for year={year}, week={week}, using provided post_id={post_id}")
                except Exception as e:
                    logger.warning(f"Week resolver failed for header search term: {e}, using provided post_id={post_id}")
            
            with db_manager.get_cursor() as cursor:
                # Get selected theme name and expanded_idea for target_post_id
                theme_name = ''
                expanded_idea = ''
                
                if year and week:
                    # Check if new tables exist, fallback to old calendar_schedule if not
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'calendar_week_selection'
                        )
                    """)
                    has_new_table = cursor.fetchone()['exists']
                    
                    if has_new_table:
                        # Use new V2 architecture
                        cursor.execute("""
                            SELECT cws.selected_theme_id, ct.theme_title as theme_name
                            FROM calendar_week_selection cws
                            JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                            WHERE cws.year = %s AND cws.week_number = %s
                        """, (year, week))
                    else:
                        # Fallback to old calendar_schedule
                        cursor.execute("""
                            SELECT cs.theme_id, ct.theme_title as theme_name
                            FROM calendar_schedule cs
                            LEFT JOIN calendar_themes ct ON cs.theme_id = ct.id
                            WHERE cs.year = %s AND cs.week_number = %s
                            AND cs.theme_id IS NOT NULL
                            ORDER BY cs.updated_at DESC
                            LIMIT 1
                        """, (year, week))
                    
                    theme_row = cursor.fetchone()
                    if theme_row:
                        theme_name = theme_row.get('theme_name', '')
                
                cursor.execute("""
                    SELECT expanded_idea FROM post_development WHERE post_id = %s
                """, (target_post_id,))
                dev_row = cursor.fetchone()
                if dev_row:
                    expanded_idea = dev_row.get('expanded_idea', '') or ''
                
                # Get prompt
                cursor.execute("""
                    SELECT prompt_text, system_prompt
                    FROM llm_prompt 
                    WHERE name = 'Header Image Search Prompt (Photo-harvesting)'
                    ORDER BY updated_at DESC LIMIT 1
                """)
                prompt_row = cursor.fetchone()
                if not prompt_row:
                    return jsonify({'error': 'Header Image Search Prompt (Photo-harvesting) not found'}), 404
                
                prompt_text = prompt_row['prompt_text']
                system_prompt = prompt_row['system_prompt']
                
                # Replace placeholders
                prompt_text = prompt_text.replace('[data:theme_name]', theme_name or '')
                prompt_text = prompt_text.replace('[data:expanded_idea]', expanded_idea or '')
                
                # Call LLM
                messages = [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt_text}
                ]
                
                llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                if 'error' in llm_response:
                    return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
                
                search_term = llm_response.get('content', '').strip()
                if not search_term:
                    return jsonify({'error': 'Empty search term generated'}), 500
                
                return jsonify({'success': True, 'search_term': search_term})
                
        except Exception as e:
            logger.error(f"Error generating header search term: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/photo-search/posts/<int:post_id>/header/search', methods=['POST'])
    def header_api_photo_search(post_id: int):
        """Search header images via Pexels/Unsplash and persist results to header/raw JSON.
        Does not require week context for storage; relies on resolved post_id.
        """
        try:
            data = request.get_json() or {}
            search_term = (data.get('search_term') or '').strip()
            provider = data.get('provider', 'both')
            per_page = int(data.get('per_page', 20))
            orientation = data.get('orientation')
            if not search_term:
                return jsonify({'success': False, 'error': 'search_term is required'}), 400

            from utils.photo_apis_adapter import run_photo_search

            pexels_key = os.getenv('PEXELS_API_KEY')
            unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
            if provider == 'pexels' and not pexels_key:
                return jsonify({'success': False, 'error': 'PEXELS_API_KEY is not configured'}), 400
            if provider == 'unsplash' and not unsplash_key:
                return jsonify({'success': False, 'error': 'UNSPLASH_ACCESS_KEY is not configured'}), 400
            if provider == 'both' and (not pexels_key and not unsplash_key):
                return jsonify({'success': False, 'error': 'No photo provider API keys configured (PEXELS_API_KEY / UNSPLASH_ACCESS_KEY)'}), 400

            results = run_photo_search(provider, pexels_key, unsplash_key, search_term, per_page, orientation)

            # Persist to header/raw JSON
            raw_dir = f"static/content/posts/{post_id}/header/raw"
            os.makedirs(raw_dir, exist_ok=True)
            payload = {
                'timestamp': _dt.now().isoformat(),
                'post_id': post_id,
                'search_term': search_term,
                'provider': provider,
                'orientation': orientation,
                'count': len(results),
                'results': results,
            }
            ts_name = _dt.now().strftime('%Y%m%d_%H%M%S')
            with open(f"{raw_dir}/photo_search_results_{ts_name}.json", 'w') as f:
                _json.dump(payload, f, indent=2)
            with open(f"{raw_dir}/photo_search_results_latest.json", 'w') as f:
                _json.dump(payload, f, indent=2)

            return jsonify({'success': True, 'results': results, 'count': len(results), 'orientation': orientation})
        except Exception as e:
            logger.error(f"Header photo search error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/photo-search/posts/<int:post_id>/header/results', methods=['GET'])
    def header_api_photo_results(post_id: int):
        """Load persisted header search results from header/raw JSON (latest)."""
        try:
            latest = f"static/content/posts/{post_id}/header/raw/photo_search_results_latest.json"
            if not os.path.exists(latest):
                return jsonify({'success': True, 'results': [], 'count': 0})
            with open(latest, 'r') as f:
                data = _json.load(f)
            return jsonify({'success': True, 'results': data.get('results', []), 'count': data.get('count', 0)})
        except Exception as e:
            logger.error(f"Header photo results error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/photo-search/posts/<int:post_id>/header/select', methods=['POST'])
    def header_api_photo_select(post_id: int):
        """Select a header photo; persist JSON to header/optimized/selected_{orientation}.json and trigger Unsplash download."""
        try:
            data = request.get_json() or {}
            provider = data.get('provider')
            image_id = data.get('image_id')
            orientation = data.get('orientation')  # 'landscape' or 'portrait'
            if not provider or not image_id:
                return jsonify({'success': False, 'error': 'provider and image_id are required'}), 400
            if orientation and orientation not in ('landscape', 'portrait'):
                return jsonify({'success': False, 'error': 'orientation must be "landscape" or "portrait"'}), 400

            # Load latest results
            latest = f"static/content/posts/{post_id}/header/raw/photo_search_results_latest.json"
            if not os.path.exists(latest):
                return jsonify({'success': False, 'error': 'No search results found'}), 404
            with open(latest, 'r') as f:
                payload = _json.load(f)
            results = payload.get('results', [])

            # Find selected photo
            selected = None
            for p in results:
                if p.get('provider') == provider and str(p.get('image_id')) == str(image_id):
                    selected = p
                    break
            if not selected:
                return jsonify({'success': False, 'error': 'Photo not found in results'}), 404

            # Determine orientation if not provided
            width, height = selected.get('width', 0), selected.get('height', 0)
            if not orientation:
                orientation = 'landscape' if width >= height else 'portrait'

            # Trigger Unsplash download event if needed
            if selected.get('provider') == 'unsplash':
                try:
                    access_key = os.getenv('UNSPLASH_ACCESS_KEY')
                    api = selected.get('api_response') or {}
                    links = api.get('links') or {}
                    download_loc = selected.get('download_location') or links.get('download_location')
                    if access_key and download_loc:
                        parsed = urlparse.urlparse(download_loc)
                        qs = urlparse.parse_qs(parsed.query)
                        url = download_loc if 'client_id' in qs else (download_loc + ('&' if parsed.query else '?') + f"client_id={access_key}")
                        try:
                            urlrequest.urlopen(url, timeout=3)
                        except Exception:
                            pass
                except Exception as _e:
                    logger.warning(f"Unsplash download trigger failed: {_e}")

            # Persist selection
            optimized_dir = f"static/content/posts/{post_id}/header/optimized"
            os.makedirs(optimized_dir, exist_ok=True)
            record = {
                'post_id': post_id,
                'orientation': orientation,
                'photo': selected,
            }
            with open(f"{optimized_dir}/selected_{orientation}.json", 'w') as f:
                _json.dump(record, f, indent=2)

            return jsonify({'success': True, 'selected_photo': selected, 'orientation': orientation})
        except Exception as e:
            logger.error(f"Header photo select error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/photo-search/posts/<int:post_id>/header/selected', methods=['GET'])
    def header_api_photo_selected(post_id: int):
        """Return selected header photos for both orientations if present."""
        try:
            optimized_dir = f"static/content/posts/{post_id}/header/optimized"
            out = {'landscape': None, 'portrait': None}
            for ori in ('landscape', 'portrait'):
                path = f"{optimized_dir}/selected_{ori}.json"
                if os.path.exists(path):
                    try:
                        with open(path, 'r') as f:
                            out[ori] = _json.load(f)
                    except Exception:
                        pass
            return jsonify({'success': True, 'selected_landscape': out['landscape'], 'selected_portrait': out['portrait']})
        except Exception as e:
            logger.error(f"Header photo selected error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

