#!/usr/bin/env python3
"""
Web-Research-Based Family Research Tool
Performs targeted web research for each research section separately.

Usage:
    python3 scripts/research_family_web.py <family_id_or_name> [--sections <section1,section2>] [--save] [--update]
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
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


# Research sections and their specific search strategies
RESEARCH_SECTIONS = {
    'etymology': {
        'name': 'Etymology',
        'search_queries': [
            '{surname} surname etymology',
            '{surname} name origin meaning',
            '{surname} surname dictionary',
            '{surname} onomastics',
            '{surname} name etymology Scotland'
        ],
        'known_sources': [
            'ancestry.com surname meaning',
            'houseofnames.com',
            'surnamedb.com',
            'behindthename.com',
            'etymonline.com'
        ],
        'focus': 'language origins, root words, name meaning, name type'
    },
    'early_records': {
        'name': 'Early Records',
        'search_queries': [
            '{surname} earliest records Scotland',
            '{surname} first mention Scotland',
            '{surname} medieval records',
            '{surname} historical records Scotland',
            '{surname} earliest attestation'
        ],
        'known_sources': [
            'scotlandspeople.gov.uk',
            'nationalarchives.gov.uk',
            'familysearch.org',
            'ancestry.com historical records'
        ],
        'focus': 'earliest documented appearances, dates, locations, record types'
    },
    'distribution_historic': {
        'name': 'Historic Distribution',
        'search_queries': [
            '{surname} distribution Scotland historical',
            '{surname} surname map Scotland',
            '{surname} geographic distribution 1800s',
            '{surname} census distribution Scotland',
            '{surname} surname concentration Scotland'
        ],
        'known_sources': [
            'surnamedb.com distribution',
            'ancestry.com surname distribution',
            'forebears.io',
            'scotlandspeople.gov.uk census'
        ],
        'focus': 'pre-1900 geographic distribution, regional concentrations'
    },
    'distribution_modern': {
        'name': 'Modern Distribution',
        'search_queries': [
            '{surname} modern distribution',
            '{surname} surname frequency Scotland',
            '{surname} surname statistics',
            '{surname} name frequency by country',
            '{surname} surname ranking'
        ],
        'known_sources': [
            'forebears.io',
            'surnamedb.com',
            'ancestry.com surname distribution',
            'worldnames.publicprofiler.org'
        ],
        'focus': 'current/modern distribution by country, frequency, trends'
    },
    'clan_association': {
        'name': 'Clan Association',
        'search_queries': [
            '{surname} Scottish clan',
            '{surname} clan sept Scotland',
            '{surname} Scottish clan association',
            '{surname} Lord Lyon Scotland',
            '{surname} clan tartan'
        ],
        'known_sources': [
            'clan.com',
            'scotclans.com',
            'electricscotland.com',
            'scotsclans.com',
            'lyon-court.com'
        ],
        'focus': 'Scottish clan/sept connections, official status, territorial associations'
    },
    'heraldry': {
        'name': 'Heraldry',
        'search_queries': [
            '{surname} coat of arms Scotland',
            '{surname} heraldry Scotland',
            '{surname} arms Lord Lyon',
            '{surname} tartan Scotland',
            '{surname} family motto Scotland'
        ],
        'known_sources': [
            'lyon-court.com',
            'scotlandspeople.gov.uk heraldry',
            'tartanregister.gov.uk',
            'clan.com tartan',
            'heraldry-wiki.com'
        ],
        'focus': 'coats of arms, mottoes, tartans, heraldic records'
    },
    'variants': {
        'name': 'Variants',
        'search_queries': [
            '{surname} spelling variants',
            '{surname} surname variations',
            '{surname} name variants',
            '{surname} alternative spellings',
            '{surname} surname forms'
        ],
        'known_sources': [
            'ancestry.com surname variations',
            'familysearch.org surname variants',
            'surnamedb.com variants'
        ],
        'focus': 'spelling variants, language forms, related surnames'
    },
    'migration': {
        'name': 'Migration',
        'search_queries': [
            '{surname} migration Scotland',
            '{surname} emigration Scotland',
            '{surname} diaspora Scotland',
            '{surname} Scottish migration patterns',
            '{surname} Highland Clearances'
        ],
        'known_sources': [
            'scotlandspeople.gov.uk emigration',
            'nationalarchives.gov.uk migration',
            'ancestry.com migration records'
        ],
        'focus': 'movement patterns, diaspora, emigration waves, historical migration'
    },
    'notables': {
        'name': 'Notables',
        'search_queries': [
            '{surname} famous people Scotland',
            '{surname} notable Scots',
            '{surname} historical figures Scotland',
            '{surname} Scottish biography',
            '{surname} prominent Scots'
        ],
        'known_sources': [
            'wikipedia.org',
            'biography.com',
            'scottish-places.info',
            'electricscotland.com'
        ],
        'focus': 'notable individuals with the surname, verifiable biographical information'
    },
    'cultural_notes': {
        'name': 'Cultural Notes',
        'search_queries': [
            '{surname} Scottish culture',
            '{surname} literature references',
            '{surname} Scottish folklore',
            '{surname} cultural associations',
            '{surname} Scottish heritage'
        ],
        'known_sources': [
            'wikipedia.org',
            'electricscotland.com',
            'scotland.org',
            'visitscotland.com'
        ],
        'focus': 'literary references, cultural associations, folklore, stereotypes'
    },
    'genealogy_resources': {
        'name': 'Genealogy Resources',
        'search_queries': [
            '{surname} family society Scotland',
            '{surname} genealogy resources',
            '{surname} family history Scotland',
            '{surname} one-name study',
            '{surname} family records Scotland'
        ],
        'known_sources': [
            'familysearch.org',
            'scotlandspeople.gov.uk',
            'ancestry.com',
            'scottishgenealogy.org',
            'scotsgenealogy.com'
        ],
        'focus': 'family societies, published histories, record-rich areas, research resources'
    }
}


def get_family_context(family_id: Optional[int] = None, family_name: Optional[str] = None) -> Optional[Dict]:
    """Get existing family data and relationships from database."""
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
            
            family_id = family['id']
            
            # Get relationships
            cur.execute("""
                SELECT alias_name FROM family_aliases WHERE family_id = %s
            """, (family_id,))
            aliases = [row['alias_name'] for row in cur.fetchall()]
            
            cur.execute("""
                SELECT f2.name as variant_name
                FROM family_spellings fs
                JOIN families f2 ON fs.family_id = f2.id
                WHERE fs.spelling_of_id = %s
            """, (family_id,))
            variants = [row['variant_name'] for row in cur.fetchall()]
            
            cur.execute("""
                SELECT f2.name as sept_name
                FROM family_septs fs
                JOIN families f2 ON fs.family_id = f2.id
                WHERE fs.sept_of_id = %s
            """, (family_id,))
            septs = [row['sept_name'] for row in cur.fetchall()]
            
            cur.execute("""
                SELECT f2.name as parent_name
                FROM family_spellings fs
                JOIN families f2 ON fs.spelling_of_id = f2.id
                WHERE fs.family_id = %s
            """, (family_id,))
            spelling_of = [row['parent_name'] for row in cur.fetchall()]
            
            cur.execute("""
                SELECT resource_type, resource_category, resource_value
                FROM family_resources
                WHERE family_id = %s
            """, (family_id,))
            resources = cur.fetchall()
            
            return {
                'family': dict(family),
                'aliases': aliases,
                'variants': variants,
                'septs': septs,
                'spelling_of': spelling_of,
                'resources': [dict(r) for r in resources]
            }


def load_template() -> Dict:
    """Load JSON template from file."""
    template_path = Path(__file__).parent.parent / 'data' / 'research_data_template.json'
    with open(template_path, 'r') as f:
        return json.load(f)


def load_research_guide_section(section: str) -> str:
    """Load the specific section from research guide."""
    guide_path = Path(__file__).parent.parent / 'docs' / 'surname_research_guide.md'
    if not guide_path.exists():
        return ""
    
    with open(guide_path, 'r') as f:
        content = f.read()
    
    # Extract section content (simple approach - look for section headers)
    section_num = list(RESEARCH_SECTIONS.keys()).index(section) + 1
    section_header = f"## {section_num}. `{section}`"
    
    # Find the section and extract until next section
    start_idx = content.find(section_header)
    if start_idx == -1:
        return ""
    
    # Find next section (## X. `section_name`)
    import re
    next_section_match = re.search(r'^## \d+\. `', content[start_idx + len(section_header):], re.MULTILINE)
    if next_section_match:
        end_idx = start_idx + len(section_header) + next_section_match.start()
        return content[start_idx:end_idx]
    else:
        return content[start_idx:]


def post_process_research_data(data: Dict) -> Dict:
    """Post-process research data to fix common issues."""
    # Fix root_words structure
    if 'etymology' in data and 'root_words' in data['etymology']:
        root_words = data['etymology']['root_words']
        if root_words and isinstance(root_words, list):
            fixed = []
            for item in root_words:
                if isinstance(item, str):
                    # Convert string to object
                    fixed.append({
                        'language': 'Unknown',
                        'form': item,
                        'meaning': ''
                    })
                elif isinstance(item, dict):
                    fixed.append(item)
            data['etymology']['root_words'] = fixed
    
    # Fix earliest_known_forms structure
    if 'etymology' in data and 'earliest_known_forms' in data['etymology']:
        forms = data['etymology']['earliest_known_forms']
        if forms and isinstance(forms, list):
            fixed = []
            for item in forms:
                if isinstance(item, str):
                    # Convert string to object
                    fixed.append({
                        'spelling': item,
                        'approx_date': '',
                        'region': None,
                        'source_hint': ''
                    })
                elif isinstance(item, dict):
                    fixed.append(item)
            data['etymology']['earliest_known_forms'] = fixed
    
    # Fix year fields (never use 0, use null)
    if 'early_records' in data:
        er = data['early_records']
        if 'earliest_attestation' in er:
            att = er['earliest_attestation']
            if 'year' in att:
                year = att['year']
                if year == 0 or (isinstance(year, int) and year < 100):
                    # Likely error - set to null
                    att['year'] = None
                    att['approximate'] = True
                elif isinstance(year, int) and year < 1000:
                    # Probably missing digits (e.g., 12, 13, 15 are likely 1100s, 1200s, 1500s)
                    # But without context, safer to set to null
                    att['year'] = None
                    att['approximate'] = True
                    if 'record_notes' not in er:
                        er['record_notes'] = ''
                    er['record_notes'] += f" Note: Original year value ({year}) appeared incorrect and was set to null."
        
        # Fix other_attestations - remove entries with invalid years
        if 'other_attestations' in er and isinstance(er['other_attestations'], list):
            fixed_attestations = []
            for item in er['other_attestations']:
                if item and isinstance(item, dict):
                    year = item.get('year')
                    # Only keep if year is valid (>= 1000) or null
                    if year is None or (isinstance(year, int) and year >= 1000):
                        # Also fix invalid years in attestations
                        if isinstance(year, int) and year < 1000:
                            item['year'] = None
                            item['approximate'] = True
                        fixed_attestations.append(item)
            er['other_attestations'] = fixed_attestations
    
    # Fix distribution_historic structure
    if 'distribution_historic' in data and 'regions' in data['distribution_historic']:
        regions = data['distribution_historic']['regions']
        if regions and isinstance(regions, list):
            fixed = []
            for item in regions:
                if isinstance(item, dict):
                    # Convert to proper structure
                    fixed_item = {
                        'country': item.get('country', item.get('name', 'Unknown')),
                        'subregion_type': item.get('subregion_type', 'county'),
                        'subregion_name': item.get('subregion_name', item.get('name', '')),
                        'relative_frequency': item.get('relative_frequency', item.get('qualitative_frequency', 'unknown')),
                        'evidence_hint': item.get('evidence_hint', '')
                    }
                    fixed.append(fixed_item)
            data['distribution_historic']['regions'] = fixed
    
    # Fix distribution_modern structure
    if 'distribution_modern' in data and 'by_country' in data['distribution_modern']:
        countries = data['distribution_modern']['by_country']
        if countries and isinstance(countries, list):
            fixed = []
            for item in countries:
                if isinstance(item, dict):
                    # Convert frequency number to relative_frequency enum
                    freq = item.get('frequency')
                    if isinstance(freq, (int, float)):
                        if freq > 0.01:
                            rel_freq = 'very_high'
                        elif freq > 0.001:
                            rel_freq = 'high'
                        elif freq > 0.0001:
                            rel_freq = 'medium'
                        elif freq > 0.00001:
                            rel_freq = 'low'
                        else:
                            rel_freq = 'very_low'
                    else:
                        rel_freq = item.get('relative_frequency', 'unknown')
                    
                    fixed_item = {
                        'country': item.get('country', ''),
                        'relative_frequency': rel_freq,
                        'approx_rank': item.get('approx_rank'),
                        'trend': item.get('trend', 'unknown')
                    }
                    fixed.append(fixed_item)
            data['distribution_modern']['by_country'] = fixed
    
    # Fix heraldry structure
    if 'heraldry' in data:
        h = data['heraldry']
        # Fix arms structure
        if 'arms' in h and isinstance(h['arms'], list):
            fixed_arms = []
            for arm in h['arms']:
                if isinstance(arm, dict):
                    fixed_arm = {
                        'armiger_name': arm.get('armiger_name', arm.get('individual_armiger', 'Unknown')),
                        'jurisdiction': arm.get('jurisdiction', 'Scotland'),
                        'approx_date': arm.get('approx_date'),
                        'blazon': arm.get('blazon', arm.get('description', '')),
                        'notes': arm.get('notes', '')
                    }
                    fixed_arms.append(fixed_arm)
            h['arms'] = fixed_arms
        
        # Fix mottoes structure
        if 'mottoes' in h and isinstance(h['mottoes'], list):
            fixed_mottoes = []
            for motto in h['mottoes']:
                if isinstance(motto, dict):
                    fixed_motto = {
                        'text': motto.get('text', ''),
                        'language': motto.get('language', 'Latin'),
                        'translation': motto.get('translation'),
                        'attribution': motto.get('attribution', '')
                    }
                    fixed_mottoes.append(fixed_motto)
            h['mottoes'] = fixed_mottoes
    
    # Fix migration phases structure
    if 'migration' in data and 'phases' in data['migration']:
        phases = data['migration']['phases']
        if phases and isinstance(phases, list):
            fixed_phases = []
            for phase in phases:
                if isinstance(phase, dict):
                    from_to = phase.get('from/to_regions', [])
                    if isinstance(from_to, list):
                        # Try to split from/to
                        if len(from_to) > 1:
                            from_regions = from_to[:len(from_to)//2] if len(from_to) > 2 else [from_to[0]]
                            to_regions = from_to[len(from_to)//2:] if len(from_to) > 2 else from_to[1:]
                        else:
                            from_regions = []
                            to_regions = from_to
                    else:
                        from_regions = phase.get('from_regions', [])
                        to_regions = phase.get('to_regions', [])
                    
                    fixed_phase = {
                        'period': phase.get('period', ''),
                        'from_regions': from_regions if isinstance(from_regions, list) else [],
                        'to_regions': to_regions if isinstance(to_regions, list) else [],
                        'drivers': phase.get('drivers', phase.get('main_drivers', [])),
                        'evidence_hint': phase.get('evidence_hint', '')
                    }
                    fixed_phases.append(fixed_phase)
            data['migration']['phases'] = fixed_phases
    
    # Fix cultural_notes - remove null from uncertainty_flags and remove source_hint
    if 'cultural_notes' in data:
        cn = data['cultural_notes']
        if 'uncertainty_flags' in cn and isinstance(cn['uncertainty_flags'], list):
            cn['uncertainty_flags'] = [f for f in cn['uncertainty_flags'] if f is not None]
        if 'source_hint' in cn:
            del cn['source_hint']
    
    return data


def perform_web_search(query: str, max_results: int = 5) -> List[Dict]:
    """Perform web search and return results.
    
    Tries multiple search engines in order:
    1. Google Custom Search API (if configured)
    2. Bing Web Search API (if configured)
    3. SerpAPI (if configured)
    4. DuckDuckGo HTML scraping (fallback)
    """
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
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', [])[:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'rank': len(results) + 1
                    })
                if results:
                    return results
        except Exception as e:
            print(f"    Google Search API failed: {e}")
    
    # Try Bing Web Search API
    bing_key = os.getenv('BING_SEARCH_API_KEY', '')
    if bing_key:
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {'Ocp-Apim-Subscription-Key': bing_key}
            params = {'q': query, 'count': min(max_results, 10)}
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('webPages', {}).get('value', [])[:max_results]:
                    results.append({
                        'title': item.get('name', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('snippet', ''),
                        'rank': len(results) + 1
                    })
                if results:
                    return results
        except Exception as e:
            print(f"    Bing Search API failed: {e}")
    
    # Try SerpAPI
    serpapi_key = os.getenv('SERPAPI_KEY', '')
    if serpapi_key:
        try:
            url = "https://serpapi.com/search"
            params = {
                'api_key': serpapi_key,
                'q': query,
                'engine': 'google',
                'num': min(max_results, 10)
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('organic_results', [])[:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'rank': len(results) + 1
                    })
                if results:
                    return results
        except Exception as e:
            print(f"    SerpAPI failed: {e}")
    
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
            # DuckDuckGo result structure
            for i, result in enumerate(soup.select('.result')[:max_results]):
                title_elem = result.select_one('.result__a')
                snippet_elem = result.select_one('.result__snippet')
                if title_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'rank': len(results) + 1
                    })
            if results:
                return results
    except Exception as e:
        print(f"    DuckDuckGo search failed: {e}")
    
    # If all else fails, return empty
    print(f"    Warning: No search results for: {query}")
    return []


def research_section(section_key: str, section_config: Dict, surname: str, 
                     family_context: Dict, llm_service: LLMService, 
                     template_section: Dict) -> Dict:
    """Research a single section using web search and LLM synthesis."""
    print(f"\n{'='*60}")
    print(f"Researching: {section_config['name']}")
    print(f"{'='*60}")
    
    # Build search queries
    search_queries = [q.format(surname=surname) for q in section_config['search_queries']]
    known_sources = section_config['known_sources']
    
    print(f"  Search queries: {len(search_queries)}")
    print(f"  Known sources: {len(known_sources)}")
    
    # Perform web searches
    all_search_results = []
    for i, query in enumerate(search_queries[:3], 1):  # Limit to 3 queries per section
        print(f"  Searching: {query}")
        results = perform_web_search(query, max_results=3)
        all_search_results.extend(results)
        time.sleep(1)  # Rate limiting
    
    # Also search known sources
    for source in known_sources[:2]:  # Limit to 2 known sources
        query = f"{surname} {source}"
        print(f"  Searching known source: {source}")
        results = perform_web_search(query, max_results=2)
        all_search_results.extend(results)
        time.sleep(1)
    
    print(f"  Total search results: {len(all_search_results)}")
    
    if not all_search_results:
        print("  Warning: No search results found")
        return template_section
    
    # Create synthesis prompt
    section_guide = load_research_guide_section(section_key)
    
    # Format search results for LLM
    results_text = "\n\n".join([
        f"Result {r['rank']}:\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for r in all_search_results[:10]  # Limit to top 10 results
    ])
    
    synthesis_prompt = f"""You are a surname research specialist. Your task is to synthesize information from multiple web search results about the {section_config['name']} of the surname "{surname}".

