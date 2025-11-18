"""
Authoring API - Image Prompts

Handles image prompt generation using proper system prompts.
Keeps file size under 300 lines as per user requirements.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from modules.llm_service import llm_service
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('authoring_prompts', __name__, url_prefix='/authoring')


def apply_model_aware_substitutions(text, max_chars):
    """
    Apply model-aware character limit substitutions to prompt text.
    Mirrors frontend llm-prompts-panel.js applyModelAwareSubstitutions().
    """
    if not text or not max_chars:
        return text
    
    import re
    
    t = str(text)
    
    # Replace common range caps like "380–400 characters" or "380-400 characters"
    t = re.sub(r'\b\d{2,4}\s*[–-]\s*\d{2,4}\s*characters?', 
               f'up to {max_chars} characters', t, flags=re.IGNORECASE)
    
    # Replace phrases like "exceeds 400 characters"
    t = re.sub(r'exceeds\s+\d{2,4}\s*characters?', 
               f'exceeds {max_chars} characters', t, flags=re.IGNORECASE)
    
    # Replace "≤ 400" or "<= 400"
    t = re.sub(r'(?:≤|<=)\s*\d{2,4}\b', 
               f'≤ {max_chars}', t, flags=re.IGNORECASE)
    
    # Replace solitary "400 characters" with "{max} characters" for typical caps (<= 1000)
    def replace_char_limit(match):
        num = int(match.group(1))
        return f'{max_chars} characters' if num <= 1000 else match.group(0)
    
    t = re.sub(r'\b(\d{2,4})\s*characters\b', replace_char_limit, t, flags=re.IGNORECASE)
    
    return t


def handle_exact_request(data):
    """Handle request using exact stored messages from Complete LLM Input field"""
    try:
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        exact_messages = data.get('exact_messages')
        exact_model = data.get('exact_model')
        exact_options = data.get('exact_options')
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
            
        if not exact_messages:
            return jsonify({'error': 'Missing exact_messages'}), 400
        
        logger.info(f"[DEBUG] Using exact stored messages for post_id={post_id}, section_id={section_id}")
        
        # Create intercept context
        intercept_context = {
            'post_id': post_id,
            'section_id': section_id
        }
        
        # Determine provider from model
        provider = 'ollama' if 'llama' in exact_model.lower() else 'openai'
        
        # Execute LLM request with exact stored messages
        result = llm_service.execute_llm_request(
            provider=provider,
            model=exact_model,
            messages=exact_messages,
            intercept_context=intercept_context
        )
        
        logger.info(f"[DEBUG] LLM result: {result}")
        
        if result:
            # The result contains the response content directly
            response_content = result.get('content', '') or result.get('response', '')
            logger.info(f"[DEBUG] LLM response content: {response_content[:200]}...")
            
            # Try to extract JSON from response
            try:
                import re
                json_match = re.search(r'\{[^}]*"image_prompt"[^}]*\}', response_content)
                if json_match:
                    import json
                    response_json = json.loads(json_match.group())
                    image_prompt = response_json.get('image_prompt', response_content)
                else:
                    image_prompt = response_content
            except Exception as e:
                logger.error(f"[DEBUG] JSON parsing error: {e}")
                image_prompt = response_content
            
            return jsonify({
                'success': True,
                'image_prompt': image_prompt,
                'message': 'Image prompt generated using exact stored messages',
                'actual_llm_messages': exact_messages,
                'character_limit': 2000,
                'compression_used': False,
                'expansion_used': False,
                'final_length': len(image_prompt)
            })
        else:
            logger.error(f"[DEBUG] LLM request failed: {result}")
            return jsonify({'error': 'LLM request failed'}), 500
            
    except Exception as e:
        logger.error(f"Error handling exact request: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/generate-image-prompt-from-builder-v2', methods=['POST'])
def api_generate_image_prompt_from_builder():
    """Generate image prompt using the compiled prompt from Prompt Builder"""
    try:
        data = request.get_json()
        
        # Check if we're using exact stored messages
        use_exact_request = data.get('use_exact_request', False)
        if use_exact_request:
            return handle_exact_request(data)
        
        compiled_prompt = data.get('compiled_prompt')
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        
        # CRITICAL: Check for week context in request data or URL params
        url_year = request.args.get('year', type=int) or data.get('year')
        url_week = request.args.get('week', type=int) or data.get('week')
        logger.info(f"[IMAGE_PROMPTS] Week context from request: year={url_year}, week={url_week}")
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"[IMAGE_PROMPTS] Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"[IMAGE_PROMPTS] Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        else:
            logger.warning(f"[IMAGE_PROMPTS] No week context provided - using URL post_id {post_id}")
        
        logger.info(f"[IMAGE_PROMPTS] Using target_post_id={target_post_id} for generation")
        
        # Get concept data from frontend
        concept_content = data.get('concept_content')
        selected_concept = data.get('selected_concept')
        logger.info(f"[IMAGE_PROMPTS] Frontend sent: section_id={section_id}, selected_concept={selected_concept}, has_concept_content={bool(concept_content)}")
        
        # Get user preferences for compression/expansion
        enable_compression = data.get('enable_compression', True)
        enable_expansion = data.get('enable_expansion', False)
        
        llm_provider = data.get('llm_provider', 'Ollama')
        llm_model = data.get('llm_model', 'llama3.2:latest')
        
        # Track all LLM calls for transparency
        pipeline_steps = []
        
        logger.info(f"[DEBUG] API received: post_id={post_id}, section_id={section_id}, target_post_id={target_post_id}")
        logger.info(f"[DEBUG] Compiled prompt: {compiled_prompt[:100] if compiled_prompt else 'None'}...")
        
        if not compiled_prompt:
            return jsonify({'error': 'Missing compiled_prompt'}), 400
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
        
        # Get section data from post_section table
        with db_manager.get_cursor() as cursor:
            # Topics are currently not used in this endpoint
            topics = []
            # Photo-harvesting has been archived - only LLM-creation is used
            illustration_method = 'LLM-creation'
            logger.info(f"[IMAGE_PROMPTS] Using LLM-creation method (Photo-harvesting archived)")
            
            # Get post data for context - use target_post_id for lookup
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, p.summary
                FROM post p
                WHERE p.id = %s
            """, (target_post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get imaging model selection and character limit - use target_post_id
            cursor.execute("""
                SELECT imaging_model_selection
                FROM post_development
                WHERE post_id = %s
            """, (target_post_id,))
            
            imaging_model_row = cursor.fetchone()
            imaging_model_key = imaging_model_row['imaging_model_selection'] if imaging_model_row else 'sdxl-lora'
            
            # Get model specs for character limit
            cursor.execute("""
                SELECT api_params
                FROM llm_model
                WHERE name = %s
            """, (imaging_model_key,))
            
            model_spec_row = cursor.fetchone()
            max_chars = None
            if model_spec_row and model_spec_row['api_params']:
                api_params = model_spec_row['api_params']
                if isinstance(api_params, dict):
                    max_chars = api_params.get('max_prompt_chars')
                elif isinstance(api_params, str):
                    api_params_dict = json.loads(api_params)
                    max_chars = api_params_dict.get('max_prompt_chars')
            
            logger.info(f"[DEBUG] Imaging model: {imaging_model_key}, max_chars: {max_chars}")
            
            # Get section data - use target_post_id for lookup
            # CRITICAL: Handle section_id matching - try id first, then section_order
            logger.info(f"[IMAGE_PROMPTS] Looking up section: post_id={target_post_id}, section_id={section_id}")
            
            section = None
            # First try direct ID match (if section_id is numeric)
            # Convert section_id to string for isdigit() check
            section_id_str = str(section_id)
            if section_id_str.isdigit():
                cursor.execute("""
                    SELECT id, section_order, section_heading, section_description, 
                           status, draft, polished, ideas_to_include, facts_to_include,
                           highlighting, image_concepts, image_prompts, image_captions,
                           image_alt_text, selected_image_concept
                    FROM post_section
                    WHERE post_id = %s AND id = %s
                """, (target_post_id, int(section_id_str)))
                section = cursor.fetchone()
            
            # If not found by ID, try by section_order (section_id might be order-based)
            if not section and section_id_str.isdigit():
                cursor.execute("""
                    SELECT id, section_order, section_heading, section_description, 
                           status, draft, polished, ideas_to_include, facts_to_include,
                           highlighting, image_concepts, image_prompts, image_captions,
                           image_alt_text, selected_image_concept
                    FROM post_section
                    WHERE post_id = %s AND section_order = %s
                """, (target_post_id, int(section_id_str)))
                section = cursor.fetchone()
            
            # If still not found, try matching via post_development.sections
            if not section:
                cursor.execute("""
                    SELECT sections FROM post_development 
                    WHERE post_id = %s AND sections IS NOT NULL
                """, (target_post_id,))
                result = cursor.fetchone()
                
                if result and result['sections']:
                    try:
                        sections_data = json.loads(result['sections']) if isinstance(result['sections'], str) else result['sections']
                        if isinstance(sections_data, dict) and 'sections' in sections_data:
                            sections_list = sections_data['sections']
                        elif isinstance(sections_data, list):
                            sections_list = sections_data
                        else:
                            sections_list = []
                        
                        # Find the section by ID with improved matching
                        for i, section_data in enumerate(sections_list):
                            section_id_from_data = section_data.get('id', f'section_{i+1}')
                            section_order_from_data = section_data.get('order', i+1)
                            
                            # Try multiple matching strategies
                            section_matches = False
                            if str(section_id_from_data) == section_id_str:
                                section_matches = True
                            elif section_id_str.isdigit() and int(section_order_from_data) == int(section_id_str):
                                section_matches = True
                            
                            if section_matches:
                                logger.info(f"[IMAGE_PROMPTS] Matched section from post_development: id={section_id_from_data}, order={section_order_from_data}")
                                section_order = section_order_from_data
                                
                                # Get section from post_section using section_order
                                cursor.execute("""
                                    SELECT id, section_order, section_heading, section_description, 
                                           status, draft, polished, ideas_to_include, facts_to_include,
                                           highlighting, image_concepts, image_prompts, image_captions,
                                           image_alt_text, selected_image_concept
                                    FROM post_section
                                    WHERE post_id = %s AND section_order = %s
                                """, (target_post_id, section_order))
                                section = cursor.fetchone()
                                break
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")
            
            if not section:
                logger.error(f"[IMAGE_PROMPTS] Section not found: post_id={target_post_id}, section_id={section_id_str}")
                return jsonify({'error': f'Section {section_id_str} not found for post {target_post_id}'}), 404
            
            logger.info(f"[IMAGE_PROMPTS] Found section: id={section.get('id')}, order={section.get('section_order')}, heading='{section.get('section_heading', '')[:50]}'")
            logger.info(f"[IMAGE_PROMPTS] Section selected_image_concept from DB: {section.get('selected_image_concept')}")
            
            # Get active image style
            active_style = None
            cursor.execute("""
                SELECT extra_settings
                FROM post
                WHERE id = %s
            """, (target_post_id,))
            post_row = cursor.fetchone()
            
            if post_row and post_row['extra_settings']:
                extra_settings = post_row['extra_settings']
                if isinstance(extra_settings, str):
                    extra_settings = json.loads(extra_settings)
                
                imaging = extra_settings.get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]

            # If still no active style, use taxonomy default or system default (do NOT persist)
            if not active_style:
                # Try to get default style from taxonomy first
                from utils.taxonomy_helpers import get_default_image_style
                taxonomy_style = get_default_image_style(target_post_id)
                
                if taxonomy_style:
                    active_style = taxonomy_style
                    logger.info(f"[DEBUG] Using taxonomy default image style: {active_style.get('name', 'Unknown')}")
                else:
                    # Fallback to permanent system default (Watercolour and Pen & Ink)
                    active_style = {
                        'name': 'Watercolour and Pen & Ink',
                        'style_json': {
                            'medium': 'watercolour and pen and ink',
                            'technique': 'brushstrokes fading out by ending towards the edges of the image',
                            'palette': ['ochres', 'siennas', 'umbers', 'celestial blues', 'golds'],
                            'composition': 'rule-of-thirds with negative space',
                            'lighting': 'soft, ethereal, golden hour',
                            'constraints': ['no text', 'no watermark in frame', 'edges fade to white'],
                            'negatives': ['hyperrealism', 'sharp edges', 'solid borders']
                        }
                    }
                    logger.info(f"[DEBUG] Using system default image style (no taxonomy default found)")
            
            logger.info(f"[DEBUG] Active style: {active_style['name'] if active_style else 'None'}")
            
            # Set topics to empty for now (topic allocation system removed)
            topics = []
            
            # Get the user-configured image prompts prompt
            prompt_name = 'Image Prompts Generation'
            logger.info(f"[IMAGE_PROMPTS] Using prompt: {prompt_name}")
            
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            
            prompt_data = cursor.fetchone()

            if not prompt_data:
                return jsonify({'error': f'User-configured Image Prompts prompt "{prompt_name}" not found. Please configure prompts in the LLM Prompts panel first.'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Apply model-aware substitutions if we have character limit
            if max_chars:
                prompt_text = apply_model_aware_substitutions(prompt_text, max_chars)
                system_prompt = apply_model_aware_substitutions(system_prompt, max_chars)
                logger.info(f"[DEBUG] Applied model-aware substitutions for {imaging_model_key} (max: {max_chars} chars)")
            
            logger.info(f"[DEBUG] System prompt length: {len(system_prompt) if system_prompt else 0}")
            logger.info(f"[DEBUG] System prompt preview: {system_prompt[:100] if system_prompt else 'None'}")
            logger.info(f"[DEBUG] *** SYSTEM PROMPT DEBUG ***")
            
            # Theme data not needed for simple LLM-creation
            theme_data = ''
            # Remove theme_data placeholder if present
            if '{theme_data}' in prompt_text or '[data:theme_data]' in prompt_text:
                # Get theme name and expanded idea from week context (same logic as header.py)
                url_year = request.args.get('year', type=int)
                url_week = request.args.get('week', type=int)
                if not url_year or not url_week:
                    # Try from request JSON body
                    data_json = request.get_json() if request.is_json else {}
                    url_year = url_year or data_json.get('year')
                    url_week = url_week or data_json.get('week')
                
                if url_year and url_week:
                    # Resolve post for week
                    from utils.week_post_resolver import resolve_post_for_week
                    resolved_post_id = resolve_post_for_week(url_year, url_week)
                    
                    if resolved_post_id:
                        # Check if calendar_week_selection table exists before querying
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = 'calendar_week_selection'
                            ) as table_exists
                        """)
                        table_check = cursor.fetchone()
                        has_table = table_check.get('table_exists', False) if table_check else False
                        
                        theme_name = None
                        if has_table:
                            # Get selected theme for this week
                            cursor.execute("""
                                SELECT ct.theme_title
                                FROM calendar_week_selection cws
                                JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                                WHERE cws.year = %s AND cws.week_number = %s
                            """, (url_year, url_week))
                            theme_result = cursor.fetchone()
                            theme_name = theme_result.get('theme_title') if theme_result else None
                        
                        # Get expanded idea from post_development
                        cursor.execute("""
                            SELECT expanded_idea
                            FROM post_development
                            WHERE post_id = %s
                        """, (resolved_post_id,))
                        idea_result = cursor.fetchone()
                        expanded_idea = idea_result.get('expanded_idea') if idea_result else None
                        
                        # Build theme_data string
                        if theme_name and expanded_idea:
                            theme_data = f"{theme_name}: {expanded_idea}"
                        elif theme_name:
                            theme_data = theme_name
                        elif expanded_idea:
                            theme_data = expanded_idea
                        
                        logger.info(f"[IMAGE_PROMPTS] Retrieved theme_data: {theme_data[:100] if theme_data else 'None'}")
                    else:
                        logger.warning(f"[IMAGE_PROMPTS] No post found for week {url_year}/{url_week}, cannot retrieve theme_data")
            
            # Replace placeholders with actual data
            logger.info(f"[IMAGE_PROMPTS] Building prompt with section data:")
            logger.info(f"  - section_id: {section_id}")
            logger.info(f"  - section.id: {section.get('id')}")
            logger.info(f"  - section.section_heading: '{section.get('section_heading')}'")
            
            # Remove theme_data placeholder if present (not needed for simple LLM-creation)
            prompt_text = prompt_text.replace('{theme_data}', '')
            prompt_text = prompt_text.replace('[data:theme_data]', '')
            
            # Replace simple placeholders (not needed for concept-based generation, but keep for template compatibility)
            prompt_text = prompt_text.replace('[data:idea_seed]', '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', '')
            prompt_text = prompt_text.replace('[data:title]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:section_text]', '')
            
            # Automatically extract concept data from database - CRITICAL: Must get correct section's concept
            concept_text = ''
            
            # Get image_concepts - first try post_section, then fallback to post_development.sections
            image_concepts_data = None
            selected_concept_id = section.get('selected_image_concept')
            logger.info(f"[IMAGE_PROMPTS] Initial selected_concept_id from section.get('selected_image_concept'): {selected_concept_id}")
            
            if section['image_concepts']:
                # Use image_concepts from post_section table
                try:
                    image_concepts_data = json.loads(section['image_concepts']) if isinstance(section['image_concepts'], str) else section['image_concepts']
                except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Error parsing image_concepts from post_section for section {section_id}: {e}")
            
            # NO FALLBACKS - if image_concepts is missing from post_section, fail explicitly
            if not image_concepts_data:
                logger.error(f"[IMAGE_PROMPTS] ERROR: No image_concepts found in post_section for section {section_id}. Cannot generate prompt without concepts.")
            
            # Extract concept text from the found image_concepts data
            logger.info(f"[IMAGE_PROMPTS] Extracting concept: selected_concept_id={selected_concept_id}, has_concepts_data={bool(image_concepts_data)}")
            
            if not selected_concept_id:
                logger.error(f"[IMAGE_PROMPTS] ERROR: selected_concept_id is None/empty for section {section_id}. Section had: {section.get('selected_image_concept')}")
                return jsonify({'error': f'No selected_image_concept found for section {section_id}'}), 400
            
            if image_concepts_data and selected_concept_id:
                try:
                    if isinstance(image_concepts_data, dict):
                        concepts = image_concepts_data.get('concepts', [])
                        logger.info(f"[IMAGE_PROMPTS] Found {len(concepts)} concepts, looking for concept_id={selected_concept_id}")
                        logger.info(f"[IMAGE_PROMPTS] Available concept_ids: {[c.get('concept_id') for c in concepts]}")
                        
                        for concept in concepts:
                            concept_id = concept.get('concept_id')
                            logger.info(f"[IMAGE_PROMPTS] Comparing: concept_id='{concept_id}' (type: {type(concept_id).__name__}) == selected_concept_id='{selected_concept_id}' (type: {type(selected_concept_id).__name__}) -> {str(concept_id) == str(selected_concept_id)}")
                            if str(concept_id) == str(selected_concept_id):
                                # Build concept text from the selected concept
                                concept_parts = []
                                if concept.get('concept_description'):
                                    concept_parts.append(concept['concept_description'])
                                if concept.get('concept_mood'):
                                    concept_parts.append(f"Mood: {concept['concept_mood']}")
                                if concept.get('key_visual_elements'):
                                    concept_parts.append(f"Key Elements: {concept['key_visual_elements']}")
                                concept_text = '\n'.join(concept_parts)
                                logger.info(f"[IMAGE_PROMPTS] Extracted concept_text from database (concept_id={concept_id}, method={illustration_method}): {concept_text[:100]}...")
                                break
                        else:
                            logger.warning(f"[IMAGE_PROMPTS] Could not find concept with id={selected_concept_id} in {len(concepts)} concepts")
                except (KeyError, TypeError) as e:
                    logger.warning(f"Error extracting concept from image_concepts_data for section {section_id}: {e}")
            
            # NO FALLBACKS - if database extraction failed, return error
            if not concept_text:
                logger.error(f"[IMAGE_PROMPTS] ERROR: Failed to extract concept_text from database for section {section_id}. selected_concept_id={selected_concept_id}, has_concepts_data={bool(image_concepts_data)}")
                return jsonify({'error': f'Failed to extract concept from database for section {section_id}. Please ensure image_concepts and selected_image_concept are set in the database.'}), 400
            
            
            logger.info(f"[IMAGE_PROMPTS] Final concept_text (length {len(concept_text)}): {concept_text[:200] if concept_text else 'EMPTY'}...")
            prompt_text = prompt_text.replace('[data:selected_concept]', concept_text)
            topics_text = '\n'.join([f'- {topic}' for topic in topics])
            prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
            # Add style information to prompt
            style_text = ""
            if active_style:
                style_name = active_style.get('name', '')
                style_json = active_style.get('style_json', {})
                
                # Format style information
                style_parts = []
                if style_name:
                    style_parts.append(f"Style: {style_name}")
                
                if style_json:
                    # Add key style elements
                    if style_json.get('medium'):
                        style_parts.append(f"Medium: {style_json['medium']}")
                    if style_json.get('technique'):
                        style_parts.append(f"Technique: {style_json['technique']}")
                    if style_json.get('palette'):
                        palette = ', '.join(style_json['palette'])
                        style_parts.append(f"Color Palette: {palette}")
                    if style_json.get('constraints'):
                        constraints = ', '.join(style_json['constraints'])
                        style_parts.append(f"Constraints: {constraints}")
                    if style_json.get('negatives'):
                        negatives = ', '.join(style_json['negatives'])
                        style_parts.append(f"Avoid: {negatives}")
                
                style_text = '\n'.join(style_parts)
                logger.info(f"[DEBUG] Style text: {style_text}")
            
            # Replace [data:style] placeholder with actual style information
            if '[data:style]' in prompt_text:
                prompt_text = prompt_text.replace('[data:style]', style_text if style_text else '')
            elif style_text:
                # If placeholder not found, append style information to prompt
                prompt_text += f"\n\nStyle Guidelines:\n{style_text}"
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
                logger.info(f"[DEBUG] Added system message: {len(system_prompt)} chars")
            else:
                logger.info(f"[DEBUG] No system prompt to add")
            messages.append({'role': 'user', 'content': prompt_text})
            
            logger.info(f"[DEBUG] Messages prepared: {len(messages)} messages")
            logger.info(f"[DEBUG] System message included: {any(m['role'] == 'system' for m in messages)}")
            logger.info(f"[DEBUG] First message role: {messages[0]['role'] if messages else 'None'}")
            
            # Log the final prompt being sent to LLM
            logger.info(f"[IMAGE_PROMPTS] Final prompt text (first 500 chars): {prompt_text[:500]}")
            
            # Execute LLM request with retry logic for valid JSON
            max_retries = 3
            generated_prompt = None
            
            for attempt in range(max_retries):
                # Add intercept context for message capture - use target_post_id
                intercept_context = {
                    'post_id': target_post_id,
                    'section_id': section_id
                }
                result = llm_service.execute_llm_request(llm_provider.lower(), llm_model, messages, intercept_context=intercept_context)
                
                if 'error' in result:
                    if attempt == max_retries - 1:  # Last attempt
                        return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
                    continue
                
                raw_content = result['content']
                
                # Log the generated prompt
                logger.info(f"[IMAGE_PROMPTS] Generated prompt (raw, first 200 chars): {raw_content[:200]}")
                
                # Try to parse as JSON first
                try:
                    parsed_json = json.loads(raw_content)
                    if 'image_prompt' in parsed_json:
                        generated_prompt = parsed_json['image_prompt']
                        break
                except json.JSONDecodeError:
                    pass
                
                # If not JSON, use the raw content
                generated_prompt = raw_content.strip()
                break
            
            if not generated_prompt:
                return jsonify({'error': 'Failed to generate prompt after retries'}), 500
            
            # Prepend Selected Idea (theme name) to the generated prompt
            # Use theme_name that was already retrieved earlier (from theme_data processing)
            selected_idea = None
            if url_year and url_week:
                # Check if calendar_week_selection table exists before querying
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_selection'
                    ) as table_exists
                """)
                table_check = cursor.fetchone()
                has_table = table_check.get('table_exists', False) if table_check else False
                
                if has_table:
                    # Get theme name from calendar_week_selection (reuse logic from theme_data section)
                    cursor.execute("""
                        SELECT ct.theme_title
                        FROM calendar_week_selection cws
                        JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                        WHERE cws.year = %s AND cws.week_number = %s
                    """, (url_year, url_week))
                    theme_result = cursor.fetchone()
                    if theme_result:
                        selected_idea = theme_result.get('theme_title')
            
            # If no theme from week context, try to get from post title
            if not selected_idea:
                if post_data and post_data.get('title'):
                    selected_idea = post_data['title']
            
            # Prepend Selected Idea if available
            if selected_idea:
                generated_prompt = f"{selected_idea}: {generated_prompt}"
                logger.info(f"[IMAGE_PROMPTS] Prepended Selected Idea '{selected_idea}' to generated prompt")
            
            # Log the generation step
            pipeline_steps.append({
                'step': 'initial_generation',
                'input': prompt_text,
                'output': generated_prompt,
                'llm_call': {'provider': llm_provider, 'model': llm_model, 'messages': messages, 'system_prompt': system_prompt}
            })
            
            # Get model-specific character limit first
            imaging_limit = 2000  # Default for GPT-Image-1
            if 'sdxl' in llm_model.lower():
                imaging_limit = 400
            
            # Apply compression if enabled and needed (only for SDXL models)
            compression_used = False
            if enable_compression and 'sdxl' in llm_model.lower() and len(generated_prompt) > imaging_limit:
                # Simple compression - truncate to model's character limit (SDXL only)
                generated_prompt = generated_prompt[:imaging_limit].rsplit(' ', 1)[0] + '.'
                compression_used = True
                
                pipeline_steps.append({
                    'step': 'compression',
                    'input': generated_prompt,
                    'output': generated_prompt,
                    'llm_call': None
                })
            
            # Apply expansion if enabled and needed
            expansion_used = False
            if enable_expansion and len(generated_prompt) < 200:
                # Simple expansion - add descriptive details
                expanded_prompt = f"{generated_prompt} The scene features rich atmospheric details, intricate textures, and dramatic lighting that creates a sense of depth and mystery."
                if len(expanded_prompt) <= 400:
                    generated_prompt = expanded_prompt
                    expansion_used = True
                    
                    pipeline_steps.append({
                        'step': 'expansion',
                        'input': generated_prompt,
                        'output': generated_prompt,
                        'llm_call': None
                    })
            
            # imaging_limit already calculated above
            
            # Append style name to the final generated prompt (for display and use)
            final_prompt_with_style = generated_prompt
            if illustration_method != 'Photo-harvesting' and active_style:
                style_name = active_style.get('name', '')
                if style_name:
                    final_prompt_with_style = f"{generated_prompt}, style: {style_name}"
                    logger.info(f"[IMAGE_PROMPTS] Appended style '{style_name}' to final prompt")
            
            # Save to database (save the version WITH style for consistency)
            try:
                # Update the post_section table with the generated prompt
                image_prompts_json = json.dumps({
                    'image_prompt': final_prompt_with_style,
                    'base_concept': compiled_prompt
                })
                
                cursor.execute("""
                    UPDATE post_section 
                    SET image_prompts = %s 
                    WHERE post_id = %s AND id = %s
                """, (image_prompts_json, target_post_id, section_id))
                    
            except Exception as e:
                logger.error(f"Error updating post_section for image prompts: {e}")
                return jsonify({'error': 'Failed to update section data'}), 500
            
            cursor.connection.commit()
            
            logger.info(f"[DEBUG] Generated prompt: {final_prompt_with_style[:100]}...")
            logger.info(f"[DEBUG] Saved to database for post {post_id}, section {section_id}")
            
            # Return detailed pipeline information (return the version WITH style)
            return jsonify({
                'success': True,
                'image_prompt': final_prompt_with_style,
                'message': 'Image prompt generated and saved successfully',
                'pipeline_steps': pipeline_steps,
                'final_length': len(final_prompt_with_style),
                'character_limit': imaging_limit,
                'compression_used': compression_used,
                'expansion_used': expansion_used,
                'actual_llm_messages': messages  # NEW: Return the actual messages sent to LLM
            })
            
    except Exception as e:
        logger.error(f"Error generating image prompt: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/sections/<section_id>/llm-prompt-details', methods=['GET'])
def api_get_llm_prompt_details(post_id, section_id):
    """Get the actual system prompt and user prompt that will be sent to the LLM.
    IMPORTANT: Uses week context to resolve the correct post (no fallbacks) and selects
    the correct prompt based on illustration_method. Excludes style for Photo-harvesting.
    """
    try:
        # Resolve target_post_id from week context if provided
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"[LLM_PROMPT_DETAILS] Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"[LLM_PROMPT_DETAILS] Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")

        with db_manager.get_cursor() as cursor:
            # Use utility function to get illustration_method
            from utils.taxonomy_helpers import get_illustration_method
            illustration_method = get_illustration_method(target_post_id)
            
            # Get post data
            cursor.execute("""
                SELECT p.title, p.subtitle, p.summary
                FROM post p
                WHERE p.id = %s
            """, (target_post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get imaging model selection and character limit (use target_post_id)
            cursor.execute("""
                SELECT imaging_model_selection
                FROM post_development
                WHERE post_id = %s
            """, (target_post_id,))
            imaging_model_row = cursor.fetchone()
            imaging_model_key = imaging_model_row['imaging_model_selection'] if imaging_model_row else 'sdxl-lora'
            
            cursor.execute("""
                SELECT api_params
                FROM llm_model
                WHERE name = %s
            """, (imaging_model_key,))
            model_spec_row = cursor.fetchone()
            max_chars = None
            if model_spec_row and model_spec_row['api_params']:
                api_params = model_spec_row['api_params']
                if isinstance(api_params, dict):
                    max_chars = api_params.get('max_prompt_chars')
                elif isinstance(api_params, str):
                    api_params_dict = json.loads(api_params)
                    max_chars = api_params_dict.get('max_prompt_chars')
            
            # Get section data using target_post_id
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (target_post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Active style only for LLM-creation
            active_style = None
            if illustration_method != 'Photo-harvesting':
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (target_post_id,))
                post_row = cursor.fetchone()
                if post_row and post_row.get('extra_settings'):
                    extra_settings = post_row['extra_settings']
                    if isinstance(extra_settings, str):
                        extra_settings = json.loads(extra_settings)
                    imaging = extra_settings.get('imaging', {})
                    styles = imaging.get('styles', [])
                    active_index = imaging.get('activeIndex', 0)
                    if styles and 0 <= active_index < len(styles):
                        active_style = styles[active_index]
            
            # Prompt selection based on illustration_method (no fallbacks)
            prompt_name = 'Image Prompts Generation (Photo-harvesting)' if illustration_method == 'Photo-harvesting' else 'Image Prompts Generation'
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': f'Image Prompts prompt "{prompt_name}" not found'}), 404
            
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Apply model-aware substitutions if we have character limit
            if max_chars:
                prompt_text = apply_model_aware_substitutions(prompt_text, max_chars)
                system_prompt = apply_model_aware_substitutions(system_prompt, max_chars)
                logger.info(f"[DEBUG] Applied model-aware substitutions for {imaging_model_key} (max: {max_chars} chars)")
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:idea_seed]', post_data['title'] or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['subtitle'] or '')
            prompt_text = prompt_text.replace('[data:title]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:section_text]', section.get('polished') or section.get('draft') or '')
            
            # Get the selected concept for [data:selected_concept]
            # First try post_section, then fallback to post_development.sections
            # Selected concept handling
            selected_concept = ""
            if illustration_method == 'Photo-harvesting':
                # Only accept the selected concept from post_section.image_concepts
                if not section.get('image_concepts') or not section.get('selected_image_concept'):
                    return jsonify({'error': 'No selected image concept for this section. Generate concepts on the image_concepts step and select one first.'}), 400
                try:
                    concepts_data = section['image_concepts']
                    if isinstance(concepts_data, str):
                        concepts_data = json.loads(concepts_data)
                    selected_id = section['selected_image_concept']
                    if isinstance(concepts_data, dict) and 'concepts' in concepts_data:
                        for c in concepts_data['concepts']:
                            if c.get('concept_id') == selected_id:
                                # Build concise concept text for search
                                parts = []
                                if c.get('concept_description'):
                                    parts.append(c['concept_description'])
                                if c.get('concept_mood'):
                                    parts.append(f"Mood: {c['concept_mood']}")
                                if c.get('key_visual_elements'):
                                    parts.append(f"Key Elements: {c['key_visual_elements']}")
                                selected_concept = '\n'.join(parts)
                                break
                    if not selected_concept:
                        return jsonify({'error': 'Selected image concept could not be found. Re-select the concept.'}), 400
                except Exception as e:
                    logger.error(f"[LLM_PROMPT_DETAILS] Error parsing image concepts: {e}")
                    return jsonify({'error': 'Invalid image concepts data'}), 500
            else:
                image_concepts_data = None
                selected_concept_id = section.get('selected_image_concept', 'CONCEPT-1')
                if section.get('image_concepts'):
                    try:
                        image_concepts_data = json.loads(section['image_concepts']) if isinstance(section['image_concepts'], str) else section['image_concepts']
                    except (json.JSONDecodeError, TypeError):
                        pass
                if not image_concepts_data:
                    cursor.execute("""
                        SELECT sections FROM post_development WHERE post_id = %s
                    """, (target_post_id,))
                    dev_result = cursor.fetchone()
                    if dev_result and dev_result.get('sections'):
                        try:
                            dev_sections_data = json.loads(dev_result['sections']) if isinstance(dev_result['sections'], str) else dev_result['sections']
                            if isinstance(dev_sections_data, dict) and 'sections' in dev_sections_data:
                                dev_sections_list = dev_sections_data['sections']
                            elif isinstance(dev_sections_data, list):
                                dev_sections_list = dev_sections_data
                            else:
                                dev_sections_list = []
                            for dev_section in dev_sections_list:
                                if str(dev_section.get('id', '')) == str(section_id):
                                    dev_image_concepts = dev_section.get('image_concepts')
                                    if dev_image_concepts:
                                        try:
                                            image_concepts_data = json.loads(dev_image_concepts) if isinstance(dev_image_concepts, str) else dev_image_concepts
                                            if not selected_concept_id or selected_concept_id == 'CONCEPT-1':
                                                selected_concept_id = dev_section.get('selected_image_concept', 'CONCEPT-1')
                                            break
                                        except (json.JSONDecodeError, TypeError):
                                            pass
                        except (json.JSONDecodeError, TypeError, KeyError):
                            pass
                if image_concepts_data:
                    try:
                        if isinstance(image_concepts_data, dict) and 'concepts' in image_concepts_data:
                            concepts = image_concepts_data['concepts']
                            for concept in concepts:
                                if concept.get('concept_id') == selected_concept_id:
                                    selected_concept = concept.get('concept_description', '')
                                    break
                    except (KeyError, TypeError):
                        pass
            
            prompt_text = prompt_text.replace('[data:selected_concept]', selected_concept)
            # Topics currently unused; keep empty string for compatibility
            topics_text = ''
            prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
            # Add style information to prompt (LLM-creation only)
            style_text = ""
            if active_style and illustration_method != 'Photo-harvesting':
                style_name = active_style.get('name', '')
                style_json = active_style.get('style_json', {})
                
                # Format style information
                style_parts = []
                if style_name:
                    style_parts.append(f"Style: {style_name}")
                
                if style_json:
                    # Add key style elements
                    if style_json.get('medium'):
                        style_parts.append(f"Medium: {style_json['medium']}")
                    if style_json.get('technique'):
                        style_parts.append(f"Technique: {style_json['technique']}")
                    if style_json.get('palette'):
                        palette = ', '.join(style_json['palette'])
                        style_parts.append(f"Color Palette: {palette}")
                    if style_json.get('constraints'):
                        constraints = ', '.join(style_json['constraints'])
                        style_parts.append(f"Constraints: {constraints}")
                    if style_json.get('negatives'):
                        negatives = ', '.join(style_json['negatives'])
                        style_parts.append(f"Avoid: {negatives}")
                
                style_text = '\n'.join(style_parts)
                logger.info(f"[DEBUG] Style text: {style_text}")
            
            # Replace [data:style] placeholder with actual style information
            if '[data:style]' in prompt_text:
                if style_text:
                    prompt_text = prompt_text.replace('[data:style]', style_text)
                else:
                    # For Photo-harvesting, remove the placeholder completely
                    prompt_text = prompt_text.replace('[data:style]', '')
            else:
                # If placeholder not found, append style information only for LLM-creation
                if style_text and illustration_method != 'Photo-harvesting':
                    prompt_text += f"\n\nStyle Guidelines:\n{style_text}"
            
            # Get active style details
            style_details = "No style information available"
            cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (target_post_id,))
            post_row = cursor.fetchone()
            if post_row and post_row.get('extra_settings'):
                imaging = post_row['extra_settings'].get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]
                    style_json = active_style.get('style_json', {})
                    if style_json:
                        style_details = json.dumps(style_json, indent=2)
            
            # Ensure topics is defined in this scope
            if 'topics' not in locals():
                topics = []
            
            return jsonify({
                'success': True,
                'system_prompt': system_prompt,
                'user_prompt': prompt_text,
                'style_details': style_details,
                'selected_concept': selected_concept,
                'topics': topics
            })
            
    except Exception as e:
        logger.error(f"Error getting LLM prompt details: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/save-image-prompt', methods=['POST'])
def api_save_image_prompt(post_id, section_id):
    """Save image prompt for a section"""
    try:
        data = request.get_json()
        image_prompt = data.get('image_prompt')
        
        if not image_prompt:
            return jsonify({'error': 'Image prompt is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current sections data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row:
                return jsonify({'error': 'Post development data not found'}), 404
            
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                for s in sections_list:
                    if s.get('id') == section_id:
                        s['image_prompts'] = {
                            'image_prompt': image_prompt
                        }
                        break
                
                # Update database
                cursor.execute("""
                    UPDATE post_development 
                    SET sections = %s 
                    WHERE post_id = %s
                """, (json.dumps(sections_data), post_id))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Image prompt saved successfully'
                })
            else:
                return jsonify({'error': 'Invalid sections data structure'}), 500
                
    except Exception as e:
        logger.error(f"Error saving image prompt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/generate-image-captions', methods=['POST'])
def api_generate_image_captions(post_id, section_id):
    """Generate image captions and alt text for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section data from post_section table
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get the selected concept details
            selected_concept_text = ''
            selected_concept_id = section.get('selected_image_concept')

            # First try post_section.image_concepts
            if section.get('image_concepts'):
                try:
                    concepts_data = section['image_concepts']
                    if isinstance(concepts_data, str):
                        concepts_data = json.loads(concepts_data)
                    if isinstance(concepts_data, dict) and concepts_data.get('concepts') and selected_concept_id:
                        selected_concept = next((c for c in concepts_data['concepts'] if c.get('concept_id') == selected_concept_id), None)
                        if selected_concept:
                            selected_concept_text = f"{selected_concept.get('concept_description','')}\nMood: {selected_concept.get('concept_mood','')}\nKey Elements: {selected_concept.get('key_visual_elements','')}"
                except Exception as e:
                    logger.error(f"Error parsing selected concept from post_section: {e}")

            # Fallback to post_development.sections if not found
            if not selected_concept_text:
                try:
                    cursor.execute("""
                        SELECT sections FROM post_development WHERE post_id = %s
                    """, (post_id,))
                    dev_row = cursor.fetchone()
                    if dev_row and dev_row.get('sections'):
                        dev_sections = dev_row['sections']
                        if isinstance(dev_sections, str):
                            dev_sections = json.loads(dev_sections)
                        dev_list = dev_sections['sections'] if isinstance(dev_sections, dict) and 'sections' in dev_sections else (dev_sections if isinstance(dev_sections, list) else [])
                        for s in dev_list:
                            if str(s.get('id')) == str(section_id):
                                # Update selected concept id if absent on post_section
                                if not selected_concept_id:
                                    selected_concept_id = s.get('selected_image_concept')
                                concepts = s.get('image_concepts')
                                if isinstance(concepts, str):
                                    try:
                                        concepts = json.loads(concepts)
                                    except Exception:
                                        concepts = None
                                if isinstance(concepts, dict) and concepts.get('concepts') and selected_concept_id:
                                    sel = next((c for c in concepts['concepts'] if c.get('concept_id') == selected_concept_id), None)
                                    if sel:
                                        selected_concept_text = f"{sel.get('concept_description','')}\nMood: {sel.get('concept_mood','')}\nKey Elements: {sel.get('key_visual_elements','')}"
                                break
                except Exception as e:
                    logger.error(f"Error reading selected concept from post_development: {e}")
            
            # Get illustration_method from post taxonomy for prompt selection
            # For recipe posts, use post_type instead of taxonomy
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            if post_type == 'recipe':
                # Recipe posts don't use taxonomy for content_type
                illustration_method = 'LLM-creation'
                content_type_name = None
            else:
                cursor.execute("""
                    SELECT content_type.illustration_method, content_type.display_name as content_type_name
                    FROM post p
                    LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                    WHERE p.id = %s
                """, (post_id,))
                taxonomy_data = cursor.fetchone()
                
                illustration_method = taxonomy_data.get('illustration_method') if taxonomy_data else 'LLM-creation'
                content_type_name = taxonomy_data.get('content_type_name') if taxonomy_data else None
            
            # Use utility function to get category-specific prompt name
            from utils.taxonomy_helpers import get_category_prompt_name
            prompt_name = get_category_prompt_name(
                'Image Captions Generation',
                illustration_method,
                content_type_name
            )
            
            logger.info(f"[IMAGE_CAPTIONS] Using prompt: {prompt_name} (illustration_method: {illustration_method}, content_type: {content_type_name})")
            
            # Get the image captions prompt - try category-specific first, then fall back to base
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            
            prompt_data = cursor.fetchone()
            
            # Fallback to base prompt if category-specific not found
            if not prompt_data and prompt_name != 'Image Captions Generation':
                logger.info(f"[IMAGE_CAPTIONS] Category-specific prompt '{prompt_name}' not found, falling back to base prompt")
                cursor.execute("""
                    SELECT prompt_text, system_prompt
                    FROM llm_prompt 
                    WHERE name = 'Image Captions Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({
                    'error': f'Image Captions prompt "{prompt_name}" not found. Please configure prompts in the LLM Prompts panel first.'
                }), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # For recipe posts, use image prompt as input instead of section content
            image_prompt_text = ''
            if post_type == 'recipe':
                # Get image prompt from section
                image_prompts = section.get('image_prompts')
                if image_prompts:
                    if isinstance(image_prompts, str):
                        try:
                            image_prompts_data = json.loads(image_prompts)
                            if isinstance(image_prompts_data, dict):
                                # Handle nested JSON: image_prompt might be a JSON string itself
                                prompt_value = image_prompts_data.get('image_prompt') or image_prompts_data.get('description') or image_prompts_data.get('subject')
                                if prompt_value:
                                    # If it's a string that looks like JSON, try to parse it
                                    if isinstance(prompt_value, str) and prompt_value.strip().startswith('{'):
                                        try:
                                            nested_json = json.loads(prompt_value)
                                            if isinstance(nested_json, dict):
                                                image_prompt_text = nested_json.get('description') or nested_json.get('image_prompt') or prompt_value
                                            else:
                                                image_prompt_text = prompt_value
                                        except (json.JSONDecodeError, TypeError):
                                            image_prompt_text = prompt_value
                                    else:
                                        image_prompt_text = prompt_value
                                else:
                                    image_prompt_text = str(image_prompts_data)
                            else:
                                image_prompt_text = image_prompts
                        except (json.JSONDecodeError, TypeError):
                            # If it's not JSON, use as-is
                            image_prompt_text = image_prompts
                    elif isinstance(image_prompts, dict):
                        prompt_value = image_prompts.get('image_prompt') or image_prompts.get('description') or image_prompts.get('subject')
                        if prompt_value and isinstance(prompt_value, str) and prompt_value.strip().startswith('{'):
                            try:
                                nested_json = json.loads(prompt_value)
                                if isinstance(nested_json, dict):
                                    image_prompt_text = nested_json.get('description') or nested_json.get('image_prompt') or prompt_value
                                else:
                                    image_prompt_text = prompt_value
                            except (json.JSONDecodeError, TypeError):
                                image_prompt_text = prompt_value
                        else:
                            image_prompt_text = prompt_value or str(image_prompts)
                    else:
                        image_prompt_text = str(image_prompts)
                    
                    logger.info(f"[IMAGE_CAPTIONS] Extracted image prompt text (length: {len(image_prompt_text)}) for recipe post {post_id}, section {section_id}")
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[SECTION_TITLE]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[SECTION_DESCRIPTION]', section['section_description'] or '')
            
            # For recipe posts, use image prompt as the selected concept; for others, use section content
            if post_type == 'recipe' and image_prompt_text:
                # For recipe posts, the image prompt IS the concept we want to caption
                prompt_text = prompt_text.replace('[data:selected_concept]', image_prompt_text)
                prompt_text = prompt_text.replace('[SECTION_CONTENT]', image_prompt_text)
                prompt_text = prompt_text.replace('[IMAGE_PROMPT]', image_prompt_text)
                logger.info(f"[IMAGE_CAPTIONS] Using image prompt as selected concept for recipe post {post_id}, section {section_id}")
            else:
                # For non-recipe posts, use the selected concept or section content
                prompt_text = prompt_text.replace('[data:selected_concept]', selected_concept_text or '')
                prompt_text = prompt_text.replace('[SECTION_CONTENT]', section.get('polished') or section.get('draft') or '')
                prompt_text = prompt_text.replace('[IMAGE_PROMPT]', image_prompt_text or '')

            # Enforce UK British English spelling in captions and alt text with examples
            uk_english_guidance = (
                "Use UK British English spelling and style. Examples: honour not honor; colour not color; "
                "centre not center; organise/organisation not organize/organization; defence not defense; "
                "jewellery not jewelry; programme (non-computing) not program."
            )
            if system_prompt:
                system_prompt = f"{system_prompt}\n\nCRITICAL: {uk_english_guidance}"
            else:
                prompt_text = f"CRITICAL: {uk_english_guidance}\n\n{prompt_text}"
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Create intercept context for message capture
            intercept_context = {
                'post_id': post_id,
                'section_id': section_id
            }
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, intercept_context=intercept_context)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            raw_content = result.get('content')
            if not raw_content or not raw_content.strip():
                logger.error(f"Empty LLM response for post {post_id}, section {section_id}")
                return jsonify({'error': 'LLM returned empty response. Please check Ollama is running and try again.'}), 500
            
            # Parse JSON response
            try:
                # Strip markdown code blocks if present
                content = raw_content.strip()
                if content.startswith('```') and content.endswith('```'):
                    content = content[3:-3].strip()
                elif content.startswith('```json'):
                    content = content[7:-3].strip()
                elif content.startswith('```'):
                    content = content[3:-3].strip()
                
                # Extract only the JSON part (before any additional text)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    content = content[json_start:json_end]
                
                parsed_json = json.loads(content)
                
                if not isinstance(parsed_json, dict) or 'caption' not in parsed_json or 'alt_text' not in parsed_json:
                    raise ValueError("Missing 'caption' or 'alt_text' keys")
                
                if not parsed_json['caption'] or not parsed_json['caption'].strip():
                    raise ValueError("caption field is empty")
                
                if not parsed_json['alt_text'] or not parsed_json['alt_text'].strip():
                    raise ValueError("alt_text field is empty")
                
                # Save to database
                cursor.execute("""
                    UPDATE post_section 
                    SET image_captions = %s, image_alt_text = %s
                    WHERE post_id = %s AND id = %s
                """, (parsed_json['caption'].strip(), parsed_json['alt_text'].strip(), post_id, section_id))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'caption': parsed_json['caption'].strip(),
                    'alt_text': parsed_json['alt_text'].strip(),
                    'image_captions': parsed_json['caption'].strip(),  # Alias for frontend compatibility
                    'image_alt_text': parsed_json['alt_text'].strip(),  # Alias for frontend compatibility
                    'message': 'Image captions generated successfully'
                })
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing LLM response: {e}")
                logger.error(f"Raw content: {raw_content}")
                return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
                
    except Exception as e:
        logger.error(f"Error generating image captions: {e}")
        return jsonify({'error': str(e)}), 500
