"""
Families & Clans Browser Blueprint
Browse and filter Scottish families and clans
"""

from flask import Blueprint, render_template, request, jsonify, abort
from config.database import db_manager
import logging
import json
import csv
import os
from pathlib import Path
from urllib.parse import quote

logger = logging.getLogger(__name__)

# In-memory store for filtered ID sets for navigation between families.
# Maps a short key to {'ids': [int], 'created_at': datetime}
FILTERED_ID_SETS = {}
FILTERED_ID_SETS_MAX_AGE_SECONDS = 3600  # 1 hour

bp = Blueprint('families', __name__, url_prefix='/families')


def get_families_with_srt_data() -> set:
    """Get a set of all family names that have SRT data.
    
    Returns:
        Set of family names (lowercase) that have tartans in the SRT register.
    """
    base_path = Path(__file__).parent.parent
    clan_csv = base_path / 'side-projects' / 'tartan-design' / 'data' / 'tartan_designs_clan_full.csv'
    srt_file = base_path / 'side-projects' / 'tartan-design' / 'data' / 'tartan_designs_register_full.csv'
    
    if not clan_csv.exists() or not srt_file.exists():
        return set()
    
    families_with_srt = set()
    
    try:
        # Get all families from clan CSV
        with open(clan_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                family = row.get('family', '').strip()
                register_id = row.get('register_id', '').strip()
                legacy_id = row.get('legacy_id', '').strip()
                
                if family:
                    families_with_srt.add(family.lower())
        
        # Also check for families connected via STA Reference -> Legacy ID
        # Load all legacy_ids from clan CSV
        legacy_ids_by_family = {}  # legacy_id -> set of families
        with open(clan_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                family = row.get('family', '').strip()
                legacy_id = row.get('legacy_id', '').strip()
                if family and legacy_id:
                    if legacy_id not in legacy_ids_by_family:
                        legacy_ids_by_family[legacy_id] = set()
                    legacy_ids_by_family[legacy_id].add(family.lower())
        
        # Check register CSV for STA references that match legacy_ids
        with open(srt_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sta_ref = row.get('sta_ref', '').strip()
                if sta_ref and sta_ref in legacy_ids_by_family:
                    families_with_srt.update(legacy_ids_by_family[sta_ref])
    
    except Exception as e:
        logger.error(f"Error loading SRT family names: {e}", exc_info=True)
    
    return families_with_srt


def load_srt_data_for_family(family_name: str) -> list:
    """Load Scottish Register of Tartans data for a family.
    
    Uses two matching methods:
    1. Family name -> register_id (via clan CSV)
    2. STA Reference -> Legacy ID (for additional connections)
    
    Args:
        family_name: The family name (used to match against SRT clan CSV)
    
    Returns:
        List of tartan records sorted by registration_date (newest first), then by tartan_name
        Each record contains ALL fields from both Register CSV and Clan CSV
    """
    base_path = Path(__file__).parent.parent
    clan_csv = base_path / 'side-projects' / 'tartan-design' / 'data' / 'tartan_designs_clan_full.csv'
    srt_file = base_path / 'side-projects' / 'tartan-design' / 'data' / 'tartan_designs_register_full.csv'
    
    if not clan_csv.exists() or not srt_file.exists():
        logger.warning(f"SRT data files not found: {clan_csv} or {srt_file}")
        return []
    
    tartans = []
    seen_register_ids = set()  # Track register_ids we've already added to avoid duplicates
    
    try:
        # Step 1: Load clan CSV to find register_ids and collect clan data for this family name
        clan_data_by_register_id = {}  # Maps register_id -> clan CSV row data
        register_ids = []
        legacy_ids_for_family = []  # Collect legacy_ids for this family for STA matching
        
        with open(clan_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clan_family = row.get('family', '').strip()
                if clan_family and clan_family.lower() == family_name.lower():
                    register_id = row.get('register_id', '').strip()
                    legacy_id = row.get('legacy_id', '').strip()
                    
                    if register_id:
                        register_ids.append(register_id)
                        # Store all clan CSV fields (prefix with 'clan_' to avoid conflicts)
                        clan_data_by_register_id[register_id] = {
                            'clan_id': row.get('id', ''),
                            'clan_preview': row.get('preview', ''),
                            'clan_type': row.get('type', ''),
                            'clan_family': row.get('family', ''),
                            'clan_name': row.get('name', ''),
                            'clan_nationality': row.get('nationality', ''),
                            'clan_legacy_id': legacy_id,
                            'clan_attribute': row.get('attribute', ''),
                            'clan_offline': row.get('offline', ''),
                            'clan_restriction_supplier': row.get('restriction_supplier', ''),
                            'clan_active': row.get('active', ''),
                            'clan_customers': row.get('customers', ''),
                            'clan_created_at': row.get('created_at', ''),
                            'clan_description': row.get('description', ''),
                            'clan_register_id': register_id,
                        }
                    
                    if legacy_id:
                        legacy_ids_for_family.append(legacy_id)
        
        # Step 2: Load register CSV to get tartan details
        # First, get tartans via register_id matching
        with open(srt_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                register_id = row.get('id', '').strip()
                sta_ref = row.get('sta_ref', '').strip()
                
                # Method 1: Direct register_id match
                if register_id in register_ids:
                    seen_register_ids.add(register_id)
                    tartan_record = _build_tartan_record(row, clan_data_by_register_id.get(register_id))
                    tartans.append(tartan_record)
                
                # Method 2: STA Reference -> Legacy ID match (only if not already added)
                elif sta_ref and sta_ref in legacy_ids_for_family and register_id not in seen_register_ids:
                    seen_register_ids.add(register_id)
                    # Find the clan data for this legacy_id
                    clan_data_for_legacy = None
                    for reg_id, clan_data in clan_data_by_register_id.items():
                        if clan_data.get('clan_legacy_id') == sta_ref:
                            clan_data_for_legacy = clan_data
                            break
                    
                    # If no clan data found, try to find it in the full clan CSV
                    if not clan_data_for_legacy:
                        with open(clan_csv, 'r', encoding='utf-8') as f2:
                            clan_reader = csv.DictReader(f2)
                            for clan_row in clan_reader:
                                if (clan_row.get('family', '').strip().lower() == family_name.lower() and
                                    clan_row.get('legacy_id', '').strip() == sta_ref):
                                    clan_data_for_legacy = {
                                        'clan_id': clan_row.get('id', ''),
                                        'clan_preview': clan_row.get('preview', ''),
                                        'clan_type': clan_row.get('type', ''),
                                        'clan_family': clan_row.get('family', ''),
                                        'clan_name': clan_row.get('name', ''),
                                        'clan_nationality': clan_row.get('nationality', ''),
                                        'clan_legacy_id': sta_ref,
                                        'clan_attribute': clan_row.get('attribute', ''),
                                        'clan_offline': clan_row.get('offline', ''),
                                        'clan_restriction_supplier': clan_row.get('restriction_supplier', ''),
                                        'clan_active': clan_row.get('active', ''),
                                        'clan_customers': clan_row.get('customers', ''),
                                        'clan_created_at': clan_row.get('created_at', ''),
                                        'clan_description': clan_row.get('description', ''),
                                        'clan_register_id': clan_row.get('register_id', ''),
                                    }
                                    break
                    
                    tartan_record = _build_tartan_record(row, clan_data_for_legacy)
                    tartans.append(tartan_record)
        
        # Sort by registration_date (newest first), then by tartan_name
        def sort_key(t):
            reg_date = t.get('registration_date', '')
            name = t.get('tartan_name', '')
            # Parse date for sorting (YYYY-MM-DD format)
            try:
                if reg_date:
                    # Return tuple: (year, month, day) for sorting, with None last
                    parts = reg_date.split('-')
                    if len(parts) == 3:
                        return (int(parts[0]), int(parts[1]), int(parts[2]), name)
                return (0, 0, 0, name)  # No date, sort by name
            except (ValueError, IndexError):
                return (0, 0, 0, name)
        
        tartans.sort(key=sort_key, reverse=True)
        
    except Exception as e:
        logger.error(f"Error loading SRT data for family {family_name}: {e}", exc_info=True)
    
    return tartans


def _build_tartan_record(register_row: dict, clan_data: dict = None) -> dict:
    """Build a tartan record from register CSV row and optional clan CSV data."""
    tartan_record = {
        # Register CSV fields
        'register_id': register_row.get('id', ''),
        'tartan_name': register_row.get('tartan_name', ''),
        'reference': register_row.get('reference', ''),
        'designer': register_row.get('designer', ''),
        'tartan_date': register_row.get('tartan_date', '').strip(),
        'registration_date': register_row.get('registration_date', '').strip(),
        'category': register_row.get('category', ''),
        'restrictions': register_row.get('restrictions', ''),
        'registration_notes': register_row.get('registration_notes', ''),
        'woven_sample': register_row.get('woven_sample', ''),
        'registrant_details': register_row.get('registrant_details', ''),
        'sta_ref': register_row.get('sta_ref', ''),
        'stwr_ref': register_row.get('stwr_ref', ''),
        'register_created_at': register_row.get('created_at', ''),
        'register_updated_at': register_row.get('updated_at', ''),
        'register_clan_id': register_row.get('clan_id', ''),
    }
    
    # Merge in clan CSV data if available
    if clan_data:
        tartan_record.update(clan_data)
    
    return tartan_record


def get_clan_com_image_url(family_name: str, resource_category: str, resource_value: str) -> str:
    """Generate a clan.com static image URL from local resource data.
    
    Two URL patterns:
    1. families_processed/ - for images with subdirectories (e.g., crests)
       Pattern: .../families_processed/{category}/{family_name}/{image_name}.png
    2. families/ - for simple images without subdirectories
       Pattern: .../families/{category}/{family_name}.png
    """
    base_url = "https://static.clan.com/media/resized/250_auto_1_1_0/swfabrics/"
    
    # Map resource categories to clan.com category paths
    category_map = {
        'crest_scottish_svg': 'crest_scottish_belt_png',
        'crest_scottish': 'crest_scottish_belt_png',
        'crest_english_svg': 'crest_english_belt_png',
        'crest_english': 'crest_english_belt_png',
        'gaelic_crest_irish_svg': 'gaelic_crest_irish_png',
        'gaelic_crest_irish': 'gaelic_crest_irish_png',
    }
    
    # Get the mapped category
    # For SVG categories, map to the base category (without _svg), not _png
    if resource_category in category_map:
        mapped_category = category_map[resource_category]
    elif resource_category.endswith('_svg'):
        # Remove _svg suffix to get base category (e.g., bookplate_scottish_svg -> bookplate_scottish)
        mapped_category = resource_category.replace('_svg', '')
    else:
        mapped_category = resource_category
    
    # Determine which pattern to use based on whether resource_value has a subdirectory
    has_subdirectory = '/' in resource_value and not resource_value.startswith(family_name + '/')
    
    if has_subdirectory or resource_category in ['crest_scottish_svg', 'crest_scottish', 'crest_english_svg', 'crest_english', 'gaelic_crest_irish_svg', 'gaelic_crest_irish']:
        # Pattern 1: families_processed/ with subdirectory
        # Extract image filename from resource_value
        # Value might be "Family/Image.svg" or "Family/Image.png"
        if '/' in resource_value:
            image_name = resource_value.split('/')[-1]  # Get last part after /
        else:
            image_name = resource_value
        
        # Remove extension and add .png
        image_name_no_ext = image_name.rsplit('.', 1)[0] if '.' in image_name else image_name
        image_name_png = f"{image_name_no_ext}.png"
        
        # URL encode the image name
        encoded_image = quote(image_name_png)
        
        return f"{base_url}families_processed/{mapped_category}/{family_name}/{encoded_image}"
    else:
        # Pattern 2: families/ - simple direct image
        # Extract filename from resource_value (might be "Family.png", "family.jpg", etc.)
        if '/' in resource_value:
            image_name = resource_value.split('/')[-1]
        else:
            image_name = resource_value
        
        # Preserve the original extension and case from resource_value
        # Only convert .svg to .png, otherwise keep original extension
        if image_name.lower().endswith('.svg'):
            # Convert SVG to PNG
            image_name_no_ext = image_name.rsplit('.', 1)[0]
            image_filename = f"{image_name_no_ext}.png"
        else:
            # Keep original filename (preserves case and extension like .jpg, .png)
            image_filename = image_name
        
        return f"{base_url}families/{mapped_category}/{image_filename}"


@bp.app_context_processor
def inject_clan_com_url():
    """Make get_clan_com_image_url available in templates."""
    return dict(get_clan_com_image_url=get_clan_com_image_url)


@bp.route('/')
def browser():
    """Main families browser page with filters."""
    return render_template('families/browser.html')


@bp.route('/<int:family_id>/narrative')
@bp.route('/<int:family_id>/narrative/')
def family_narrative(family_id):
    """Shareable narrative page for a family."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family
                cur.execute("SELECT id, name, research_data FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                
                if not family:
                    return render_template('families/not_found.html', family_id=family_id), 404
                
                family_dict = dict(family)
                
                # Parse research_data from JSONB if present
                if family_dict.get('research_data'):
                    if isinstance(family_dict['research_data'], str):
                        family_dict['research_data'] = json.loads(family_dict['research_data'])
                
                # Check if narrative exists
                narrative = None
                if (family_dict.get('research_data') and 
                    family_dict['research_data'].get('metadata') and 
                    family_dict['research_data']['metadata'].get('narrative')):
                    narrative = family_dict['research_data']['metadata']['narrative']
                    last_updated = family_dict['research_data']['metadata'].get('last_updated', 'Unknown')
                    word_count = family_dict['research_data']['metadata'].get('narrative_word_count', 0)
                else:
                    return render_template('families/narrative_not_found.html', 
                                         family_name=family_dict['name'], 
                                         family_id=family_id), 404
                
                return render_template('families/narrative.html', 
                                     family_name=family_dict['name'],
                                     family_id=family_id,
                                     narrative=narrative,
                                     last_updated=last_updated,
                                     word_count=word_count)
    
    except Exception as e:
        logger.error(f"Error loading narrative: {e}", exc_info=True)
        return render_template('families/error.html', error=str(e)), 500


@bp.route('/<int:family_id>')
@bp.route('/<int:family_id>/')
def family_detail(family_id):
    """Family detail page."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family
                cur.execute("SELECT * FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                
                if not family:
                    return render_template('families/not_found.html', family_id=family_id), 404
                
                family_dict = dict(family)
                
                # Get filtered family IDs from server-side filter key (if present)
                # Otherwise, fall back to previous behaviour.
                filter_key = request.args.get('filter_key')
                filtered_ids_param = request.args.get('filtered_ids')
                if filter_key:
                    from datetime import datetime, timedelta
                    # Clean up expired keys
                    now = datetime.utcnow()
                    expired_keys = [
                        k for k, v in FILTERED_ID_SETS.items()
                        if (now - v.get('created_at', now)) > timedelta(seconds=FILTERED_ID_SETS_MAX_AGE_SECONDS)
                    ]
                    for k in expired_keys:
                        FILTERED_ID_SETS.pop(k, None)
                    
                    id_set = FILTERED_ID_SETS.get(filter_key)
                    filtered_ids = id_set.get('ids', []) if id_set else []
                    if filtered_ids and family_id in filtered_ids:
                        current_index = filtered_ids.index(family_id)
                        if current_index > 0:
                            prev_id = filtered_ids[current_index - 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (prev_id,))
                            prev_family = cur.fetchone()
                            family_dict['prev_family'] = dict(prev_family) if prev_family else None
                        else:
                            family_dict['prev_family'] = None
                        
                        if current_index < len(filtered_ids) - 1:
                            next_id = filtered_ids[current_index + 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (next_id,))
                            next_family = cur.fetchone()
                            family_dict['next_family'] = dict(next_family) if next_family else None
                        else:
                            family_dict['next_family'] = None
                    else:
                        family_dict['prev_family'] = None
                        family_dict['next_family'] = None
                elif filtered_ids_param:
                    try:
                        filtered_ids = [int(id) for id in filtered_ids_param.split(',')]
                        current_index = filtered_ids.index(family_id) if family_id in filtered_ids else -1
                        
                        if current_index > 0:
                            prev_id = filtered_ids[current_index - 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (prev_id,))
                            prev_family = cur.fetchone()
                            family_dict['prev_family'] = dict(prev_family) if prev_family else None
                        else:
                            family_dict['prev_family'] = None
                        
                        if current_index >= 0 and current_index < len(filtered_ids) - 1:
                            next_id = filtered_ids[current_index + 1]
                            cur.execute("SELECT id, name FROM families WHERE id = %s", (next_id,))
                            next_family = cur.fetchone()
                            family_dict['next_family'] = dict(next_family) if next_family else None
                        else:
                            family_dict['next_family'] = None
                    except (ValueError, IndexError):
                        # Fallback to ID-based navigation if parsing fails
                        cur.execute("SELECT id, name FROM families WHERE id < %s ORDER BY id DESC LIMIT 1", (family_id,))
                        prev_family = cur.fetchone()
                        cur.execute("SELECT id, name FROM families WHERE id > %s ORDER BY id ASC LIMIT 1", (family_id,))
                        next_family = cur.fetchone()
                        family_dict['prev_family'] = dict(prev_family) if prev_family else None
                        family_dict['next_family'] = dict(next_family) if next_family else None
                else:
                    # Default: get previous and next by ID order
                    cur.execute("SELECT id, name FROM families WHERE id < %s ORDER BY id DESC LIMIT 1", (family_id,))
                    prev_family = cur.fetchone()
                    cur.execute("SELECT id, name FROM families WHERE id > %s ORDER BY id ASC LIMIT 1", (family_id,))
                    next_family = cur.fetchone()
                    family_dict['prev_family'] = dict(prev_family) if prev_family else None
                    family_dict['next_family'] = dict(next_family) if next_family else None
                
                # Pass current filters to template for navigation links
                family_dict['current_filters'] = dict(request.args)
                
                # Parse research_data from JSONB if present
                if family_dict.get('research_data'):
                    import json
                    if isinstance(family_dict['research_data'], str):
                        family_dict['research_data'] = json.loads(family_dict['research_data'])
                    # If it's already a dict (psycopg parsed it), keep it as is
                
                # Get relationships
                cur.execute("""
                    SELECT alias_name FROM family_aliases 
                    WHERE family_id = %s ORDER BY alias_name
                """, (family_id,))
                family_dict['aliases'] = [row['alias_name'] for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.spelling_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['variants'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.spelling_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['spelling_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.sept_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['septs'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.sept_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['sept_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT DISTINCT ON (resource_type, resource_category, resource_value)
                        resource_type, resource_category, resource_value, resource_metadata
                    FROM family_resources
                    WHERE family_id = %s
                    ORDER BY resource_type, resource_category, resource_value
                """, (family_id,))
                all_resources = [dict(row) for row in cur.fetchall()]
                
                # Group image resources by style to avoid duplicates
                image_groups = {}
                for resource in all_resources:
                    if resource['resource_type'] == 'image' and resource['resource_value']:
                        category = resource['resource_category'] or ''
                        category_lower = category.lower()
                        
                        # Map category to style group
                        style_group = None
                        style_title = None
                        
                        if 'bookplate' in category_lower:
                            style_group = 'bookplate'
                            style_title = 'Bookplate'
                        elif 'book_cover' in category_lower:
                            style_group = 'book_cover'
                            style_title = 'Book Cover'
                        elif 'british_fleet' in category_lower:
                            style_group = 'british_fleet'
                            style_title = 'British (Fleet)'
                        elif 'crest_scottish' in category_lower or (category.startswith('crest') and 'scottish' in category_lower):
                            style_group = 'crest_scottish'
                            style_title = 'Crest (Scottish)'
                        elif 'crest_english' in category_lower or (category.startswith('crest') and 'english' in category_lower):
                            style_group = 'crest_english'
                            style_title = 'Crest (English)'
                        elif 'gaelic_crest' in category_lower or 'crest_irish' in category_lower:
                            style_group = 'crest_irish'
                            style_title = 'Crest (Irish)'
                        elif 'families_of_britain' in category_lower:
                            style_group = 'families_of_britain'
                            style_title = 'Families (Of Britain Pro Scottish)'
                        elif 'fighting_irish' in category_lower:
                            style_group = 'fighting_irish'
                            style_title = 'Fighting (Irish)'
                        elif 'scottish_gentry' in category_lower:
                            style_group = 'scottish_gentry'
                            style_title = 'Scottish (Gentry)'
                        elif 'hero_badge' in category_lower or 'hero' in category_lower:
                            style_group = 'hero'
                            style_title = 'Hero Badge'
                        elif category_lower.startswith('badge_'):
                            style_group = 'badge'
                            style_title = 'Badge'
                        else:
                            style_group = category or 'other'
                            style_title = category.replace('_', ' ').title() if category else 'Other'
                        
                        # Store in group, preferring non-SVG versions
                        if style_group not in image_groups:
                            image_groups[style_group] = {
                                'title': style_title,
                                'resource': resource
                            }
                        elif not resource['resource_value'].endswith('.svg') and image_groups[style_group]['resource']['resource_value'].endswith('.svg'):
                            # Prefer non-SVG if we have one
                            image_groups[style_group]['resource'] = resource
                
                # Add grouped images to resources list (always set, even if empty)
                family_dict['image_groups'] = list(image_groups.values())
                family_dict['resources'] = all_resources
                
                cur.execute("""
                    SELECT design_id, design_year, design_url, is_default
                    FROM family_designs
                    WHERE family_id = %s
                    ORDER BY is_default DESC, design_year DESC
                """, (family_id,))
                family_dict['designs'] = [dict(row) for row in cur.fetchall()]
                
                # Load SRT (Scottish Register of Tartans) data
                srt_data = load_srt_data_for_family(family_dict['name'])
                family_dict['srt_tartans'] = srt_data
                
                return render_template('families/detail.html', family=family_dict)
    except Exception as e:
        logger.error(f"Error loading family detail: {e}", exc_info=True)
        return render_template('families/error.html', error=str(e)), 500


@bp.route('/<int:family_id>/export')
def family_export(family_id):
    """Export-friendly view of family data with all images and text."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family data (same as detail view)
                cur.execute("""
                    SELECT 
                        f.id, f.name, f.is_clan, f.spelling_of, f.has_history,
                        f.research_data, f.popularity_rating, f.research_approved
                    FROM families f
                    WHERE f.id = %s
                """, (family_id,))
                family_row = cur.fetchone()
                
                if not family_row:
                    abort(404)
                
                family_dict = dict(family_row)
                
                # Get all resources (same grouping logic as detail)
                cur.execute("""
                    SELECT DISTINCT ON (resource_type, resource_category, resource_value)
                        resource_type, resource_category, resource_value, resource_metadata
                    FROM family_resources
                    WHERE family_id = %s
                    ORDER BY resource_type, resource_category, resource_value
                """, (family_id,))
                all_resources = [dict(row) for row in cur.fetchall()]
                
                # Group image resources by style (same logic as detail)
                image_groups = {}
                for resource in all_resources:
                    if resource['resource_type'] == 'image' and resource['resource_value']:
                        category = resource['resource_category'] or ''
                        category_lower = category.lower()
                        
                        style_group = None
                        style_title = None
                        
                        if 'bookplate' in category_lower:
                            style_group = 'bookplate'
                            style_title = 'Bookplate'
                        elif 'book_cover' in category_lower:
                            style_group = 'book_cover'
                            style_title = 'Book Cover'
                        elif 'british_fleet' in category_lower:
                            style_group = 'british_fleet'
                            style_title = 'British (Fleet)'
                        elif 'crest_scottish' in category_lower or (category.startswith('crest') and 'scottish' in category_lower):
                            style_group = 'crest_scottish'
                            style_title = 'Crest (Scottish)'
                        elif 'crest_english' in category_lower or (category.startswith('crest') and 'english' in category_lower):
                            style_group = 'crest_english'
                            style_title = 'Crest (English)'
                        elif 'gaelic_crest' in category_lower or 'crest_irish' in category_lower:
                            style_group = 'crest_irish'
                            style_title = 'Crest (Irish)'
                        elif 'families_of_britain' in category_lower:
                            style_group = 'families_of_britain'
                            style_title = 'Families (Of Britain Pro Scottish)'
                        elif 'fighting_irish' in category_lower:
                            style_group = 'fighting_irish'
                            style_title = 'Fighting (Irish)'
                        elif 'scottish_gentry' in category_lower:
                            style_group = 'scottish_gentry'
                            style_title = 'Scottish (Gentry)'
                        elif 'hero_badge' in category_lower or 'hero' in category_lower:
                            style_group = 'hero'
                            style_title = 'Hero Badge'
                        elif category_lower.startswith('badge_'):
                            style_group = 'badge'
                            style_title = 'Badge'
                        else:
                            style_group = category or 'other'
                            style_title = category.replace('_', ' ').title() if category else 'Other'
                        
                        if style_group not in image_groups:
                            image_groups[style_group] = {
                                'title': style_title,
                                'resource': resource
                            }
                        elif not resource['resource_value'].endswith('.svg') and image_groups[style_group]['resource']['resource_value'].endswith('.svg'):
                            image_groups[style_group]['resource'] = resource
                
                family_dict['image_groups'] = list(image_groups.values())
                family_dict['resources'] = all_resources
                
                # Get text resources
                text_resources = [r for r in all_resources if r['resource_type'] == 'text']
                family_dict['text_resources'] = text_resources
                
                # Get legacy histories
                legacy_histories = [r for r in text_resources if r['resource_category'] == 'history_legacy']
                family_dict['legacy_histories'] = legacy_histories
                
                # Get generated legacy
                generated_legacy = [r for r in text_resources if r['resource_category'] == 'history_legacy_generated']
                family_dict['generated_legacy'] = generated_legacy[0] if generated_legacy else None
                
                # Parse research_data
                if family_dict.get('research_data'):
                    import json
                    if isinstance(family_dict['research_data'], str):
                        family_dict['research_data'] = json.loads(family_dict['research_data'])
                
                # Get narrative_fact_checked from research_data
                narrative_fact_checked = None
                if family_dict.get('research_data') and isinstance(family_dict['research_data'], dict):
                    metadata = family_dict['research_data'].get('metadata', {})
                    narrative_fact_checked = metadata.get('narrative_fact_checked')
                family_dict['narrative_fact_checked'] = narrative_fact_checked
                
            return render_template('families/export.html', family=family_dict)
    except Exception as e:
        logger.error(f"Error loading family export: {e}", exc_info=True)
        abort(500)


@bp.route('/api/list')
def api_list():
    """API endpoint for listing families with filters."""
    try:
        # Get filter parameters
        search = request.args.get('search', '').strip()
        is_clan = request.args.get('is_clan')
        is_canonical = request.args.get('is_canonical')
        has_history = request.args.get('has_history')
        has_research = request.args.get('has_research')
        has_srt = request.args.get('has_srt')  # 'true', 'false', or None
        is_virtual = request.args.get('is_virtual')
        name_has_of = request.args.get('name_has_of')  # 'include', 'exclude', or None
        popularity_min = request.args.get('popularity_min')
        popularity_max = request.args.get('popularity_max')
        sort_by = request.args.get('sort_by', 'name')  # name, popularity
        sort_order = request.args.get('sort_order', 'asc')  # asc, desc
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Build WHERE clause
                conditions = []
                params = []
                
                if search:
                    conditions.append("f.name ILIKE %s")
                    params.append(f"%{search}%")
                
                if is_clan is not None:
                    conditions.append("f.is_clan = %s")
                    params.append(is_clan.lower() == 'true')
                
                if is_canonical is not None:
                    # Use spelling_of IS NULL to identify canonical names
                    if is_canonical.lower() == 'true':
                        conditions.append("f.spelling_of IS NULL")
                    else:
                        conditions.append("f.spelling_of IS NOT NULL")
                
                if has_history is not None:
                    conditions.append("f.has_history = %s")
                    params.append(has_history.lower() == 'true')
                
                if has_research is not None:
                    if has_research.lower() == 'true':
                        conditions.append("f.research_data IS NOT NULL")
                    else:
                        conditions.append("f.research_data IS NULL")
                
                # Filter by is_virtual (true/false)
                if is_virtual is not None and is_virtual != '':
                    conditions.append("f.is_virtual = %s")
                    params.append(is_virtual.lower() == 'true')
                
                # Filter by names containing the exact string ' of ' (with spaces)
                if name_has_of in ('include', 'exclude'):
                    if name_has_of == 'include':
                        conditions.append("f.name LIKE %s")
                        params.append("% of %")
                    else:
                        conditions.append("f.name NOT LIKE %s")
                        params.append("% of %")
                
                if popularity_min is not None:
                    try:
                        conditions.append("f.popularity_rating >= %s")
                        params.append(int(popularity_min))
                    except ValueError:
                        pass
                
                if popularity_max is not None:
                    try:
                        conditions.append("f.popularity_rating <= %s")
                        params.append(int(popularity_max))
                    except ValueError:
                        pass
                
                # Filter by SRT data (has_srt)
                if has_srt is not None:
                    srt_families = get_families_with_srt_data()
                    if has_srt.lower() == 'true':
                        # Only families with SRT data
                        if srt_families:
                            # Create a list of family names for IN clause
                            placeholders = ','.join(['%s'] * len(srt_families))
                            conditions.append(f"LOWER(f.name) IN ({placeholders})")
                            params.extend(list(srt_families))
                        else:
                            # No SRT families, so this filter returns nothing
                            conditions.append("1=0")
                    else:
                        # Only families without SRT data
                        if srt_families:
                            placeholders = ','.join(['%s'] * len(srt_families))
                            conditions.append(f"LOWER(f.name) NOT IN ({placeholders})")
                            params.extend(list(srt_families))
                        # If no SRT families, all families match (no filter needed)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Get SRT families set for has_srt field (used in SELECT and stats)
                srt_families_set = get_families_with_srt_data()
                srt_families_list = list(srt_families_set)
                
                # Build ORDER BY clause
                valid_sort_fields = {'name': 'f.name', 'popularity': 'f.popularity_rating'}
                sort_field = valid_sort_fields.get(sort_by, 'f.name')
                sort_dir = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
                
                # Handle NULL values in popularity sorting
                if sort_by == 'popularity':
                    # Put NULLs last regardless of sort order
                    order_clause = f"f.popularity_rating {sort_dir} NULLS LAST, f.name ASC"
                else:
                    order_clause = f"{sort_field} {sort_dir}"
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM families f
                    WHERE {where_clause}
                """
                cur.execute(count_query, params)
                total = cur.fetchone()['total']
                
                # Build has_srt CASE statement
                if srt_families_list:
                    srt_placeholders = ','.join(['%s'] * len(srt_families_list))
                    has_srt_case = f"CASE WHEN LOWER(f.name) IN ({srt_placeholders}) THEN true ELSE false END"
                else:
                    has_srt_case = "FALSE"
                
                # Get families with relationships
                query = f"""
                    SELECT 
                        f.id,
                        f.name,
                        f.is_clan,
                        (f.spelling_of IS NULL) as is_canonical,
                        f.has_history,
                        f.is_virtual,
                        f.popularity_rating,
                        CASE WHEN f.research_data IS NOT NULL THEN true ELSE false END as has_research,
                        CASE WHEN f.research_data IS NOT NULL AND jsonb_typeof(f.research_data) = 'object' AND (f.research_data::text != '{{}}'::text) THEN true ELSE false END as has_json,
                        CASE WHEN f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative' THEN true ELSE false END as has_compiled,
                        CASE WHEN f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked' THEN true ELSE false END as has_openai,
                        (
                            SELECT COUNT(*) 
                            FROM family_resources fr 
                            WHERE fr.family_id = f.id 
                              AND fr.resource_type = 'text'
                              AND fr.resource_category = 'history_legacy'
                              AND fr.resource_value IS NOT NULL
                              AND array_length(
                                    string_to_array(
                                        regexp_replace(fr.resource_value, '\\s+', ' ', 'g'),
                                        ' '
                                    ),
                                    1
                                  ) > 50
                        ) as legacy_history_count,
                        CASE WHEN EXISTS (
                            SELECT 1 
                            FROM family_resources fr2
                            WHERE fr2.family_id = f.id
                              AND fr2.resource_type = 'text'
                              AND fr2.resource_category = 'history_legacy_generated'
                        ) THEN true ELSE false END as has_legacy_generated,
                        {has_srt_case} as has_srt,
                        (SELECT COUNT(*) FROM family_aliases WHERE family_id = f.id) as alias_count,
                        (SELECT COUNT(*) FROM family_spellings WHERE family_id = f.id) as variant_count,
                        (SELECT COUNT(*) FROM family_spellings WHERE spelling_of_id = f.id) as has_variants_count,
                        (SELECT COUNT(*) FROM family_septs WHERE family_id = f.id) as sept_count,
                        (SELECT COUNT(*) FROM family_septs WHERE sept_of_id = f.id) as has_septs_count,
                        (SELECT COUNT(*) FROM family_resources WHERE family_id = f.id) as resource_count,
                        (SELECT COUNT(*) FROM family_designs WHERE family_id = f.id) as design_count
                    FROM families f
                    WHERE {where_clause}
                    ORDER BY {order_clause}
                    LIMIT %s OFFSET %s
                """
                # Build has_srt filter for stats query
                if srt_families_list:
                    srt_stats_placeholders = ','.join(['%s'] * len(srt_families_list))
                    srt_stats_filter = f"LOWER(f.name) IN ({srt_stats_placeholders})"
                else:
                    srt_stats_filter = "FALSE"
                
                # Get filtered stats for the current filter set (before adding pagination params)
                stats_query = f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE f.is_clan = TRUE) as clans,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL) as canonical,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE) as with_history,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL) as with_research,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND jsonb_typeof(f.research_data) = 'object' AND (f.research_data::text != '{{}}'::text)) as with_json,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative') as with_compiled,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_openai,
                        COUNT(*) FILTER (
                            WHERE EXISTS (
                                SELECT 1 
                                FROM family_resources frg
                                WHERE frg.family_id = f.id
                                  AND frg.resource_type = 'text'
                                  AND frg.resource_category = 'history_legacy_generated'
                            )
                        ) as with_legacy_generated,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE AND f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_both,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL AND f.has_history = FALSE AND (f.research_data IS NULL OR NOT (f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked'))) as canonical_no_content,
                        COUNT(*) FILTER (WHERE {srt_stats_filter}) as with_srt
                    FROM families f
                    WHERE {where_clause}
                """
                # Add SRT family names to stats query params
                stats_params = list(params)
                if srt_families_list:
                    stats_params.extend(srt_families_list)
                cur.execute(stats_query, stats_params)
                filtered_stats = dict(cur.fetchone())
                
                # Execute main query - add SRT family names to params if needed
                query_params = list(params)
                if srt_families_list:
                    query_params.extend(srt_families_list)
                query_params.extend([per_page, offset])
                cur.execute(query, query_params)
                families = [dict(row) for row in cur.fetchall()]

                return jsonify({
                    'families': families,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page,
                    'filtered_stats': filtered_stats
                })
    
    except Exception as e:
        logger.error(f"Error listing families: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/store_filter_ids', methods=['POST'])
def api_store_filter_ids():
    """Store filtered family IDs server-side and return a short key."""
    try:
        data = request.get_json(silent=True) or {}
        ids = data.get('ids') or []
        # Normalise to list of ints
        try:
            ids = [int(i) for i in ids]
        except (TypeError, ValueError):
            ids = []
        
        if not ids:
            return jsonify({'error': 'No ids provided'}), 400
        
        from uuid import uuid4
        from datetime import datetime, timedelta

        # Prune expired keys
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in FILTERED_ID_SETS.items()
            if (now - v.get('created_at', now)) > timedelta(seconds=FILTERED_ID_SETS_MAX_AGE_SECONDS)
        ]
        for k in expired_keys:
            FILTERED_ID_SETS.pop(k, None)
        
        key = uuid4().hex[:12]
        FILTERED_ID_SETS[key] = {
            'ids': ids,
            'created_at': now,
        }
        
        return jsonify({'key': key})
    except Exception as e:
        logger.error(f"Error storing filter ids: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/<int:family_id>/approve', methods=['POST', 'PUT'])
def api_family_approve(family_id):
    """Update the research_approved status for a family."""
    try:
        data = request.get_json()
        approved = data.get('approved', False)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE families 
                    SET research_approved = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (approved, family_id))
                conn.commit()
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Family not found'}), 404
                
                return jsonify({'success': True, 'approved': approved})
    
    except Exception as e:
        logger.error(f"Error updating approval status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/<int:family_id>/feedback', methods=['POST'])
def api_family_feedback(family_id):
    """Submit feedback for a family's research data and trigger regeneration."""
    try:
        data = request.get_json()
        feedback = data.get('feedback', '').strip()
        
        if not feedback:
            return jsonify({'error': 'Feedback is required'}), 400
        
        # Get family info
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                if not family:
                    return jsonify({'error': 'Family not found'}), 404
        
        # Run regeneration script
        import subprocess
        import sys
        from pathlib import Path
        
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        result = subprocess.run(
            [sys.executable, str(scripts_dir / 'regenerate_with_feedback.py'), 
             str(family_id), feedback],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Parse report from stdout
        import re
        import json
        report = None
        report_match = re.search(
            r'FEEDBACK_PROCESSING_REPORT_START\s*(.*?)\s*FEEDBACK_PROCESSING_REPORT_END',
            result.stdout,
            re.DOTALL
        )
        if report_match:
            try:
                report = json.loads(report_match.group(1))
            except json.JSONDecodeError:
                logger.warning(f"Could not parse report JSON for family {family_id}")
        
        if result.returncode != 0:
            logger.error(f"Error regenerating family {family_id}: {result.stderr}")
            logger.error(f"Script stdout: {result.stdout}")
            return jsonify({
                'error': 'Failed to process feedback',
                'details': result.stderr[:500] if result.stderr else 'Unknown error',
                'stdout': result.stdout[:500] if result.stdout else '',
                'report': report
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Feedback processed successfully',
            'output': result.stdout,
            'report': report
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Processing timed out'}), 500
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/<int:family_id>')
def api_family_detail(family_id):
    """Get detailed information about a specific family."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get family
                cur.execute("SELECT * FROM families WHERE id = %s", (family_id,))
                family = cur.fetchone()
                
                if not family:
                    return jsonify({'error': 'Family not found'}), 404
                
                family_dict = dict(family)
                
                # Get relationships
                cur.execute("""
                    SELECT alias_name FROM family_aliases 
                    WHERE family_id = %s ORDER BY alias_name
                """, (family_id,))
                family_dict['aliases'] = [row['alias_name'] for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.spelling_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['variants'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_spellings fs
                    JOIN families f2 ON fs.spelling_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['spelling_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.family_id = f2.id
                    WHERE fs.sept_of_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['septs'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT f2.id, f2.name
                    FROM family_septs fs
                    JOIN families f2 ON fs.sept_of_id = f2.id
                    WHERE fs.family_id = %s
                    ORDER BY f2.name
                """, (family_id,))
                family_dict['sept_of'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT resource_type, resource_category, resource_value
                    FROM family_resources
                    WHERE family_id = %s
                    ORDER BY resource_type, resource_category
                """, (family_id,))
                family_dict['resources'] = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT design_id, design_year, design_url, is_default
                    FROM family_designs
                    WHERE family_id = %s
                    ORDER BY is_default DESC, design_year DESC
                """, (family_id,))
                family_dict['designs'] = [dict(row) for row in cur.fetchall()]
                
                return jsonify(family_dict)
    
    except Exception as e:
        logger.error(f"Error getting family detail: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/stats')
def api_stats():
    """Get statistics about families, optionally filtered."""
    try:
        # Get filter parameters (same as api_list)
        search = request.args.get('search', '').strip()
        is_clan = request.args.get('is_clan')
        is_canonical = request.args.get('is_canonical')
        has_history = request.args.get('has_history')
        has_research = request.args.get('has_research')
        has_srt = request.args.get('has_srt')  # 'true', 'false', or None
        is_virtual = request.args.get('is_virtual')
        name_has_of = request.args.get('name_has_of')  # 'include', 'exclude', or None
        popularity_min = request.args.get('popularity_min')
        popularity_max = request.args.get('popularity_max')
        
        # Get SRT families set for stats
        srt_families_set = get_families_with_srt_data()
        srt_families_list = list(srt_families_set)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Build WHERE clause (same logic as api_list)
                conditions = []
                params = []
                
                if search:
                    conditions.append("f.name ILIKE %s")
                    params.append(f"%{search}%")
                
                if is_clan is not None:
                    conditions.append("f.is_clan = %s")
                    params.append(is_clan.lower() == 'true')
                
                if is_canonical is not None:
                    if is_canonical.lower() == 'true':
                        conditions.append("f.spelling_of IS NULL")
                    else:
                        conditions.append("f.spelling_of IS NOT NULL")
                
                if has_history is not None:
                    conditions.append("f.has_history = %s")
                    params.append(has_history.lower() == 'true')
                
                if has_research is not None:
                    if has_research.lower() == 'true':
                        conditions.append("f.research_data IS NOT NULL")
                    else:
                        conditions.append("f.research_data IS NULL")
                
                # Filter by is_virtual (true/false)
                if is_virtual is not None and is_virtual != '':
                    conditions.append("f.is_virtual = %s")
                    params.append(is_virtual.lower() == 'true')
                
                # Filter by names containing the exact string ' of ' (with spaces)
                if name_has_of in ('include', 'exclude'):
                    if name_has_of == 'include':
                        conditions.append("f.name LIKE %s")
                        params.append("% of %")
                    else:
                        conditions.append("f.name NOT LIKE %s")
                        params.append("% of %")
                
                if popularity_min is not None:
                    try:
                        conditions.append("f.popularity_rating >= %s")
                        params.append(int(popularity_min))
                    except ValueError:
                        pass
                
                if popularity_max is not None:
                    try:
                        conditions.append("f.popularity_rating <= %s")
                        params.append(int(popularity_max))
                    except ValueError:
                        pass
                
                # Filter by SRT data (has_srt)
                if has_srt is not None:
                    if has_srt.lower() == 'true':
                        if srt_families_list:
                            placeholders = ','.join(['%s'] * len(srt_families_list))
                            conditions.append(f"LOWER(f.name) IN ({placeholders})")
                            params.extend(list(srt_families_list))
                        else:
                            conditions.append("1=0")
                    else:
                        if srt_families_list:
                            placeholders = ','.join(['%s'] * len(srt_families_list))
                            conditions.append(f"LOWER(f.name) NOT IN ({placeholders})")
                            params.extend(list(srt_families_list))
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Build has_srt filter for stats query
                if srt_families_list:
                    srt_stats_placeholders = ','.join(['%s'] * len(srt_families_list))
                    srt_stats_filter = f"LOWER(f.name) IN ({srt_stats_placeholders})"
                else:
                    srt_stats_filter = "FALSE"
                
                # Get stats with breakdown of research data
                query = f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE f.is_clan = TRUE) as clans,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL) as canonical,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE) as with_history,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL) as with_research,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND jsonb_typeof(f.research_data) = 'object' AND (f.research_data::text != '{{}}'::text)) as with_json,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative') as with_compiled,
                        COUNT(*) FILTER (WHERE f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_openai,
                        COUNT(*) FILTER (
                            WHERE EXISTS (
                                SELECT 1 
                                FROM family_resources frg
                                WHERE frg.family_id = f.id
                                  AND frg.resource_type = 'text'
                                  AND frg.resource_category = 'history_legacy_generated'
                            )
                        ) as with_legacy_generated,
                        COUNT(*) FILTER (WHERE f.has_history = TRUE AND f.research_data IS NOT NULL AND f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked') as with_both,
                        COUNT(*) FILTER (WHERE f.spelling_of IS NULL AND f.has_history = FALSE AND (f.research_data IS NULL OR NOT (f.research_data ? 'metadata' AND f.research_data->'metadata' ? 'narrative_fact_checked'))) as canonical_no_content,
                        COUNT(*) FILTER (WHERE {srt_stats_filter}) as with_srt
                    FROM families f
                    WHERE {where_clause}
                """
                # Add SRT family names to query params
                query_params = list(params)
                if srt_families_list:
                    query_params.extend(srt_families_list)
                cur.execute(query, query_params)
                stats = dict(cur.fetchone())
                
                return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

