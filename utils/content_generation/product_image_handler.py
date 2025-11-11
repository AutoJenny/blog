"""
Product Image Handler

Handles auto-pulling section images from CLAN product data and generating hero/header images.
"""

import logging
import requests
from typing import Dict, List, Optional
from config.database import db_manager

logger = logging.getLogger(__name__)


class ProductImageHandler:
    """Handles product images for generated articles."""
    
    def __init__(self, api_base_url: str = 'http://localhost:5000'):
        """
        Initialize product image handler.
        
        Args:
            api_base_url: Base URL for internal API calls
        """
        self.api_base_url = api_base_url
    
    def fetch_product_images(self, product_id: int, sku: str) -> Dict:
        """
        Fetch all product images from CLAN API.
        
        Args:
            product_id: Product ID
            sku: Product SKU
            
        Returns:
            Dictionary with main image URL and all_images array
        """
        try:
            # Get main image from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT image_url FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                
                product = cursor.fetchone()
                main_image_url = product.get('image_url') if product else None
            
            # Fetch all images via API
            all_images = []
            try:
                api_url = f"{self.api_base_url}/api/clan/products/{sku}/full"
                response = requests.get(api_url, params={'all_images': 'true'}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('product'):
                        product_data = data['product']
                        all_images = product_data.get('all_images', [])
                        
                        # Ensure main image is included
                        if main_image_url and all_images:
                            # Check if main image is already in all_images
                            main_in_list = any(
                                img.get('url') == main_image_url 
                                for img in all_images
                            )
                            if not main_in_list:
                                # Add main image as first item
                                all_images.insert(0, {
                                    'url': main_image_url,
                                    'alt': 'Main product image'
                                })
                else:
                    logger.warning(f"Failed to fetch all_images for SKU {sku}: {response.status_code}")
            except Exception as e:
                logger.warning(f"Error fetching all_images for SKU {sku}: {e}")
                # Fallback: use main image only
                if main_image_url:
                    all_images = [{'url': main_image_url, 'alt': 'Main product image'}]
            
            return {
                'main_image_url': main_image_url,
                'all_images': all_images,
                'image_count': len(all_images)
            }
        except Exception as e:
            logger.error(f"Error fetching product images for product {product_id}: {e}")
            return {
                'main_image_url': None,
                'all_images': [],
                'image_count': 0
            }
    
    def auto_pull_section_images(self, post_id: int, product_id: int, 
                                section_ids: List[int]) -> Dict:
        """
        Automatically link product images to sections.
        
        Args:
            post_id: Post ID
            product_id: Product ID
            section_ids: List of section IDs to link images to
            
        Returns:
            Dictionary with image linking results
        """
        try:
            # Get product SKU
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT sku FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                
                product = cursor.fetchone()
                if not product:
                    return {
                        'success': False,
                        'error': f'Product {product_id} not found'
                    }
                
                sku = product.get('sku')
            
            # Fetch all product images
            images_data = self.fetch_product_images(product_id, sku)
            
            if not images_data.get('all_images'):
                return {
                    'success': False,
                    'error': 'No product images available',
                    'images_linked': 0
                }
            
            all_images = images_data['all_images']
            
            # Link images to sections (distribute across sections)
            images_linked = 0
            with db_manager.get_cursor() as cursor:
                for i, section_id in enumerate(section_ids):
                    # Select image for this section (cycle through available images)
                    image_index = i % len(all_images)
                    image_data = all_images[image_index]
                    image_url = image_data.get('url')
                    
                    if not image_url:
                        continue
                    
                    # Check if section already has an image
                    cursor.execute("""
                        SELECT pi.id, pi.image_id FROM post_images pi
                        WHERE pi.post_id = %s AND pi.section_id = %s AND pi.image_type = 'section_optimized'
                        LIMIT 1
                    """, (post_id, section_id))
                    
                    existing = cursor.fetchone()
                    
                    # Get or create image record in images table
                    cursor.execute("""
                        SELECT id FROM images
                        WHERE file_path = %s
                        LIMIT 1
                    """, (image_url,))
                    
                    image_record = cursor.fetchone()
                    if image_record:
                        image_id = image_record['id']
                    else:
                        # Create new image record for external URL
                        cursor.execute("""
                            INSERT INTO images (file_path, filename, created_at, updated_at)
                            VALUES (%s, %s, NOW(), NOW())
                            RETURNING id
                        """, (image_url, image_url.split('/')[-1] or 'product_image.jpg'))
                        
                        image_id = cursor.fetchone()['id']
                    
                    if existing:
                        # Update existing post_images link
                        cursor.execute("""
                            UPDATE post_images
                            SET image_id = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (image_id, existing['id']))
                    else:
                        # Create new post_images link
                        cursor.execute("""
                            INSERT INTO post_images 
                            (post_id, section_id, image_id, image_type, created_at)
                            VALUES (%s, %s, %s, 'section_optimized', NOW())
                            RETURNING id
                        """, (post_id, section_id, image_id))
                        
                        cursor.fetchone()  # Consume result
                    
                    images_linked += 1
            
            logger.info(f"Auto-linked {images_linked} product images to {len(section_ids)} sections")
            
            return {
                'success': True,
                'images_linked': images_linked,
                'total_images': len(all_images),
                'main_image_url': images_data.get('main_image_url')
            }
        except Exception as e:
            logger.error(f"Error auto-pulling section images: {e}")
            return {
                'success': False,
                'error': str(e),
                'images_linked': 0
            }
    
    def generate_hero_image_prompt(self, product_id: int, product_data: Dict) -> str:
        """
        Generate prompt for hero/header image generation.
        
        Creates detailed instructions for imaging LLM to generate aspirational image
        featuring the product.
        
        Args:
            product_id: Product ID
            product_data: Product data from ClanDataExtractor
            
        Returns:
            Formatted prompt string for hero image generation
        """
        product_name = product_data.get('name', 'Product')
        product_description = product_data.get('description') or product_data.get('short_description', '')
        supplier_name = product_data.get('supplier_name', '')
        category_names = []
        
        if product_data.get('categories'):
            category_names = [cat.get('name', '') for cat in product_data['categories'] if cat.get('name')]
        
        # Build aspirational prompt
        prompt_parts = [
            f"Create an aspirational, lifestyle hero image featuring: {product_name}",
            "",
            "Product Details:",
            f"- Product: {product_name}",
        ]
        
        if supplier_name:
            prompt_parts.append(f"- Crafted by: {supplier_name}")
        
        if category_names:
            prompt_parts.append(f"- Category: {', '.join(category_names)}")
        
        if product_description:
            # Use first 200 characters of description
            desc_preview = product_description[:200].replace('\n', ' ').strip()
            prompt_parts.append(f"- Description: {desc_preview}...")
        
        prompt_parts.extend([
            "",
            "Image Requirements:",
            "- Aspirational, lifestyle context (e.g., elegant setting, Scottish heritage atmosphere)",
            "- Product should be the focal point, beautifully presented",
            "- Warm, professional aesthetic matching CLAN brand",
            "- High quality, magazine-style photography",
            "- Scottish heritage and craftsmanship should be evident",
            "- Avoid cluttered backgrounds, focus on product elegance",
            "",
            "Style Guidelines:",
            "- Professional product photography",
            "- Natural lighting preferred",
            "- Scottish cultural context (subtle, not overwhelming)",
            "- Premium, luxury feel",
            "- CLAN brand aesthetic: warm, authentic, heritage-focused"
        ])
        
        return "\n".join(prompt_parts)
    
    def prepare_hero_image_generation(self, post_id: int, product_id: int, 
                                      product_data: Dict) -> Dict:
        """
        Prepare hero/header image generation by creating prompt and storing product image reference.
        
        Args:
            post_id: Post ID
            product_id: Product ID
            product_data: Product data from ClanDataExtractor
            
        Returns:
            Dictionary with hero image prompt and product image URL
        """
        try:
            # Generate hero image prompt
            hero_prompt = self.generate_hero_image_prompt(product_id, product_data)
            
            # Get product image URL
            main_image_url = product_data.get('image_url')
            
            # Store prompt in post_development or images table
            # For now, we'll return it to be stored via the header image workflow
            return {
                'success': True,
                'hero_prompt': hero_prompt,
                'product_image_url': main_image_url,
                'product_name': product_data.get('name', 'Product')
            }
        except Exception as e:
            logger.error(f"Error preparing hero image generation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

