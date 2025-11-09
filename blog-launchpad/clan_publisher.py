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
    
    def _dump_api_call(self, call_type, url, data, files=None, filename=None, json_args=None, html_content=None, image_info=None):
        """Dump exact API call data to diagnostic file"""
        try:
            import json
            import os
            from datetime import datetime
            
            # Create log directory if it doesn't exist
            log_dir = "/Users/nickfiddes/Code/projects/blog/blog-launchpad/log"
            os.makedirs(log_dir, exist_ok=True)
            
            # Create diagnostic data
            diagnostic_data = {
                'timestamp': datetime.now().isoformat(),
                'call_type': call_type,
                'url': url,
                'data': data,
                'files_info': {},
                'json_args_raw': json_args,
                'html_content_length': len(html_content) if html_content else 0,
                'image_info': image_info
            }
            
            # Parse and add the actual JSON args if provided
            if json_args:
                try:
                    parsed_args = json.loads(json_args) if isinstance(json_args, str) else json_args
                    diagnostic_data['json_args_parsed'] = parsed_args
                except:
                    diagnostic_data['json_args_parsed'] = "Failed to parse JSON"
            
            # Add file information if files are provided
            if files:
                for key, file_tuple in files.items():
                    if isinstance(file_tuple, tuple) and len(file_tuple) >= 2:
                        file_info = {
                            'filename': file_tuple[0],
                            'mime_type': file_tuple[2] if len(file_tuple) > 2 else 'unknown'
                        }
                        
                        # For image files, try to get file size and path info
                        if key == 'image' and hasattr(file_tuple[1], 'name'):
                            try:
                                file_path = file_tuple[1].name
                                if os.path.exists(file_path):
                                    file_info['file_size'] = os.path.getsize(file_path)
                                    file_info['file_path'] = file_path
                            except:
                                pass
                        
                        # For HTML files, capture content length
                        elif key == 'html_file':
                            try:
                                if hasattr(file_tuple[1], 'read'):
                                    current_pos = file_tuple[1].tell()
                                    file_tuple[1].seek(0, 2)  # Seek to end
                                    file_size = file_tuple[1].tell()
                                    file_tuple[1].seek(current_pos)  # Restore position
                                    file_info['content_length'] = file_size
                            except:
                                pass
                        
                        diagnostic_data['files_info'][key] = file_info
            
            # Add HTML content preview if provided
            if html_content:
                diagnostic_data['html_content_preview'] = html_content[:1000] + "..." if len(html_content) > 1000 else html_content
            
            # Write to diagnostic file (overwrites previous)
            diagnostic_file = os.path.join(log_dir, f"clan_api_diagnostic_{call_type}.json")
            with open(diagnostic_file, 'w') as f:
                json.dump(diagnostic_data, f, indent=2)
            
            # Also write a separate HTML content file for post creation
            if call_type == 'post_create_update' and html_content:
                html_file = os.path.join(log_dir, f"clan_api_diagnostic_html_content.html")
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"DIAGNOSTIC: HTML content dumped to {html_file}")
            
            logger.info(f"DIAGNOSTIC: API call data dumped to {diagnostic_file}")
            
        except Exception as e:
            logger.error(f"Failed to dump API call data: {e}")
    
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
        
        # Generate from title for new posts - clean text-based URLs only
        title = post.get('title')
        if not title:
            raise ValueError("Post title is required but not provided")
        
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        url_key = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        url_key = re.sub(r'\s+', '-', url_key).strip('-')
        
        # Ensure it's not empty - use clean text only, no IDs or timestamps
        if not url_key:
            url_key = 'untitled-post'
        
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
        meta_title = post.get('meta_title') or post.get('title')
        if not meta_title:
            raise ValueError("Post title is required but not provided")
        
        meta_tags = post.get('meta_tags') or self._generate_meta_tags(post)
        
        # Clean meta_description - require at least one description field
        raw_description = post.get('meta_description') or post.get('subtitle') or post.get('summary', '')
        if not raw_description:
            raise ValueError("Post must have meta_description, subtitle, or summary")
        
        # Strip HTML tags and limit to 160 characters
        import re
        clean_description = re.sub(r'<[^>]+>', '', raw_description)
        meta_description = clean_description[:160] if clean_description else raw_description[:160]
        
        # Ensure all meta fields are strings and not None
        meta_title = str(meta_title)
        meta_tags = str(meta_tags) if meta_tags else 'scottish,heritage,culture,blog'
        meta_description = str(meta_description)
        
        # Get OG-specific meta fields
        meta_image = post.get('meta_image', 'https://clan.com/images/default-scottish-heritage.jpg')
        meta_type = post.get('meta_type', 'article')
        meta_site_name = post.get('meta_site_name', 'Clan.com Blog')
        
        # Build the API data structure
        api_data = {
            'title': post.get('title'),
            'url_key': self._generate_url_key(post),
            'short_content': post.get('subtitle') or post.get('summary'),  # prioritize subtitle over summary
            'status': 2,  # 2 = enabled
            'categories': [14, 15],  # Default clan.com categories
            'list_thumbnail': list_thumbnail,
            'post_thumbnail': post_thumbnail,
            'meta_title': meta_title,
            'meta_tags': meta_tags,
            'meta_description': meta_description,
            'meta_image': meta_image,
            'meta_type': meta_type,
            'meta_site_name': meta_site_name
        }
        
        return api_data
    
    def upload_image(self, image_path, filename=None):
        """Upload an image to clan.com and return the uploaded URL
        Supports both local file paths and remote URLs (downloads and uploads to clan.com CDN)
        """
        temp_file_path = None
        try:
            if not filename:
                filename = os.path.basename(image_path)
            
            # Check if it's a local path or URL
            if image_path.startswith('/static/'):
                # Convert local static path to full local file path using path resolver
                from config.paths import path_resolver
                local_path = path_resolver.convert_web_path_to_filesystem(image_path)
                if not os.path.exists(local_path):
                    logger.warning(f"Local image not found: {local_path}")
                    return None
                image_path = local_path
            elif image_path.startswith('http'):
                # Download remote image to temp file
                logger.info(f"Downloading remote image: {image_path}")
                response = requests.get(image_path, timeout=30)
                if response.status_code == 200:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
                    temp_file.write(response.content)
                    temp_file.close()
                    temp_file_path = temp_file.name
                    image_path = temp_file_path
                    logger.info(f"Downloaded to temp file: {temp_file_path} ({len(response.content)} bytes)")
                else:
                    logger.warning(f"Failed to download image: {image_path} (status: {response.status_code})")
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
                
                # DIAGNOSTIC LOGGING: Dump exact API data being sent
                # Capture image file info for diagnostic
                image_info = {
                    'original_path': image_path,
                    'filename': filename,
                    'file_size': os.path.getsize(image_path) if os.path.exists(image_path) else 0,
                    'mime_type': mime_type
                }
                self._dump_api_call('image_upload', upload_url, data, files, filename, image_info=image_info)
                
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
                            logger.info(f"✅ Image uploaded successfully: {uploaded_url}")
                            # Clean up temp file before returning
                            if temp_file_path and os.path.exists(temp_file_path):
                                try:
                                    os.unlink(temp_file_path)
                                    logger.info(f"🧹 Cleaned up temporary file: {temp_file_path}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not delete temp file {temp_file_path}: {e}")
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
        finally:
            # Clean up temp file if we created one (fallback cleanup)
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file in finally block: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete temp file in finally: {e}")
    
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
        from config.paths import path_resolver
        uploaded_images = {}
        
        logger.info(f"=== PROCESS_IMAGES DEBUG START ===")
        logger.info(f"Post ID: {post.get('id')}")
        logger.info(f"Post header_image: {post.get('header_image')}")
        logger.info(f"Post header_image_id: {post.get('header_image_id')}")
        
        # Process header image - use header image path from post data
        logger.info(f"=== PROCESS_IMAGES: Checking for header image ===")
        logger.info(f"post.get('header_image'): {post.get('header_image')}")
        header_path = post.get('header_image', {}).get('path')
        logger.info(f"header_path extracted: {header_path}")
        if header_path:
            logger.info(f"✅ Found header image: {header_path}")
            
            # Generate unique filename with timestamp for cache busting
            filename = f"header_{post['id']}_{int(time.time())}.jpg"
            logger.info(f"Uploading header image with filename: {filename}")
            
            try:
                # Convert web path to file system path for upload
                # Try path_resolver first, but also check static/ directly if it fails
                fs_path = path_resolver.convert_web_path_to_filesystem(header_path)
                logger.info(f"Converting web path '{header_path}' to file system path '{fs_path}'")
                
                # NO FALLBACKS - path_resolver should find it or fail clearly
                if not os.path.exists(fs_path):
                    logger.error(f"❌ Header image file NOT found at: {fs_path}")
                    logger.error(f"   Web path was: {header_path}")
                    logger.error(f"   Project root: {path_resolver.project_root}")
                    logger.error(f"   This should not happen - path_resolver should find files in project_root/static/")
                
                # Check if file exists before attempting upload
                if os.path.exists(fs_path):
                    logger.info(f"✅ Header image file exists at: {fs_path}")
                    logger.info(f"File size: {os.path.getsize(fs_path)} bytes")
                    
                    uploaded_url = self.upload_image(fs_path, filename)
                    logger.info(f"upload_image returned: {uploaded_url}")
                    
                    if uploaded_url:
                        uploaded_images[header_path] = uploaded_url
                        logger.info(f"✅ Header image uploaded successfully: {header_path} -> {uploaded_url}")
                        logger.info(f"✅ Stored in uploaded_images with key: '{header_path}' (type: {type(header_path)}, len: {len(header_path)})")
                        logger.info(f"✅ uploaded_images keys: {list(uploaded_images.keys())}")
                        logger.info(f"✅ uploaded_images values: {list(uploaded_images.values())}")
                    else:
                        logger.error(f"❌ upload_image returned None/empty for: {header_path}")
                else:
                    logger.error(f"❌ Header image file NOT found at: {fs_path}")
                    logger.error(f"Current working directory: {os.getcwd()}")
                    logger.error(f"Web path was: {header_path}")
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
                
                # Reject URLs (Photo-harvesting deprecated - only local files supported)
                if section_path.startswith(('http://', 'https://')):
                    logger.warning(f"⚠️ URL detected in section image (Photo-harvesting deprecated): {section_path}")
                    logger.warning(f"   Section ID: {section.get('id')}")
                    logger.warning(f"   Skipping URL - only local files are supported")
                    continue
                
                # Check if file exists - convert web path to file system path
                fs_path = path_resolver.convert_web_path_to_filesystem(section_path)
                if os.path.exists(fs_path):
                    logger.info(f"✅ Section image file exists at: {fs_path}")
                    logger.info(f"File size: {os.path.getsize(fs_path)} bytes")
                else:
                    logger.error(f"❌ Section image file NOT found at: {fs_path}")
                    logger.error(f"Current working directory: {os.getcwd()}")
                
                # Generate unique filename
                filename = f"section_{post['id']}_{i+1}_{int(time.time())}.jpg"
                logger.info(f"Uploading section image with filename: {filename}")
                
                try:
                    # Convert web path to file system path for upload
                    fs_path = path_resolver.convert_web_path_to_filesystem(section_path)
                    logger.info(f"Converting section web path '{section_path}' to file system path '{fs_path}'")
                    
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
        
        # Save image mappings to database for future reference
        if uploaded_images:
            self._save_image_mappings_to_db(post, sections, uploaded_images)
        
        return uploaded_images
    
    def _save_image_mappings_to_db(self, post, sections, uploaded_images):
        """Save section image mappings to database for future reference."""
        try:
            import os
            from config.database import db_manager
            
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                
                # Clear existing mappings for this post
                cursor.execute("""
                    DELETE FROM section_image_mappings 
                    WHERE post_id = %s
                """, (post['id'],))
                
                # Insert new mappings
                # Track which sections we've already mapped to avoid duplicates
                mapped_sections = set()
                
                for local_path, clan_url in uploaded_images.items():
                    # Skip duplicate mappings (we map both exact path and base URL)
                    from urllib.parse import urlparse
                    if local_path.startswith('http'):
                        # For Photo-harvesting URLs, only save the exact path mapping (not base URL)
                        parsed = urlparse(local_path)
                        base_url = parsed.scheme + '://' + parsed.netloc + parsed.path
                        if local_path == base_url and base_url in uploaded_images:
                            # This is a base URL mapping, skip it (we'll save the exact path version)
                            continue
                    
                    # Find which section this image belongs to
                    section_id = None
                    for section in sections:
                        if section.get('image') and section['image'].get('path'):
                            section_img_path = section['image']['path']
                            # For Photo-harvesting URLs, match by base URL (without query params)
                            if local_path.startswith('http') and section_img_path.startswith('http'):
                                from urllib.parse import urlparse as _urlparse
                                local_base = _urlparse(local_path).scheme + '://' + _urlparse(local_path).netloc + _urlparse(local_path).path
                                section_base = _urlparse(section_img_path).scheme + '://' + _urlparse(section_img_path).netloc + _urlparse(section_img_path).path
                                if local_base == section_base:
                                    section_id = section['id']
                                    break
                            elif section_img_path == local_path:
                                section_id = section['id']
                                break
                    
                    # If no section_id found, check if it's a header image
                    if not section_id and 'header' in local_path:
                        section_id = None  # Header images have section_id = NULL
                    
                    # Skip if we've already mapped this section (avoid duplicates)
                    if section_id is not None and section_id in mapped_sections:
                        continue
                    
                    # Save mapping for both section images and header images
                    if section_id is not None or ('header' in local_path and section_id is None):
                        # Extract filename
                        filename = os.path.basename(local_path)
                        if not filename or filename.startswith('http'):
                            # For Photo-harvesting URLs, extract from path
                            parsed = urlparse(local_path) if local_path.startswith('http') else None
                            if parsed:
                                filename = os.path.basename(parsed.path) or 'photo-harvesting.jpg'
                            else:
                                filename = 'photo-harvesting.jpg'
                        
                        # Get file size and dimensions if possible
                        file_size = None
                        dimensions = None
                        
                        # For Photo-harvesting URLs, skip filesystem checks (they're remote)
                        if not local_path.startswith('http'):
                            # Convert web path to file system path for file info
                            from config.paths import path_resolver as _pr
                            fs_path = _pr.convert_web_path_to_filesystem(local_path)
                            if os.path.exists(fs_path):
                                file_size = os.path.getsize(fs_path)
                                # Try to get dimensions using PIL
                                try:
                                    from PIL import Image
                                    with Image.open(fs_path) as img:
                                        dimensions = f"{img.width}x{img.height}"
                                except:
                                    dimensions = "Unknown"
                        
                        # Insert the mapping
                        cursor.execute("""
                            INSERT INTO section_image_mappings 
                            (post_id, section_id, local_image_path, clan_uploaded_url, image_filename, image_size_bytes, image_dimensions)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (post['id'], section_id, local_path, clan_url, filename, file_size, dimensions))
                        
                        if section_id:
                            mapped_sections.add(section_id)
                        
                        logger.info(f"✅ Saved image mapping: {local_path} -> {clan_url} (section_id: {section_id})")
                
                logger.info(f"✅ Saved {len(uploaded_images)} image mappings to database")
            
            # Commit the transaction
            conn.commit()
            logger.info("✅ Image mappings transaction committed")
                
        except Exception as e:
            logger.error(f"❌ Error saving image mappings to database: {str(e)}")
            # Don't fail the upload process if database save fails
            pass
    
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
            
            # Set thumbnails based on uploaded header image availability
            # CRITICAL: These fields are MANDATORY according to clan.com API docs
            list_thumbnail = '/blog/placeholder.jpg'  # Default fallback that should exist on clan.com
            post_thumbnail = '/blog/placeholder.jpg'  # Default fallback that should exist on clan.com
            
            # Get header image path from post data (not from uploaded_images keys)
            header_image_path = None
            if post.get('header_image') and post['header_image'].get('path'):
                header_image_path = post['header_image']['path']
            
            logger.info(f"=== CREATE_OR_UPDATE_POST: Looking for header image ===")
            logger.info(f"Header image path from post: '{header_image_path}' (type: {type(header_image_path)}, len: {len(header_image_path) if header_image_path else 0})")
            logger.info(f"uploaded_images keys: {list(uploaded_images.keys()) if uploaded_images else 'None'}")
            if uploaded_images:
                for key, value in uploaded_images.items():
                    logger.info(f"  Key: '{key}' (type: {type(key)}, len: {len(key)}) -> Value: {value}")
            
            # Look for the header image in uploaded_images using EXACT match only (NO FALLBACKS)
            header_uploaded_url = None
            if header_image_path and uploaded_images:
                logger.info(f"Searching for exact match: '{header_image_path}'")
                
                # Try exact match only
                if header_image_path in uploaded_images:
                    header_uploaded_url = uploaded_images[header_image_path]
                    logger.info(f"✅ Found header image with EXACT path match: '{header_image_path}' -> {header_uploaded_url}")
                else:
                    logger.error(f"❌ EXACT MATCH FAILED: '{header_image_path}' not in uploaded_images")
                    logger.error(f"   Looking for: '{header_image_path}' (repr: {repr(header_image_path)})")
                    logger.error(f"   Available keys:")
                    for key in uploaded_images.keys():
                        logger.error(f"     '{key}' (repr: {repr(key)})")
                        logger.error(f"     Match: {key == header_image_path}")
                        logger.error(f"     Equal: {key == header_image_path}")
                        if key == header_image_path:
                            logger.error(f"     WHY DIDN'T IT MATCH???")
            
            logger.info(f"header_uploaded_url: {header_uploaded_url}")
            if header_uploaded_url:
                # Check if it's a clan.com media URL
                if '/media/blog/' in header_uploaded_url or '/media/' in header_uploaded_url:
                    # Extract filename from URL like "https://static.clan.com/media/blog/header_53_1703123456.jpg"
                    # We need the path relative to /media, so extract everything after /media/
                    media_path = header_uploaded_url.split('/media/')[-1]
                    thumbnail_path = f"/{media_path}"  # This gives us /blog/header_53_1703123456.jpg
                    list_thumbnail = thumbnail_path
                    post_thumbnail = thumbnail_path
                    logger.info(f"✅ Using uploaded header image for thumbnails: {thumbnail_path}")
                else:
                    logger.warning(f"⚠️ Header image URL doesn't contain /media/: {header_uploaded_url}")
            else:
                # No header image found - use placeholder (DO NOT fall back to section images)
                if header_image_path:
                    logger.warning(f"⚠️ Header image path exists ({header_image_path}) but not found in uploaded_images. Using placeholder.")
                    if uploaded_images:
                        logger.warning(f"Available image paths: {list(uploaded_images.keys())}")
                else:
                    logger.info("No header image available, using default placeholder thumbnails")
            
            # Common post metadata - using new database meta fields for proper OG tags
            meta_title = post.get('meta_title') or post.get('title')
            if not meta_title:
                raise ValueError("Post title is required but not provided")
            
            meta_tags = post.get('meta_tags') or self._generate_meta_tags(post)
            
            # Clean meta_description - require at least one description field
            raw_description = post.get('meta_description') or post.get('subtitle') or post.get('summary', '')
            if not raw_description:
                raise ValueError("Post must have meta_description, subtitle, or summary")
            
            # Strip HTML tags and limit to 160 characters
            import re
            clean_description = re.sub(r'<[^>]+>', '', raw_description)
            meta_description = clean_description[:160] if clean_description else raw_description[:160]
            
            # Ensure all meta fields are strings and not None
            meta_title = str(meta_title)
            meta_tags = str(meta_tags) if meta_tags else 'scottish,heritage,culture,blog'
            meta_description = str(meta_description)
            
            # Get OG-specific meta fields
            meta_image = post.get('meta_image', 'https://clan.com/images/default-scottish-heritage.jpg')
            meta_type = post.get('meta_type', 'article')
            meta_site_name = post.get('meta_site_name', 'Clan.com Blog')
            
            # Ensure OG fields are strings
            meta_image = str(meta_image)
            meta_type = str(meta_type)
            meta_site_name = str(meta_site_name)
            
            # Log the meta data being sent for debugging
            logger.info(f"Meta data for post {post.get('id')}:")
            logger.info(f"   meta_title: {repr(meta_title)}")
            logger.info(f"   meta_tags: {repr(meta_tags)}")
            logger.info(f"   meta_description: {repr(meta_description)}")
            logger.info(f"   meta_image: {repr(meta_image)}")
            logger.info(f"   meta_type: {repr(meta_type)}")
            logger.info(f"   meta_site_name: {repr(meta_site_name)}")
            
            # Check for problematic characters
            logger.info(f"Meta title length: {len(meta_title)}")
            logger.info(f"Meta tags length: {len(meta_tags)}")
            logger.info(f"Meta description length: {len(meta_description)}")
            
            # Validate meta data before sending
            if not isinstance(meta_title, str) or len(meta_title) > 200:
                logger.error(f"Invalid meta_title: {type(meta_title)}, length: {len(meta_title) if isinstance(meta_title, str) else 'N/A'}")
                raise ValueError(f"Invalid meta_title: must be string under 200 chars, got {type(meta_title)} with length {len(meta_title) if isinstance(meta_title, str) else 'N/A'}")
            
            if not isinstance(meta_tags, str) or len(meta_tags) > 500:
                logger.error(f"Invalid meta_tags: {type(meta_tags)}, length: {len(meta_tags) if isinstance(meta_tags, str) else 'N/A'}")
                raise ValueError(f"Invalid meta_tags: must be string under 500 chars, got {type(meta_tags)} with length {len(meta_tags) if isinstance(meta_tags, str) else 'N/A'}")
            
            if not isinstance(meta_description, str) or len(meta_description) > 160:
                logger.error(f"Invalid meta_description: {type(meta_description)}, length: {len(meta_description) if isinstance(meta_description, str) else 'N/A'}")
                raise ValueError(f"Invalid meta_description: must be string under 160 chars, got {type(meta_description)} with length {len(meta_description) if isinstance(meta_description, str) else 'N/A'}")
            
            json_args.update({
                'title': post.get('title'),  # required
                'url_key': self._generate_url_key(post),  # required - use slug or generate from title
                'short_content': post.get('subtitle') or post.get('summary'),  # prioritize subtitle over summary
                'status': 2,  # required - 2 = enabled (not 'published' string)
                'categories': [14, 15],  # required - note: 'categories' not 'category_ids'
                'list_thumbnail': list_thumbnail,  # required - path from /media (now uses real uploaded image)
                'post_thumbnail': post_thumbnail,  # required - path from /media (now uses real uploaded image)
                'meta_title': meta_title,  # use new meta_title field
                'meta_tags': meta_tags,  # use new meta_tags field
                'meta_description': meta_description,  # use new meta_description field
                'meta_image': meta_image,  # OG image URL
                'meta_type': meta_type,  # OG type (default: article)
                'meta_site_name': meta_site_name  # OG site name (default: Clan.com Blog)
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
                files = {'html_file': (html_filename, open(html_filepath, 'rb'), 'text/html')}
                
                # DIAGNOSTIC LOGGING: Dump exact API data being sent
                self._dump_api_call('post_create_update', endpoint, api_data, files, html_filename, json_args, html_content)
                
                response = requests.post(endpoint, data=api_data, files=files, timeout=15)
                
                # Close file handles
                for file_tuple in files.values():
                    if hasattr(file_tuple[1], 'close'):
                        file_tuple[1].close()
                
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
                        'clan_url': post_url,
                        'url': post_url  # Keep for backward compatibility
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
            from config.database import db_manager
            from config.paths import path_resolver
            with db_manager.get_cursor() as cursor:
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
            
            # Merge the passed post data with the database data (passed data takes precedence)
            # CRITICAL: Preserve header_image from post data if it exists, as it was set by the Flask route
            logger.info(f"=== CLAN_PUBLISHER MERGE DEBUG ===")
            logger.info(f"post.get('header_image') BEFORE merge: {post.get('header_image')}")
            logger.info(f"full_post_data.get('header_image') BEFORE merge: {full_post_data.get('header_image')}")
            
            header_image_from_post = post.get('header_image')
            full_post_data.update(post)
            
            # If post had header_image, ensure it's preserved (update might have overwritten it)
            if header_image_from_post:
                full_post_data['header_image'] = header_image_from_post
                logger.info(f"✅ Preserved header_image from post data: {header_image_from_post.get('path')}")
            else:
                logger.warning(f"⚠️ No header_image in post data to preserve")
            
            logger.info(f"full_post_data.get('header_image') AFTER merge: {full_post_data.get('header_image')}")
            logger.info(f"full_post_data['header_image'].get('path') AFTER merge: {full_post_data.get('header_image', {}).get('path') if full_post_data.get('header_image') else 'None'}")
            
            # Check if this is an update (post already exists on clan.com)
            is_update = bool(full_post_data.get('clan_post_id'))
            logger.info(f"Is update: {is_update} (clan_post_id: {full_post_data.get('clan_post_id')})")
            
            logger.info(f"Post header_image_id: {full_post_data.get('header_image_id')}")
            
            # Use sections passed from the endpoint (already loaded with images)
            sections_list = sections
            logger.info(f"Using {len(sections_list)} sections passed from endpoint")
            
            # Step 0: Finding image paths from file system
            logger.info("Step 0: Finding image paths from file system...")
            
            # CRITICAL: Ensure header_image is set BEFORE process_images is called
            # Preserve header image from post data if it exists, otherwise look it up from database
            if not full_post_data.get('header_image') or not full_post_data['header_image'].get('path'):
                header_image_path = post.get('header_image', {}).get('path') if post.get('header_image') else None
                logger.info(f"Looking up header image from post data: {header_image_path}")
                
                # If still not found, try to load from database using find_header_image
                if not header_image_path:
                    logger.warning("⚠️ No header_image in post data, attempting to load from database")
                    try:
                        # Define find_header_image locally to avoid import issues
                        # CRITICAL: Use same logic as app.py find_header_image - check project_static first, then blog_images_static
                        def find_header_image_local(post_id):
                            """Find header image for a post - local definition to avoid import issues."""
                            import urllib.parse
                            
                            # Get project root (same logic as app.py)
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            project_root = os.path.dirname(current_dir)  # Go up from blog-launchpad/ to project root
                            
                            # Try project static/ first (unified app location), then blog-images/static/ (legacy)
                            project_static = os.path.join(project_root, 'static')
                            blog_images_static = os.path.join(project_root, 'blog-images', 'static')
                            
                            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
                            image_types = ['optimized', 'watermarked', 'raw']  # Check optimized first
                            
                            # Check both static directories for each image type
                            for image_type in image_types:
                                for static_dir in [project_static, blog_images_static]:
                                    header_path = os.path.join(static_dir, "content", "posts", str(post_id), "header", image_type)
                                    if os.path.exists(header_path):
                                        image_files = [f for f in os.listdir(header_path)
                                                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
                                        if image_files:
                                            image_filename = image_files[0]
                                            encoded_filename = urllib.parse.quote(image_filename)
                                            return f"/static/content/posts/{post_id}/header/{image_type}/{encoded_filename}"
                            return None
                        
                        header_image_path = find_header_image_local(full_post_data.get('id'))
                        if header_image_path:
                            logger.info(f"✅ Loaded header_image from database: {header_image_path}")
                        else:
                            logger.warning("❌ No header image found in database either")
                    except Exception as e:
                        logger.error(f"❌ Error loading header image from database: {str(e)}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                
                if header_image_path:
                    # Preserve existing header_image structure if it exists
                    if not full_post_data.get('header_image'):
                        full_post_data['header_image'] = {}
                    full_post_data['header_image']['path'] = header_image_path
                    logger.info(f"✅ Set header_image path in full_post_data: {header_image_path}")
                    logger.info(f"✅ Set full_post_data['header_image']['path'] = '{header_image_path}'")
                else:
                    logger.warning("❌ No header image found anywhere")
            else:
                logger.info(f"✅ Preserving existing header image: {full_post_data['header_image'].get('path')}")
            
            # CRITICAL: Verify header_image is set before process_images
            logger.info(f"=== PRE-PROCESS_IMAGES HEADER IMAGE VERIFICATION ===")
            logger.info(f"full_post_data.get('header_image'): {full_post_data.get('header_image')}")
            if full_post_data.get('header_image'):
                logger.info(f"full_post_data['header_image'].get('path'): {full_post_data['header_image'].get('path')}")
            else:
                logger.error(f"❌ ERROR: full_post_data['header_image'] is None/empty before process_images!")
            
            # Sections already have image paths structured in section['image']['path'] from endpoint
            for i, section in enumerate(sections_list):
                has_image = section.get('image') and section['image'].get('path') and not section['image'].get('placeholder')
                logger.info(f"Section {i+1} ({section.get('section_heading', 'No title')}): has_image = {has_image}")
                if has_image:
                    logger.info(f"  Image path: {section['image']['path']}")
                
            # Step 1: Process and upload images (header + section images)
            logger.info("Step 1: Processing and uploading images...")
            try:
                uploaded_images = self.process_images(full_post_data, sections_list)
                logger.info(f"✅ Image processing completed. Uploaded {len(uploaded_images)} images.")
                logger.info(f"uploaded_images dictionary: {uploaded_images}")
                
                # Fallback: If no images were uploaded/mapped, force-upload header and section images
                if not uploaded_images or len(uploaded_images) == 0:
                    logger.warning("⚠️ uploaded_images is empty. Forcing image uploads for header and sections...")
                    # Attempt header image upload
                    header_image_path = full_post_data.get('header_image', {}).get('path')
                    if header_image_path:
                        try:
                            fs_path = path_resolver.convert_web_path_to_filesystem(header_image_path)
                            if os.path.exists(fs_path):
                                filename = f"header_{full_post_data['id']}_{int(time.time())}.jpg"
                                uploaded_url = self.upload_image(fs_path, filename)
                                if uploaded_url:
                                    uploaded_images[header_image_path] = uploaded_url
                                    logger.info(f"✅ Forced header image upload: {header_image_path} -> {uploaded_url}")
                            else:
                                logger.warning(f"⚠️ Forced upload skipped: header fs_path not found: {fs_path}")
                        except Exception as e:
                            logger.error(f"❌ Forced upload error (header): {e}")
                    # Attempt each section image upload
                    for i, section in enumerate(sections_list):
                        try:
                                section_img = section.get('image') or {}
                                section_path = section_img.get('path')
                                if section_path and not section_img.get('placeholder'):
                                    # Try path_resolver first, then fallback to direct path in project root
                                    fs_path = path_resolver.convert_web_path_to_filesystem(section_path)
                                    if not os.path.exists(fs_path):
                                        # Fallback: try direct path in project root static/ directory
                                        import os
                                        project_root = os.path.dirname(os.path.dirname(__file__))
                                        fs_path = os.path.join(project_root, section_path.lstrip('/'))
                                    if os.path.exists(fs_path):
                                        filename = f"section_{full_post_data['id']}_{i+1}_{int(time.time())}.jpg"
                                        uploaded_url = self.upload_image(fs_path, filename)
                                        if uploaded_url:
                                            uploaded_images[section_path] = uploaded_url
                                            logger.info(f"✅ Forced section image upload: {section_path} -> {uploaded_url}")
                                else:
                                    logger.warning(f"⚠️ Forced upload skipped: section fs_path not found: {fs_path}")
                        except Exception as e:
                            logger.error(f"❌ Forced upload error (section {i+1}): {e}")
                    logger.info(f"After forced uploads, uploaded_images: {uploaded_images}")

                # Fix: Ensure header image is included in uploaded_images for HTML replacement
                header_image_path = full_post_data.get('header_image', {}).get('path')
                if header_image_path and header_image_path not in uploaded_images:
                    # Header image was processed but not added to uploaded_images
                    # We need to upload it separately and add to uploaded_images
                    logger.info(f"Header image not in uploaded_images, uploading separately: {header_image_path}")
                    try:
                        fs_path = path_resolver.convert_web_path_to_filesystem(header_image_path)
                        if os.path.exists(fs_path):
                            filename = f"header_{full_post_data['id']}_{int(time.time())}.jpg"
                            uploaded_url = self.upload_image(fs_path, filename)
                            if uploaded_url:
                                uploaded_images[header_image_path] = uploaded_url
                                logger.info(f"✅ Header image uploaded and added to uploaded_images: {header_image_path} -> {uploaded_url}")
                            else:
                                logger.warning(f"❌ Header image upload failed: {header_image_path}")
                        else:
                            logger.warning(f"❌ Header image file not found: {fs_path}")
                    except Exception as e:
                        logger.error(f"❌ Error uploading header image: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Error during image processing: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': f'Image processing failed: {str(e)}'
                }
            
            # Step 2: Mapping cross-promotion data (with auto-selection when missing)
            logger.info("Step 2: Mapping cross-promotion data...")
            try:
                cp_changed = False
                # If missing, auto-select random IDs and default positions
                if not (full_post_data.get('cross_promotion_category_id') or full_post_data.get('cross_promotion_product_id')):
                    from config.database import db_manager
                    with db_manager.get_cursor() as cursor:
                        # Random category
                        cursor.execute("SELECT id, name FROM clan_categories ORDER BY RANDOM() LIMIT 1")
                        cat = cursor.fetchone()
                        if cat:
                            full_post_data['cross_promotion_category_id'] = cat['id']
                            full_post_data['cross_promotion_category_title'] = cat.get('name') or 'Related Department'
                            full_post_data['cross_promotion_category_position'] = 2
                            cp_changed = True
                        # Random product
                        cursor.execute("SELECT id, name FROM clan_products ORDER BY RANDOM() LIMIT 1")
                        prod = cursor.fetchone()
                        if prod:
                            full_post_data['cross_promotion_product_id'] = prod['id']
                            full_post_data['cross_promotion_product_title'] = prod.get('name') or 'Related Products'
                            full_post_data['cross_promotion_product_position'] = 4
                            cp_changed = True
                        if cp_changed:
                            cursor.execute("""
                                UPDATE post SET 
                                    cross_promotion_category_id = %s,
                                    cross_promotion_category_title = %s,
                                    cross_promotion_product_id = %s,
                                    cross_promotion_product_title = %s,
                                    cross_promotion_category_position = %s,
                                    cross_promotion_product_position = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (
                                full_post_data.get('cross_promotion_category_id'),
                                full_post_data.get('cross_promotion_category_title'),
                                full_post_data.get('cross_promotion_product_id'),
                                full_post_data.get('cross_promotion_product_title'),
                                full_post_data.get('cross_promotion_category_position'),
                                full_post_data.get('cross_promotion_product_position'),
                                full_post_data['id']
                            ))
                            cursor.connection.commit()
                            logger.info("✅ Auto-selected random cross-promotion IDs and persisted to DB")
                
                # Build cross_promotion object
                if full_post_data.get('cross_promotion_category_id') or full_post_data.get('cross_promotion_product_id'):
                    full_post_data['cross_promotion'] = {
                        'category_id': full_post_data.get('cross_promotion_category_id'),
                        'category_title': full_post_data.get('cross_promotion_category_title', ''),
                        'product_id': full_post_data.get('cross_promotion_product_id'),
                        'product_title': full_post_data.get('cross_promotion_product_title', ''),
                        'category_position': full_post_data.get('cross_promotion_category_position'),
                        'product_position': full_post_data.get('cross_promotion_product_position'),
                        'category_widget_html': full_post_data.get('cross_promotion_category_widget_html'),
                        'product_widget_html': full_post_data.get('cross_promotion_product_widget_html')
                    }
                    # Auto-generate widget HTML if missing
                    widget_changed = False
                    cp = full_post_data['cross_promotion']
                    if cp.get('category_id') and cp.get('category_position') and not cp.get('category_widget_html'):
                        cp['category_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_category\" category_id=\"{cp.get('category_id')}\"}}}}"
                        widget_changed = True
                    if cp.get('product_id') and cp.get('product_position') and not cp.get('product_widget_html'):
                        cp['product_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_product\" product_id=\"{cp.get('product_id')}\"}}}}"
                        widget_changed = True
                    if widget_changed:
                        from config.database import db_manager as _db
                        with _db.get_cursor() as c2:
                            c2.execute("""
                                UPDATE post SET 
                                    cross_promotion_category_widget_html = %s,
                                    cross_promotion_product_widget_html = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (
                                cp.get('category_widget_html'),
                                cp.get('product_widget_html'),
                                full_post_data['id']
                            ))
                            c2.connection.commit()
                            logger.info("✅ Auto-generated widget HTML and persisted to DB")
                    logger.info(f"✅ Mapped cross-promotion: cat_id={cp.get('category_id')}, prod_id={cp.get('product_id')}")
                else:
                    logger.info("No cross-promotion data found after auto-selection attempt")
            except Exception as e:
                logger.warning(f"Cross-promotion auto-selection/generation error: {e}")
            
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
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # Get the template directory - find templates/launchpad/ relative to this file
            # clan_publisher.py is in blog-launchpad/, go up one level to root, then to templates/launchpad/
            current_dir = os.path.dirname(__file__)
            templates_dir = os.path.join(current_dir, '..', 'templates', 'launchpad')
            templates_abs = os.path.abspath(templates_dir)
            
            # Create Jinja2 environment with FileSystemLoader so it can find the template
            env = Environment(loader=FileSystemLoader(templates_abs))
            env.trim_blocks = True
            env.lstrip_blocks = True
            
            def strip_html_doc(content):
                """Strip HTML document tags and return just the content"""
                if not content:
                    return content
                # Remove DOCTYPE, html, head, body tags but preserve their content
                # CRITICAL: Only match if content starts with these tags (full document), not fragments
                import re
                content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
                # Only remove <html> wrapper if it's at the start (full document)
                # Extract content between <html> and </html> if present
                if content.strip().startswith('<html'):
                    match = re.match(r'^<html[^>]*>(.*?)</html>', content, flags=re.DOTALL)
                    if match:
                        content = match.group(1)
                # Only remove <head> if it's at the start
                if content.strip().startswith('<head'):
                    content = re.sub(r'^<head[^>]*>.*?</head>', '', content, flags=re.DOTALL)
                # Only remove <body> wrapper but preserve content
                if content.strip().startswith('<body'):
                    match = re.match(r'^<body[^>]*>(.*?)</body>', content, flags=re.DOTALL)
                    if match:
                        content = match.group(1)
                return content.strip()
            
            def strip_h2_headings(content):
                """Strip H2 headings and their content from HTML."""
                if not content:
                    return content
                import re
                content = re.sub(r'<h2[^>]*>.*?</h2>', '', content, flags=re.IGNORECASE | re.DOTALL)
                return content
            
            def is_recipe_section(value):
                """Check if a section_type value indicates a recipe section."""
                if not value:
                    return False
                return str(value).startswith('recipe_')
            
            env.filters['strip_html_doc'] = strip_html_doc
            env.filters['strip_h2_headings'] = strip_h2_headings
            env.tests['is_recipe_section'] = is_recipe_section
            
            # Load the template from the FileSystemLoader
            template = env.get_template('clan_post_raw.html')
            
            # Fix author_name if it's the literal string "author_name" (database column name)
            post_for_template = post.copy()
            if not post_for_template.get('author_name') or post_for_template.get('author_name') == 'author_name':
                # Use author from database (post.author_id) - no recipe-specific logic
                # Author should come from post.author_id via JOIN in query
                # If missing, use template default
                if not post_for_template.get('author_name'):
                    post_for_template['author_name'] = 'Caitrin Stewart'  # Template default
                    logger.info(f"Using default author_name: 'Caitrin Stewart'")
            
            # Exclude header image from HTML content (Clan.com adds it as featured image automatically)
            post_for_template['exclude_header_image'] = True
            
            # Ensure header_image is set for template
            if not post_for_template.get('header_image') or not post_for_template['header_image'].get('path'):
                logger.warning("⚠️ No header_image in post data, attempting to load from database")
                try:
                    from config.database import db_manager
                    with db_manager.get_cursor() as cursor:
                        cursor.execute('SELECT header_image_id FROM post WHERE id = %s', (post.get('id'),))
                        row = cursor.fetchone()
                        if row and row.get('header_image_id'):
                            # Load header image data from database
                            cursor.execute("""
                                SELECT id, filename, file_path as path, alt_text, caption
                                FROM images WHERE id = %s
                            """, (row['header_image_id'],))
                            img_row = cursor.fetchone()
                            if img_row and img_row.get('path'):
                                # Use optimized path
                                optimized_path = img_row['path'].replace('/raw/', '/optimized/').replace('.png', '.jpg')
                                post_for_template['header_image'] = {
                                    'path': optimized_path,
                                    'alt_text': img_row.get('alt_text'),
                                    'title': img_row.get('filename'),
                                    'caption': img_row.get('caption')
                                }
                                logger.info(f"✅ Loaded header_image from database: {optimized_path}")
                except Exception as e:
                    logger.error(f"Failed to load header_image from database: {e}")
            
            # Render using the same data used for preview to ensure exact match
            html_content = template.render(post=post_for_template, sections=sections)
            
            # Merge uploaded_images with DB mappings from section_image_mappings
            merged_uploaded_images = uploaded_images.copy() if uploaded_images else {}
            try:
                from config.database import db_manager
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT local_image_path, clan_uploaded_url 
                        FROM section_image_mappings 
                        WHERE post_id = %s AND local_image_path IS NOT NULL
                    """, (post.get('id'),))
                    db_mappings = cursor.fetchall()
                    for row in db_mappings:
                        if row.get('local_image_path') and row.get('clan_uploaded_url'):
                            merged_uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                            logger.info(f"Merged DB mapping: {row['local_image_path']} -> {row['clan_uploaded_url']}")
            except Exception as e:
                logger.warning(f"Could not load DB image mappings: {e}")
            
            logger.info(f'Final merged_uploaded_images: {merged_uploaded_images}')
            logger.info(f'uploaded_images keys: {list(merged_uploaded_images.keys()) if merged_uploaded_images else "None"}')
            
            # Translate local image/file paths to uploaded clan.com URLs
            if merged_uploaded_images:
                logger.info('Translating image paths to clan.com URLs...')
                logger.info(f'Uploaded images mapping: {uploaded_images}')
                
                # Create a comprehensive path mapping
                path_mapping = {}
                for local_path, clan_url in merged_uploaded_images.items():
                    # Add the exact path as found in uploaded_images
                    path_mapping[local_path] = clan_url
                    
                    # Also add variations that might appear in the HTML
                    if local_path.startswith('/static/'):
                        # Keep the original path
                        path_mapping[local_path] = clan_url
                        
                        # Add the path without /static/ prefix (in case HTML uses relative paths)
                        relative_path = local_path[7:]  # Remove '/static/' prefix
                        path_mapping[relative_path] = clan_url
                        logger.info(f"Added relative path mapping: {relative_path} -> {clan_url}")
                
                logger.info(f'Final path mapping: {path_mapping}')
                
                # Replace all paths in the HTML content
                # Note: Photo-harvesting URLs that were uploaded to clan.com CDN should be replaced
                replacements_made = 0
                for local_path, clan_url in path_mapping.items():
                    # If this is a Photo-harvesting URL that we uploaded, replace it with clan.com URL
                    # If it's NOT in our mapping, it means upload failed, so we'll leave it as-is
                    if local_path.startswith(('http://', 'https://')):
                        logger.info(f"🔄 Replacing Photo-harvesting URL (uploaded to CDN): {local_path} -> {clan_url}")
                        # Continue to replacement logic below
                    
                    # For Photo-harvesting URLs, we need to match the base URL without query params
                    # because the template might use a different sized URL than what we uploaded with
                    if local_path.startswith(('http://', 'https://')):
                        # Extract base URL (without query parameters) for matching
                        from urllib.parse import urlparse
                        base_url = urlparse(local_path).scheme + '://' + urlparse(local_path).netloc + urlparse(local_path).path
                        
                        # Find all src attributes with this base URL (with any query params)
                        import re
                        pattern = re.compile(r'src="(' + re.escape(base_url) + r'[^"]*)"')
                        matches = pattern.findall(html_content)
                        if matches:
                            for match in set(matches):  # Use set to avoid duplicate replacements
                                html_content = html_content.replace(f'src="{match}"', f'src="{clan_url}"')
                                replacements_made += 1
                                logger.info(f"Replaced Photo-harvesting src (base URL match): {match[:80]}... -> {clan_url}")
                    else:
                        # For local paths, use exact matching
                        # Replace src attributes
                        if f'src="{local_path}"' in html_content:
                            html_content = html_content.replace(f'src="{local_path}"', f'src="{clan_url}"')
                            replacements_made += 1
                            logger.info(f"Replaced src: {local_path} -> {clan_url}")
                        # Replace href attributes  
                        if f'href="{local_path}"' in html_content:
                            html_content = html_content.replace(f'href="{local_path}"', f'href="{clan_url}"')
                            replacements_made += 1
                            logger.info(f"Replaced href: {local_path} -> {clan_url}")
                        # Replace any other occurrences (but count them)
                        if local_path in html_content and local_path not in clan_url:
                            before_count = html_content.count(local_path)
                            html_content = html_content.replace(local_path, clan_url)
                            after_count = html_content.count(local_path)
                            if after_count < before_count:
                                replacements_made += (before_count - after_count)
                                logger.info(f"Replaced {before_count - after_count} occurrences: {local_path} -> {clan_url}")
                
                # Diagnostic: Check if any /static/ paths remain
                import re
                remaining_static = re.findall(r'/static/content/posts/\d+/sections/\d+/optimized/\d+\.jpg', html_content)
                if remaining_static:
                    logger.warning(f"⚠️ After replacement, {len(remaining_static)} /static/ paths remain in HTML:")
                    for path in set(remaining_static):
                        logger.warning(f"  Remaining path: {path}")
                    logger.warning(f"  Available mapping keys: {list(path_mapping.keys())}")
                else:
                    logger.info(f"✅ All image paths replaced successfully. Made {replacements_made} replacements.")
            
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
