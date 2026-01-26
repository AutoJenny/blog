"""
Platform Publishers
-------------------

Simple platform-specific publishing functions. These functions assume that
scheduled dates have already been validated by the centralized scheduler.
They only handle the actual publishing logic for each platform.

All functions take a queue_id and return a dict with success status.
"""

import os
import sys
import time
import logging
import requests
from typing import Dict
from datetime import datetime

from config.database import db_manager
from utils.posting_queue_helpers import get_posting_queue_row

logger = logging.getLogger(__name__)


def format_message_for_facebook(message_text: str) -> str:
    """
    Format message text with extra line breaks for better Facebook display.
    
    Adds line breaks:
    - After em dashes (—) followed by text
    - Between sentences (period followed by capital letter, with or without existing newline)
    
    Example:
    "We answer the phone ourselves — via freephone in the UK and toll-free in the US.
    There's no charge for calling, and no automated systems."
    
    Becomes:
    "We answer the phone ourselves — 
    
    via freephone in the UK and toll-free in the US.
    
    There's no charge for calling, and no automated systems."
    """
    import re
    
    # Start with the original text
    formatted = message_text
    
    # Add line break after em dash followed by space and lowercase letter
    # Pattern: "— " followed by lowercase letter -> "— \n\n" 
    formatted = re.sub(r'— ([a-z])', r'— \n\n\1', formatted)
    
    # Add line break after period followed by newline and capital letter
    # Pattern: ".\n" followed by capital letter -> ".\n\n" followed by capital letter
    formatted = re.sub(r'\.\n([A-Z])', r'.\n\n\1', formatted)
    
    # Add line break after period-space-capital letter (sentence boundary without newline)
    # Pattern: ". " followed by capital letter -> ".\n\n" followed by capital letter
    formatted = re.sub(r'\. ([A-Z])', r'.\n\n\1', formatted)
    
    # Clean up any triple or more newlines (normalize to double)
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # Ensure it ends cleanly
    formatted = formatted.strip()
    
    return formatted


