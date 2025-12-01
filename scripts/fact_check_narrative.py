#!/usr/bin/env python3
"""
Fact-Check and Refine Narrative using OpenAI API
Sends generated narrative to ChatGPT for fact-checking and style improvement.
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager

# Load environment variables
load_dotenv()

def get_narrative_from_db(family_id: int) -> Optional[Dict]:
    """Get narrative from database."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, research_data FROM families WHERE id = %s", (family_id,))
            row = cur.fetchone()
            if not row:
                return None
            
            family = dict(row)
            if not family.get('research_data'):
                return None
            
            research_data = family['research_data']
            if isinstance(research_data, str):
                research_data = json.loads(research_data)
            
            narrative = research_data.get('metadata', {}).get('narrative')
            if not narrative:
                return None
            
            return {
                'family_id': family['id'],
                'family_name': family['name'],
                'narrative': narrative,
                'research_data': research_data
            }

def fact_check_with_openai(narrative_html: str, family_name: str, model: str = "gpt-4.1", custom_instructions: str = None) -> Optional[str]:
    """Send narrative to OpenAI for fact-checking and refinement."""
    import openai
    import re
    
    # Pre-filter: Remove any quotations that mention other surnames
    # This prevents cross-contamination from being sent to OpenAI
    family_name_lower = family_name.lower()
    family_variations = [family_name_lower, family_name_lower.replace('ie', 'y'), family_name_lower.replace('y', 'ie')]
    
    # Find and remove blockquotes that mention other surnames
    def should_remove_quotation(blockquote_text: str) -> bool:
        blockquote_lower = blockquote_text.lower()
        # Check if it mentions the target family
        mentions_target = any(var in blockquote_lower for var in family_variations)
        # Check if it mentions other common Scottish surnames
        other_surnames = ['abernethy', 'stewart', 'campbell', 'douglas', 'bruce', 'wallace', 'fraser', 'macdonald']
        mentions_other = any(other in blockquote_lower and other not in family_variations for other in other_surnames)
        
        # Remove if it mentions other surnames OR doesn't mention the target
        return mentions_other or not mentions_target
    
    # Remove problematic blockquotes
    blockquote_pattern = r'<blockquote>.*?</blockquote>'
    def remove_if_other_family(match):
        blockquote_text = match.group(0)
        if should_remove_quotation(blockquote_text):
            return ''  # Remove the entire blockquote
        return blockquote_text
    
    narrative_html = re.sub(blockquote_pattern, remove_if_other_family, narrative_html, flags=re.DOTALL | re.IGNORECASE)
    
    # Also remove any inline quotations that mention other surnames
    # Look for patterns like "By th' sword o' Abernethy" etc.
    other_surname_patterns = [
        r'[Bb]y th.*?sword.*?[Aa]bernethy.*?',
        r'[Aa]bernethy.*?clan.*?stand',
        r'[Ss]word.*?[Aa]bernethy'
    ]
    for pattern in other_surname_patterns:
        narrative_html = re.sub(pattern, '', narrative_html, flags=re.DOTALL | re.IGNORECASE)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return None
    
    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = f"""You are a professional historical editor specialising in Scottish surnames, families, and clans.

Your task is to rewrite a historical narrative to be fully accurate and authoritative, cutting out fluff and negative statements so it reads like an authoritative history.

CRITICAL PRINCIPLES:
- Focus on what IS known and documented, not what isn't
- Write as an authoritative historian presenting established facts
- Remove negative statements like "there is no evidence", "cannot be substantiated", "cannot be confirmed", "there is no verifiable evidence"
- Simply omit unsubstantiated claims rather than stating they cannot be proven
- Remove phrases like "in conclusion", "in summary", "to conclude", "ultimately", "in the end"
- Remove introductory commentary like "This family's story begins..." or "Let us explore..."
- Start directly with factual content about the family (e.g., etymology, origins, early records)
- End with factual content about the family's current state or legacy, not a conclusion paragraph
- Write in UK-British spelling throughout
- Format as HTML with <p>, <h3>, and <blockquote> tags
- Target 500-1000 words - be comprehensive and detailed about what IS documented

QUOTATIONS - CRITICAL:
- You MUST retain quotations from the original narrative ONLY if they are about {family_name} (or variations like Abercromby for Abercrombie)
- REMOVE any quotations that mention other surnames (e.g., if writing about Abercrombie, remove quotations about Abernethy, Stewart, etc.)
- Each quotation should appear ONLY ONCE in the narrative - do NOT duplicate quotations
- Format: <p>Contextualisation text.</p><blockquote>Quoted text here</blockquote><p>Continuation.</p>
- CRITICAL: Zero tolerance for cross-contamination - if a quotation mentions another surname, remove it entirely

BLOCKQUOTE USAGE - ABSOLUTELY CRITICAL:
- <blockquote> tags MUST ONLY be used for actual quotations (verbatim text from historical sources, poems, verses, speeches, etc.)
- DO NOT use <blockquote> for regular narrative sentences, even if they are descriptive or important
- DO NOT use <blockquote> for emphasis or to highlight important information
- DO NOT use <blockquote> for any text that is your own writing or paraphrasing
- ONLY use <blockquote> when you are reproducing exact, verbatim quoted material from a source
- All regular narrative text must be in <p> tags, never in <blockquote> tags
- If you are unsure whether something is a quotation, use <p> tags, not <blockquote>

STYLE - CRITICAL:
- Write as an authoritative historian presenting established historical facts
- Use precise, clear language that conveys what is documented and known
- Avoid flowery language, dramatic flourishes, or romanticised descriptions
- Do NOT include negative statements about what cannot be proven
- Instead of "There is no evidence that X happened", write about what DID happen
- Instead of "Claims cannot be substantiated", simply omit unsubstantiated claims
- Present the family's history based on documented sources and established facts
- Be comprehensive - cover etymology, early records, historical development, notable figures, modern distribution

LANGUAGE - CRITICAL:
- Avoid technical/academic terms where simpler alternatives exist
- Replace "diaspora" with "{family_name}s Across the World" or "The {family_name} Family Worldwide"
- Replace "migration patterns" with "movements" or "where {family_name}s settled"
- Use accessible, everyday language while maintaining historical accuracy"""

    # Add custom instructions if provided
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\nADDITIONAL FEEDBACK/INSTRUCTIONS:\n{custom_instructions}\n\nPlease address these specific points in your rewrite.\n"
    
    user_prompt = f"""Please rewrite this historical narrative about the {family_name} family/clan fully accurately, also cutting out fluff like "in conclusion..." so it reads more like an authoritative history.{custom_section}

CRITICAL: Remove any quotations that mention surnames other than {family_name} (or its variations like Abercromby for Abercrombie). If you see a quotation about Abernethy, Stewart, Campbell, or any other surname, REMOVE IT ENTIRELY - this is cross-contamination and must not appear in the narrative.

Focus on what IS documented and known. Remove negative statements like "there is no evidence" or "cannot be substantiated" - simply omit unsubstantiated claims rather than stating they cannot be proven.

Write in an authoritative, accessible style without flowery language. Use UK-British spelling throughout. Target 500-1000 words. Maintain HTML format with <p> and <h3> tags.

CRITICAL - BLOCKQUOTE USAGE:
- Use <blockquote> tags ONLY for actual verbatim quotations (historical quotes, poems, verses, speeches, etc.)
- DO NOT use <blockquote> for regular narrative sentences, descriptions, or your own writing
- DO NOT use <blockquote> for emphasis or to highlight information
- All regular narrative text must be in <p> tags
- If uncertain whether something is a quotation, use <p> tags, not <blockquote>

Return ONLY the HTML content - do NOT include any explanatory text, justifications, or notes after the HTML.

Here is the narrative:

{narrative_html}"""

    try:
        print("Sending to OpenAI for fact-checking and refinement...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower temperature for more factual, less creative output
            max_tokens=4000
        )
        
        refined_narrative = response.choices[0].message.content.strip()
        
        # Extract only the HTML content - remove any explanatory text after </html> or </body>
        # OpenAI sometimes adds explanations after the HTML
        import re
        # Try to find the HTML content
        html_match = re.search(r'(<!DOCTYPE html>.*?</html>)', refined_narrative, re.DOTALL | re.IGNORECASE)
        if html_match:
            refined_narrative = html_match.group(1)
        else:
            # If no DOCTYPE, try to find content between <html> and </html>
            html_match = re.search(r'(<html.*?</html>)', refined_narrative, re.DOTALL | re.IGNORECASE)
            if html_match:
                refined_narrative = html_match.group(1)
            else:
                # If no HTML tags, try to find content up to </body>
                body_match = re.search(r'(.*?</body>)', refined_narrative, re.DOTALL | re.IGNORECASE)
                if body_match:
                    refined_narrative = body_match.group(1)
        
        return refined_narrative.strip()
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def save_refined_narrative(family_id: int, family_name: str, refined_narrative: str, 
                          original_narrative: str, update_db: bool = False):
    """Save refined narrative to file and optionally update database."""
    # Save to file
    output_file = f"data/narrative_{family_name.replace(' ', '_')}_{family_id}_fact_checked.html"
    with open(output_file, 'w') as f:
        f.write(refined_narrative)
    print(f"✓ Saved refined narrative to: {output_file}")
    
    # Also save original for comparison
    original_file = f"data/narrative_{family_name.replace(' ', '_')}_{family_id}_original.html"
    with open(original_file, 'w') as f:
        f.write(original_narrative)
    print(f"✓ Saved original narrative to: {original_file}")
    
    # Update database if requested
    if update_db:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT research_data FROM families WHERE id = %s", (family_id,))
                row = cur.fetchone()
                if row:
                    research_data = dict(row)['research_data']
                    if isinstance(research_data, str):
                        research_data = json.loads(research_data)
                    
                    if 'metadata' not in research_data:
                        research_data['metadata'] = {}
                    
                    research_data['metadata']['narrative_fact_checked'] = refined_narrative
                    research_data['metadata']['narrative_original'] = original_narrative
                    research_data['metadata']['narrative_fact_checked_word_count'] = len(refined_narrative.split())
                    
                    cur.execute(
                        "UPDATE families SET research_data = %s WHERE id = %s",
                        (json.dumps(research_data), family_id)
                    )
                    conn.commit()
                    print(f"✓ Updated database with fact-checked narrative")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fact-check and refine narrative using OpenAI')
    parser.add_argument('family', help='Family ID or name')
    parser.add_argument('--update-db', action='store_true', help='Update database with fact-checked version')
    parser.add_argument('--save-original', action='store_true', help='Save original narrative to file')
    parser.add_argument('--model', type=str, default='gpt-4.1', help='OpenAI model to use (default: gpt-4.1)')
    parser.add_argument('--custom-instructions', type=str, help='Custom instructions/feedback to include in the prompt')
    
    args = parser.parse_args()
    
    # Get family ID
    try:
        family_id = int(args.family)
        family_name = None
    except ValueError:
        family_id = None
        family_name = args.family
    
    # Get narrative from database
    if family_id:
        data = get_narrative_from_db(family_id)
    else:
        # Search by name
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM families WHERE name = %s", (family_name,))
                row = cur.fetchone()
                if row:
                    family_id = row['id']
                    data = get_narrative_from_db(family_id)
                else:
                    print(f"Error: Family not found: {args.family}")
                    return 1
    
    if not data:
        print(f"Error: No narrative found for family ID {family_id}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"Fact-Checking Narrative: {data['family_name']} (ID: {family_id})")
    print(f"{'='*60}\n")
    
    original_narrative = data['narrative']
    print(f"Original narrative: {len(original_narrative.split())} words")
    
    # Send to OpenAI
    refined_narrative = fact_check_with_openai(
        original_narrative, 
        data['family_name'], 
        model=args.model,
        custom_instructions=args.custom_instructions
    )
    
    if not refined_narrative:
        print("Failed to get refined narrative from OpenAI")
        return 1
    
    print(f"Refined narrative: {len(refined_narrative.split())} words")
    
    # Save results
    save_refined_narrative(
        family_id, 
        data['family_name'], 
        refined_narrative, 
        original_narrative,
        update_db=args.update_db
    )
    
    print(f"\n{'='*60}")
    print("Fact-Checking Complete")
    print(f"{'='*60}\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

