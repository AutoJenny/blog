#!/usr/bin/env python3
"""Import family/clan data from CSV into PostgreSQL.

This script parses the family.csv file, extracts clean data from HTML,
and imports it into normalized database tables.
"""

import sys
import os
import csv
import re
import json
from html.parser import HTMLParser
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
from config.unified_config import get_config
import psycopg
from psycopg.rows import dict_row

# Global counters
stats = {
    'families': 0,
    'aliases': 0,
    'spellings': 0,
    'septs': 0,
    'resources': 0,
    'designs': 0,
    'errors': 0
}


def extract_names_from_html(html_content: str, relationship_type: str) -> List[str]:
    """Extract family names from HTML forms.
    
    Args:
        html_content: HTML string containing forms
        relationship_type: 'child' for aliases, 'parent' for spellings/septs
    
    Returns:
        List of extracted family names
    """
    if not html_content or html_content.strip() == '':
        return []
    
    names = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all links with class "auto_name_filter" - these contain the actual names
        links = soup.find_all('a', class_='auto_name_filter')
        for link in links:
            name = link.get_text(strip=True)
            if name:
                names.append(name)
        
        # Also check for data-relationship attributes
        elements = soup.find_all(attrs={'data-relationship': relationship_type})
        for elem in elements:
            name = elem.get('data-name', '').strip()
            if name:
                names.append(name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name.lower() not in seen:
                seen.add(name.lower())
                unique_names.append(name)
        
        return unique_names
    except Exception as e:
        print(f"Warning: Error parsing HTML for {relationship_type}: {e}")
        return []


def extract_spelling_relationships(html_content: str) -> List[str]:
    """Extract spelling-of relationships (parent relationships)."""
    return extract_names_from_html(html_content, 'parent')


def extract_sept_relationships(html_content: str) -> List[str]:
    """Extract sept-of relationships (parent relationships)."""
    return extract_names_from_html(html_content, 'parent')


def extract_aliases(html_content: str) -> List[str]:
    """Extract alias relationships (child relationships)."""
    return extract_names_from_html(html_content, 'child')


def parse_resources(html_content: str) -> List[Dict]:
    """Parse resources from HTML div structure.
    
    Returns list of dicts with: type, category, value, metadata
    """
    if not html_content or html_content.strip() == '':
        return []
    
    resources = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Resources are organized in divs with <strong> headers
        current_type = None
        for element in soup.find_all(['div', 'strong']):
            if element.name == 'strong':
                # This is a type header (image, text, json)
                current_type = element.get_text(strip=True).lower()
            elif element.name == 'div' and current_type:
                # Extract title attribute (filename or content)
                title = element.get('title', '').strip()
                if not title:
                    # Try getting text content
                    text = element.get_text(strip=True)
                    if text and text.startswith('•'):
                        # Format: "• category_name"
                        parts = text[1:].strip().split()
                        if len(parts) >= 1:
                            category = parts[0]
                            resources.append({
                                'type': current_type,
                                'category': category,
                                'value': title if title else text,
                                'metadata': {}
                            })
                else:
                    # Has title attribute
                    text = element.get_text(strip=True)
                    if text.startswith('•'):
                        category = text[1:].strip().split()[0] if text[1:].strip() else None
                        
                        # Special handling for JSON resources
                        if current_type == 'json':
                            try:
                                # Try to parse as JSON
                                json_data = json.loads(title)
                                resources.append({
                                    'type': 'json',
                                    'category': category or 'data',
                                    'value': title,  # Keep original string
                                    'metadata': json_data
                                })
                            except:
                                resources.append({
                                    'type': 'json',
                                    'category': category or 'data',
                                    'value': title,
                                    'metadata': {}
                                })
                        else:
                            resources.append({
                                'type': current_type,
                                'category': category,
                                'value': title,
                                'metadata': {}
                            })
        
        return resources
    except Exception as e:
        print(f"Warning: Error parsing resources: {e}")
        return []


def parse_designs(html_content: str) -> List[Dict]:
    """Parse design information from HTML.
    
    Returns list of dicts with: design_id, design_year, design_url, is_default
    """
    if not html_content or html_content.strip() == '':
        return []
    
    designs = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all links
        links = soup.find_all('a')
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Extract design ID from URL like: /admin/swfabrics_design/edit/id/300265/
            design_id_match = re.search(r'/edit/id/(\d+)/', href)
            design_id = int(design_id_match.group(1)) if design_id_match else None
            
            # Extract year from text like "(2015)"
            year_match = re.search(r'\((\d{4})\)', text)
            design_year = int(year_match.group(1)) if year_match else None
            
            # Check if it's the default design
            is_default = 'default' in link.get('style', '').lower() or 'font-weight:bold' in link.get('style', '')
            
            if design_id:
                designs.append({
                    'design_id': design_id,
                    'design_year': design_year,
                    'design_url': href if href.startswith('http') else None,
                    'is_default': is_default
                })
        
        return designs
    except Exception as e:
        print(f"Warning: Error parsing designs: {e}")
        return []


def get_or_create_family_id(cursor, name: str) -> Optional[int]:
    """Get family ID by name, or return None if not found."""
    cursor.execute("SELECT id FROM families WHERE name = %s", (name,))
    row = cursor.fetchone()
    return row['id'] if row else None


def import_family(cursor, family_data: Dict, skip_existing: bool = False) -> Optional[int]:
    """Import a single family record.
    
    Args:
        cursor: Database cursor
        family_data: Family data dictionary
        skip_existing: If True, skip families that already exist
    
    Returns the family ID if successful, None otherwise.
    """
    try:
        family_id = family_data['id']
        
        # Check if family already exists
        if skip_existing:
            cursor.execute("SELECT id FROM families WHERE id = %s", (family_id,))
            if cursor.fetchone():
                # Family exists, skip it
                return family_id
        
        # Insert or update family
        cursor.execute("""
            INSERT INTO families (id, name, is_clan, is_virtual)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name,
                is_clan = EXCLUDED.is_clan,
                is_virtual = EXCLUDED.is_virtual,
                updated_at = CURRENT_TIMESTAMP
        """, (
            family_id,
            family_data['name'],
            family_data['is_clan'] == 'Yes',
            family_data['is_virtual'] == 'Yes'
        ))
        
        stats['families'] += 1
        
        # Import aliases
        for alias_name in family_data.get('aliases', []):
            try:
                cursor.execute("""
                    INSERT INTO family_aliases (family_id, alias_name)
                    VALUES (%s, %s)
                    ON CONFLICT (family_id, alias_name) DO NOTHING
                """, (family_id, alias_name))
                stats['aliases'] += 1
            except Exception as e:
                print(f"Error importing alias {alias_name} for family {family_id}: {e}")
                stats['errors'] += 1
        
        # Import spellings (spelling_of relationships)
        for spelling_of_name in family_data.get('spellings', []):
            try:
                # Find the target family ID
                target_id = get_or_create_family_id(cursor, spelling_of_name)
                if target_id:
                    cursor.execute("""
                        INSERT INTO family_spellings (family_id, spelling_of_id)
                        VALUES (%s, %s)
                        ON CONFLICT (family_id, spelling_of_id) DO NOTHING
                    """, (family_id, target_id))
                    stats['spellings'] += 1
            except Exception as e:
                print(f"Error importing spelling relationship {spelling_of_name} for family {family_id}: {e}")
                stats['errors'] += 1
        
        # Import septs
        for sept_of_name in family_data.get('septs', []):
            try:
                # Find the target family ID (the clan this is a sept of)
                target_id = get_or_create_family_id(cursor, sept_of_name)
                if target_id:
                    cursor.execute("""
                        INSERT INTO family_septs (family_id, sept_of_id)
                        VALUES (%s, %s)
                        ON CONFLICT (family_id, sept_of_id) DO NOTHING
                    """, (family_id, target_id))
                    stats['septs'] += 1
            except Exception as e:
                print(f"Error importing sept relationship {sept_of_name} for family {family_id}: {e}")
                stats['errors'] += 1
        
        # Import resources
        for resource in family_data.get('resources', []):
            try:
                metadata_json = json.dumps(resource.get('metadata', {})) if resource.get('metadata') else None
                cursor.execute("""
                    INSERT INTO family_resources (family_id, resource_type, resource_category, resource_value, resource_metadata)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                """, (
                    family_id,
                    resource['type'],
                    resource.get('category'),
                    resource['value'],
                    metadata_json
                ))
                stats['resources'] += 1
            except Exception as e:
                print(f"Error importing resource for family {family_id}: {e}")
                stats['errors'] += 1
        
        # Import designs
        for design in family_data.get('designs', []):
            try:
                cursor.execute("""
                    INSERT INTO family_designs (family_id, design_id, design_year, design_url, is_default)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    family_id,
                    design.get('design_id'),
                    design.get('design_year'),
                    design.get('design_url'),
                    design.get('is_default', False)
                ))
                stats['designs'] += 1
            except Exception as e:
                print(f"Error importing design for family {family_id}: {e}")
                stats['errors'] += 1
        
        return family_id
        
    except Exception as e:
        print(f"Error importing family {family_data.get('name', 'unknown')}: {e}")
        stats['errors'] += 1
        return None


def process_csv_row(row: Dict) -> Dict:
    """Process a single CSV row and extract clean data."""
    family_data = {
        'id': int(row['ID']),
        'name': row['Name'].strip(),
        'is_clan': row.get('Is Clan', 'No'),
        'is_virtual': row.get('Is Virtual', 'No'),
        'aliases': extract_aliases(row.get('Aliases', '')),
        'spellings': extract_spelling_relationships(row.get('Spellings', '')),
        'septs': extract_sept_relationships(row.get('Septs', '')),
        'resources': parse_resources(row.get('Resources', '')),
        'designs': parse_designs(row.get('Designs', ''))
    }
    
    return family_data


def main(skip_existing: bool = False, start_row: int = 1, csv_file: str = None):
    """Main import function.
    
    Args:
        skip_existing: If True, skip families that already exist in database
        start_row: Row number to start from (1-based, excluding header)
        csv_file: Optional path to CSV file (defaults to data/family.csv)
    """
    if csv_file is None:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'family.csv')
    else:
        csv_path = csv_file
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        return 1
    
    print(f"Reading CSV file: {csv_path}")
    if skip_existing:
        print("Mode: Skipping existing families")
    if start_row > 1:
        print(f"Starting from row {start_row}")
    
    # Read and process CSV
    families_data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            # Skip rows before start_row
            if row_num < start_row + 1:  # +1 because row_num starts at 2
                continue
                
            try:
                family_data = process_csv_row(row)
                families_data.append(family_data)
            except Exception as e:
                print(f"Error processing row {row_num}: {e}")
                stats['errors'] += 1
    
    print(f"Processed {len(families_data)} families from CSV")
    if len(families_data) == 0:
        print("No families to import.")
        return 0
    
    print("Importing into database...")
    
    # Import into database
    # Create connection without autocommit for batch processing
    config = get_config()
    conn = psycopg.connect(
        config.DATABASE_URL,
        row_factory=dict_row,
        autocommit=False
    )
    
    try:
        with conn.cursor() as cursor:
            for i, family_data in enumerate(families_data, 1):
                if i % 100 == 0:
                    print(f"  Processed {i}/{len(families_data)} families...")
                    conn.commit()  # Commit every 100 records
                
                import_family(cursor, family_data, skip_existing=skip_existing)
            
            # Final commit
            conn.commit()
            print("✓ Import complete!")
    except Exception as e:
        conn.rollback()
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()
    
    # Print statistics
    print("\nImport Statistics:")
    print(f"  Families: {stats['families']}")
    print(f"  Aliases: {stats['aliases']}")
    print(f"  Spellings: {stats['spellings']}")
    print(f"  Septs: {stats['septs']}")
    print(f"  Resources: {stats['resources']}")
    print(f"  Designs: {stats['designs']}")
    print(f"  Errors: {stats['errors']}")
    
    return 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Import family/clan data from CSV')
    parser.add_argument('--skip-existing', action='store_true', 
                       help='Skip families that already exist in database')
    parser.add_argument('--start-row', type=int, default=1,
                       help='Row number to start from (1-based, excluding header)')
    parser.add_argument('--csv-file', type=str, default=None,
                       help='Path to CSV file (defaults to data/family.csv)')
    
    args = parser.parse_args()
    sys.exit(main(skip_existing=args.skip_existing, start_row=args.start_row, csv_file=args.csv_file))

