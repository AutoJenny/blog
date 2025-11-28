#!/usr/bin/env python3
"""
Family Research Tool
Helps research and populate research_data JSON for families.

Usage:
    python3 scripts/research_family.py <family_id_or_name> [--template] [--validate <json_file>] [--update <json_file>]
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


def print_family_context(context: Dict):
    """Print family context for research."""
    family = context['family']
    print(f"\n{'='*60}")
    print(f"Family: {family['name']} (ID: {family['id']})")
    print(f"{'='*60}")
    print(f"  Is Clan: {family['is_clan']}")
    print(f"  Is Canonical: {family['is_canonical']}")
    print(f"  Has History: {family['has_history']}")
    
    if context['aliases']:
        print(f"\n  Aliases: {', '.join(context['aliases'])}")
    
    if context['variants']:
        print(f"  Has {len(context['variants'])} spelling variants")
    
    if context['septs']:
        print(f"  Has {len(context['septs'])} septs")
    
    if context['spelling_of']:
        print(f"  Is a spelling variant of: {', '.join(context['spelling_of'])}")
    
    if context['resources']:
        print(f"\n  Existing Resources:")
        for res in context['resources']:
            print(f"    - {res['resource_type']}: {res['resource_category'] or 'no category'}")
    
    print(f"\n{'='*60}\n")


def main():
    """Main research workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Family Research Tool')
    parser.add_argument('family', help='Family ID or name')
    parser.add_argument('--template', action='store_true', help='Generate template JSON file')
    parser.add_argument('--context', action='store_true', help='Show family context only')
    parser.add_argument('--validate', type=str, help='Validate JSON file')
    parser.add_argument('--update', type=str, help='Update database with JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Validate but do not update database')
    
    args = parser.parse_args()
    
    # Get family context
    try:
        family_id = int(args.family)
        family_name = None
    except ValueError:
        family_id = None
        family_name = args.family
    
    context = get_family_context(family_id, family_name)
    if not context:
        print(f"Error: Family not found: {args.family}")
        return 1
    
    family_id = context['family']['id']
    family_name = context['family']['name']
    
    # Show context
    if args.context:
        print_family_context(context)
        return 0
    
    # Generate template
    if args.template:
        template = load_template()
        template['surname'] = family_name
        template['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        output_file = f"data/research_{family_name.replace(' ', '_')}_{family_id}.json"
        with open(output_file, 'w') as f:
            json.dump(template, f, indent=2)
        print(f"Template created: {output_file}")
        print_family_context(context)
        return 0
    
    # Validate JSON file
    if args.validate:
        with open(args.validate, 'r') as f:
            data = json.load(f)
        
        is_valid, errors = validate_research_json(data)
        if is_valid:
            print("✓ JSON is valid")
        else:
            print("✗ Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        return 0
    
    # Update database
    if args.update:
        with open(args.update, 'r') as f:
            data = json.load(f)
        
        success, message = update_family_research(family_id, data, dry_run=args.dry_run)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            return 1
        return 0
    
    # Default: show context and instructions
    print_family_context(context)
    print("Usage options:")
    print("  --template          Generate template JSON file")
    print("  --validate <file>   Validate JSON file")
    print("  --update <file>     Update database with JSON file")
    print("  --dry-run           Validate without updating")
    print("\nExample workflow:")
    print(f"  1. python3 scripts/research_family.py {family_id} --template")
    print(f"  2. Edit data/research_{family_name.replace(' ', '_')}_{family_id}.json")
    print(f"  3. python3 scripts/research_family.py {family_id} --validate data/research_{family_name.replace(' ', '_')}_{family_id}.json")
    print(f"  4. python3 scripts/research_family.py {family_id} --update data/research_{family_name.replace(' ', '_')}_{family_id}.json")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

