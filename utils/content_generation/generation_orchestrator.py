"""
Generation Orchestrator

Coordinates the content generation process using vector search and LLM.
"""

import logging
import json
import re
from typing import Dict, List, Optional
from modules.llm_service import LLMService
from utils.vector_search.retrieval import ContentRetriever
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class GenerationOrchestrator:
    """Orchestrates content generation from products/categories."""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.retriever = ContentRetriever()
        self.prompt_manager = PromptManager()
    
    def retrieve_context(self, source_type: str, source_id: int, 
                        related_limit: int = 3) -> Dict:
        """
        Retrieve context chunks for generation.
        
        Args:
            source_type: 'product' or 'category'
            source_id: Product or category ID
            related_limit: Number of related chunks to retrieve
            
        Returns:
            Dictionary with 'primary' and 'related' chunks
        """
        # Get primary chunk
        chunks = self.retriever.search(
            query=f"{source_type} {source_id}",
            chunk_types=[source_type],
            limit=1
        )
        
        primary_chunk = None
        if chunks.get('results'):
            # Find exact match
            for result in chunks['results']:
                if result['source_id'] == source_id:
                    primary_chunk = result
                    break
        
        # If not found, try direct lookup
        if not primary_chunk:
            # Get chunk directly from database
            from config.database import db_manager
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, chunk_text, metadata
                    FROM content_chunks
                    WHERE chunk_type = %s AND source_id = %s
                    LIMIT 1
                """, (source_type, source_id))
                
                chunk_row = cursor.fetchone()
                if chunk_row:
                    import json as json_lib
                    metadata = chunk_row['metadata']
                    if isinstance(metadata, str):
                        metadata = json_lib.loads(metadata)
                    
                    primary_chunk = {
                        'chunk_id': chunk_row['id'],
                        'chunk_text': chunk_row['chunk_text'],
                        'metadata': metadata
                    }
        
        # Get related chunks
        if primary_chunk:
            # Use product/category name for related search
            name = primary_chunk.get('metadata', {}).get(
                f'{source_type}_name', 
                primary_chunk.get('metadata', {}).get('name', '')
            )
            
            if name:
                related_results = self.retriever.search(
                    query=name,
                    chunk_types=['product', 'category'],
                    limit=related_limit + 1  # +1 to exclude primary
                )
                
                # Filter out primary chunk
                related_chunks = [
                    r for r in related_results.get('results', [])
                    if r['source_id'] != source_id
                ][:related_limit]
            else:
                related_chunks = []
        else:
            related_chunks = []
        
        return {
            'primary': primary_chunk,
            'related': related_chunks
        }
    
    def generate_content(self, source_type: str, source_id: int,
                        generation_type: str = 'deep_dive',
                        tone: str = 'warm',
                        length: str = 'medium',
                        post_id: int = None) -> Dict:
        """
        Generate blog post content.
        
        Args:
            source_type: 'product' or 'category'
            source_id: Product or category ID
            generation_type: 'deep_dive', 'feature', or 'comparison'
            tone: 'warm', 'professional', or 'casual'
            length: 'short', 'medium', or 'long'
            
        Returns:
            Dictionary with generated content
        """
        # Map generation type to prompt type
        prompt_type_map = {
            'deep_dive': 'product_deep_dive' if source_type == 'product' else 'category_feature',
            'feature': 'category_feature',
            'comparison': 'product_comparison'
        }
        
        prompt_type = prompt_type_map.get(generation_type, 'product_deep_dive')
        
        # Retrieve context
        context = self.retrieve_context(source_type, source_id)
        
        if not context['primary']:
            return {
                'success': False,
                'error': f'No content found for {source_type} {source_id}'
            }
        
        # Get prompt template
        prompt_data = self.prompt_manager.get_prompt(prompt_type)
        if not prompt_data:
            return {
                'success': False,
                'error': f'Prompt template not found: {prompt_type}'
            }
        
        # Format prompt with context
        primary_text = context['primary']['chunk_text']
        related_text = '\n\n'.join([
            r['chunk_text'] for r in context['related']
        ])
        
        variables = {
            'product_context': primary_text if source_type == 'product' else '',
            'category_context': primary_text if source_type == 'category' else '',
            'related_chunks': related_text,
            'product_chunks': related_text if source_type == 'category' else primary_text
        }
        
        formatted_prompt = self.prompt_manager.format_prompt(
            prompt_data['prompt_text'],
            variables
        )
        
        # Get model config
        model_config = self.prompt_manager.get_model_config(prompt_type)
        
        # Prepare LLM messages
        messages = [
            {'role': 'system', 'content': prompt_data['system_prompt']},
            {'role': 'user', 'content': formatted_prompt}
        ]
        
        # Generate content (post_id should be provided for intercept context)
        if not post_id:
            return {
                'success': False,
                'error': 'post_id is required for LLM intercept_context'
            }
        
        intercept_context = {
            'post_id': post_id,
            'section_id': None
        }
        
        logger.info(f"Generating content for {source_type} {source_id}...")
        llm_response = self.llm_service.execute_llm_request(
            provider='ollama',
            model=model_config['model'],
            messages=messages,
            intercept_context=intercept_context
        )
        
        if 'error' in llm_response:
            return {
                'success': False,
                'error': f"LLM generation failed: {llm_response['error']}"
            }
        
        # Parse JSON response
        generated_text = llm_response.get('content', '').strip()
        
        def clean_json_text(text):
            """Clean text to extract valid JSON."""
            # Remove markdown code blocks
            text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'```\s*', '', text)
            text = text.strip()
            
            # Find the JSON object boundaries
            brace_start = text.find('{')
            if brace_start == -1:
                return None
            
            # Find matching closing brace
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i
                        break
            
            if brace_end == -1:
                return None
            
            # Extract JSON portion
            json_text = text[brace_start:brace_end + 1]
            
            # Escape control characters in JSON string values using regex
            # This finds content between quotes (string values) and escapes control chars
            import string
            
            def escape_control_chars_in_strings(json_str):
                """Escape control characters within JSON string values."""
                # Use regex to find string values and escape control chars within them
                # Pattern: "..." where ... can contain escaped quotes
                def replace_control_in_match(match):
                    """Replace control chars in a matched string value."""
                    full_match = match.group(0)
                    # Extract the content between quotes
                    content = match.group(1)
                    
                    # Replace control characters (except \n, \r, \t) with their unicode escape
                    cleaned_content = ''
                    for char in content:
                        if ord(char) < 32 and char not in '\n\r\t':
                            # Escape as unicode
                            cleaned_content += '\\u{:04x}'.format(ord(char))
                        else:
                            cleaned_content += char
                    
                    return '"' + cleaned_content + '"'
                
                # Match string values: "..." handling escaped quotes and backslashes
                # This is tricky because we need to handle escaped characters
                # Simpler approach: iterate character by character
                result = []
                i = 0
                in_string = False
                escape_next = False
                
                while i < len(json_str):
                    char = json_str[i]
                    
                    if escape_next:
                        result.append(char)
                        escape_next = False
                        i += 1
                        continue
                    
                    if char == '\\':
                        result.append(char)
                        escape_next = True
                        i += 1
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        result.append(char)
                        i += 1
                        continue
                    
                    if in_string:
                        # Inside string: escape control chars
                        if ord(char) < 32 and char not in '\n\r\t':
                            result.append('\\u{:04x}'.format(ord(char)))
                        else:
                            result.append(char)
                    else:
                        result.append(char)
                    
                    i += 1
                
                return ''.join(result)
            
            # Clean control characters
            cleaned_json = escape_control_chars_in_strings(json_text)
            
            return cleaned_json
        
        try:
            # Strategy 1: Try parsing the entire response as JSON
            try:
                content_data = json.loads(generated_text)
            except json.JSONDecodeError:
                # Strategy 2: Clean and extract JSON
                cleaned_json = clean_json_text(generated_text)
                if not cleaned_json:
                    raise ValueError("Could not extract JSON from response")
                
                content_data = json.loads(cleaned_json)
                
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response (first 1000 chars): {generated_text[:1000]}")
            
            # Final attempt: more aggressive cleaning
            try:
                # Remove all markdown formatting
                cleaned = re.sub(r'```[a-z]*\s*', '', generated_text, flags=re.IGNORECASE)
                cleaned = cleaned.strip()
                
                # Extract JSON with balanced braces
                cleaned_json = clean_json_text(cleaned)
                if cleaned_json:
                    content_data = json.loads(cleaned_json)
                else:
                    raise ValueError("Could not extract JSON after aggressive cleaning")
            except Exception as e2:
                logger.error(f"Failed to parse even after aggressive cleaning: {e2}")
                # Log more of the response for debugging
                logger.error(f"Full response length: {len(generated_text)}")
                logger.error(f"Response preview: {generated_text[:1500]}")
                return {
                    'success': False,
                    'error': f'Failed to parse LLM response: {str(e)}. The response may contain invalid JSON or control characters.'
                }
        
        return {
            'success': True,
            'content': content_data,
            'context': context
        }

