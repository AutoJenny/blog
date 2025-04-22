from datetime import datetime
import os
import logging
import requests
from flask import current_app
from bs4 import BeautifulSoup
from app.models import Post, Image
from app import db

class SyndicationError(Exception):
    """Custom exception for syndication-related errors."""
    pass

def prepare_content_for_syndication(post):
    """
    Prepare post content for syndication by processing HTML content.
    
    Args:
        post (Post): The post to prepare
        
    Returns:
        str: Processed HTML content ready for syndication
    """
    # Parse HTML content
    soup = BeautifulSoup(post.content, 'html.parser')
    
    # Remove any unwanted elements (comments, navigation, etc.)
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
        
    # Process images to use full URLs
    image_base_url = current_app.config['CLAN_IMAGE_BASE_URL']
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and src.startswith('/'):
            img['src'] = f"{image_base_url.rstrip('/')}{src}"
            
    return str(soup)

def prepare_api_args(post):
    """
    Prepare arguments for the clan.com API.
    
    Args:
        post (Post): The post to prepare arguments for
        
    Returns:
        dict: API arguments
    """
    # Get category IDs from config (fallback to defaults if not set)
    default_categories = current_app.config.get('CLAN_DEFAULT_CATEGORIES', [14, 15])
    
    # Prepare header image URL
    header_image_url = None
    if post.header_image:
        header_image_url = f"{current_app.config['CLAN_IMAGE_BASE_URL']}{post.header_image.url}"
    
    return {
        'title': post.title,
        'content': prepare_content_for_syndication(post),
        'summary': post.summary,
        'categories': default_categories,
        'header_image_url': header_image_url,
        'published_at': post.published_at.isoformat() if post.published_at else None,
        'author': post.author.name if post.author else None
    }

def call_clan_api(endpoint, method='POST', **kwargs):
    """
    Make a call to the clan.com API.
    
    Args:
        endpoint (str): API endpoint to call
        method (str): HTTP method to use
        **kwargs: Additional arguments for requests
        
    Returns:
        dict: API response
        
    Raises:
        SyndicationError: If the API call fails
    """
    api_base_url = current_app.config['CLAN_API_BASE_URL']
    api_key = current_app.config['CLAN_API_KEY']
    api_user = current_app.config['CLAN_API_USER']
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'X-API-User': api_user
    }
    
    try:
        response = requests.request(
            method,
            f"{api_base_url.rstrip('/')}/{endpoint.lstrip('/')}",
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise SyndicationError(f"API call failed: {str(e)}")

def syndicate_post(post):
    """
    Syndicate a post to clan.com.
    
    Args:
        post (Post): The post to syndicate
        
    Raises:
        SyndicationError: If syndication fails
    """
    if not post.published:
        raise SyndicationError("Cannot syndicate unpublished post")
        
    try:
        # Prepare API arguments
        api_args = prepare_api_args(post)
        
        # Check if post already exists on clan.com
        if post.clan_post_id:
            # Update existing post
            response = call_clan_api(
                f'posts/{post.clan_post_id}',
                method='PUT',
                json=api_args
            )
        else:
            # Create new post
            response = call_clan_api(
                'posts',
                json=api_args
            )
            
            # Store clan.com post ID
            post.clan_post_id = response['id']
            db.session.commit()
            
        current_app.logger.info(f"Successfully syndicated post {post.id} to clan.com (clan_post_id: {post.clan_post_id})")
        
    except Exception as e:
        raise SyndicationError(f"Failed to syndicate post: {str(e)}")

def remove_syndicated_post(post):
    """
    Remove a syndicated post from clan.com.
    
    Args:
        post (Post): The post to remove
        
    Raises:
        SyndicationError: If removal fails
    """
    if not post.clan_post_id:
        raise SyndicationError("Post is not syndicated")
        
    try:
        # Call API to delete post
        call_clan_api(f'posts/{post.clan_post_id}', method='DELETE')
        
        # Clear clan.com post ID
        post.clan_post_id = None
        db.session.commit()
        
        current_app.logger.info(f"Successfully removed post {post.id} from clan.com")
        
    except Exception as e:
        raise SyndicationError(f"Failed to remove syndicated post: {str(e)}") 