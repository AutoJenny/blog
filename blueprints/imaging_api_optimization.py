"""
Image Optimization API Endpoints
API routes for optimizing images with watermarks
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from blueprints.imaging_optimization import optimize_image_with_watermark
import logging
import os
import re

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register image optimization API routes with the blueprint"""
    
    @bp.route('/api/optimize/posts/<int:post_id>/sections/<section_id>/optimize-image', methods=['POST'])
    def imaging_optimize_image(post_id, section_id):
        """Optimize image with watermark and caption for a specific section"""
        try:
            # Get parameters from request
            params = request.get_json() or {}
            
            # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
            resolved_section_id = None
            if section_id.isdigit():
                resolved_section_id = int(section_id)
            else:
                # Try to parse trailing number from patterns like section_1
                m = re.search(r'(\d+)$', section_id)
                if m:
                    section_order = int(m.group(1))
                    with db_manager.get_cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT id FROM post_section
                            WHERE post_id = %s AND section_order = %s
                            """,
                            (post_id, section_order),
                        )
                        row = cursor.fetchone()
                        if row:
                            resolved_section_id = row['id']

            if resolved_section_id is None:
                return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

            # Verify section exists
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, section_order, section_heading
                    FROM post_section
                    WHERE id = %s AND post_id = %s
                """, (resolved_section_id, post_id))
                
                section = cursor.fetchone()
                if not section:
                    return jsonify({'success': False, 'error': 'Section not found'})
            
            # Optimize the image with parameters
            result = optimize_image_with_watermark(post_id, resolved_section_id, params)
            
            if result['success']:
                # Save optimized image to image table and create post_images link
                with db_manager.get_cursor() as cursor:
                    # Get optimized image path
                    optimized_path = result['optimized_path'].lstrip('/')  # Remove leading /
                    
                    # Insert or update image record
                    cursor.execute("""
                        INSERT INTO image (filename, path, alt_text, caption)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (path) DO UPDATE 
                        SET filename = EXCLUDED.filename, alt_text = EXCLUDED.alt_text, caption = EXCLUDED.caption
                        RETURNING id
                    """, (
                        f"{resolved_section_id}_optimized.jpg",
                        f"/{optimized_path}",
                        f"Optimized image for {section.get('section_heading', 'section')}",
                        "AI-generated image"
                    ))
                    image_record = cursor.fetchone()
                    image_id = image_record['id']
                    
                    # Delete any existing post_images link for this section's optimized image
                    cursor.execute("""
                        DELETE FROM post_images 
                        WHERE section_id = %s AND image_type = 'section_optimized'
                    """, (resolved_section_id,))
                    
                    # Create post_images link (include post_id as required by schema)
                    cursor.execute("""
                        INSERT INTO post_images (post_id, section_id, image_id, image_type)
                        VALUES (%s, %s, %s, 'section_optimized')
                    """, (post_id, resolved_section_id, image_id))
                
                return jsonify({
                    'success': True,
                    'optimized_path': result['optimized_path'],
                    'message': 'Image optimized successfully'
                })
            else:
                return jsonify({'success': False, 'error': result['error']})
                
        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

    @bp.route('/api/optimize/posts/<int:post_id>/optimize-all', methods=['POST'])
    def imaging_optimize_all_images(post_id):
        """Optimize all images for a post with watermark and caption"""
        try:
            # Get all sections with raw images
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, section_order, section_heading
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
                
                sections = cursor.fetchall()
            
            if not sections:
                return jsonify({'success': False, 'error': 'No sections found'})
            
            results = []
            successful = 0
            failed = 0
            
            for section in sections:
                section_id = section['id']
                raw_image_path = f"static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
                
                # Skip if raw image doesn't exist
                if not os.path.exists(raw_image_path):
                    results.append({
                        'section_id': section_id,
                        'section_heading': section['section_heading'],
                        'success': False,
                        'error': 'Raw image not found',
                        'skipped': True
                    })
                    continue
                
                # Optimize the image
                result = optimize_image_with_watermark(post_id, section_id)
                
                if result['success']:
                    results.append({
                        'section_id': section_id,
                        'section_heading': section['section_heading'],
                        'success': True,
                        'optimized_path': result['optimized_path'],
                        'skipped': False
                    })
                    successful += 1
                else:
                    results.append({
                        'section_id': section_id,
                        'section_heading': section['section_heading'],
                        'success': False,
                        'error': result['error'],
                        'skipped': False
                    })
                    failed += 1
            
            return jsonify({
                'success': True,
                'total_sections': len(sections),
                'successful': successful,
                'failed': failed,
                'results': results,
                'message': f'Optimization complete: {successful} successful, {failed} failed'
            })
            
        except Exception as e:
            logger.error(f"Error optimizing all images: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

