#!/usr/bin/env python3
"""
Story Facts Research Tool - Second Pass
Extracts narrative elements and story facts for extended content.

Usage:
    python3 scripts/research_family_story_facts.py <family_id_or_name> [--save] [--update]
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
from config.unified_config import get_config
import psycopg
from psycopg.rows import dict_row

# Import LLM service
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
    from app.llm.services import LLMService
except ImportError:
    from blueprints.planning_llm import LLMService


# Prompt templates
FACT_EXTRACTION_PROMPT = """Surname: "{{SURNAME}}"

Text chunk to analyse:

<<<
{{CHUNK_TEXT}}
>>>

Task:

1. Read the text carefully and ignore:
   - generic genealogy advice,
   - site boilerplate,
   - advertising or product pitches.

2. Extract ONLY information that clearly concerns the {{SURNAME}} family/clan:
   - named individuals,
   - titles/roles,
   - key events or turning points,
   - important places linked to the family,
   - legends / notorious episodes,
   - recurring themes (e.g. royal service, rebellion, exile).

3. Represent everything as a JSON object with this shape:

{{
  "time_span": {{
    "earliest_century": "string or 'unknown'",
    "latest_century": "string or 'unknown'",
    "notes": "string"
  }},
  "key_figures": [ ... ],
  "turning_points": [ ... ],
  "places": [ ... ],
  "legends_and_dark_episodes": [ ... ],
  "themes": [ ... ],
  "sources_summary": [ ... ],
  "quotations": [ ... ]
}}

Each field is OPTIONAL in this fragment; if you have nothing for a field, use an empty array or null.

4. Rules:
   - Use ONLY information that can reasonably be read from this chunk.
   - If the text itself labels something as legend, tradition, or "said to be", set `is_mostly_legend` to true and explain in `caution`.
   - If dates or details conflict inside this chunk, include the conflict in `uncertainty_flags` rather than resolving it.
   - Do NOT copy long sentences; paraphrase into short, dry notes.

5. If the chunk contains a clearly marked historical quotation, extract it verbatim and place it in the quotations array with:
   - the quoted text (exactly as found, verbatim),
   - the attributed speaker (if clearly stated),
   - the approximate date or period (if given),
   - a short context summary based on the text,
   - any explicit doubts (e.g. "tradition says…", "attributed to… but disputed").
   
   Do NOT include partial quotations or reconstruct missing lines.
   Do NOT guess speakers.
   Only extract quotations that appear explicitly as quoted or poetic lines.

Return ONLY valid JSON, no commentary."""

SYSTEM_PROMPT = """You are a cautious historical fact-extractor for surname and clan histories.

Your ONLY job is to extract structured, verifiable story facts about the family or clan
associated with the surname "{{SURNAME}}", from the given text.

You must NOT invent or infer specific dates, people, or places beyond what the text clearly supports."""

STORY_WRITING_SYSTEM_PROMPT = """You are a historical storyteller specialising in surnames, families, and Scottish clans.

You must write an immersive narrative history for the surname "{{SURNAME}}",
grounded in the structured JSON data provided, but with interpretive freedom for narrative flow.

CRITICAL OUTPUT FORMAT - YOU MUST FOLLOW THIS EXACTLY:
- You MUST output HTML format, NOT plain text and NOT Markdown.
- EVERY paragraph must be wrapped in <p> tags: <p>Your text here</p>
- EVERY section heading must use <h3> tags: <h3>Section Title</h3>
- EVERY quotation must use <blockquote> tags: <blockquote>Quote text</blockquote>
- Do NOT output plain text without HTML tags.
- Do NOT use ** for bold or ## for headings.
- Your entire output must be valid HTML.

CRITICAL RULE: You may NOT invent SPECIFIC factual claims (named people, exact dates, specific events, 
named places, battles, treaties, relationships) that are not present in the JSON.

HOWEVER, you MAY:
- Add general historical context (e.g., "the 13th century was marked by...")
- Make interpretive connections between facts
- Use thematic synthesis to weave facts together
- Create narrative flow with connecting phrases
- Infer general patterns from the data (e.g., "a pattern of royal service emerged")"""

STORY_WRITING_USER_PROMPT = """CRITICAL: Your output MUST be HTML format. Every paragraph needs <p> tags, every heading needs <h3> tags, every quotation needs <blockquote> tags. Do NOT output plain text.

