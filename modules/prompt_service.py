# modules/prompt_service.py
"""
Prompt Service - Handles canonical prompt processing and model-specific rendering
Integrates with existing image generation system
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from config.database import db_manager
from modules.prompt_renderers import CanonicalPrompt, render_prompt_for_model, parse_legacy_prompt

logger = logging.getLogger(__name__)

class PromptService:
    """Service for handling prompt processing and model-specific rendering"""
    
    def __init__(self):
        self.model_specs_cache = {}
        self._load_model_specs()
    
    def _load_model_specs(self):
        """Load model specifications from database"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT lm.name, lm.api_params, lp.name as provider_name
                    FROM llm_model lm
                    JOIN llm_provider lp ON lm.provider_id = lp.id
                    WHERE lm.api_params->>'type' = 'image'
                """)
                models = cursor.fetchall()
                
                for model in models:
                    model_key = model['name']
                    api_params = model['api_params'] or {}
                    
                    self.model_specs_cache[model_key] = {
                        'provider': model['provider_name'],
                        'constraints': {
                            'max_prompt_chars': api_params.get('max_prompt_chars', 1000),
                            'supported_sizes': api_params.get('sizes', []),
                            'supported_qualities': api_params.get('quality', []),
                            'supported_styles': api_params.get('style', [])
                        }
                    }
                
                logger.info(f"Loaded model specs for {len(self.model_specs_cache)} models")
                
        except Exception as e:
            logger.error(f"Error loading model specs: {e}")
            self.model_specs_cache = {}
    
    def get_canonical_prompt(self, post_id: int, section_id: int) -> CanonicalPrompt:
        """Get canonical prompt for a section, handling legacy formats"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT image_prompts FROM post_section 
                    WHERE id = %s AND post_id = %s
                """, (section_id, post_id))
                
                result = cursor.fetchone()
                if not result or not result['image_prompts']:
                    return CanonicalPrompt({})
                
                prompt_text = result['image_prompts']
                return parse_legacy_prompt(prompt_text)
                
        except Exception as e:
            logger.error(f"Error getting canonical prompt for section {section_id}: {e}")
            return CanonicalPrompt({})
    
    def get_prompt_override(self, post_id: int, section_id: int, model_key: str) -> Optional[str]:
        """Get model-specific prompt override if it exists"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT prompt_text FROM image_prompt_override
                    WHERE post_id = %s AND section_id = %s AND model_key = %s AND active = TRUE
                """, (post_id, section_id, model_key))
                
                result = cursor.fetchone()
                return result['prompt_text'] if result else None
                
        except Exception as e:
            logger.error(f"Error getting prompt override: {e}")
            return None
    
    def save_prompt_override(self, post_id: int, section_id: int, model_key: str, prompt_text: str) -> bool:
        """Save model-specific prompt override"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO image_prompt_override (post_id, section_id, model_key, prompt_text, active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (post_id, section_id, model_key)
                    DO UPDATE SET prompt_text = %s, active = TRUE, updated_at = CURRENT_TIMESTAMP
                """, (post_id, section_id, model_key, prompt_text, prompt_text))
                
                cursor.connection.commit()
                logger.info(f"Saved prompt override for {model_key}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving prompt override: {e}")
            return False
    
    def render_header_prompt_for_model(self, post_id: int, model_key: str, use_override: bool = True) -> Tuple[str, Dict[str, Any]]:
        """Render header prompt for specific model by compiling prompts from all sections"""
        try:
            # Get model constraints
            model_spec = self.model_specs_cache.get(model_key, {})
            constraints = model_spec.get('constraints', {'max_prompt_chars': 1000})
            
            # Get all sections for the post
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, section_heading, image_prompts
                    FROM post_section 
                    WHERE post_id = %s AND image_prompts IS NOT NULL AND image_prompts != ''
                    ORDER BY section_order
                """, (post_id,))
                
                sections = cursor.fetchall()
            
            if not sections:
                return "", {
                    'source': 'error',
                    'model_key': model_key,
                    'error': 'No sections with prompts found'
                }
            
            # Compile prompts from all sections
            section_prompts = []
            for section in sections:
                canonical = parse_legacy_prompt(section['image_prompts'])
                if canonical.subject:
                    section_prompts.append(canonical.subject)
            
            if not section_prompts:
                return "", {
                    'source': 'error',
                    'model_key': model_key,
                    'error': 'No valid prompts found in sections'
                }
            
            # Create a collage-style prompt
            if model_key == 'sdxl-lora':
                # For SDXL, create a tag-style collage
                collage_prompt = f"collage composition featuring: {', '.join(section_prompts[:5])}, artistic illustration, pen and ink watercolor style"
            else:
                # For DALL-E, create a descriptive collage
                collage_prompt = f"A collage-style header image combining elements from: {'; '.join(section_prompts[:3])}. Create a cohesive composition that represents the overall theme of the blog post."
            
            # Render for model
            rendered_prompt = render_prompt_for_model(
                CanonicalPrompt({'subject': collage_prompt}), 
                model_key, 
                constraints
            )
            
            return rendered_prompt, {
                'source': 'header_collage',
                'model_key': model_key,
                'section_count': len(sections),
                'char_count': len(rendered_prompt),
                'max_chars': constraints.get('max_prompt_chars', 1000),
                'truncated': len(rendered_prompt) >= constraints.get('max_prompt_chars', 1000),
                'sections_used': len(section_prompts)
            }
            
        except Exception as e:
            logger.error(f"Error rendering header prompt for {model_key}: {e}")
            return "", {
                'source': 'error',
                'model_key': model_key,
                'error': str(e)
            }

    def render_prompt_for_model(self, post_id: int, section_id: int, model_key: str, use_override: bool = True) -> Tuple[str, Dict[str, Any]]:
        """Render prompt for specific model, using override if available"""
        try:
            # Get model constraints
            model_spec = self.model_specs_cache.get(model_key, {})
            constraints = model_spec.get('constraints', {'max_prompt_chars': 1000})
            
            # Check for override first
            if use_override:
                override_prompt = self.get_prompt_override(post_id, section_id, model_key)
                if override_prompt:
                    logger.info(f"Using override prompt for {model_key}")
                    return override_prompt, {
                        'source': 'override',
                        'model_key': model_key,
                        'char_count': len(override_prompt),
                        'max_chars': constraints.get('max_prompt_chars', 1000)
                    }
            
            # Get canonical prompt
            canonical = self.get_canonical_prompt(post_id, section_id)
            
            # Render for model
            rendered_prompt = render_prompt_for_model(canonical, model_key, constraints)
            
            return rendered_prompt, {
                'source': 'rendered',
                'model_key': model_key,
                'canonical': canonical.to_dict(),
                'char_count': len(rendered_prompt),
                'max_chars': constraints.get('max_prompt_chars', 1000),
                'truncated': len(rendered_prompt) >= constraints.get('max_prompt_chars', 1000)
            }
            
        except Exception as e:
            logger.error(f"Error rendering prompt for {model_key}: {e}")
            return "", {
                'source': 'error',
                'model_key': model_key,
                'error': str(e)
            }
    
    def log_generation_event(self, post_id: int, section_id: int, model_key: str, 
                           params: Dict[str, Any], prompt_text: str, rendered_prompt: str,
                           result_path: str, success: bool = True, error_message: str = None,
                           generation_time_ms: int = None) -> bool:
        """Log image generation event for audit trail"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO image_generation_event 
                    (post_id, section_id, model_key, params_json, prompt_text, rendered_prompt, 
                     result_path, success, error_message, generation_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (post_id, section_id, model_key, json.dumps(params), prompt_text, 
                      rendered_prompt, result_path, success, error_message, generation_time_ms))
                
                cursor.connection.commit()
                logger.info(f"Logged generation event for {model_key}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging generation event: {e}")
            return False
    
    def get_generation_events(self, post_id: int = None, section_id: int = None, 
                            model_key: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get generation events for audit/debugging"""
        try:
            with db_manager.get_cursor() as cursor:
                conditions = []
                params = []
                
                if post_id:
                    conditions.append("post_id = %s")
                    params.append(post_id)
                
                if section_id:
                    conditions.append("section_id = %s")
                    params.append(section_id)
                
                if model_key:
                    conditions.append("model_key = %s")
                    params.append(model_key)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                params.append(limit)
                
                cursor.execute(f"""
                    SELECT * FROM image_generation_event
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                """, params)
                
                events = cursor.fetchall()
                return [dict(event) for event in events]
                
        except Exception as e:
            logger.error(f"Error getting generation events: {e}")
            return []
    
    def get_model_constraints(self, model_key: str) -> Dict[str, Any]:
        """Get constraints for a specific model"""
        model_spec = self.model_specs_cache.get(model_key, {})
        return model_spec.get('constraints', {'max_prompt_chars': 1000})
    
    def refresh_model_specs(self):
        """Refresh model specifications from database"""
        self.model_specs_cache.clear()
        self._load_model_specs()

# Global service instance
prompt_service = PromptService()
