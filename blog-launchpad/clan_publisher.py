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
import re
import html
import time

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
        import re
        import time
        
        # If this is an update and we have an existing clan_uploaded_url, extract the URL key from it
        if post.get('clan_post_id') and post.get('clan_uploaded_url'):
            # Extract the URL key from the existing clan.com URL
            existing_url = post['clan_uploaded_url']
            if '/blog/' in existing_url:
                url_key = existing_url.split('/blog/')[-1]
                logger.info(f"Using existing URL key from clan.com for update: {url_key}")
                return url_key
        
        # Generate from title for new posts
        title = post.get('title', 'Untitled Post')
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        url_key = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        url_key = re.sub(r'\s+', '-', url_key).strip('-')
        
        # For consistency, use a fixed timestamp based on post ID instead of current time
        # This ensures the same post always gets the same URL key
        post_id = post.get('id', 0)
        fixed_timestamp = 1755600000 + (post_id * 1000)  # Base timestamp + post ID offset
        
        # Ensure it's not empty and add post ID + fixed timestamp for consistency
        if not url_key:
            url_key = f'post-{post_id}-{fixed_timestamp}'
        else:
            url_key = f'{url_key}-{post_id}-{fixed_timestamp}'
        
        return url_key
    
    def _generate_meta_tags(self, post):
        """Generate meta tags for the post"""
        # First priority: use the new database meta_tags field
        if post.get('meta_tags'):
            logger.info(f"Using database meta_tags: {post.get('meta_tags')}")
            return post.get('meta_tags')
        
        # Second priority: try to get keywords from the post
        keywords = post.get('keywords', [])
        
        # If keywords is a list and not empty, join them
        if isinstance(keywords, list) and keywords:
            return ','.join(keywords)
        
        # Third priority: generate some from the title and content
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
    
    def _prepare_api_data(self, post, sections):
        """Prepare the API data structure that gets sent to Clan.com"""
        # Get header image path for thumbnails
        header_image_path = None
        if post.get('header_image') and post['header_image'].get('path'):
            header_image_path = post['header_image']['path']
        
        # Set thumbnails - use placeholder for now since we don't have uploaded_images in this context
        list_thumbnail = '/blog/placeholder.jpg'
        post_thumbnail = '/blog/placeholder.jpg'
        
        # Common post metadata - using new database meta fields for proper OG tags
        try:
            meta_title = post.get('meta_title') or post.get('title', 'Untitled Post')
            meta_tags = post.get('meta_tags') or self._generate_meta_tags(post)
            # Clean meta_description - use subtitle as fallback if meta_description is empty
            raw_description = post.get('meta_description') or post.get('subtitle') or post.get('summary', '') or 'No description available'
            # Strip HTML tags and limit to 160 characters
            import re
            clean_description = re.sub(r'<[^>]+>', '', raw_description)
            meta_description = clean_description[:160] if clean_description else 'No description available'
            
            # Ensure all meta fields are strings and not None
            meta_title = str(meta_title) if meta_title else 'Untitled Post'
            meta_tags = str(meta_tags) if meta_tags else 'scottish,heritage,culture,blog'
            meta_description = str(meta_description) if meta_description else 'No description available'
            
        except Exception as e:
            logger.error(f"Error processing meta data: {str(e)}")
            # Fallback to safe defaults
            meta_title = post.get('title', 'Untitled Post')
            meta_tags = 'scottish,heritage,culture,blog'
            meta_description = 'No description available'
        
        # Build the API data structure
        api_data = {
            'title': post.get('title', 'Untitled Post'),
            'url_key': self._generate_url_key(post),
            'short_content': post.get('subtitle') or post.get('summary') or 'No summary available',  # prioritize subtitle over summary
            'status': 2,  # 2 = enabled
            'categories': [14, 15],  # Default clan.com categories
            'list_thumbnail': list_thumbnail,
            'post_thumbnail': post_thumbnail,
            'meta_title': meta_title,
            'meta_tags': meta_tags,
            'meta_description': meta_description
        }
        
        return api_data
    
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
            
            # Determine MIME type based on file extension
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type or not mime_type.startswith('image/'):
                # Fallback to common image types
                if filename.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                    mime_type = 'image/jpeg'
                elif filename.lower().endswith('.webp'):
                    mime_type = 'image/webp'
                else:
                    mime_type = 'image/jpeg'  # Default fallback
            
            with open(image_path, 'rb') as f:
                files = {'image': (filename, f, mime_type)}
                data = {
                    'api_user': self.api_user,
                    'api_key': self.api_key,
                    'json_args': '[]'  # Required by clan.com API (empty array for image uploads)
                }
                
                logger.info(f"Uploading image: {filename} to {upload_url}")
                logger.info(f"MIME type: {mime_type}")
                logger.info(f"API data: {data}")
                response = requests.post(upload_url, files=files, data=data, timeout=15)
                
                logger.info(f"Upload response status: {response.status_code}")
                logger.info(f"Upload response headers: {dict(response.headers)}")
                logger.info(f"Upload response text: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Upload response JSON: {result}")
                    
                    # Check for success status (clan.com uses 'status' field)
                    if result.get('status') == 'success' or result.get('success'):
                        # Extract URL from message or url field
                        uploaded_url = result.get('url')
                        if not uploaded_url and result.get('message'):
                            # Extract URL from message like "File uploaded successfully: https://static.clan.com/media/blog/filename.jpg"
                            message = result.get('message', '')
                            if 'https://' in message:
                                uploaded_url = message.split('https://')[-1]
                                uploaded_url = 'https://' + uploaded_url
                        
                        if uploaded_url:
                            logger.info(f"Image uploaded successfully: {uploaded_url}")
                            return uploaded_url
                        else:
                            logger.error("Image upload succeeded but no URL found in response")
                            return None
                    else:
                        error_msg = result.get('error', 'Unknown upload error')
                        logger.error(f"Image upload failed: {error_msg}")
                        logger.error(f"Full upload response: {result}")
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
    
    def _safe_url_test(self, url, uploaded_images):
        """Test version of safe_url for debugging"""
        if not url:
            return ''
        
        # If we have uploaded_images mapping, use the clan.com URL
        if uploaded_images and url in uploaded_images:
            return html.escape(uploaded_images[url])
        
        # Basic URL validation - only allow http/https URLs
        if url.startswith(('http://', 'https://')):
            return html.escape(url)
        # For relative URLs, ensure they're safe
        if url.startswith('/'):
            return html.escape(url)
        # Reject potentially dangerous URLs
        return ''
    
    def _safe_html_test(self, text):
        """Test version of safe_html for debugging"""
        if not text:
            return ''
        
        import re
        text_str = str(text)
        
        # Check if content already contains HTML tags - be more specific
        # Only treat as HTML if it contains actual HTML tag patterns
        if re.search(r'<[a-z][^>]*>', text_str, re.IGNORECASE) or re.search(r'</[a-z][^>]*>', text_str, re.IGNORECASE):
            # Content has actual HTML tags - clean it but preserve structure
            # Remove DOCTYPE, html, head, body tags
            text_str = re.sub(r'<!DOCTYPE[^>]*>', '', text_str)
            text_str = re.sub(r'<html[^>]*>', '', text_str)
            text_str = re.sub(r'</html>', '', text_str)
            text_str = re.sub(r'<head[^>]*>.*?</head>', '', text_str, flags=re.DOTALL)
            text_str = re.sub(r'<body[^>]*>', '', text_str)
            text_str = re.sub(r'</body>', '', text_str)
            
            # Fix double <p> tags
            text_str = re.sub(r'<p>\s*<p>', '<p>', text_str)
            text_str = re.sub(r'</p>\s*</p>', '</p>', text_str)
            
            # Clean up any remaining HTML entities that shouldn't be there
            text_str = re.sub(r'&lt;', '<', text_str)
            text_str = re.sub(r'&gt;', '>', text_str)
            
            return text_str
        else:
            # Plain text - escape HTML special characters
            return html.escape(text_str)

    def process_images(self, post, sections):
        """Upload all images and update paths in the post content"""
        import time
        uploaded_images = {}
        
        logger.info(f"=== PROCESS_IMAGES DEBUG START ===")
        logger.info(f"Post ID: {post.get('id')}")
        logger.info(f"Post header_image: {post.get('header_image')}")
        logger.info(f"Post header_image_id: {post.get('header_image_id')}")
        
        # Process header image - use find_header_image function to discover it
        from app import find_header_image
        header_path = find_header_image(post['id'])
        if header_path:
            logger.info(f"✅ Found header image: {header_path}")
            
            # Check if file exists - convert web path to file system path
            if header_path.startswith('/static/'):
                # Convert /static/... to full file system path
                fs_path = f"/Users/nickfiddes/Code/projects/blog/blog-images{header_path}"
                if os.path.exists(fs_path):
                    logger.info(f"✅ Header image file exists at: {fs_path}")
                    logger.info(f"File size: {os.path.getsize(fs_path)} bytes")
                else:
                    logger.error(f"❌ Header image file NOT found at: {fs_path}")
                    logger.error(f"Current working directory: {os.getcwd()}")
            else:
                # Already a file system path
                if os.path.exists(header_path):
                    logger.info(f"✅ Header image file exists at: {header_path}")
                    logger.info(f"File size: {os.path.getsize(header_path)} bytes")
                else:
                    logger.error(f"❌ Header image file NOT found at: {header_path}")
                    logger.error(f"Current working directory: {os.getcwd()}")
            
            # Generate unique filename with timestamp for cache busting
            filename = f"header_{post['id']}_{int(time.time())}.jpg"
            logger.info(f"Uploading header image with filename: {filename}")
            
            try:
                # Convert web path to file system path for upload
                if header_path.startswith('/static/'):
                    fs_path = f"/Users/nickfiddes/Code/projects/blog/blog-images{header_path}"
                    logger.info(f"Converting web path '{header_path}' to file system path '{fs_path}'")
                else:
                    fs_path = header_path
                
                uploaded_url = self.upload_image(fs_path, filename)
                logger.info(f"upload_image returned: {uploaded_url}")
                
                if uploaded_url:
                    uploaded_images[header_path] = uploaded_url
                    logger.info(f"✅ Header image uploaded successfully: {header_path} -> {uploaded_url}")
                    logger.info(f"✅ uploaded_images dictionary now contains: {uploaded_images}")
                else:
                    logger.error(f"❌ upload_image returned None/empty for: {header_path}")
            except Exception as e:
                logger.error(f"❌ Exception during header image upload: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning(f"❌ No header image found using find_header_image function")
        
        # Process section images
        logger.info(f"Processing {len(sections)} sections for images...")
        for i, section in enumerate(sections):
            logger.info(f"Section {i+1}: {section.get('title', 'No title')}")
            logger.info(f"Section image data: {section.get('image')}")
            
            if section.get('image') and section['image'].get('path') and not section['image'].get('placeholder'):
                section_path = section['image']['path']
                logger.info(f"Processing section image: {section_path}")
                
                # Check if file exists - convert web path to file system path
                if section_path.startswith('/static/'):
                    # Convert /static/... to full file system path
                    fs_path = f"/Users/nickfiddes/Code/projects/blog/blog-images{section_path}"
                    if os.path.exists(fs_path):
                        logger.info(f"✅ Section image file exists at: {fs_path}")
                        logger.info(f"File size: {os.path.getsize(fs_path)} bytes")
                    else:
                        logger.error(f"❌ Section image file NOT found at: {fs_path}")
                        logger.error(f"Current working directory: {os.getcwd()}")
                else:
                    # Already a file system path
                    if os.path.exists(section_path):
                        logger.info(f"✅ Section image file exists at: {section_path}")
                        logger.info(f"File size: {os.path.getsize(section_path)} bytes")
                    else:
                        logger.error(f"❌ Section image file NOT found at: {section_path}")
                        logger.error(f"Current working directory: {os.getcwd()}")
                
                # Generate unique filename
                filename = f"section_{post['id']}_{i+1}_{int(time.time())}.jpg"
                logger.info(f"Uploading section image with filename: {filename}")
                
                try:
                    # Convert web path to file system path for upload
                    if section_path.startswith('/static/'):
                        fs_path = f"/Users/nickfiddes/Code/projects/blog/blog-images{section_path}"
                        logger.info(f"Converting section web path '{section_path}' to file system path '{fs_path}'")
                    else:
                        fs_path = section_path
                    
                    uploaded_url = self.upload_image(fs_path, filename)
                    if uploaded_url:
                        uploaded_images[section_path] = uploaded_url
                        logger.info(f"✅ Section image uploaded: {section_path} -> {uploaded_url}")
                    else:
                        logger.error(f"❌ Failed to upload section image: {section_path}")
                except Exception as e:
                    logger.error(f"❌ Exception during section image upload: {str(e)}")
            else:
                logger.info(f"No image for section {i+1}")
        
        logger.info(f"=== PROCESS_IMAGES DEBUG END ===")
        logger.info(f"Final uploaded_images dictionary: {uploaded_images}")
        logger.info(f"Final uploaded_images count: {len(uploaded_images)}")
        
        return uploaded_images
    
    def render_post_html(self, post, sections, uploaded_images=None):
        """REMOVED: This method should not exist. The script should use the preview HTML template verbatim."""
        raise NotImplementedError("This method should not exist. Use the preview HTML template instead.")
    
    def create_or_update_post(self, post, html_content, is_update=False, uploaded_images=None):
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
            
            # Get header image path for thumbnails
            header_image_path = None
            if post.get('header_image') and post['header_image'].get('path'):
                header_image_path = post['header_image']['path']
            
            # Set thumbnails based on uploaded header image availability
            # CRITICAL: These fields are MANDATORY according to clan.com API docs
            list_thumbnail = '/blog/placeholder.jpg'  # Default fallback that should exist on clan.com
            post_thumbnail = '/blog/placeholder.jpg'  # Default fallback that should exist on clan.com
            
            # Look for header image in uploaded_images
            header_image_path = None
            for path in uploaded_images.keys():
                if 'header' in path:
                    header_image_path = path
                    break
            
            if uploaded_images and header_image_path and header_image_path in uploaded_images:
                # Extract the filename from the clan.com URL and create the thumbnail path
                uploaded_url = uploaded_images[header_image_path]
                if uploaded_url and '/media/blog/' in uploaded_url:
                    # Extract filename from URL like "https://static.clan.com/media/blog/header_53_1703123456.jpg"
                    # We need the path relative to /media, so extract everything after /media/
                    media_path = uploaded_url.split('/media/')[-1]
                    thumbnail_path = f"/{media_path}"  # This gives us /blog/header_53_1703123456.jpg
                    list_thumbnail = thumbnail_path
                    post_thumbnail = thumbnail_path
                    logger.info(f"✅ Using uploaded header image for thumbnails: {thumbnail_path}")
                else:
                    logger.warning(f"Unexpected uploaded URL format: {uploaded_url}")
                    logger.info("Using default placeholder thumbnails due to unexpected URL format")
            elif uploaded_images:
                # Try to use any available image as thumbnail if no header image
                first_image_url = list(uploaded_images.values())[0]
                if first_image_url and '/media/blog/' in first_image_url:
                    media_path = first_image_url.split('/media/')[-1]
                    thumbnail_path = f"/{media_path}"
                    list_thumbnail = thumbnail_path
                    post_thumbnail = thumbnail_path
                    logger.info(f"✅ Using first available image for thumbnails: {thumbnail_path}")
                else:
                    logger.info("No header image available, using default placeholder thumbnails")
            else:
                logger.info("No images available, using default placeholder thumbnails")
            
            # Common post metadata - using new database meta fields for proper OG tags
            try:
                meta_title = post.get('meta_title') or post.get('title', 'Untitled Post')
                meta_tags = post.get('meta_tags') or self._generate_meta_tags(post)
                # Clean meta_description - use subtitle as fallback if meta_description is empty
                raw_description = post.get('meta_description') or post.get('subtitle') or post.get('summary', '') or 'No description available'
                # Strip HTML tags and limit to 160 characters
                import re
                clean_description = re.sub(r'<[^>]+>', '', raw_description)
                meta_description = clean_description[:160] if clean_description else 'No description available'
                
                # Ensure all meta fields are strings and not None
                meta_title = str(meta_title) if meta_title else 'Untitled Post'
                meta_tags = str(meta_tags) if meta_tags else 'scottish,heritage,culture,blog'
                meta_description = str(meta_description) if meta_description else 'No description available'
                
            except Exception as e:
                logger.error(f"Error processing meta data: {str(e)}")
                # Fallback to safe defaults
                meta_title = post.get('title', 'Untitled Post')
                meta_tags = 'scottish,heritage,culture,blog'
                meta_description = 'No description available'
            
            # Log the meta data being sent for debugging
            logger.info(f"Meta data for post {post.get('id')}:")
            logger.info(f"   meta_title: {repr(meta_title)}")
            logger.info(f"   meta_tags: {repr(meta_tags)}")
            logger.info(f"   meta_description: {repr(meta_description)}")
            
            # Check for problematic characters
            logger.info(f"Meta title length: {len(meta_title)}")
            logger.info(f"Meta tags length: {len(meta_tags)}")
            logger.info(f"Meta description length: {len(meta_description)}")
            
            # Validate meta data before sending
            if not isinstance(meta_title, str) or len(meta_title) > 200:
                logger.error(f"Invalid meta_title: {type(meta_title)}, length: {len(meta_title) if isinstance(meta_title, str) else 'N/A'}")
                meta_title = str(meta_title)[:200] if meta_title else 'Untitled Post'
            
            if not isinstance(meta_tags, str) or len(meta_tags) > 500:
                logger.error(f"Invalid meta_tags: {type(meta_tags)}, length: {len(meta_tags) if isinstance(meta_tags, str) else 'N/A'}")
                meta_tags = str(meta_tags)[:500] if meta_tags else 'scottish,heritage,culture,blog'
            
            if not isinstance(meta_description, str) or len(meta_description) > 160:
                logger.error(f"Invalid meta_description: {type(meta_description)}, length: {len(meta_description) if isinstance(meta_description, str) else 'N/A'}")
                meta_description = str(meta_description)[:160] if meta_description else 'No description available'
            
            json_args.update({
                'title': post.get('title', 'Untitled Post'),  # required
                'url_key': self._generate_url_key(post),  # required - use slug or generate from title
                'short_content': post.get('subtitle') or post.get('summary') or 'No summary available',  # prioritize subtitle over summary
                'status': 2,  # required - 2 = enabled (not 'published' string)
                'categories': [14, 15],  # required - note: 'categories' not 'category_ids'
                'list_thumbnail': list_thumbnail,  # required - path from /media (now uses real uploaded image)
                'post_thumbnail': post_thumbnail,  # required - path from /media (now uses real uploaded image)
                'meta_title': meta_title,  # use new meta_title field
                'meta_tags': meta_tags,  # use new meta_tags field
                'meta_description': meta_description  # use new meta_description field
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
            try:
                # Test JSON serialization before sending
                json_test = json.dumps(json_args)
                logger.info(f"JSON serialization test successful, length: {len(json_test)}")
                
                api_data = {
                    'api_user': self.api_user,
                    'api_key': self.api_key,
                    'json_args': json_test
                }
            except Exception as e:
                logger.error(f"JSON serialization failed: {str(e)}")
                logger.error(f"Problematic json_args: {json_args}")
                return {
                    'success': False,
                    'error': f'JSON serialization failed: {str(e)}'
                }
            
            logger.info(f"Sending to {endpoint}")
            logger.info(f"API data: {api_data}")
            logger.info(f"JSON args: {json_args}")
            
            # Debug: Log each field value
            for field, value in json_args.items():
                logger.info(f"Field '{field}': {value} (type: {type(value)})")
            
            # Create HTML file in a known location that clan.com can access
            import os
            import time
            html_filename = f"post_{post['id']}_{int(time.time())}.html"
            html_filepath = os.path.join(os.getcwd(), html_filename)
            
            try:
                # Write HTML content to file
                with open(html_filepath, 'w', encoding='utf-8') as html_file:
                    html_file.write(html_content)
                
                logger.info(f"{'Updating' if is_update else 'Creating'} post: {json_args['title']}")
                logger.info(f"HTML content length: {len(html_content)} characters")
                logger.info(f"HTML file created at: {html_filepath}")
                
                # Send the request with the actual HTML file content
                with open(html_filepath, 'rb') as html_file:
                    files = {'html_file': (html_filename, html_file, 'text/html')}
                    response = requests.post(endpoint, data=api_data, files=files, timeout=15)
                
            finally:
                # Clean up the HTML file
                try:
                    os.unlink(html_filepath)
                    logger.info(f"Cleaned up HTML file: {html_filepath}")
                except Exception as e:
                    logger.warning(f"Failed to clean up HTML file: {e}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Clan.com API response: {result}")
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                logger.info(f"Response text: {response.text}")
                
                # Check for success status (clan.com uses 'status' field like with image uploads)
                if result.get('status') == 'success' or result.get('success'):
                    # Extract post ID from response
                    clan_post_id = result.get('post_id')
                    
                    # If no post_id field, try to extract from message like "Post created: 384"
                    if not clan_post_id and result.get('message'):
                        message = result.get('message', '')
                        if 'Post created:' in message:
                            try:
                                clan_post_id = int(message.split(':')[-1].strip())
                            except (ValueError, IndexError):
                                logger.warning(f"Could not extract post ID from message: {message}")
                        elif 'Post updated:' in message:
                            try:
                                clan_post_id = int(message.split(':')[-1].strip())
                            except (ValueError, IndexError):
                                logger.warning(f"Could not extract post ID from message: {message}")
                    
                    # Construct the correct URL using the URL key (not post ID)
                    url_key = self._generate_url_key(post)
                    post_url = result.get('url') or f"https://clan.com/blog/{url_key}" if url_key else "https://clan.com/blog/"
                    
                    # Update the database with the clan_post_id if this was a new post
                    if not is_update and clan_post_id:
                        try:
                            from app import get_db_conn
                            conn = get_db_conn()
                            cursor = conn.cursor()
                            cursor.execute('UPDATE post SET clan_post_id = %s WHERE id = %s', (clan_post_id, post['id']))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            logger.info(f"✅ Updated database: post {post['id']} now has clan_post_id {clan_post_id}")
                        except Exception as e:
                            logger.error(f"❌ Failed to update database with clan_post_id: {e}")
                    
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
                    logger.error(f"Response text: {response.text}")
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

    def publish_to_clan(self, post, sections):
        """Main method to publish a post to clan.com"""
        try:
            logger.info("=== PUBLISH_TO_CLAN DEBUG START ===")
            logger.info(f"Post ID: {post.get('id')}")
            
            # Step 0: Get full post data from database to determine if this is an update
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM post WHERE id = %s', (post['id'],))
            post_row = cursor.fetchone()
            
            if not post_row:
                return {
                    'success': False,
                    'error': f'Post {post["id"]} not found in database'
                }
            
            # Get column names and convert to dict
            column_names = [desc[0] for desc in cursor.description]
            full_post_data = dict(zip(column_names, post_row))
            
            # Check if this is an update (post already exists on clan.com)
            is_update = bool(full_post_data.get('clan_post_id'))
            logger.info(f"Is update: {is_update} (clan_post_id: {full_post_data.get('clan_post_id')})")
            
            logger.info(f"Post header_image_id: {full_post_data.get('header_image_id')}")
            logger.info(f"Post header_image: {full_post_data.get('header_image')}")
            
            # Load sections from DB using the same function as the local route
            from app import get_post_sections_with_images
            sections_list = get_post_sections_with_images(post['id'])
            logger.info(f"Loaded {len(sections_list)} sections from DB using get_post_sections_with_images")
            
            # Step 0: Finding image paths from file system
            logger.info("Step 0: Finding image paths from file system...")
            from app import find_header_image, find_section_image
            
            # Set header image path
            header_image_path = find_header_image(full_post_data['id'])
            logger.info(f"find_header_image returned: {header_image_path}")
            
            if header_image_path:
                full_post_data['header_image'] = {'path': header_image_path}
                logger.info(f"✅ Set full_post_data['header_image'] = {{'path': '{header_image_path}'}}")
            else:
                logger.warning("❌ No header image found")
            
            # Attach section image paths
            for i, section in enumerate(sections_list):
                section_image_path = find_section_image(full_post_data['id'], section['id'])
                logger.info(f"Section {i+1} ({section.get('section_heading', 'No title')}): find_section_image returned: {section_image_path}")
                if section_image_path:
                    section['image'] = {'path': section_image_path}
                
            # Step 1: Process and upload images (header + section images)
            logger.info("Step 1: Processing and uploading images...")
            try:
                uploaded_images = self.process_images(full_post_data, sections_list)
                logger.info(f"✅ Image processing completed. Uploaded {len(uploaded_images)} images.")
                logger.info(f"uploaded_images dictionary: {uploaded_images}")
            except Exception as e:
                logger.error(f"❌ Error during image processing: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': f'Image processing failed: {str(e)}'
                }
            
            # Step 2: Mapping cross-promotion data
            logger.info("Step 2: Mapping cross-promotion data...")
            if full_post_data.get('cross_promotion_category_id'):
                full_post_data['cross_promotion'] = {
                    'category_id': full_post_data['cross_promotion_category_id'],
                    'category_title': full_post_data.get('cross_promotion_category_title', ''),
                    'product_id': full_post_data.get('cross_promotion_product_id'),
                    'product_title': full_post_data.get('cross_promotion_product_title', '')
                }
                logger.info(f"✅ Mapped cross-promotion data: category_id={full_post_data['cross_promotion']['category_id']}, title='{full_post_data['cross_promotion']['category_title']}'")
            else:
                logger.info("No cross-promotion data found")
            
            # Step 3: Render HTML content
            logger.info("Step 3: Rendering HTML content...")
            try:
                # Use the clan_post.html template instead of generating HTML from scratch
                html_content = self.get_preview_html_content(full_post_data, sections_list, uploaded_images)
                if not html_content:
                    return {
                        'success': False,
                        'error': 'Failed to get preview HTML content'
                    }
                logger.info(f"✅ Preview HTML content retrieved. Content length: {len(html_content)}")
                
                # Add the header_image data that was set earlier
                if full_post_data.get('header_image'):
                    logger.info(f"✅ Header image data ready for clan.com API: {full_post_data['header_image']}")
                
            except Exception as e:
                logger.error(f"❌ Error getting preview HTML content: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': f'Preview HTML content retrieval failed: {str(e)}'
                }
            
            # Step 4: Create or update post on clan.com
            logger.info("Step 4: Creating/updating post on clan.com...")
            logger.info(f"Is update: {is_update} (clan_post_id: {full_post_data.get('clan_post_id')})")
            
            try:
                result = self.create_or_update_post(full_post_data, html_content, is_update, uploaded_images)
                if result['success']:
                    logger.info(f"✅ Successfully published post {full_post_data['id']} to clan.com")
                    return result
                else:
                    logger.error(f"❌ Failed to publish post {full_post_data['id']}: {result.get('error', 'Unknown error')}")
                    return result
            except Exception as e:
                logger.error(f"❌ Error during post creation/update: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': f'Post creation/update failed: {str(e)}'
                }
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in publish_to_clan: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
        finally:
            logger.info("=== PUBLISH_TO_CLAN DEBUG END ===")

    def get_preview_html_content(self, post, sections, uploaded_images=None):
        """Generate HTML using clan_post_raw.html template for clan.com upload.
        This shows the ACTUAL HTML that gets uploaded, not placeholder widgets.
        """
        try:
            import os
            
            # Get the clan_post_raw.html template content
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'clan_post_raw.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Create Jinja2 environment with the strip_html_doc filter
            from jinja2 import Environment, BaseLoader
            
            def strip_html_doc(content):
                """Strip HTML document tags and return just the content"""
                if not content:
                    return content
                # Remove DOCTYPE, html, head, body tags and their content
                import re
                content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
                content = re.sub(r'<html[^>]*>.*?</html>', '', content, flags=re.DOTALL)
                content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL)
                content = re.sub(r'<body[^>]*>.*?</body>', '', content, flags=re.DOTALL)
                return content.strip()
            
            env = Environment(loader=BaseLoader())
            env.filters['strip_html_doc'] = strip_html_doc
            
            template = env.from_string(template_content)
            html_content = template.render(post=post, sections=sections)
            
            # Translate local image/file paths to uploaded clan.com URLs
            if uploaded_images:
                logger.info('Translating image paths to clan.com URLs...')
                logger.info(f'Uploaded images mapping: {uploaded_images}')
                
                # Create a comprehensive path mapping
                path_mapping = {}
                for local_path, clan_url in uploaded_images.items():
                    # Add the exact path as found in uploaded_images
                    path_mapping[local_path] = clan_url
                    
                    # Also add variations that might appear in the HTML
                    if local_path.startswith('/static/'):
                        # Keep the original path
                        path_mapping[local_path] = clan_url
                        
                        # Add the path without /static/ prefix (in case HTML uses relative paths)
                        if local_path.startswith('/static/'):
                            relative_path = local_path[7:]  # Remove '/static/' prefix
                            path_mapping[relative_path] = clan_url
                            logger.info(f"Added relative path mapping: {relative_path} -> {clan_url}")
                
                logger.info(f'Final path mapping: {path_mapping}')
                
                # Replace all paths in the HTML content
                for local_path, clan_url in path_mapping.items():
                    # Replace src attributes
                    html_content = html_content.replace(f'src="{local_path}"', f'src="{clan_url}"')
                    # Replace href attributes  
                    html_content = html_content.replace(f'href="{local_path}"', f'href="{clan_url}"')
                    # Replace any other occurrences
                    html_content = html_content.replace(local_path, clan_url)
                    logger.info(f"Replaced {local_path} -> {clan_url}")
            
            # Remove localhost refs that may linger
            import re
            html_content = re.sub(r'http://localhost:\d+', '', html_content)
            
            # Save the HTML file for inspection
            debug_file = f'/tmp/upload_html_post_{post["id"]}_{int(time.time())}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Upload HTML saved to: {debug_file}")
            
            logger.info(f"Final HTML content length: {len(html_content)}")
            return html_content
        except Exception as e:
            logger.error(f"Error generating HTML content: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