Here is the structured data for the surname "{{SURNAME}}":

<<<JSON
{{SURNAME_JSON}}
>>>

Task:

1. Write a comprehensive, information-rich historical narrative of approximately {{WORD_TARGET}} words
   about the "{{SURNAME}}" family/clan.
   
   CRITICAL LENGTH REQUIREMENT: This narrative MUST be substantial - aim for {{WORD_TARGET}} words or more.
   Do NOT write a short summary. This should be a detailed, comprehensive article packed with information.
   
   CRITICAL: This narrative should be substantial and information-dense. Use ALL available data from the JSON:
   - Draw extensively from etymology, early_records, distribution_historic, distribution_modern
   - Include details from clan_association, heraldry, variants, migration, notables
   - Weave in story_facts (key_figures, turning_points, places, legends, themes)
   - Use quotations where available
   - Do NOT include template-like phrases or placeholder text
   - Do NOT start with generic statements like "An introductory paragraph about..."
   - Start directly with specific, factual content about {{SURNAME}}
   
   Writing style - CRITICAL:
   - Authoritative and direct, like a scholarly but accessible history book
   - DO NOT use flowery prose. AVOID phrases like:
     * "misty Highlands" → use "the Highlands" or "Highland Scotland"
     * "whispers of history linger" → delete this entirely
     * "woven a tale" → use "the family's history" or "the clan's story"
     * "indelible mark" → use "significant role" or "important contribution"
     * "born from the bloodlines" → use "descended from" or "originated from"
     * "shrouded in mystery" → use "uncertain" or "not fully documented"
   - Use clear, precise language that conveys facts and historical context
   - Write in a confident, informative tone - you are an expert historian
   - Focus on what happened, when, where, and why, rather than poetic descriptions
   - Be direct and factual, not evocative or atmospheric

2. Grounding in JSON facts - STRICT RULES:
   
   **FORBIDDEN (Hallucination):**
   - Do NOT invent specific named people not in `key_figures`
   - Do NOT invent specific dates not in `turning_points`, `early_records`, or other JSON fields
   - Do NOT invent specific events, battles, treaties, or named places not in the JSON
   - Do NOT invent specific relationships (e.g., "X was the son of Y") unless stated in JSON
   - Do NOT create specific historical episodes not in `turning_points` or `legends_and_dark_episodes`
   
   **ALLOWED (Interpretive Freedom):**
   - Add general historical context for the period (e.g., "The 13th century saw...", "Medieval Scotland was...")
   - Make interpretive connections: "This suggests...", "It appears that...", "This pattern indicates..."
   - Use thematic synthesis: connect facts through themes from `story_facts.themes`
   - Add evocative language and atmosphere: "The misty Highlands...", "In the shadow of..."
   - Create narrative flow: "Over the following decades", "In the generations that followed", "As time passed"
   - Infer general patterns: "A tradition of...", "The family's role in...", "This established a pattern of..."
   - Use conditional language for gaps: "Perhaps...", "It may be that...", "One can imagine..."

3. Structure - Comprehensive Coverage:
   - Begin with a substantive introductory paragraph that includes:
     * Specific etymology and meaning of the name from `etymology`
     * Geographic origins from `distribution_historic` and `early_records`
     * Time period and initial context
     * Do NOT use generic phrases - be specific and factual
   - Create 4–6 substantial titled sections using HTML heading tags, for example:
     <h3>A bloody birth</h3>, <h3>A dynasty is born</h3>, <h3>Rebellion and ruin</h3>, <h3>Legacy and diaspora</h3>.
     Choose titles that fit the JSON content. Each section should be substantial (200-400 words minimum).
     The total narrative should reach approximately {{WORD_TARGET}} words.
   - Within these sections, comprehensively weave together:
     * `story_facts.turning_points` (detailed accounts of key episodes with dates and places)
     * `story_facts.key_figures` (include names, titles, roles, and their significance)
     * `story_facts.places` (specific locations and their importance)
     * `story_facts.legends_and_dark_episodes` (with appropriate uncertainty signals)
     * `story_facts.themes` (recurring patterns and characteristics)
     * `early_records` (specific early mentions and documents)
     * `clan_association` (clan connections and relationships)
     * `heraldry` (coat of arms, symbols, mottos)
     * `notables` (significant individuals and their achievements)
     * `migration` (movements and diaspora patterns)
   - Include a substantial section on modern distribution and legacy:
     * Draw from `distribution_modern` (current geographic spread)
     * Include `migration` patterns (where families moved and when)
     * Reference `genealogy_resources` if relevant
   - End with a substantive closing that ties together the family's historical trajectory

