#!/usr/bin/env python3
"""
LLM-Assisted Family Research Tool
Uses LLM to research and populate research_data JSON for families.

Usage:
    python3 scripts/research_family_llm.py <family_id_or_name> [--model <model_name>] [--save] [--update]
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
from config.unified_config import get_config
import psycopg
from psycopg.rows import dict_row

# Import LLM service
try:
    # Try blog-core first (has generate method)
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
    from app.llm.services import LLMService
except ImportError:
    # Fallback to blueprints location (different interface)
    from blueprints.planning_llm import LLMService
    # We'll need to adapt the interface


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


def load_research_guide() -> str:
    """Load the research guide text."""
    guide_path = Path(__file__).parent.parent / 'docs' / 'surname_research_guide.md'
    if guide_path.exists():
        with open(guide_path, 'r') as f:
            return f.read()
    return "Research guide not found. Please refer to docs/surname_research_guide.md"


def format_family_context_for_llm(context: Dict) -> str:
    """Format family context for LLM prompt."""
    family = context['family']
    lines = [
        f"Family Name: {family['name']}",
        f"Family ID: {family['id']}",
        f"Is Clan: {family['is_clan']}",
        f"Is Canonical: {family.get('is_canonical', True)}",
        f"Has History: {family.get('has_history', False)}",
    ]
    
    if context['aliases']:
        lines.append(f"Aliases: {', '.join(context['aliases'])}")
    
    if context['variants']:
        lines.append(f"Spelling Variants: {', '.join(context['variants'])}")
    
    if context['septs']:
        lines.append(f"Septs: {', '.join(context['septs'])}")
    
    if context['spelling_of']:
        lines.append(f"Is a spelling variant of: {', '.join(context['spelling_of'])}")
    
    if context['resources']:
        lines.append("\nExisting Resources:")
        for res in context['resources']:
            lines.append(f"  - {res['resource_type']}: {res['resource_category'] or 'no category'}")
    
    return "\n".join(lines)


def create_research_prompt(family_context: str, research_guide: str, template: Dict) -> str:
    """Create the LLM prompt for research."""
    prompt = f"""You are a surname research specialist. Your task is to research a Scottish surname and populate a structured JSON record with factual, well-sourced information.

## Family Context from Database:
{family_context}

## Research Instructions:
{research_guide}

## JSON Template Structure:
{json.dumps(template, indent=2)}

## Your Task:
Research the surname "{family_context.split('Family Name: ')[1].split('\\n')[0]}" and populate the JSON structure with factual information. 

**Critical Requirements:**
1. Only include information you can verify from reputable sources
2. Use `null` for unknown values (not `0` or empty strings)
3. Use empty arrays `[]` when no items exist (not `null`)
4. Mark uncertainty explicitly in `uncertainty_flags` and confidence levels
5. Cite sources in `metadata.sources` (short identifiers or URLs if allowed)
6. Cross-reference with the database relationships shown above
7. Set `canonical_form` to match the database name unless there's a specific reason to differ
8. For `is_scottish_name`, set to `true` if the name has ANY Scottish association (clan, sept, territorial, or historical presence)
9. Set `has_documented_arms` to `true` ONLY if the `arms` array has entries
10. Use `null` for unknown years, not `0`

**Output Format:**
Return ONLY valid JSON matching the template structure. Do not include markdown code blocks or explanatory text - just the JSON object.