## Research Section: {section_config['name']}
## Focus: {section_config['focus']}

## Research Instructions:
{section_guide}

## Web Search Results:
{results_text}

## Family Context from Database:
- Is Clan: {family_context['family'].get('is_clan', False)}
- Is Canonical: {family_context['family'].get('spelling_of') is None}
- Aliases: {', '.join(family_context.get('aliases', [])) or 'None'}
- Variants: {', '.join(family_context.get('variants', [])) or 'None'}
- Septs: {', '.join(family_context.get('septs', [])) or 'None'}

## JSON Template for This Section:
{json.dumps(template_section, indent=2)}

## Your Task:
1. Analyze the web search results above
2. Compare information from multiple sources
3. Identify conflicts or uncertainties
4. Synthesize a definitive record for this research section
5. Populate the JSON structure with factual information only
6. Mark uncertainty explicitly in uncertainty_flags
7. Cite sources in source_hint fields

**Critical Requirements:**
- Only include information found in the search results
- Use `null` for unknown values (not `0` or empty strings)
- Use empty arrays `[]` when no items exist (not `null`)
- Mark uncertainty explicitly
- If sources conflict, note this in uncertainty_flags
- Be honest about confidence levels

**Data Structure Requirements:**
- For `root_words`: Each item must be an object with `language`, `form`, and `meaning` fields
- For `earliest_known_forms`: Each item must be an object with `spelling`, `approx_date`, `region` (or null), and `source_hint`
- For `year` fields: Use `null` for unknown, never use `0`. If approximate, set `approximate: true`
- For arrays: Always use `[]` when empty, never `null`
- For `other_attestations`: Only include if you have actual records, otherwise use empty array `[]`