4. Handling uncertainty and legend:
   - Where `uncertainty_flags` or `is_mostly_legend` are true, clearly signal this in the prose
     (e.g. "tradition claims that…", "later storytellers blamed…", "historians disagree on whether…").
   - Do NOT silently convert doubtful material into firm fact.

5. Tone and Style:
   - Authoritative and direct, like a scholarly but accessible history book.
   - Avoid flowery prose, excessive adjectives, or overly dramatic language.
   - Use clear, precise language that conveys facts and historical context.
   - Write in a confident, informative tone - you are an expert historian.
   - Avoid phrases like "destined to", "weave a tale", "indelible mark" - be more direct.
   - Focus on what happened, when, where, and why, rather than poetic descriptions.
   - Write in your own words - do NOT copy source phrasing.
   - Balance factual grounding with narrative flow - the story should feel complete and engaging,
     even when the JSON data is sparse.
   - When data is limited, use general historical context and thematic interpretation to create
     a coherent narrative arc, but always signal uncertainty where appropriate.
   
6. Language and Spelling - CRITICAL:
   - You MUST use UK-British English spelling throughout.
   - Examples of Americanisms to AVOID (use British equivalents instead):
     * "color" → "colour"
     * "honor" → "honour"
     * "favor" → "favour"
     * "center" → "centre"
     * "theater" → "theatre"
     * "organize" → "organise"
     * "recognize" → "recognise"
     * "analyze" → "analyse"
     * "defense" → "defence"
     * "offense" → "offence"
     * "license" (verb) → "licence" (noun) / "license" (verb) - be careful with this one
     * "practice" (noun) → "practice" (noun) / "practise" (verb)
     * "traveled" → "travelled"
     * "canceled" → "cancelled"
     * "labeled" → "labelled"
     * "fulfill" → "fulfil"
     * "skilful" (not "skillful")
     * "toward" → "towards" (preferred in UK English)
     * "among" → "amongst" (preferred in UK English, though "among" is acceptable)
   - Use British punctuation conventions (e.g., single quotes for quotations, full stops outside quotes when appropriate).
   - Use British date formats when mentioned (e.g., "15th March 1327" not "March 15, 1327").

7. Quotations rules - CRITICAL:
   - You may include quotations ONLY from the quotations array in the JSON for {{SURNAME}}.
   - Embed quotations naturally into the narrative flow - do NOT create a separate "Quotations" section.
   - For each quotation, follow this EXACT structure:
     a) Contextualisation in a <p> tag BEFORE the blockquote (e.g., "A verse traditionally attributed to...", "The King wrote...", etc.)
     b) ONLY the quoted text itself goes inside <blockquote> tags - nothing else
     c) Any additional notes or uncertainty signals go in a <p> tag AFTER the blockquote
   - CRITICAL: The contextualisation text goes OUTSIDE the blockquote, in regular <p> tags. Only the actual quoted text goes INSIDE <blockquote> tags.
   - Use the context_summary from the JSON to create the contextualisation
   - Signal uncertainty if uncertainty_flags exist (e.g., "traditionally attributed to…", "allegedly composed by…")
   - Do not overuse quotations; include 1–3 where they meaningfully enrich the narrative.
   - Format example (structure only - use actual quotations from {{SURNAME}} JSON):
     <p>A verse traditionally attributed to King David II reads:</p>
     
     <blockquote>By th' sword o' Abernethy, our clan doth stand<br>
     Through battle and strife, till freedom's land</blockquote>
     
     <p>While its accuracy is disputed, it remains a testament to the clan's enduring spirit.</p>
   
   - Notice: Contextualisation = <p> tag. Quoted text = <blockquote> tag. Notes = <p> tag.

