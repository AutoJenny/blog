"""
Product Article Generator

Generates product articles using CLAN-first policy with structured 7-section template.
"""

import logging
import json
import re
from typing import Dict, List, Optional
from modules.llm_service import LLMService
from utils.content_generation.clan_data_extractor import ClanDataExtractor
from utils.content_generation.prompt_manager import PromptManager
from utils.content_generation.data_source_tracker import DataSourceTracker

logger = logging.getLogger(__name__)


class ProductArticleGenerator:
    """Generates product articles with CLAN-first policy."""
    
    # Standard 7-section structure
    STANDARD_SECTIONS = [
        {"number": 1, "name": "Introduction & Historical Context"},
        {"number": 2, "name": "Craftsmanship & Materials"},
        {"number": 3, "name": "Features & Specifications"},
        {"number": 4, "name": "How to Use / Practical Guide"},
        {"number": 5, "name": "Benefits & Value"},
        {"number": 6, "name": "Alternative Products"},
        {"number": 7, "name": "Conclusion"}
    ]
    
    def __init__(self):
        self.llm_service = LLMService()
        self.data_extractor = ClanDataExtractor()
        self.prompt_manager = PromptManager()
        self.tracker = DataSourceTracker()
    
    def generate_topics(self, product_id: int, post_id: int) -> Dict:
        """
        Generate topics for all sections using CLAN data.
        
        Args:
            product_id: Product ID
            post_id: Post ID for LLM intercept_context
            
        Returns:
            Dictionary with topics for each section
        """
        # Extract and validate product data
        product_data = self.data_extractor.extract_product_data(product_id)
        validation = self.data_extractor.validate_data_completeness(product_data)
        
        # Format CLAN data for prompt
        clan_data_formatted = self.data_extractor.format_for_prompt(product_data, validation)
        
        # Get prompt template
        prompt = self.prompt_manager.get_prompt('product_article_topic_brainstorming')
        if not prompt:
            return {
                'success': False,
                'error': 'Topic brainstorming prompt not found'
            }
        
        # Format prompt
        prompt_text = self.prompt_manager.format_prompt(
            prompt['prompt_text'],
            {'clan_data_formatted': clan_data_formatted}
        )
        
        # Prepare messages
        messages = [
            {'role': 'system', 'content': prompt['system_prompt']},
            {'role': 'user', 'content': prompt_text}
        ]
        
        # Get model config
        model_config = self.prompt_manager.get_model_config('product_article_topic_brainstorming')
        
        # Generate topics
        intercept_context = {
            'post_id': post_id,
            'section_id': None
        }
        
        logger.info(f"Generating topics for product {product_id}...")
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
        topics_data = self._parse_json_response(generated_text)
        
        return {
            'success': True,
            'topics': topics_data,
            'product_data': product_data,
            'validation': validation
        }
    
    def generate_section_ideas(self, product_id: int, section_number: int, 
                               section_topics: List[str], post_id: int) -> Dict:
        """
        Generate ideas for a specific section.
        
        Args:
            product_id: Product ID
            section_number: Section number (1-7)
            section_topics: List of topics for this section
            post_id: Post ID for LLM intercept_context
            
        Returns:
            Dictionary with ideas for the section
        """
        # Extract product data
        product_data = self.data_extractor.extract_product_data(product_id)
        validation = self.data_extractor.validate_data_completeness(product_data)
        clan_data_formatted = self.data_extractor.format_for_prompt(product_data, validation)
        
        # Get section name
        section = next((s for s in self.STANDARD_SECTIONS if s['number'] == section_number), None)
        if not section:
            return {
                'success': False,
                'error': f'Invalid section number: {section_number}'
            }
        
        # Get prompt template
        prompt = self.prompt_manager.get_prompt('product_article_section_ideas')
        if not prompt:
            return {
                'success': False,
                'error': 'Section ideas prompt not found'
            }
        
        # Format prompt
        prompt_text = self.prompt_manager.format_prompt(
            prompt['prompt_text'],
            {
                'clan_data_formatted': clan_data_formatted,
                'section_name': section['name'],
                'section_number': section_number,
                'section_topics': json.dumps(section_topics)
            }
        )
        
        # Prepare messages
        messages = [
            {'role': 'system', 'content': prompt['system_prompt']},
            {'role': 'user', 'content': prompt_text}
        ]
        
        # Get model config
        model_config = self.prompt_manager.get_model_config('product_article_section_ideas')
        
        # Generate ideas
        intercept_context = {
            'post_id': post_id,
            'section_id': None
        }
        
        logger.info(f"Generating ideas for section {section_number}...")
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
        ideas_data = self._parse_json_response(generated_text)
        
        return {
            'success': True,
            'ideas': ideas_data
        }
    
    def draft_section(self, product_id: int, section_number: int, 
                     section_title: str, section_topics: List[str],
                     section_ideas: List[str], post_id: int) -> Dict:
        """
        Draft content for a specific section.
        
        Args:
            product_id: Product ID
            section_number: Section number (1-7)
            section_title: Section title
            section_topics: List of topics
            section_ideas: List of ideas
            post_id: Post ID for LLM intercept_context
            
        Returns:
            Dictionary with drafted content
        """
        # Extract product data
        product_data = self.data_extractor.extract_product_data(product_id)
        validation = self.data_extractor.validate_data_completeness(product_data)
        clan_data_formatted = self.data_extractor.format_for_prompt(product_data, validation)
        
        # Get section name
        section = next((s for s in self.STANDARD_SECTIONS if s['number'] == section_number), None)
        if not section:
            return {
                'success': False,
                'error': f'Invalid section number: {section_number}'
            }
        
        # Get alternative products for section 6
        alternative_products_data = ""
        if section_number == 6:
            alternatives = self.data_extractor.find_alternative_products(product_id, limit=5)
            if alternatives:
                alt_list = []
                for alt in alternatives:
                    alt_desc = f"- {alt.get('name', 'N/A')}"
                    if alt.get('price'):
                        alt_desc += f" (£{alt.get('price')})"
                    if alt.get('discovery_strategy'):
                        alt_desc += f" [{alt.get('discovery_strategy')}]"
                    alt_list.append(alt_desc)
                alternative_products_data = "\n".join(alt_list)
        
        # Get prompt template
        prompt = self.prompt_manager.get_prompt('product_article_section_drafting')
        if not prompt:
            return {
                'success': False,
                'error': 'Section drafting prompt not found'
            }
        
        # Format prompt
        prompt_text = self.prompt_manager.format_prompt(
            prompt['prompt_text'],
            {
                'clan_data_formatted': clan_data_formatted,
                'section_name': section['name'],
                'section_title': section_title,
                'section_topics': json.dumps(section_topics),
                'section_ideas': json.dumps(section_ideas),
                'alternative_products_data': alternative_products_data
            }
        )
        
        # Prepare messages
        messages = [
            {'role': 'system', 'content': prompt['system_prompt']},
            {'role': 'user', 'content': prompt_text}
        ]
        
        # Get model config
        model_config = self.prompt_manager.get_model_config('product_article_section_drafting')
        
        # Generate content
        intercept_context = {
            'post_id': post_id,
            'section_id': None
        }
        
        logger.info(f"Drafting section {section_number}...")
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
        
        # Return plain text content (not JSON for drafting)
        content = llm_response.get('content', '').strip()
        
        return {
            'success': True,
            'content': content,
            'section_number': section_number,
            'section_name': section['name']
        }
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from LLM response, handling markdown and extra text."""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Find JSON object boundaries
        brace_start = text.find('{')
        if brace_start == -1:
            return {}
        
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
            return {}
        
        # Extract JSON portion
        json_text = text[brace_start:brace_end + 1]
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"JSON text: {json_text[:500]}")
            return {}
    
    def get_standard_sections(self) -> List[Dict]:
        """Get the standard 7-section structure."""
        return self.STANDARD_SECTIONS.copy()