def publish_to_facebook(queue_id: int) -> Dict:
    """
    Publish post to Facebook (both pages).
    
    Assumes scheduled date/time has already been validated by the scheduler.
    Supports both weekly content and product posts.
    
    Parameters
    ----------
    queue_id:
        posting_queue.id of the post to publish.
    
    Returns
    -------
    Dict with:
    {
        'success': bool,
        'platform_post_id': str or None,
        'message': str,
        'platform_post_ids': list,  # All successful post IDs
        'error': str or None
    }
    """
    try:
        # Get posting_queue row
        queue_row = get_posting_queue_row(queue_id)
        if not queue_row:
            return {
                "success": False,
                "error": "Posting queue row not found"
            }
        
        content_type = queue_row.get('content_type')
        
        # For message posts, use text-only posting
        if content_type == 'message':
            # Get message text (preserve line breaks)
            message_text = queue_row.get('generated_content', '')
            if not message_text:
                return {
                    "success": False,
                    "error": "Message content not found"
                }
            
            # Format message text with extra line breaks for better Facebook display
            # Add line breaks after em dashes and between sentences for better readability
            formatted_message = format_message_for_facebook(message_text)
            
            # Get Facebook credentials for both pages
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT credential_key, credential_value
                    FROM platform_credentials 
                    WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                credentials = cursor.fetchall()
            
            # Convert to dictionary
            creds = {}
            for cred in credentials:
                creds[cred['credential_key']] = cred['credential_value']
            
            # Define both pages to post to
            pages_to_post = []
            
            # Page 1 (Scotweb CLAN)
            if creds.get('page_access_token') and creds.get('page_id'):
                pages_to_post.append({
                    'page_id': creds['page_id'],
                    'access_token': creds['page_access_token'],
                    'name': 'Scotweb CLAN'
                })
            
            # Page 2 (CLAN by Scotweb) - only add if different from Page 1
            if (creds.get('page_access_token_2') and creds.get('page_id_2') and 
                creds.get('page_id_2') != creds.get('page_id')):
                pages_to_post.append({
                    'page_id': creds['page_id_2'],
                    'access_token': creds['page_access_token_2'],
                    'name': 'CLAN by Scotweb'
                })
            elif creds.get('page_id_2') == creds.get('page_id'):
                logger.warning("Both Facebook pages have the same page_id - skipping duplicate posting to prevent double posts")
            
            if not pages_to_post:
                return {
                    "success": False,
                    "error": "No Facebook pages configured"
                }
            
            # Post to both pages using /feed endpoint for text-only posts
            results = []
            successful_posts = []
            failed_posts = []
            
            for page in pages_to_post:
                feed_url = f"https://graph.facebook.com/v18.0/{page['page_id']}/feed"
                feed_payload = {
                    'message': formatted_message,  # Formatted with extra line breaks for better display
                    'published': True,
                    'access_token': page['access_token']
                }
                
                logger.info(f"Posting text-only message to {page['name']} (Page ID: {page['page_id']})")
                logger.info(f"Message: {message_text[:100]}...")
                
                try:
                    response = requests.post(feed_url, data=feed_payload, timeout=30)
                    logger.info(f"Facebook API response - Status: {response.status_code}")
                    logger.info(f"Facebook API response - Content: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        fb_post_id = result.get('id')
                        successful_posts.append(fb_post_id)
                        results.append({
                            'page_name': page['name'],
                            'page_id': page['page_id'],
                            'post_id': fb_post_id,
                            'success': True
                        })
                    else:
                        error_data = response.json() if response.content else {}
                        error_msg = error_data.get('error', {}).get('message', 'Unknown Facebook API error')
                        failed_posts.append(f"{page['name']}: {error_msg}")
                        results.append({
                            'page_name': page['name'],
                            'page_id': page['page_id'],
                            'success': False,
                            'error': error_msg
                        })
                except Exception as e:
                    error_msg = str(e)
                    failed_posts.append(f"{page['name']}: {error_msg}")
                    logger.error(f"Error posting to {page['name']}: {e}")
                    results.append({
                        'page_name': page['name'],
                        'page_id': page['page_id'],
                        'success': False,
                        'error': error_msg
                    })
            
            # Return result (status update handled by scheduler)
            if successful_posts:
                platform_post_id_str = str(successful_posts[0])
                
                if len(failed_posts) == 0:
                    return {
                        "success": True,
                        "message": f"Successfully posted to {len(successful_posts)} page(s)",
                        "platform_post_id": platform_post_id_str,
                        "platform_post_ids": successful_posts,
                        "results": results
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Posted to {len(successful_posts)} page(s), failed on {len(failed_posts)}: {', '.join(failed_posts)}",
                        "platform_post_id": platform_post_id_str,
                        "platform_post_ids": successful_posts,
                        "results": results,
                        "warnings": failed_posts
                    }
            else:
                # All posts failed
                return {
                    "success": False,
                    "error": f"Failed to post to all pages: {', '.join(failed_posts)}",
                    "results": results
                }
        
        # For image posts (weekly content, products)
        # Get generated image and caption
        image_path = queue_row.get('image_path')
        caption = queue_row.get('generated_caption')
        
        if not image_path or not caption:
            return {
                "success": False,
                "error": "Image or caption not generated"
            }
        
        # Handle image URL conversion based on content type
        if content_type == 'product':
            # Product posts: image_path is already a URL (product_image_url)
            # Check if it's a full URL or needs conversion
            if image_path.startswith('http://') or image_path.startswith('https://'):
                image_url = image_path
            else:
                # Might be a relative path, try to construct full URL
                # Product images are typically on clan.com CDN already
                if 'clan.com' in image_path or 'clan-products' in image_path:
                    image_url = image_path if image_path.startswith('http') else f"https://{image_path}"
                else:
                    # Fallback: assume it's a clan.com product image
                    image_url = f"https://clan.com{image_path}" if image_path.startswith('/') else f"https://clan.com/{image_path}"
            
            logger.info(f"Using product image URL: {image_url}")
        
        else:
            # Weekly content: Upload image to clan.com CDN
            try:
                # Add blog-launchpad to path if needed
                blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad')
                if blog_launchpad_path not in sys.path:
                    sys.path.insert(0, blog_launchpad_path)
                from clan_publisher import ClanPublisher
                publisher = ClanPublisher()
                
                # Generate a unique filename for the weekly content image
                filename = f"weekly_content_{queue_row.get('idea_id', 'unknown')}_{int(time.time())}.png"
                
                logger.info(f"Uploading weekly content image to clan.com: {image_path}")
                uploaded_url = publisher.upload_image(image_path, filename)
                
                if not uploaded_url:
                    return {
                        "success": False,
                        "error": "Failed to upload image to clan.com CDN"
                    }
                
                logger.info(f"Image uploaded successfully to: {uploaded_url}")
                image_url = uploaded_url
                
            except ImportError:
                # Fallback: try to use static URL if ClanPublisher not available
                logger.warning("ClanPublisher not available, falling back to static URL")
                if os.path.exists(image_path):
                    # Extract relative path from static/
                    if 'static/' in image_path:
                        relative_path = image_path.split('static/', 1)[1]
                        # Use production domain
                        base_url = 'https://clan.com'
                        image_url = f"{base_url}/static/{relative_path}"
                    else:
                        return {
                            "success": False,
                            "error": f"Cannot convert image path to URL: {image_path}"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"Image file not found: {image_path}"
                    }
            except Exception as e:
                logger.error(f"Error uploading image to clan.com: {e}")
                return {
                    "success": False,
                    "error": f"Failed to upload image: {str(e)}"
                }
        
        # Get Facebook credentials for both pages
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT credential_key, credential_value
                FROM platform_credentials 
                WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                AND is_active = true
            """)
            credentials = cursor.fetchall()
        
        # Convert to dictionary
        creds = {}
        for cred in credentials:
            creds[cred['credential_key']] = cred['credential_value']
        
        # Define both pages to post to
        pages_to_post = []
        
        # Page 1 (Scotweb CLAN)
        if creds.get('page_access_token') and creds.get('page_id'):
            pages_to_post.append({
                'page_id': creds['page_id'],
                'access_token': creds['page_access_token'],
                'name': 'Scotweb CLAN'
            })
        
        # Page 2 (CLAN by Scotweb) - only add if different from Page 1
        if (creds.get('page_access_token_2') and creds.get('page_id_2') and 
            creds.get('page_id_2') != creds.get('page_id')):
            pages_to_post.append({
                'page_id': creds['page_id_2'],
                'access_token': creds['page_access_token_2'],
                'name': 'CLAN by Scotweb'
            })
        elif creds.get('page_id_2') == creds.get('page_id'):
            logger.warning("Both Facebook pages have the same page_id - skipping duplicate posting to prevent double posts")
        
        if not pages_to_post:
            return {
                "success": False,
                "error": "No Facebook pages configured"
            }
        
        # Post to both pages using /photos endpoint for image posts
        results = []
        successful_posts = []
        failed_posts = []
        
        for page in pages_to_post:
            photos_url = f"https://graph.facebook.com/v18.0/{page['page_id']}/photos"
            photos_payload = {
                'url': image_url,
                'caption': caption,
                'published': True,
                'access_token': page['access_token']
            }
            
            logger.info(f"Posting to {page['name']} (Page ID: {page['page_id']})")
            logger.info(f"Image URL: {image_url}")
            logger.info(f"Caption: {caption[:50]}...")
            
            try:
                response = requests.post(photos_url, data=photos_payload, timeout=30)
                logger.info(f"Facebook API response - Status: {response.status_code}")
                logger.info(f"Facebook API response - Content: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    fb_post_id = result.get('id')
                    successful_posts.append(fb_post_id)
                    results.append({
                        'page_name': page['name'],
                        'page_id': page['page_id'],
                        'post_id': fb_post_id,
                        'success': True
                    })
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', {}).get('message', 'Unknown Facebook API error')
                    failed_posts.append(f"{page['name']}: {error_msg}")
                    results.append({
                        'page_name': page['name'],
                        'page_id': page['page_id'],
                        'success': False,
                        'error': error_msg
                    })
            except Exception as e:
                error_msg = str(e)
                failed_posts.append(f"{page['name']}: {error_msg}")
                logger.error(f"Error posting to {page['name']}: {e}")
                results.append({
                    'page_name': page['name'],
                    'page_id': page['page_id'],
                    'success': False,
                    'error': error_msg
                })
        
        # Return result (status update handled by scheduler)
        if successful_posts:
            platform_post_id_str = str(successful_posts[0])
            
            if len(failed_posts) == 0:
                return {
                    "success": True,
                    "message": f"Successfully posted to {len(successful_posts)} page(s)",
                    "platform_post_id": platform_post_id_str,
                    "platform_post_ids": successful_posts,
                    "results": results
                }
            else:
                return {
                    "success": True,
                    "message": f"Posted to {len(successful_posts)} page(s), failed on {len(failed_posts)}: {', '.join(failed_posts)}",
                    "platform_post_id": platform_post_id_str,
                    "platform_post_ids": successful_posts,
                    "results": results,
                    "warnings": failed_posts
                }
        else:
            # All posts failed
            return {
                "success": False,
                "error": f"Failed to post to all pages: {', '.join(failed_posts)}",
                "results": results
            }
        
    except Exception as e:
        logger.error(f"Error publishing to Facebook: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def publish_to_instagram(queue_id: int) -> Dict:
    """
    Publish post to Instagram.
    
    Assumes scheduled date/time has already been validated by the scheduler.
    Currently not implemented.
    
    Parameters
    ----------
    queue_id:
        posting_queue.id of the post to publish.
    
    Returns
    -------
    Dict with success=False and error message.
    """
    logger.warning(f"Instagram posting not yet implemented for queue_id {queue_id}")
    return {
        'success': False,
        'error': 'Instagram posting is not yet implemented'
    }


def publish_to_twitter(queue_id: int) -> Dict:
    """
    Publish post to Twitter.
    
    Assumes scheduled date/time has already been validated by the scheduler.
    Currently not implemented.
    
    Parameters
    ----------
    queue_id:
        posting_queue.id of the post to publish.
    
    Returns
    -------
    Dict with success=False and error message.
    """
    logger.warning(f"Twitter posting not yet implemented for queue_id {queue_id}")
    return {
        'success': False,
        'error': 'Twitter posting is not yet implemented'
    }


def publish_to_linkedin(queue_id: int) -> Dict:
    """
    Publish post to LinkedIn.
    
    Assumes scheduled date/time has already been validated by the scheduler.
    Currently not implemented.
    
    Parameters
    ----------
    queue_id:
        posting_queue.id of the post to publish.
    
    Returns
    -------
    Dict with success=False and error message.
    """
    logger.warning(f"LinkedIn posting not yet implemented for queue_id {queue_id}")
    return {
        'success': False,
        'error': 'LinkedIn posting is not yet implemented'
    }