8. Output format - ABSOLUTELY CRITICAL:
   - Your ENTIRE output must be HTML. Every single paragraph must be wrapped in <p> tags.
   - Example of correct format (this shows the structure you MUST follow):
     
     <p>An introductory paragraph about the family's origins and early history.</p>
     
     <h3>A bloody birth</h3>
     
     <p>Details about early events and key figures from the JSON data. Use only facts from the provided JSON for {{SURNAME}}.</p>
     
     <p>Contextualisation leading to the quotation (e.g., "A verse traditionally attributed to...", "The King wrote...").</p>
     
     <blockquote>ONLY the quoted text itself goes here<br>
     More quoted lines if it's a poem<br>
     Nothing else - no contextualisation, no notes</blockquote>
     
     <p>Any additional notes or continuation of narrative after the quotation.</p>
   
   - DO NOT output plain text without HTML tags.
   - DO NOT use ** for bold or ## for headings.
   - DO NOT use Markdown formatting.
   - EVERY paragraph = <p>...</p>
   - EVERY heading = <h3>...</h3>
   - EVERY quotation = <blockquote>...</blockquote>
   - CRITICAL: Use ONLY data from the provided JSON for {{SURNAME}}. Do NOT include information about other families or clans.
   - No JSON, no bullet-point schema, and no references or footnotes.

Now write the narrative in HTML format. Remember: 
- EVERY paragraph must start with <p> and end with </p>
- Do NOT write any text that is not inside HTML tags
- This MUST be a comprehensive, detailed narrative of approximately {{WORD_TARGET}} words
- Use ALL available data from the JSON - do not skip sections
- Each section should be substantial (200-400 words)
- Pack the narrative with specific details, names, dates, places, and events from the JSON

Your output should look like this:

<p>First paragraph here with specific details from the JSON.</p>

<h3>Section heading</h3>

<p>Second paragraph here with more details.</p>

<p>Third paragraph here continuing the narrative.</p>

