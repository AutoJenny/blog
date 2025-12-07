"""
Story facts extraction and processing for family research.
"""

import json
import re
from typing import Dict, Optional

from .prompts import FACT_EXTRACTION_PROMPT, SYSTEM_PROMPT


def extract_facts_from_chunk(surname: str, chunk_text: str, 
                             existing_story_facts: Optional[Dict],
                             llm_service) -> Optional[Dict]:
    """Extract story facts from a single text chunk using Prompt 1."""
    # Build prompt
    system_prompt = SYSTEM_PROMPT.replace('{{SURNAME}}', surname)
    user_prompt = FACT_EXTRACTION_PROMPT.replace('{{SURNAME}}', surname)
    user_prompt = user_prompt.replace('{{CHUNK_TEXT}}', chunk_text)
    
    # Optionally include existing story_facts for consistency
    if existing_story_facts:
        user_prompt += f"\n\nExisting story_facts (for consistency):\n{json.dumps(existing_story_facts, indent=2)}"
    
    # Call LLM
    try:
        if hasattr(llm_service, 'generate'):
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = llm_service.generate(
                prompt=full_prompt,
                model_name='llama3.2:latest',
                temperature=0.2,  # Lower temperature for more factual extraction
                max_tokens=2000,
                timeout=120
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
                max_tokens=2000,
                temperature=0.2
            )
            if 'error' in result:
                print(f"  Error: {result['error']}")
                return None
            response = result.get('content', '')
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                facts = json.loads(json_match.group(0))
                return facts
            except json.JSONDecodeError:
                print(f"  Warning: Could not parse JSON from LLM response")
                return None
        else:
            print(f"  Warning: No JSON found in LLM response")
            return None
            
    except Exception as e:
        print(f"  Error during fact extraction: {e}")
        return None


def post_process_story_facts(story_facts: Dict) -> Dict:
    """Post-process story_facts to normalize data structures."""
    # Normalize key_figures - convert strings to objects
    if 'key_figures' in story_facts and isinstance(story_facts['key_figures'], list):
        normalized_figures = []
        seen_names = set()
        for item in story_facts['key_figures']:
            if isinstance(item, str):
                name = item.strip()
                if name and name.lower() not in seen_names:
                    normalized_figures.append({
                        'name': name,
                        'titles_or_roles': [],
                        'life_dates': None,
                        'alignment': 'unknown',
                        'one_line': '',
                        'sources_hint': [],
                        'uncertainty_flags': []
                    })
                    seen_names.add(name.lower())
            elif isinstance(item, dict):
                name = item.get('name', '').strip()
                if name and name.lower() not in seen_names:
                    # Normalize structure
                    normalized_item = {
                        'name': name,
                        'titles_or_roles': [],
                        'life_dates': None,
                        'alignment': 'unknown',
                        'one_line': '',
                        'sources_hint': [],
                        'uncertainty_flags': []
                    }
                    # Extract title if present
                    if 'title' in item and item['title']:
                        normalized_item['titles_or_roles'] = [item['title']]
                    # Copy other fields if present
                    for field in ['titles_or_roles', 'life_dates', 'alignment', 'one_line', 'sources_hint', 'uncertainty_flags']:
                        if field in item and item[field]:
                            normalized_item[field] = item[field]
                    normalized_figures.append(normalized_item)
                    seen_names.add(name.lower())
        story_facts['key_figures'] = normalized_figures
    
    # Normalize turning_points structure
    if 'turning_points' in story_facts and isinstance(story_facts['turning_points'], list):
        normalized_points = []
        seen_ids = set()
        for item in story_facts['turning_points']:
            if isinstance(item, dict):
                # Generate ID if missing
                if 'id' not in item or not item['id']:
                    title = item.get('title', item.get('event', 'unknown'))
                    item_id = title.lower().replace(' ', '_').replace("'", '').replace(',', '')[:50]
                    item['id'] = item_id
                
                if item['id'] not in seen_ids:
                    normalized_item = {
                        'id': item['id'],
                        'title': item.get('title', item.get('event', 'Unknown event')),
                        'approx_date': item.get('approx_date', item.get('date', None)),
                        'place': item.get('place', item.get('location', None)),
                        'involved_figures': item.get('involved_figures', []),
                        'summary': item.get('summary', item.get('notes', '')),
                        'consequences': item.get('consequences', ''),
                        'is_legendary': item.get('is_legendary', False),
                        'sources_hint': item.get('sources_hint', []),
                        'uncertainty_flags': item.get('uncertainty_flags', [])
                    }
                    normalized_points.append(normalized_item)
                    seen_ids.add(item['id'])
        story_facts['turning_points'] = normalized_points
    
    # Normalize places structure
    if 'places' in story_facts and isinstance(story_facts['places'], list):
        normalized_places = []
        seen_names = set()
        for item in story_facts['places']:
            if isinstance(item, str):
                name = item.strip()
                if name and name.lower() not in seen_names:
                    normalized_places.append({
                        'name': name,
                        'type': 'other',
                        'location_description': '',
                        'period_relevance': '',
                        'link_to_family': '',
                        'sources_hint': []
                    })
                    seen_names.add(name.lower())
            elif isinstance(item, dict):
                name = item.get('name', '').strip()
                if name and name.lower() not in seen_names:
                    normalized_item = {
                        'name': name,
                        'type': item.get('type', 'other'),
                        'location_description': item.get('location_description', item.get('location', '')),
                        'period_relevance': item.get('period_relevance', ''),
                        'link_to_family': item.get('link_to_family', ''),
                        'sources_hint': item.get('sources_hint', [])
                    }
                    normalized_places.append(normalized_item)
                    seen_names.add(name.lower())
        story_facts['places'] = normalized_places
    
    # Normalize quotations structure
    if 'quotations' in story_facts and isinstance(story_facts['quotations'], list):
        normalized_quotations = []
        seen_texts = set()
        for item in story_facts['quotations']:
            if isinstance(item, dict):
                quoted_text = item.get('quoted_text', item.get('text', '')).strip()
                if quoted_text and quoted_text.lower() not in seen_texts:
                    # Generate ID if missing
                    if 'id' not in item or not item['id']:
                        speaker = item.get('speaker', 'unknown')
                        item_id = f"{speaker.lower().replace(' ', '_')}_{len(normalized_quotations)}"
                        item['id'] = item_id
                    
                    normalized_item = {
                        'id': item['id'],
                        'quoted_text': quoted_text,
                        'speaker': item.get('speaker', None),
                        'approx_date': item.get('approx_date', item.get('date', None)),
                        'context_summary': item.get('context_summary', item.get('context', '')),
                        'source_hint': item.get('source_hint', []),
                        'reliability': item.get('reliability', 'uncertain'),
                        'uncertainty_flags': item.get('uncertainty_flags', item.get('doubts', []))
                    }
                    normalized_quotations.append(normalized_item)
                    seen_texts.add(quoted_text.lower())
        story_facts['quotations'] = normalized_quotations
    
    # Ensure all required fields exist
    if 'time_span' not in story_facts:
        story_facts['time_span'] = {'earliest_century': 'unknown', 'latest_century': 'unknown', 'notes': ''}
    if 'themes' not in story_facts:
        story_facts['themes'] = []
    if 'sources_summary' not in story_facts:
        story_facts['sources_summary'] = []
    
    return story_facts

