"""
Clan.com Publishing Module
Handles publishing blog posts to clan.com
"""

import os
import requests
import logging
from flask import render_template
from datetime import datetime
import tempfile
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClanPublisher:
    def __init__(self):
        self.api_base_url = os.getenv('CLAN_API_BASE_URL', 'https://clan.com/clan/blog_api/')
        self.api_user = os.getenv('CLAN_API_USER', 'blog')
        self.api_key = os.getenv('CLAN_API_KEY')
        
        if not self.api_key:
            raise ValueError("CLAN_API_KEY environment variable is required")
        
        # Ensure trailing slash
        if not self.api_base_url.endswith('/'):
            self.api_base_url += '/'
    
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
                    'user': self.api_user,
                    'key': self.api_key
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
        """Render the post HTML using our clan_post.html template"""
        try:
            from flask import current_app
            with current_app.app_context():
                html_content = render_template('clan_post.html', post=post, sections=sections)
                return html_content
        except Exception as e:
            logger.error(f"Error rendering post HTML: {str(e)}")
            return None
    
    def create_or_update_post(self, post, html_content, is_update=False):
        """Create or update a post on clan.com"""
        try:
            # Determine endpoint
            if is_update and post.get('clan_post_id'):
                endpoint = f"{self.api_base_url}editPost"
                post_data = {
                    'post_id': post['clan_post_id']
                }
            else:
                endpoint = f"{self.api_base_url}createPost"
                post_data = {}
            
            # Common post data
            post_data.update({
                'user': self.api_user,
                'key': self.api_key,
                'title': post.get('title', 'Untitled Post'),
                'content': html_content,
                'status': 'published',  # or 'draft'
                'category_ids': [14, 15],  # Default categories for Scottish content
                'tags': post.get('keywords', []) if isinstance(post.get('keywords'), list) else [],
                'meta_description': post.get('summary', '')[:160] if post.get('summary') else '',
                'author': 'Caitrin Stewart'
            })
            
            logger.info(f"{'Updating' if is_update else 'Creating'} post: {post_data['title']}")
            response = requests.post(endpoint, data=post_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
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
                    logger.error(f"API error: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg
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