Start writing now with <p> tags. Make it comprehensive and detailed."""


def get_family_context(family_id: Optional[int] = None, family_name: Optional[str] = None) -> Optional[Dict]:
    """Get existing family data from database."""
    if not family_id and not family_name:
        return None
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            if family_id:
                cur.execute("SELECT * FROM families WHERE id = %s", (family_id,))
            else:
                cur.execute("SELECT * FROM families WHERE name = %s", (family_name,))
            
            family = cur.fetchone()
            if not family:
                return None
            
            return {'family': dict(family)}


def load_template() -> Dict:
    """Load JSON template from file."""
    template_path = Path(__file__).parent.parent / 'data' / 'research_data_template.json'
    with open(template_path, 'r') as f:
        return json.load(f)


def perform_web_search(query: str, max_results: int = 5) -> List[Dict]:
    """Perform web search and return results."""
    import requests
    import os
    from bs4 import BeautifulSoup
    
    results = []
    
    # Try Google Custom Search API first
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY', '')
    engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')
    
    if api_key and engine_id:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': engine_id,
                'q': query,
                'num': min(max_results, 10)
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', [])[:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'rank': len(results) + 1
                    })
                return results
        except Exception as e:
            print(f"    Google Search API failed: {e}, trying DuckDuckGo...")
    
    # Fallback to DuckDuckGo HTML scraping
    try:
        ddg_url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        params = {'q': query}
        response = requests.get(ddg_url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for i, result in enumerate(soup.select('.result')[:max_results]):
                title_elem = result.select_one('.result__a')
                snippet_elem = result.select_one('.result__snippet')
                if title_elem:
                    url = title_elem.get('href', '')
                    # Extract actual URL from DuckDuckGo redirect
                    if url.startswith('//') and 'uddg=' in url:
                        from urllib.parse import unquote, parse_qs, urlparse
                        try:
                            parsed = urlparse('https:' + url)
                            if 'uddg' in parsed.query:
                                params = parse_qs(parsed.query)
                                if 'uddg' in params:
                                    url = unquote(params['uddg'][0])
                        except:
                            pass
                    elif url.startswith('//'):
                        url = 'https:' + url
                    
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': url,
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'rank': len(results) + 1
                    })
            return results
    except Exception as e:
        print(f"    DuckDuckGo search failed: {e}")
    
    return []


def fetch_page_content(url: str) -> Optional[str]:
    """Fetch and extract text content from a web page."""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import unquote, urlparse
    
    try:
        # Fix DuckDuckGo redirect URLs
        if url.startswith('//'):
            # Extract actual URL from DuckDuckGo redirect
            if 'uddg=' in url:
                # Parse the encoded URL
                parsed = urlparse('https:' + url)
                if 'uddg' in parsed.query:
                    from urllib.parse import parse_qs
                    params = parse_qs(parsed.query)
                    if 'uddg' in params:
                        url = unquote(params['uddg'][0])
            else:
                url = 'https:' + url
        elif not url.startswith('http'):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            # Get text
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
    return None


def chunk_text(text: str, chunk_size: int = 3000) -> List[str]:
    """Split text into chunks of approximately chunk_size characters."""
    chunks = []
    words = text.split()
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        if current_size + word_size > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


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


def generate_narrative(surname: str, surname_json: Dict, 
                       llm_service: LLMService, word_target: int = 2500) -> Optional[str]:
    """Generate immersive narrative using Prompt 2."""
    # Build prompt
    system_prompt = STORY_WRITING_SYSTEM_PROMPT.replace('{{SURNAME}}', surname)
    user_prompt = STORY_WRITING_USER_PROMPT.replace('{{SURNAME}}', surname)
    user_prompt = user_prompt.replace('{{WORD_TARGET}}', str(word_target))
    user_prompt = user_prompt.replace('{{SURNAME_JSON}}', json.dumps(surname_json, indent=2))
    
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


def extract_facts_from_chunk(surname: str, chunk_text: str, 
                             existing_story_facts: Optional[Dict],
                             llm_service: LLMService) -> Optional[Dict]:
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
        import re
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


def main():
    """Main story facts research workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Story Facts Research Tool - Second Pass')
    parser.add_argument('family', help='Family ID or name')
    parser.add_argument('--save', action='store_true', help='Save JSON to file and update database')
    parser.add_argument('--no-update', action='store_true', help='Save to file but do NOT update database')
    parser.add_argument('--dry-run', action='store_true', help='Validate but do not update database')
    parser.add_argument('--model', type=str, default='llama3.2:latest', help='LLM model name')
    parser.add_argument('--word-target', type=int, default=2500, help='Target word count for narrative (default: 2500)')
    parser.add_argument('--narrative-only', action='store_true', help='Generate narrative from existing story_facts (skip fact extraction)')
    
    args = parser.parse_args()
    
    # Get family context
    try:
        family_id = int(args.family)
        family_name = None
    except ValueError:
        family_id = None
        family_name = args.family
    
    print("Fetching family context from database...")
    context = get_family_context(family_id, family_name)
    if not context:
        print(f"Error: Family not found: {args.family}")
        return 1
    
    family_id = context['family']['id']
    family_name = context['family']['name']
    
    print(f"\n{'='*60}")
    print(f"Story Facts Research (Second Pass): {family_name} (ID: {family_id})")
    print(f"{'='*60}\n")
    
    # Load existing research data
    template = load_template()
    existing_story_facts = template.get('story_facts', {})
    
    # Check if family already has research_data
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
            existing = cur.fetchone()
            if existing and existing['research_data']:
                import json
                existing_data = existing['research_data']
                if isinstance(existing_data, str):
                    existing_data = json.loads(existing_data)
                if 'story_facts' in existing_data:
                    existing_story_facts = existing_data['story_facts']
                    print(f"  Loaded existing story_facts")
    
    # Initialize LLM service
    print("Initializing LLM service...")
    llm_service = LLMService()
    
    # If narrative-only, skip fact extraction
    if args.narrative_only:
        print("\nNarrative-only mode: Generating narrative from existing story_facts...")
        # Load existing research data
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
                existing = cur.fetchone()
                if existing and existing['research_data']:
                    import json
                    existing_data = existing['research_data']
                    if isinstance(existing_data, str):
                        existing_data = json.loads(existing_data)
                    research_data = existing_data
                else:
                    print("Error: No existing research_data found. Run fact extraction first.")
                    return 1
        
        narrative = generate_narrative(family_name, research_data, llm_service, word_target=args.word_target)
        
        if narrative:
            if 'metadata' not in research_data:
                research_data['metadata'] = {}
            research_data['metadata']['narrative'] = narrative
            research_data['metadata']['narrative_word_count'] = len(narrative.split())
            print(f"\n✓ Generated narrative ({len(narrative.split())} words)")
            
            # Also save narrative to separate text file
            if args.save:
                narrative_file = f"data/narrative_{family_name.replace(' ', '_')}_{family_id}.md"
                with open(narrative_file, 'w') as f:
                    f.write(f"# {family_name}: A Historical Narrative\n\n")
                    f.write(narrative)
                print(f"✓ Narrative saved to: {narrative_file}")
        else:
            print("\n✗ Failed to generate narrative")
            return 1
        
        # Save and update
        if args.save:
            output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}_story_facts.json"
            with open(output_file, 'w') as f:
                json.dump(research_data, f, indent=2)
            print(f"✓ Saved to: {output_file}")
        
        should_update = args.save and not args.no_update
        if should_update:
            import importlib.util
            research_family_path = Path(__file__).parent / 'research_family.py'
            spec = importlib.util.spec_from_file_location("research_family", research_family_path)
            research_family = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(research_family)
            
            success, message = research_family.update_family_research(family_id, research_data, dry_run=args.dry_run)
            if success:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                return 1
        
        return 0
    
    # Search for story-focused content
    print("\nSearching for story-focused content...")
    search_queries = [
        f"{family_name} clan history",
        f"{family_name} Scottish history",
        f"{family_name} key figures",
        f"{family_name} historical events",
        f"{family_name} legends stories"
    ]
    
    all_search_results = []
    for query in search_queries:
        print(f"  Searching: {query}")
        results = perform_web_search(query, max_results=3)
        all_search_results.extend(results)
        time.sleep(1)  # Rate limiting
    
    print(f"  Found {len(all_search_results)} search results")
    
    # Fetch and process pages
    print("\nFetching and processing pages...")
    accumulated_facts = existing_story_facts.copy() if existing_story_facts else {}
    
    for i, result in enumerate(all_search_results[:10], 1):  # Limit to top 10
        print(f"\n  Processing {i}/{min(10, len(all_search_results))}: {result['title']}")
        print(f"    URL: {result['url']}")
        
        # Fetch page content
        content = fetch_page_content(result['url'])
        if not content:
            print("    Skipping: Could not fetch content")
            continue
        
        # Chunk the content
        chunks = chunk_text(content, chunk_size=3000)
        print(f"    Split into {len(chunks)} chunks")
        
        # Process each chunk
        for j, chunk in enumerate(chunks, 1):
            print(f"    Processing chunk {j}/{len(chunks)}...")
            facts = extract_facts_from_chunk(
                family_name,
                chunk,
                accumulated_facts if accumulated_facts else None,
                llm_service
            )
            
            if facts:
                # Merge facts into accumulated_facts with deduplication
                for key in ['key_figures', 'turning_points', 'places', 
                           'legends_and_dark_episodes', 'themes', 'sources_summary', 'quotations']:
                    if key in facts and facts[key]:
                        if key not in accumulated_facts:
                            accumulated_facts[key] = []
                        if isinstance(accumulated_facts[key], list):
                            # Merge with deduplication
                            existing_items = accumulated_facts[key]
                            for new_item in facts[key]:
                                # Check for duplicates based on key-specific criteria
                                is_duplicate = False
                                
                                if key == 'quotations':
                                    # For quotations: check by identical text or similar speaker+text
                                    for existing in existing_items:
                                        if isinstance(existing, dict) and isinstance(new_item, dict):
                                            # Exact text match
                                            if existing.get('quoted_text', '').strip().lower() == new_item.get('quoted_text', '').strip().lower():
                                                is_duplicate = True
                                                # If attribution differs, merge uncertainty flags
                                                if existing.get('speaker') != new_item.get('speaker'):
                                                    if 'uncertainty_flags' not in existing:
                                                        existing['uncertainty_flags'] = []
                                                    existing['uncertainty_flags'].append(
                                                        f"Also attributed in one source to {new_item.get('speaker', 'unknown')}."
                                                    )
                                                break
                                
                                elif key == 'key_figures':
                                    # For key_figures: check by name
                                    for existing in existing_items:
                                        if isinstance(existing, dict) and isinstance(new_item, dict):
                                            if existing.get('name', '').strip().lower() == new_item.get('name', '').strip().lower():
                                                is_duplicate = True
                                                break
                                
                                elif key == 'turning_points':
                                    # For turning_points: check by id or title
                                    for existing in existing_items:
                                        if isinstance(existing, dict) and isinstance(new_item, dict):
                                            if existing.get('id') == new_item.get('id') or \
                                               existing.get('title', '').strip().lower() == new_item.get('title', '').strip().lower():
                                                is_duplicate = True
                                                break
                                
                                elif key == 'places':
                                    # For places: check by name
                                    for existing in existing_items:
                                        if isinstance(existing, dict) and isinstance(new_item, dict):
                                            if existing.get('name', '').strip().lower() == new_item.get('name', '').strip().lower():
                                                is_duplicate = True
                                                break
                                
                                elif key == 'themes':
                                    # For themes: check by exact string match
                                    if isinstance(new_item, str):
                                        if new_item.strip().lower() in [t.strip().lower() for t in existing_items if isinstance(t, str)]:
                                            is_duplicate = True
                                    else:
                                        # If it's not a string, skip deduplication for themes
                                        pass
                                
                                if not is_duplicate:
                                    existing_items.append(new_item)
                            
                            accumulated_facts[key] = existing_items
                
                # Update time_span if we have better info
                if 'time_span' in facts and facts['time_span']:
                    if 'time_span' not in accumulated_facts:
                        accumulated_facts['time_span'] = {}
                    ts = facts['time_span']
                    if ts.get('earliest_century') and ts['earliest_century'] != 'unknown':
                        if not accumulated_facts['time_span'].get('earliest_century') or \
                           accumulated_facts['time_span']['earliest_century'] == 'unknown':
                            accumulated_facts['time_span']['earliest_century'] = ts['earliest_century']
                    if ts.get('latest_century') and ts['latest_century'] != 'unknown':
                        if not accumulated_facts['time_span'].get('latest_century') or \
                           accumulated_facts['time_span']['latest_century'] == 'unknown':
                            accumulated_facts['time_span']['latest_century'] = ts['latest_century']
            
            time.sleep(1)  # Rate limiting
    
    # Post-process accumulated_facts to normalize structure
    accumulated_facts = post_process_story_facts(accumulated_facts)
    
    # Load existing research data and merge with accumulated_facts
    research_data = None
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
            existing = cur.fetchone()
            if existing and existing['research_data']:
                import json
                existing_data = existing['research_data']
                if isinstance(existing_data, str):
                    existing_data = json.loads(existing_data)
                existing_data['story_facts'] = accumulated_facts
                research_data = existing_data
            else:
                research_data = template.copy()
                research_data['surname'] = family_name
                research_data['story_facts'] = accumulated_facts
    
    if not research_data:
        research_data = template.copy()
        research_data['surname'] = family_name
        research_data['story_facts'] = accumulated_facts
    
    research_data['surname'] = family_name
    if 'metadata' not in research_data:
        research_data['metadata'] = {}
    research_data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Apply Prompt 2 (Story Writing) - Generate final narrative
    print("\n" + "="*60)
    print("Generating immersive narrative (Prompt 2)...")
    print("="*60)
    
    narrative = generate_narrative(family_name, research_data, llm_service, word_target=args.word_target)
    
    if narrative:
        # Store narrative in research_data metadata
        if 'metadata' not in research_data:
            research_data['metadata'] = {}
        research_data['metadata']['narrative'] = narrative
        research_data['metadata']['narrative_word_count'] = len(narrative.split())
        print(f"\n✓ Generated narrative ({len(narrative.split())} words)")
        
        # Also save narrative to separate text file
        if args.save:
            narrative_file = f"data/narrative_{family_name.replace(' ', '_')}_{family_id}.md"
            with open(narrative_file, 'w') as f:
                f.write(f"# {family_name}: A Historical Narrative\n\n")
                f.write(narrative)
            print(f"✓ Narrative saved to: {narrative_file}")
    else:
        print("\n✗ Failed to generate narrative")
    
    # Save to file
    if args.save:
        output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}_story_facts.json"
        with open(output_file, 'w') as f:
            json.dump(research_data, f, indent=2)
        print(f"\n✓ Saved to: {output_file}")
    
    # Update database
    should_update = args.save and not args.no_update
    if should_update:
        # Import validation and update functions
        import importlib.util
        research_family_path = Path(__file__).parent / 'research_family.py'
        spec = importlib.util.spec_from_file_location("research_family", research_family_path)
        research_family = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(research_family)
        
        success, message = research_family.update_family_research(family_id, research_data, dry_run=args.dry_run)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            return 1
    
    print(f"\n{'='*60}")
    print("Story Facts Research Complete")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

