"""
Planning Concept - Section Content Mapping

Visual mapping of CLAN product data to the 7-section structure.
"""

from flask import render_template, request
from config.database import db_manager
import logging
import re
from utils.content_generation.clan_data_extractor import ClanDataExtractor
from utils.content_generation.section_mapper import SectionMapper
from utils.taxonomy_helpers import get_post_type

logger = logging.getLogger(__name__)


def planning_concept_section_content_mapping(post_id):
    """
    Section Content Mapping page - shows which data maps to which section.
    
    For generated product posts, displays visual mapping of CLAN data to 7 sections.
    """
    try:
        # Verify this is a generated post
        post_type = get_post_type(post_id)
        if post_type != 'generated':
            from flask import redirect, url_for
            return redirect(url_for('planning.planning_concept_brainstorm', post_id=post_id))
        
        # Get product ID from post's generated_source_type and idea_seed
        product_id = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.generated_source_type, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if result:
                source_type = result.get('generated_source_type')
                idea_seed = result.get('idea_seed', '')
                
                # Extract product ID from idea_seed (same logic as product-data-review)
                if source_type == 'product' and idea_seed:
                    # Try Format 1: Extract ID from "(ID: 123)"
                    match = re.search(r'\(ID:\s*(\d+)\)', idea_seed)
                    if match:
                        product_id = int(match.group(1))
                    else:
                        # Try Format 2: Extract number from "product 185"
                        number_match = re.search(r'product[:\s]+(?:product\s+)?(\d+)', idea_seed, re.IGNORECASE)
                        if number_match:
                            product_id = int(number_match.group(1))
                        else:
                            # Fallback: try to find product by name
                            name_match = re.search(r'product:\s*([^(]+)', idea_seed, re.IGNORECASE)
                            if name_match:
                                product_name = name_match.group(1).strip()
                                cursor.execute("""
                                    SELECT id FROM clan_products
                                    WHERE name = %s
                                    LIMIT 1
                                """, (product_name,))
                                product_result = cursor.fetchone()
                                if product_result:
                                    product_id = product_result['id']
        
        if not product_id:
            # No product ID found - show error
            return render_template('planning/concept/section_content_mapping.html',
                                 post_id=post_id,
                                 post_type=post_type,
                                 error="Product ID not found. Please ensure this post was generated from a product.",
                                 blueprint_name='planning')
        
        # Extract product data
        extractor = ClanDataExtractor()
        product_data = extractor.extract_product_data(product_id)
        validation = extractor.validate_data_completeness(product_data)
        
        # Map data to sections
        mapper = SectionMapper()
        section_mapping = mapper.map_data_to_sections(product_data)
        
        # Get content type name for category banner
        content_type_name = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if result:
                content_type_name = result.get('content_type_name')
        
        # Get year and week from URL params
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        return render_template('planning/concept/section_content_mapping.html',
                              post_id=post_id,
                              year=year,
                              week=week,
                              post_type=post_type,
                              product_data=product_data,
                              product_id=product_id,
                              section_mapping=section_mapping,
                              validation=validation,
                              content_type_name=content_type_name,
                              blueprint_name='planning')
    
    except Exception as e:
        logger.error(f"Error in section_content_mapping for post {post_id}: {e}")
        import traceback
        traceback.print_exc()
        return render_template('planning/concept/section_content_mapping.html',
                             post_id=post_id,
                             post_type=get_post_type(post_id),
                             error=f"Error loading section mapping: {str(e)}",
                             blueprint_name='planning')

