"""
Image Prompt Management API Endpoints
API routes for prompt management, diagnostics, and debugging
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from modules.prompt_service import prompt_service
from modules.prompt_renderers import PromptRendererFactory
import logging
import json
import traceback

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register prompt management API routes with the blueprint"""
    
    @bp.route('/prompts/image-generation', methods=['GET', 'PUT'])
    def imaging_prompts_image_generation():
        """Get or update the image generation prompt - imaging standalone version"""
        try:
            with db_manager.get_cursor() as cursor:
                if request.method == 'GET':
                    # Get the prompt
                    cursor.execute("""
                        SELECT id, name, prompt_text, description
                        FROM llm_prompt
                        WHERE name = 'Image Generation'
                    """)
                    prompt = cursor.fetchone()
                    
                    if prompt:
                        return jsonify({
                            'success': True,
                            'prompt': {
                                'id': prompt['id'],
                                'name': prompt['name'],
                                'text': prompt['prompt_text'],
                                'description': prompt['description']
                            }
                        })
                    else:
                        return jsonify({'success': False, 'error': 'Prompt not found'})
                
                elif request.method == 'PUT':
                    # Update the prompt
                    data = request.get_json()
                    prompt_text = data.get('text', '')
                    
                    cursor.execute("""
                        UPDATE llm_prompt
                        SET prompt_text = %s, updated_at = NOW()
                        WHERE name = 'Image Generation'
                    """, (prompt_text,))
                    
                    return jsonify({'success': True, 'message': 'Prompt updated successfully'})
                    
        except Exception as e:
            logger.error(f"Error with Image Generation prompt: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/diagnostic/posts/<int:post_id>/sections/<section_id>/prompt-pipeline', methods=['GET'])
    def diagnostic_prompt_pipeline(post_id, section_id):
        """Comprehensive diagnostic for prompt rendering pipeline"""
        results = {
            'post_id': post_id,
            'section_id': section_id,
            'stages': {},
            'overall_status': 'pending'
        }
        
        try:
            # Stage 1: Database Retrieval
            with db_manager.get_cursor() as cursor:
                # Check post exists
                cursor.execute("SELECT id, title, extra_settings FROM post WHERE id = %s", (post_id,))
                post_row = cursor.fetchone()
                
                results['stages']['database'] = {
                    'post_exists': bool(post_row),
                    'post_title': post_row['title'] if post_row else None,
                    'extra_settings_exists': bool(post_row and post_row['extra_settings']),
                    'imaging_settings_exists': bool(post_row and post_row.get('extra_settings', {}).get('imaging')),
                    'styles_array_exists': False,
                    'active_style_exists': False,
                    'active_style_json': None
                }
                
                if post_row and post_row.get('extra_settings'):
                    imaging = post_row['extra_settings'].get('imaging', {})
                    styles = imaging.get('styles', [])
                    active_index = imaging.get('activeIndex', 0)
                    
                    results['stages']['database']['styles_array_exists'] = bool(styles)
                    results['stages']['database']['styles_count'] = len(styles) if isinstance(styles, list) else 0
                    results['stages']['database']['active_index'] = active_index
                    
                    if styles and 0 <= active_index < len(styles):
                        active_style = styles[active_index]
                        results['stages']['database']['active_style_exists'] = True
                        results['stages']['database']['active_style_name'] = active_style.get('name')
                        results['stages']['database']['active_style_json'] = active_style.get('style_json')
                
                # Check section data
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                dev_row = cursor.fetchone()
                
                results['stages']['database']['post_development_exists'] = bool(dev_row)
                
                if dev_row and dev_row['sections']:
                    sections_data = dev_row['sections']
                    if isinstance(sections_data, str):
                        sections_data = json.loads(sections_data)
                    
                    if isinstance(sections_data, dict) and 'sections' in sections_data:
                        sections_list = sections_data['sections']
                        results['stages']['database']['sections_count'] = len(sections_list)
                        
                        # Find target section
                        for section in sections_list:
                            if str(section.get('id')) == str(section_id):
                                results['stages']['database']['section_found'] = True
                                results['stages']['database']['section_has_image_prompts'] = bool(section.get('image_prompts'))
                                if section.get('image_prompts'):
                                    prompt_data = section['image_prompts']
                                    if isinstance(prompt_data, dict):
                                        results['stages']['database']['image_prompt_length'] = len(prompt_data.get('image_prompt', ''))
                                        results['stages']['database']['image_prompt_preview'] = prompt_data.get('image_prompt', '')[:100]
                                break
            
            # Stage 2: Canonical Prompt Creation
            try:
                canonical, style_json = prompt_service.get_canonical_prompt(post_id, section_id)
                results['stages']['canonical_prompt'] = {
                    'success': True,
                    'canonical_subject_length': len(canonical.subject),
                    'canonical_subject_preview': canonical.subject[:100] if canonical.subject else None,
                    'canonical_style': canonical.style,
                    'canonical_constraints': canonical.constraints,
                    'canonical_negatives': canonical.negatives,
                    'style_json_received': bool(style_json),
                    'style_json_keys': list(style_json.keys()) if isinstance(style_json, dict) else None
                }
            except Exception as e:
                results['stages']['canonical_prompt'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                results['overall_status'] = 'failed'
                return jsonify(results)
            
            # Stage 3: Renderer Selection
            model_key = request.args.get('model_key', 'gpt-image-1')
            try:
                constraints = {'max_prompt_chars': 2000 if model_key == 'gpt-image-1' else 400}
                renderer = PromptRendererFactory.create_renderer(model_key, constraints)
                results['stages']['renderer'] = {
                    'success': True,
                    'renderer_class': type(renderer).__name__,
                    'model_key': model_key,
                    'constraints': constraints
                }
            except Exception as e:
                results['stages']['renderer'] = {
                    'success': False,
                    'error': str(e)
                }
                results['overall_status'] = 'failed'
                return jsonify(results)
            
            # Stage 4: Style Integration (call internal method)
            try:
                style_description = renderer._integrate_style_details(canonical, style_json)
                results['stages']['style_integration'] = {
                    'success': True,
                    'style_description': style_description,
                    'style_description_length': len(style_description) if style_description else 0,
                    'contains_watercolor': 'watercolor' in (style_description or '').lower(),
                    'contains_pastel': 'pastel' in (style_description or '').lower()
                }
            except Exception as e:
                results['stages']['style_integration'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Stage 5: Full Rendering
            try:
                rendered_prompt = renderer.render(canonical, style_json)
                results['stages']['rendering'] = {
                    'success': True,
                    'prompt_length': len(rendered_prompt),
                    'prompt_preview_first_200': rendered_prompt[:200],
                    'prompt_preview_last_200': rendered_prompt[-200:],
                    'contains_watercolor': 'watercolor' in rendered_prompt.lower(),
                    'contains_pastel': 'pastel' in rendered_prompt.lower(),
                    'contains_white_margins': 'white margin' in rendered_prompt.lower(),
                    'contains_visible_brushstrokes': 'visible brushstroke' in rendered_prompt.lower(),
                    'contains_pen_and_ink': 'pen and ink' in rendered_prompt.lower(),
                    'contains_avoiding_dark': 'avoiding dark' in rendered_prompt.lower(),
                    'contains_avoiding_saturated': 'avoiding saturated' in rendered_prompt.lower(),
                    'contains_avoiding_digital': 'avoiding digital' in rendered_prompt.lower()
                }
            except Exception as e:
                results['stages']['rendering'] = {
                    'success': False,
                    'error': str(e)
                }
                results['overall_status'] = 'failed'
                return jsonify(results)
            
            # Stage 6: API Integration Test
            try:
                # Test the actual API path
                rendered_via_service, metadata = prompt_service.render_prompt_for_model(
                    post_id, section_id, model_key, use_override=True
                )
                results['stages']['api_integration'] = {
                    'success': True,
                    'service_prompt_length': len(rendered_via_service),
                    'matches_direct_render': rendered_via_service == rendered_prompt,
                    'metadata': metadata
                }
            except Exception as e:
                results['stages']['api_integration'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Overall assessment
            all_stages_passed = all(
                stage.get('success', False) 
                for stage in results['stages'].values() 
                if 'success' in stage
            )
            results['overall_status'] = 'passed' if all_stages_passed else 'failed'
            
            return jsonify(results)
            
        except Exception as e:
            results['overall_status'] = 'error'
            results['error'] = str(e)
            results['error_trace'] = traceback.format_exc()
            return jsonify(results), 500

    @bp.route('/api/prompt-override/posts/<int:post_id>/sections/<int:section_id>/<model_key>', methods=['GET', 'POST', 'DELETE'])
    def imaging_prompt_override(post_id, section_id, model_key):
        """Handle model-specific prompt overrides"""
        try:
            if request.method == 'GET':
                # Get override for specific model
                override = prompt_service.get_prompt_override(post_id, section_id, model_key)
                return jsonify({
                    'success': True,
                    'override': override,
                    'has_override': override is not None
                })
            
            elif request.method == 'POST':
                # Save override
                data = request.get_json()
                prompt_text = data.get('prompt_text', '')
                
                if not prompt_text.strip():
                    return jsonify({'success': False, 'error': 'Prompt text cannot be empty'}), 400
                
                success = prompt_service.save_prompt_override(post_id, section_id, model_key, prompt_text)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Prompt override saved successfully'
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to save override'}), 500
            
            elif request.method == 'DELETE':
                # Delete override (deactivate)
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE image_prompt_override 
                        SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                        WHERE post_id = %s AND section_id = %s AND model_key = %s
                    """, (post_id, section_id, model_key))
                    cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt override deleted successfully'
                })
                
        except Exception as e:
            logger.error(f"Error with prompt override: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/debug-prompt/posts/<int:post_id>/sections/<int:section_id>', methods=['GET'])
    def imaging_debug_prompt(post_id, section_id):
        """Debug endpoint to test prompt parsing"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT image_prompts FROM post_section 
                    WHERE id = %s AND post_id = %s
                """, (section_id, post_id))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({'error': 'Section not found'})
                
                prompt_data = result['image_prompts']
                
                # Test parsing
                from modules.prompt_renderers import parse_legacy_prompt
                
                if isinstance(prompt_data, dict):
                    prompt_text = prompt_data.get('image_prompt', '') or prompt_data.get('base_concept', '')
                    canonical = parse_legacy_prompt(prompt_text)
                else:
                    canonical = parse_legacy_prompt(prompt_data)
                
                return jsonify({
                    'raw_data': prompt_data,
                    'raw_type': type(prompt_data).__name__,
                    'extracted_text': prompt_text if isinstance(prompt_data, dict) else prompt_data,
                    'canonical': canonical.to_dict(),
                    'canonical_subject': canonical.subject
                })
                
        except Exception as e:
            return jsonify({'error': str(e)})

    @bp.route('/admin/generation-events')
    def imaging_admin_generation_events():
        """Admin page for viewing generation events"""
        try:
            return jsonify({
                'success': True,
                'message': 'Admin page - use /api/generation-events for data'
            })
        except Exception as e:
            logger.error(f"Error in admin generation events: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