Begin your research and return the complete JSON structure:"""
    
    return prompt


def extract_json_from_response(response: str) -> Optional[Dict]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in markdown code blocks
    import re
    
    # Look for JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try parsing the whole response
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        return None


def validate_research_json(data: Dict) -> Tuple[bool, List[str]]:
    """Validate JSON against schema and business rules."""
    errors = []
    warnings = []
    
    # Check top-level fields
    if 'surname' not in data:
        errors.append("Missing 'surname' field")
    
    if 'primary_language_region' not in data:
        errors.append("Missing 'primary_language_region' field")
    
    if 'metadata' not in data:
        errors.append("Missing 'metadata' field")
    else:
        meta = data['metadata']
        if 'last_updated' in meta and meta['last_updated']:
            # Validate date format
            try:
                datetime.strptime(meta['last_updated'], '%Y-%m-%d')
            except ValueError:
                errors.append("metadata.last_updated must be YYYY-MM-DD format")
    
    # Check heraldry boolean logic
    if 'heraldry' in data:
        heraldry = data['heraldry']
        has_arms = heraldry.get('has_documented_arms', False)
        arms_count = len(heraldry.get('arms', []))
        if has_arms and arms_count == 0:
            errors.append("heraldry.has_documented_arms is true but arms array is empty")
        if not has_arms and arms_count > 0:
            warnings.append("heraldry.has_documented_arms is false but arms array has entries")
    
    # Check early_records year handling
    if 'early_records' in data:
        er = data['early_records']
        if 'earliest_attestation' in er:
            att = er['earliest_attestation']
            if 'year' in att and att['year'] == 0:
                errors.append("early_records.earliest_attestation.year should be null for unknown, not 0")
    
    # Check array handling (should be arrays, not null)
    array_fields = [
        ('etymology', 'origin_languages'),
        ('etymology', 'root_words'),
        ('etymology', 'earliest_known_forms'),
        ('early_records', 'other_attestations'),
        ('distribution_historic', 'regions'),
        ('distribution_modern', 'by_country'),
        ('clan_association', 'clan_sept_of'),
        ('heraldry', 'arms'),
        ('heraldry', 'mottoes'),
        ('heraldry', 'tartans'),
        ('variants', 'variant_spellings'),
        ('variants', 'language_forms'),
        ('variants', 'related_surnames'),
        ('migration', 'phases'),
        ('notables', 'people'),
        ('cultural_notes', 'literary_or_media_references'),
        ('genealogy_resources', 'family_societies'),
        ('genealogy_resources', 'published_histories'),
        ('genealogy_resources', 'record_rich_areas'),
    ]
    
    for section, field in array_fields:
        if section in data and field in data[section]:
            value = data[section][field]
            if value is None:
                errors.append(f"{section}.{field} should be an array [], not null")
            elif not isinstance(value, list):
                errors.append(f"{section}.{field} should be an array, got {type(value).__name__}")
    
    return len(errors) == 0, errors + warnings


def update_family_research(family_id: int, research_data: Dict, dry_run: bool = False) -> Tuple[bool, str]:
    """Update family research_data in database."""
    # Validate first
    is_valid, errors = validate_research_json(research_data)
    if not is_valid:
        return False, f"Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
    
    if dry_run:
        return True, "Validation passed (dry run - not updating database)"
    
    # Update database
    config = get_config()
    conn = psycopg.connect(
        config.DATABASE_URL,
        row_factory=dict_row,
        autocommit=False
    )
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE families
                SET research_data = %s::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(research_data), family_id))
            conn.commit()
        return True, f"Successfully updated research_data for family ID {family_id}"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()


def main():
    """Main LLM-assisted research workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM-Assisted Family Research Tool')
    parser.add_argument('family', help='Family ID or name')
    parser.add_argument('--model', type=str, default='llama3.2:latest', help='LLM model name (default: llama3.2:latest)')
    parser.add_argument('--save', action='store_true', help='Save JSON to file')
    parser.add_argument('--update', action='store_true', help='Update database with research data')
    parser.add_argument('--dry-run', action='store_true', help='Validate but do not update database')
    parser.add_argument('--temperature', type=float, default=0.3, help='LLM temperature (default: 0.3 for more factual output)')
    parser.add_argument('--max-tokens', type=int, default=4000, help='Max tokens for LLM response (default: 4000)')
    
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
    print(f"Researching: {family_name} (ID: {family_id})")
    print(f"{'='*60}\n")
    
    # Load template and guide
    print("Loading research template and guide...")
    template = load_template()
    research_guide = load_research_guide()
    
    # Format context for LLM
    family_context_str = format_family_context_for_llm(context)
    
    # Create prompt
    print("Creating research prompt...")
    prompt = create_research_prompt(family_context_str, research_guide, template)
    
    # Initialize LLM service
    print(f"Initializing LLM service (model: {args.model})...")
    llm_service = LLMService()
    
    # Call LLM
    print("Calling LLM for research (this may take a while)...")
    try:
        # Check if LLMService has generate method (blog-core version)
        if hasattr(llm_service, 'generate'):
            response = llm_service.generate(
                prompt=prompt,
                model_name=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=120
            )
        else:
            # Use planning_llm interface (messages format)
            messages = [
                {"role": "user", "content": prompt}
            ]
            result = llm_service.execute_llm_request(
                provider='ollama',
                model=args.model,
                messages=messages,
                max_tokens=args.max_tokens,
                temperature=args.temperature
            )
            if 'error' in result:
                print(f"LLM Error: {result['error']}")
                return 1
            response = result.get('content', '')
    except Exception as e:
        print(f"Error calling LLM: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("Extracting JSON from LLM response...")
    research_data = extract_json_from_response(response)
    
    if not research_data:
        print("Error: Could not extract valid JSON from LLM response")
        print("\nLLM Response:")
        print(response[:500] + "..." if len(response) > 500 else response)
        return 1
    
    # Ensure surname matches
    research_data['surname'] = family_name
    research_data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Validate
    print("Validating research data...")
    is_valid, errors = validate_research_json(research_data)
    if not is_valid:
        print("✗ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nResearch data (may need manual fixes):")
        print(json.dumps(research_data, indent=2))
        return 1
    
    print("✓ Validation passed")
    if errors:
        print("Warnings:")
        for warning in errors:
            print(f"  - {warning}")
    
    # Save to file
    if args.save or args.update:
        output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}_llm.json"
        with open(output_file, 'w') as f:
            json.dump(research_data, f, indent=2)
        print(f"\n✓ Saved to: {output_file}")
    
    # Update database
    if args.update:
        success, message = update_family_research(family_id, research_data, dry_run=args.dry_run)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            return 1
    
    # Show summary
    print(f"\n{'='*60}")
    print("Research Summary:")
    print(f"{'='*60}")
    print(f"Surname: {research_data.get('surname', 'N/A')}")
    print(f"Primary Language Region: {research_data.get('primary_language_region', 'N/A')}")
    print(f"Research Confidence: {research_data.get('metadata', {}).get('research_confidence', 'N/A')}")
    print(f"Sources: {len(research_data.get('metadata', {}).get('sources', []))}")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

