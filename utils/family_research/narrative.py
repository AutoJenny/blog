"""
Narrative generation from family research data.
"""

import json
from typing import Dict, Optional

from .prompts import STORY_WRITING_SYSTEM_PROMPT, STORY_WRITING_USER_PROMPT


def generate_narrative(surname: str, surname_json: Dict, 
                       llm_service, word_target: int = 2500) -> Optional[str]:
    """Generate immersive narrative using Prompt 2."""
    # Clean JSON - remove narrative fields and filter quotations that don't match surname
    clean_json = surname_json.copy()
    if 'metadata' in clean_json:
        metadata_clean = clean_json['metadata'].copy()
        # Remove narrative fields that might confuse the LLM
        metadata_clean.pop('narrative', None)
        metadata_clean.pop('narrative_original', None)
        metadata_clean.pop('narrative_fact_checked', None)
        metadata_clean.pop('narrative_word_count', None)
        metadata_clean.pop('narrative_fact_checked_word_count', None)
        clean_json['metadata'] = metadata_clean
    
    # Filter story_facts.quotations to remove any that mention other surnames
    if 'story_facts' in clean_json and 'quotations' in clean_json['story_facts']:
        quotations = clean_json['story_facts']['quotations']
        filtered_quotations = []
        surname_lower = surname.lower()
        # Common variations
        surname_variations = [surname_lower, surname_lower.replace('ie', 'y'), surname_lower.replace('y', 'ie')]
        
        for q in quotations:
            if isinstance(q, dict):
                quoted_text = q.get('quoted_text', '').lower()
                # Check if quotation mentions the target surname
                mentions_target = any(var in quoted_text for var in surname_variations)
                # Check if it mentions other common Scottish surnames (potential contamination)
                other_surnames = ['abernethy', 'stewart', 'campbell', 'douglas', 'bruce', 'wallace']
                mentions_other = any(other in quoted_text and other not in surname_variations for other in other_surnames)
                
                if mentions_target and not mentions_other:
                    filtered_quotations.append(q)
                elif mentions_other:
                    # Skip quotations that mention other surnames
                    pass
                else:
                    # If unclear, include it (might be a general quote)
                    filtered_quotations.append(q)
        
        clean_json['story_facts']['quotations'] = filtered_quotations
    
    # Ensure surname is correct
    clean_json['surname'] = surname
    
    # Build prompt
    system_prompt = STORY_WRITING_SYSTEM_PROMPT.replace('{{SURNAME}}', surname)
    user_prompt = STORY_WRITING_USER_PROMPT.replace('{{SURNAME}}', surname)
    user_prompt = user_prompt.replace('{{WORD_TARGET}}', str(word_target))
    user_prompt = user_prompt.replace('{{SURNAME_JSON}}', json.dumps(clean_json, indent=2))
    
    # Call LLM
    try:
        if hasattr(llm_service, 'generate'):
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = llm_service.generate(
                prompt=full_prompt,
                model_name='llama3.2:latest',
                temperature=0.7,  # Higher temperature for more creative narrative
                max_tokens=8000,  # Much longer response for comprehensive narrative
                timeout=300
            )
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            result = llm_service.execute_llm_request(
                provider='ollama',
                model='llama3.2:latest',
                messages=messages,
                max_tokens=8000,  # Much longer response for comprehensive narrative
                temperature=0.7
            )
            if 'error' in result:
                print(f"  Error: {result['error']}")
                return None
            response = result.get('content', '')
        
        return response.strip()
            
    except Exception as e:
        print(f"  Error during narrative generation: {e}")
        return None


