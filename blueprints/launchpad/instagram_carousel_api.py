# blueprints/launchpad/instagram_carousel_api.py
"""Instagram Graph API posting functions for carousels."""

import logging
import os
import requests
from datetime import datetime
from config.database import db_manager

logger = logging.getLogger(__name__)

def get_instagram_credentials():
    """Get Instagram credentials from platform_credentials table."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT credential_key, credential_value
                FROM platform_credentials 
                WHERE platform_id = (SELECT id FROM platforms WHERE name = 'instagram')
                AND is_active = true
            """)
            credentials = cursor.fetchall()
            
            if not credentials:
                return None
            
            creds = {}
            for cred in credentials:
                creds[cred['credential_key']] = cred['credential_value']
            
            return creds
    except Exception as e:
        logger.error(f"Error getting Instagram credentials: {e}")
        return None

def get_instagram_business_account_id(page_id, access_token):
    """Get Instagram Business Account ID from Facebook Page."""
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': access_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'instagram_business_account' in data:
                return data['instagram_business_account']['id']
        else:
            logger.error(f"Failed to get Instagram Business Account: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting Instagram Business Account ID: {e}")
        return None

def upload_image_to_instagram(image_path, ig_business_account_id, access_token, base_url='http://localhost:5000'):
    """
    Upload image to Instagram and return container ID.
    
    Note: Images must be publicly accessible URLs. For local files, they need to be
    served from a public URL (e.g., through static file serving).
    """
    try:
        # Check if image_path is a local file - if so, convert to public URL
        if os.path.exists(image_path):
            # Convert local path to URL path
            if 'static/content' in image_path:
                url_path = '/' + image_path.split('static/', 1)[1]
                image_url = f"{base_url}{url_path}"
            else:
                logger.error(f"Cannot convert local path to URL: {image_path}")
                return None
        else:
            # Assume it's already a URL
            image_url = image_path
        
        # Create media container for single image
        url = f"https://graph.facebook.com/v18.0/{ig_business_account_id}/media"
        params = {
            'image_url': image_url,
            'access_token': access_token
        }
        
        response = requests.post(url, data=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('id')  # Container ID
        else:
            logger.error(f"Failed to upload image to Instagram: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading image to Instagram: {e}")
        return None

def create_instagram_carousel(container_ids, caption, ig_business_account_id, access_token, scheduled_time=None):
    """
    Create Instagram carousel post from container IDs.
    
    Args:
        container_ids: List of media container IDs (one per slide)
        caption: Caption text
        ig_business_account_id: Instagram Business Account ID
        access_token: Access token
        scheduled_time: Optional datetime for scheduling (Unix timestamp)
    
    Returns:
        dict with success status and post ID
    """
    try:
        if not container_ids:
            return {'success': False, 'error': 'No container IDs provided'}
        
        if len(container_ids) > 10:
            return {'success': False, 'error': 'Instagram carousel supports max 10 images'}
        
        # Create carousel container
        url = f"https://graph.facebook.com/v18.0/{ig_business_account_id}/media"
        params = {
            'media_type': 'CAROUSEL',
            'children': ','.join(container_ids),
            'caption': caption[:2200],  # Instagram caption limit
            'access_token': access_token
        }
        
        # Add scheduling if provided
        if scheduled_time:
            if isinstance(scheduled_time, datetime):
                scheduled_time = int(scheduled_time.timestamp())
            params['published'] = 'false'
            params['scheduled_publish_time'] = scheduled_time
        
        response = requests.post(url, data=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            creation_id = data.get('id')
            
            # If not scheduled, publish immediately
            if not scheduled_time:
                publish_result = publish_instagram_media(creation_id, ig_business_account_id, access_token)
                if publish_result['success']:
                    return {
                        'success': True,
                        'post_id': publish_result.get('post_id'),
                        'creation_id': creation_id
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to publish: {publish_result.get("error")}',
                        'creation_id': creation_id
                    }
            else:
                return {
                    'success': True,
                    'creation_id': creation_id,
                    'scheduled_time': scheduled_time
                }
        else:
            logger.error(f"Failed to create carousel container: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'API error: {response.status_code} - {response.text}'
            }
            
    except Exception as e:
        logger.error(f"Error creating Instagram carousel: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

def publish_instagram_media(creation_id, ig_business_account_id, access_token):
    """Publish a created media container."""
    try:
        url = f"https://graph.facebook.com/v18.0/{ig_business_account_id}/media_publish"
        params = {
            'creation_id': creation_id,
            'access_token': access_token
        }
        
        response = requests.post(url, data=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'post_id': data.get('id')
            }
        else:
            logger.error(f"Failed to publish media: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'API error: {response.status_code}'
            }
    except Exception as e:
        logger.error(f"Error publishing Instagram media: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def post_instagram_carousel(post_id, queue_item_id=None):
    """
    Post Instagram carousel for a blog post.
    
    Args:
        post_id: Post ID
        queue_item_id: Optional queue item ID for updating status
    
    Returns:
        dict with success status and Instagram post ID
    """
    try:
        from blueprints.launchpad.instagram_carousel import generate_instagram_caption
        
        # Get carousel slides
        carousel_dir = os.path.join('static', 'content', 'posts', str(post_id), 'instagram', 'carousel')
        if not os.path.exists(carousel_dir):
            return {
                'success': False,
                'error': 'Carousel not generated yet'
            }
        
        # Get slide files in order
        slide_files = []
        for filename in sorted(os.listdir(carousel_dir)):
            if filename.endswith('.jpg') and filename[0:2].isdigit():
                slide_path = os.path.join(carousel_dir, filename)
                slide_files.append(slide_path)
        
        if not slide_files:
            return {
                'success': False,
                'error': 'No carousel slides found'
            }
        
        # Get caption from queue or generate
        caption = None
        scheduled_timestamp = None
        if queue_item_id:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT generated_content, scheduled_timestamp
                    FROM posting_queue
                    WHERE id = %s
                """, (queue_item_id,))
                queue_item = cursor.fetchone()
                if queue_item:
                    caption = queue_item['generated_content']
                    scheduled_timestamp = queue_item['scheduled_timestamp']
        
        if not caption:
            # Generate caption
            caption_result = generate_instagram_caption(post_id)
            if caption_result['success']:
                caption = caption_result.get('caption', '')
        
        if not caption:
            caption = "Read the full article on our blog — link in bio 🔗"
        
        # Get Instagram credentials
        # First try Instagram-specific credentials
        instagram_creds = get_instagram_credentials()
        
        # If not found, try getting from Facebook Page (same Meta account)
        if not instagram_creds or not instagram_creds.get('access_token'):
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT credential_key, credential_value
                    FROM platform_credentials 
                    WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND credential_key IN ('page_access_token', 'page_id')
                    AND is_active = true
                """)
                fb_creds = {row['credential_key']: row['credential_value'] for row in cursor.fetchall()}
                
                if fb_creds.get('page_access_token') and fb_creds.get('page_id'):
                    access_token = fb_creds['page_access_token']
                    page_id = fb_creds['page_id']
                    
                    # Get Instagram Business Account ID from Facebook Page
                    ig_business_account_id = get_instagram_business_account_id(page_id, access_token)
                    
                    if not ig_business_account_id:
                        return {
                            'success': False,
                            'error': 'Could not get Instagram Business Account ID from Facebook Page'
                        }
                else:
                    return {
                        'success': False,
                        'error': 'No Instagram or Facebook credentials found'
                    }
        else:
            access_token = instagram_creds.get('access_token')
            ig_business_account_id = instagram_creds.get('ig_business_account_id')
            
            if not ig_business_account_id:
                return {
                    'success': False,
                    'error': 'Instagram Business Account ID not configured'
                }
        
        # Upload images and get container IDs
        container_ids = []
        for slide_path in slide_files:
            container_id = upload_image_to_instagram(slide_path, ig_business_account_id, access_token)
            if container_id:
                container_ids.append(container_id)
            else:
                logger.error(f"Failed to upload slide: {slide_path}")
        
        if not container_ids:
            return {
                'success': False,
                'error': 'Failed to upload any carousel images'
            }
        
        # Create and publish carousel
        carousel_result = create_instagram_carousel(
            container_ids,
            caption,
            ig_business_account_id,
            access_token,
            scheduled_time=scheduled_timestamp
        )
        
        if carousel_result['success']:
            # Update queue status
            if queue_item_id:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE posting_queue
                        SET status = 'published',
                            platform_post_id = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (carousel_result.get('post_id') or carousel_result.get('creation_id'), queue_item_id))
                    conn = cursor.connection
                    conn.commit()
        
        return carousel_result
        
    except Exception as e:
        logger.error(f"Error posting Instagram carousel: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

