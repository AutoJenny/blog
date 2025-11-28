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

def fact_check_with_openai(narrative_html: str, family_name: str, model: str = "gpt-4.1") -> Optional[str]:
    """Send narrative to OpenAI for fact-checking and refinement."""
    import openai
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return None
    
    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = """You are a rigorous historical fact-checker and editor specialising in Scottish clan and family histories.

Your task is to:
1. Fact-check the provided narrative against historical accuracy
2. Remove or correct any false information, hallucinations, or unsupported claims
3. Improve the writing style to be historically authoritative but accessible
4. Remove flowery language and overly dramatic prose
5. Remove any introductory commentary or conclusion sections - stick to factual history only
6. Ensure UK-British English spelling throughout
7. Maintain HTML format with <h3> headings and <blockquote> tags for quotations
8. Target length: 500-1000 words (condense if longer, expand if shorter with verified facts only)
9. RETAIN all quotations from the original - they are important historical sources
10. Use accessible language - avoid technical terms like "diaspora" (use "<name>s Across the World" or similar)

CRITICAL RULES:
- If a fact cannot be verified or appears to be hallucinated, OMIT it entirely
- Do NOT add new facts that aren't in the original
- Do NOT include introductory phrases like "This article discusses..." or "In conclusion..."
- Do NOT include summary or conclusion paragraphs at the end
- Start directly with factual content about the family (e.g., etymology, origins, early records)
- End with factual information about the family's current state or legacy, not conclusions
- Use UK-British spelling (colour, honour, centre, theatre, organise, recognise, analyse, defence, offence, travelled, cancelled, labelled, fulfil, skilful, towards, amongst)
- Maintain the HTML structure: <p> tags for paragraphs, <h3> for headings, <blockquote> for quotations
- Be authoritative and direct - write like a scholarly but accessible history book
- Focus on what happened, when, where, and why - not poetic descriptions

QUOTATIONS - CRITICAL:
- You MUST retain ALL quotations from the original narrative UNLESS they are found to be probably inauthentic
- Each quotation should appear ONLY ONCE in the narrative - do NOT duplicate quotations
- If the same quotation appears multiple times in the original, include it only once in the most appropriate location
- Quotations should remain in <blockquote> tags with proper formatting
- Only remove quotations if they are clearly inauthentic, fabricated, or cannot be verified as historical
- Quotations are valuable historical sources and should be preserved when authentic
- Format: <p>Contextualisation text.</p><blockquote>Quoted text here</blockquote><p>Continuation.</p>
- Before removing any quotation, verify it is likely inauthentic - when in doubt, retain it

LANGUAGE - CRITICAL:
- Avoid technical/academic terms where simpler alternatives exist
- Replace "diaspora" with "{family_name}s Across the World" or "The {family_name} Family Worldwide"
- Replace "migration patterns" with "movements" or "where {family_name}s settled"
- Use accessible, everyday language while maintaining historical accuracy"""

    user_prompt = f"""Please fact-check and refine this historical narrative about the {family_name} family/clan.

CRITICAL REQUIREMENTS:
- Remove any false information, hallucinations, or unsupported claims
- RETAIN ALL quotations from the original UNLESS they are found to be probably inauthentic
- Each quotation should appear ONLY ONCE - do not duplicate quotations that appear multiple times in the original
- If a quotation appears multiple times, include it once in the most appropriate location
- Improve the style to be authoritative but accessible, without flowery language
- Remove any introductory commentary or conclusions - stick to factual history only
- Use UK-British spelling throughout
- Avoid technical terms like "diaspora" - use "{family_name}s Across the World" or similar accessible language
- Target 500-1000 words
- Maintain HTML format with <p>, <h3>, and <blockquote> tags

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
        return refined_narrative
        
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
    refined_narrative = fact_check_with_openai(original_narrative, data['family_name'], model=args.model)
    
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