**Output Format:**
Return ONLY valid JSON for this section, matching the template structure exactly. Do not include markdown code blocks or explanatory text - just the JSON object for this section.

Return the JSON for the {section_key} section:"""
    
    # Call LLM for synthesis
    print("  Synthesizing results with LLM...")
    try:
        if hasattr(llm_service, 'generate'):
            response = llm_service.generate(
                prompt=synthesis_prompt,
                model_name='llama3.2:latest',
                temperature=0.3,
                max_tokens=2000,
                timeout=120
            )
        else:
            messages = [{"role": "user", "content": synthesis_prompt}]
            result = llm_service.execute_llm_request(
                provider='ollama',
                model='llama3.2:latest',
                messages=messages,
                max_tokens=2000,
                temperature=0.3
            )
            if 'error' in result:
                print(f"  Error: {result['error']}")
                return template_section
            response = result.get('content', '')
        
        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                section_data = json.loads(json_match.group(0))
                print("  ✓ Section research complete")
                return section_data
            except json.JSONDecodeError:
                print("  Warning: Could not parse JSON from LLM response")
                return template_section
        else:
            print("  Warning: No JSON found in LLM response")
            return template_section
            
    except Exception as e:
        print(f"  Error during LLM synthesis: {e}")
        return template_section


def main():
    """Main web-research workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web-Research-Based Family Research Tool')
    parser.add_argument('family', help='Family ID or name')
    parser.add_argument('--sections', type=str, help='Comma-separated list of sections to research (default: all)')
    parser.add_argument('--save', action='store_true', help='Save JSON to file and update database')
    parser.add_argument('--update', action='store_true', help='Update database with research data (default when --save is used)')
    parser.add_argument('--no-update', action='store_true', help='Save to file but do NOT update database')
    parser.add_argument('--dry-run', action='store_true', help='Validate but do not update database')
    parser.add_argument('--model', type=str, default='llama3.2:latest', help='LLM model name')
    
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
    print(f"Web Research: {family_name} (ID: {family_id})")
    print(f"{'='*60}\n")
    
    # Determine which sections to research
    if args.sections:
        sections_to_research = [s.strip() for s in args.sections.split(',')]
        sections_to_research = [s for s in sections_to_research if s in RESEARCH_SECTIONS]
    else:
        sections_to_research = list(RESEARCH_SECTIONS.keys())
    
    print(f"Researching {len(sections_to_research)} sections: {', '.join(sections_to_research)}\n")
    
    # Load template
    template = load_template()
    
    # Initialize LLM service
    print("Initializing LLM service...")
    llm_service = LLMService()
    
    # Load existing research data if it exists, otherwise start with template
    research_data = template.copy()
    
    # Check if family already has research_data in database
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
            existing = cur.fetchone()
            if existing and existing['research_data']:
                existing_data = existing['research_data']
                if isinstance(existing_data, str):
                    existing_data = json.loads(existing_data)
                # Merge existing data with template (existing takes precedence)
                research_data.update(existing_data)
                print(f"  Loaded existing research data for {len([k for k in existing_data.keys() if k != 'surname' and existing_data.get(k)])} sections")
    
    research_data['surname'] = family_name
    research_data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    for section_key in sections_to_research:
        section_config = RESEARCH_SECTIONS[section_key]
        template_section = research_data.get(section_key, {})
        
        section_result = research_section(
            section_key,
            section_config,
            family_name,
            context,
            llm_service,
            template_section
        )
        
        research_data[section_key] = section_result
        
        # Small delay between sections
        time.sleep(2)
    
    # Set primary_language_region based on clan_association
    if research_data.get('clan_association', {}).get('is_scottish_name'):
        research_data['primary_language_region'] = 'Scottish'
    
    # Set canonical_form
    research_data['variants']['canonical_form'] = family_name
    
    # Post-process to fix common data structure issues
    research_data = post_process_research_data(research_data)
    
    # Save to file
    if args.save or args.update:
        output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}_web.json"
        with open(output_file, 'w') as f:
            json.dump(research_data, f, indent=2)
        print(f"\n✓ Saved to: {output_file}")
    
    # Validate (reuse validation from research_family.py)
    # Import validation function
    import importlib.util
    research_family_path = Path(__file__).parent / 'research_family.py'
    spec = importlib.util.spec_from_file_location("research_family", research_family_path)
    research_family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(research_family)
    
    is_valid, errors = research_family.validate_research_json(research_data)
    if not is_valid:
        print("\n✗ Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ Validation passed")
    
    # Update database (default when --save is used, unless --no-update is specified)
    should_update = args.update or (args.save and not args.no_update)
    if should_update:
        success, message = research_family.update_family_research(family_id, research_data, dry_run=args.dry_run)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            return 1
    
    print(f"\n{'='*60}")
    print("Research Complete")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

