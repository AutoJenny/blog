"""
Clan.com Publishing Module
Handles publishing blog posts to clan.com
"""

import os
import json
import requests
import logging
from datetime import datetime
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class ClanPublisher:
    def __init__(self):
        self.api_base_url = os.getenv('CLAN_API_BASE_URL', 'https://clan.com/clan/blog_api/')
        self.api_user = os.getenv('CLAN_API_USER', 'blog')
        self.api_key = os.getenv('CLAN_API_KEY')
        
        if not self.api_key:
            raise ValueError("CLAN_API_KEY environment variable is required. Please create a .env file with your Clan.com API credentials")
        
        # Ensure trailing slash
        if not self.api_base_url.endswith('/'):
            self.api_base_url += '/'
    
    def _generate_url_key(self, post):
        """Generate a URL-friendly key for the post"""
        # Use existing slug if available
        if post.get('slug'):
            return post['slug']
        
        # Generate from title
        title = post.get('title', 'Untitled Post')
        import re
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        url_key = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        url_key = re.sub(r'\s+', '-', url_key).strip('-')
        
        # Ensure it's not empty and add post ID for uniqueness
        if not url_key:
            url_key = f'post-{post["id"]}'
        else:
            url_key = f'{url_key}-{post["id"]}'
        
        return url_key
    
    def _generate_meta_tags(self, post):
        """Generate meta tags for the post"""
        # Try to get keywords from the post
        keywords = post.get('keywords', [])
        
        # If keywords is a list and not empty, join them
        if isinstance(keywords, list) and keywords:
            return ','.join(keywords)
        
        # If no keywords, generate some from the title and content
        title = post.get('title', '')
        summary = post.get('summary', '')
        
        # Extract meaningful words from title and summary
        import re
        words = []
        
        # Add words from title
        if title:
            title_words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            words.extend(title_words[:3])  # Take first 3 meaningful words
        
        # Add words from summary
        if summary:
            summary_words = re.findall(r'\b[a-zA-Z]{3,}\b', summary.lower())
            words.extend(summary_words[:2])  # Take first 2 meaningful words
        
        # Remove duplicates and ensure we have at least some tags
        unique_words = list(set(words))
        
        if unique_words:
            return ','.join(unique_words[:5])  # Limit to 5 tags
        else:
            # Fallback to default tags
            return 'scottish,heritage,culture,blog'
    
    def upload_image(self, image_path, filename=None):
        """Upload an image to clan.com and return the uploaded URL"""
        try:
            if not filename:
                filename = os.path.basename(image_path)
            
            # Check if it's a local path or URL
            if image_path.startswith('/static/'):
                # Convert local static path to full local file path
                local_path = f"/Users/nickfiddes/Code/projects/blog/blog-images{image_path}"
                if not os.path.exists(local_path):
                    logger.warning(f"Local image not found: {local_path}")
                    return None
                image_path = local_path
            elif image_path.startswith('http'):
                # Download remote image to temp file
                response = requests.get(image_path)
                if response.status_code == 200:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
                    temp_file.write(response.content)
                    temp_file.close()
                    image_path = temp_file.name
                else:
                    logger.warning(f"Failed to download image: {image_path}")
                    return None
            
            # Upload to clan.com
            upload_url = f"{self.api_base_url}uploadImage"
            
            with open(image_path, 'rb') as f:
                files = {'image': (filename, f, 'image/jpeg')}
                data = {
                    'api_user': self.api_user,
                    'api_key': self.api_key
                }
                
                logger.info(f"Uploading image: {filename}")
                response = requests.post(upload_url, files=files, data=data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        uploaded_url = result.get('url')
                        logger.info(f"Image uploaded successfully: {uploaded_url}")
                        return uploaded_url
                    else:
                        logger.error(f"Image upload failed: {result.get('error')}")
                        return None
                else:
                    logger.error(f"Image upload failed with status {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading image {image_path}: {str(e)}")
            return None
        finally:
            # Clean up temp file if we created one
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def process_images(self, post, sections):
        """Upload all images and update paths in the post content"""
        uploaded_images = {}
        
        # Process header image
        if post.get('header_image') and post['header_image'].get('path'):
            header_path = post['header_image']['path']
            uploaded_url = self.upload_image(header_path, f"header_{post['id']}.jpg")
            if uploaded_url:
                uploaded_images[header_path] = uploaded_url
                post['header_image']['path'] = uploaded_url
        
        # Process section images
        for section in sections:
            if section.get('image') and section['image'].get('path') and not section['image'].get('placeholder'):
                section_path = section['image']['path']
                uploaded_url = self.upload_image(section_path, f"section_{post['id']}_{section.get('id', 'unknown')}.jpg")
                if uploaded_url:
                    uploaded_images[section_path] = uploaded_url
                    section['image']['path'] = uploaded_url
        
        return uploaded_images
    
    def render_post_html(self, post, sections):
        """Render the post HTML for clan.com publishing - COMPLETE VERSION matching preview"""
        try:
            import html
            
            def safe_html(text):
                """Safely escape HTML content to prevent XSS and breaking the blog"""
                if not text:
                    return ''
                # Escape HTML special characters
                return html.escape(str(text))
            
            def safe_url(url):
                """Safely validate and escape URLs"""
                if not url:
                    return ''
                # Basic URL validation - only allow http/https URLs
                if url.startswith(('http://', 'https://')):
                    return html.escape(url)
                # For relative URLs, ensure they're safe
                if url.startswith('/'):
                    return html.escape(url)
                # Reject potentially dangerous URLs
                return ''
            
            # Calculate reading time (matching preview template)
            total_chars = 0
            word_count = 0
            for section in sections:
                if section.get('polished'):
                    section_text = section['polished']
                    total_chars += len(section_text)
                    word_count += len(section_text.split())
                elif section.get('draft'):
                    section_text = section['draft']
                    total_chars += len(section_text)
                    word_count += len(section_text.split())
            
            reading_time = max(1, (word_count // 200) + (1 if word_count % 200 > 0 else 0))
            
            # Generate HTML content with proper escaping
            html_parts = []
            
            # Header
            title = safe_html(post.get('title') or post.get('main_title') or post.get('provisional_title') or 'Untitled Post')
            subtitle = safe_html(post.get('subtitle', ''))
            
            html_parts.append('<div class="mpblog-post">')
            html_parts.append('<header class="blog-post-header">')
            html_parts.append(f'<h1>{title}</h1>')
            
            if subtitle:
                html_parts.append(f'<div class="blog-post__subtitle">{subtitle}</div>')
            
            # Meta information - INCLUDING READING TIME
            created_at = post.get('created_at')
            date_str = safe_html(created_at.strftime('%B %d, %Y') if created_at else 'Unknown date')
            html_parts.append('<div class="post-meta">')
            html_parts.append('<span class="post-meta__author">By Caitrin Stewart</span>')
            html_parts.append('<span class="post-meta__separator"> | </span>')
            html_parts.append(f'<span class="post-meta__date">{date_str}</span>')
            html_parts.append('<span class="post-meta__separator"> | </span>')
            html_parts.append(f'<span class="post-meta__reading-time">{reading_time} min read</span>')
            html_parts.append('</div>')
            html_parts.append('</header>')
            
            # Header image - WITH LIGHTBOX AND DIMENSIONS
            if post.get('header_image') and post['header_image'].get('path'):
                header_img = post['header_image']
                safe_path = safe_url(header_img['path'])
                if safe_path:
                    html_parts.append('<figure class="blog-post-image">')
                    # Add lightbox link
                    html_parts.append(f'<a title="{safe_html(header_img.get("alt_text", "Header image"))}" href="{safe_path}" rel="lightbox[mpblog_{post.get("id", "unknown")}]" target="_blank">')
                    html_parts.append(f'<img src="{safe_path}" alt="{safe_html(header_img.get("alt_text", "Header image"))}"')
                    # Add dimensions if available
                    if header_img.get('width'):
                        html_parts.append(f' width="{header_img["width"]}"')
                    if header_img.get('height'):
                        html_parts.append(f' height="{header_img["height"]}"')
                    html_parts.append('>')
                    html_parts.append('</a>')
                    if header_img.get('caption'):
                        html_parts.append(f'<figcaption>{safe_html(header_img["caption"])}</figcaption>')
                    html_parts.append('</figure>')
            
            # Summary
            if post.get('summary'):
                html_parts.append('<div class="blog-post__summary">')
                html_parts.append(f'<p>{safe_html(post["summary"])}</p>')
                html_parts.append('</div>')
            
            # Sections - WITH CROSS-PROMOTION WIDGETS
            if sections:
                html_parts.append('<div class="blog-sections">')
                for i, section in enumerate(sections, 1):
                    html_parts.append(f'<section class="blog-section" id="section-{i}">')
                    
                    # Section heading
                    heading = safe_html(section.get('section_heading') or 'Untitled Section')
                    html_parts.append(f'<h2>{heading}</h2>')
                    
                    # Section content - safely escaped
                    html_parts.append('<div class="section-text">')
                    content = section.get('polished') or section.get('draft') or section.get('content') or 'No content available for this section.'
                    html_parts.append(f'<p>{safe_html(content)}</p>')
                    html_parts.append('</div>')
                    
                    # Section image - WITH LIGHTBOX AND DIMENSIONS
                    if section.get('image') and section['image'].get('path') and not section['image'].get('placeholder'):
                        img = section['image']
                        safe_path = safe_url(img['path'])
                        if safe_path:
                            html_parts.append('<figure class="section-image">')
                            # Add lightbox link
                            html_parts.append(f'<a title="{safe_html(img.get("caption") or img.get("alt_text") or "Section image")}" href="{safe_path}" rel="lightbox[mpblog_{post.get("id", "unknown")}]" target="_blank">')
                            html_parts.append(f'<img alt="{safe_html(img.get("alt_text", "Section image"))}" src="{safe_path}"')
                            # Add dimensions if available
                            if img.get('width'):
                                html_parts.append(f' width="{img["width"]}"')
                            if img.get('height'):
                                html_parts.append(f' height="{img["height"]}"')
                            html_parts.append('>')
                            html_parts.append('</a>')
                            if img.get('caption'):
                                html_parts.append(f'<figcaption>{safe_html(img["caption"])}</figcaption>')
                            html_parts.append('</figure>')
                    
                    html_parts.append('</section>')
                    
                    # INSERT CROSS-PROMOTION WIDGET AT SECTION 2 (matching preview template)
                    if i == 2 and post.get('cross_promotion', {}).get('category_id'):
                        category_id = post['cross_promotion']['category_id']
                        category_title = safe_html(post['cross_promotion'].get('category_title', ''))
                        html_parts.append(f'{{{{widget type="swcatalog/widget_crossSell_category" category_id="{category_id}" title="{category_title}"}}}}')
                
                html_parts.append('</div>')
                
                # INSERT PRODUCT WIDGET AFTER FINAL SECTION (matching preview template)
                if post.get('cross_promotion', {}).get('product_id'):
                    product_id = post['cross_promotion']['product_id']
                    product_title = safe_html(post['cross_promotion'].get('product_title', ''))
                    html_parts.append(f'{{{{widget type="swcatalog/widget_crossSell_product" product_id="{product_id}" title="{product_title}"}}}}')
            
            # Footer
            if post.get('keywords'):
                html_parts.append('<footer class="article-footer">')
                html_parts.append('<div class="article-tags">')
                html_parts.append('<strong>Tags:</strong>')
                for keyword in post['keywords']:
                    html_parts.append(f'<span class="tag">{safe_html(keyword)}</span>')
                html_parts.append('</div>')
                html_parts.append('</footer>')
            
            html_parts.append('</div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering post HTML: {str(e)}")
            return None
    
    def create_or_update_post(self, post, html_content, is_update=False):
        """Create or update a post on clan.com"""
        try:
            # Determine endpoint
            if is_update and post.get('clan_post_id'):
                endpoint = f"{self.api_base_url}editPost"
                json_args = {
                    'post_id': post['clan_post_id']
                }
            else:
                endpoint = f"{self.api_base_url}createPost"
                json_args = {}
            
            # Common post metadata - matching the working PHP script exactly
            json_args.update({
                'title': post.get('title', 'Untitled Post'),  # required
                'url_key': self._generate_url_key(post),  # required - use slug or generate from title
                'short_content': post.get('summary', '')[:200] if post.get('summary') else 'No summary available',  # required
                'status': 2,  # required - 2 = enabled (not 'published' string)
                'categories': [14, 15],  # required - note: 'categories' not 'category_ids'
                'list_thumbnail': '/blog/default-thumbnail.jpg',  # required - path from /media
                'post_thumbnail': '/blog/default-thumbnail.jpg',  # required - path from /media
                'meta_title': post.get('title', 'Untitled Post'),  # required
                'meta_tags': self._generate_meta_tags(post),  # required
                'meta_description': post.get('summary', '')[:160] if post.get('summary') else 'No description available'  # required
            })
            
            # Validate required fields
            required_fields = ['title', 'url_key', 'short_content', 'status', 'categories', 'list_thumbnail', 'post_thumbnail', 'meta_title', 'meta_tags', 'meta_description']
            missing_fields = []
            
            for field in required_fields:
                value = json_args.get(field)
                # Check if field is missing or None
                if value is None:
                    missing_fields.append(field)
                # For string fields, allow empty strings (clan.com might accept them)
                elif isinstance(value, str) and value.strip() == '':
                    logger.warning(f"Field '{field}' is empty string, but proceeding anyway")
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                logger.error(f"Field values: {json_args}")
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Prepare the API request data
            api_data = {
                'api_user': self.api_user,
                'api_key': self.api_key,
                'json_args': json.dumps(json_args)
            }
            
            logger.info(f"Sending to {endpoint}")
            logger.info(f"API data: {api_data}")
            logger.info(f"JSON args: {json_args}")
            
            # Debug: Log each field value
            for field, value in json_args.items():
                logger.info(f"Field '{field}': {value} (type: {type(value)})")
            
            # Create a temporary HTML file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            try:
                # Send the request with the HTML file
                with open(temp_file_path, 'rb') as html_file:
                    files = {'html_file': ('post.html', html_file, 'text/html')}
                    
                    logger.info(f"{'Updating' if is_update else 'Creating'} post: {json_args['title']}")
                    logger.info(f"HTML content length: {len(html_content)} characters")
                    response = requests.post(endpoint, data=api_data, files=files, timeout=60)
            finally:
                # Clean up the temporary file
                import os
                os.unlink(temp_file_path)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Clan.com API response: {result}")
                
                if result.get('success'):
                    clan_post_id = result.get('post_id')
                    post_url = result.get('url') or f"https://clan.com/blog/post-{clan_post_id}"
                    
                    logger.info(f"Post {'updated' if is_update else 'created'} successfully: {post_url}")
                    return {
                        'success': True,
                        'clan_post_id': clan_post_id,
                        'url': post_url
                    }
                else:
                    error_msg = result.get('error', 'Unknown API error')
                    logger.error(f"Clan.com API error: {error_msg}")
                    logger.error(f"Full API response: {result}")
                    return {
                        'success': False,
                        'error': f"Clan.com API error: {error_msg}"
                    }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Post publishing failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Error publishing post: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

def publish_to_clan(post, sections):
    """Main function to publish a post to clan.com"""
    try:
        publisher = ClanPublisher()
        
        # Step 0: Populate image data from file system (CRITICAL FIX)
        logger.info(f"Populating image data for post {post['id']}")
        
        # Import the image finding functions from app.py
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import find_header_image, find_section_image
        
        # Find and populate header image
        header_image_path = find_header_image(post['id'])
        if header_image_path:
            post['header_image'] = {
                'path': header_image_path,
                'alt_text': f"Header image for {post.get('title', 'Untitled Post')}",
                'caption': post.get('header_image_caption', ''),
                'width': post.get('header_image_width'),
                'height': post.get('header_image_height')
            }
            logger.info(f"Found header image: {header_image_path}")
        else:
            logger.info("No header image found")
        
        # Find and populate section images
        for section in sections:
            section_id = section.get('id')
            if section_id:
                section_image_path = find_section_image(post['id'], section_id)
                if section_image_path:
                    section['image'] = {
                        'path': section_image_path,
                        'alt_text': f"Image for section: {section.get('section_heading', 'Untitled')}",
                        'caption': section.get('image_captions', ''),
                        'width': section.get('image_width'),
                        'height': section.get('image_height'),
                        'placeholder': False
                    }
                    logger.info(f"Found section {section_id} image: {section_image_path}")
                else:
                    logger.info(f"No image found for section {section_id}")
        
        # Step 1: Upload images and update paths
        logger.info(f"Processing images for post {post['id']}")
        uploaded_images = publisher.process_images(post, sections)
        
        # Step 2: Render HTML content
        logger.info(f"Rendering HTML content for post {post['id']}")
        html_content = publisher.render_post_html(post, sections)
        
        if not html_content:
            return {
                'success': False,
                'error': 'Failed to render post HTML'
            }
        
        # Step 3: Create or update post on clan.com
        is_update = bool(post.get('clan_post_id'))
        logger.info(f"{'Updating' if is_update else 'Creating'} post {post['id']} on clan.com")
        
        result = publisher.create_or_update_post(post, html_content, is_update)
        
        if result['success']:
            logger.info(f"Successfully published post {post['id']} to clan.com")
        
        return result
        
    except Exception as e:
        error_msg = f"Publishing failed: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
