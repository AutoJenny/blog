#!/usr/bin/env python3
"""
Facebook Token Refresh Script
Automatically refreshes Facebook page access tokens using the User → Page Token method.
"""

import requests
import logging
import sys
import os
from datetime import datetime, timedelta
from config.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/facebook_token_refresh.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Facebook Graph API configuration
GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
FACEBOOK_APP_ID = "1441086457156585"
FACEBOOK_APP_SECRET = "014f104b58439c559638232df045bf8a"

# Page IDs
PAGE_IDS = {
    'scotweb_clan': '196935752675',
    'clan_by_scotweb': '108385661622841'
}

def get_long_lived_user_token(app_id, app_secret, short_user_token):
    """Exchange short-lived user token for long-lived user token (~60 days)."""
    try:
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_user_token,
        }
        
        response = requests.get(f"{GRAPH_API_BASE}/oauth/access_token", params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        long_lived_token = result["access_token"]
        
        logger.info(f"Successfully obtained long-lived user token (expires in ~60 days)")
        return long_lived_token
        
    except Exception as e:
        logger.error(f"Failed to get long-lived user token: {e}")
        raise

def get_page_token_from_user_token(user_token, page_id):
    """Get page access token from user token for specific page."""
    try:
        # Method 1: Get all pages and find the specific one
        response = requests.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": user_token},
            timeout=30
        )
        response.raise_for_status()
        
        pages = response.json().get("data", [])
        for page in pages:
            if page.get("id") == str(page_id):
                page_token = page.get("access_token")
                page_name = page.get("name", "Unknown")
                logger.info(f"Found page token for {page_name} (ID: {page_id})")
                return page_token
        
        # Method 2: Direct page query if not found in accounts
        logger.warning(f"Page {page_id} not found in /me/accounts, trying direct query")
        response = requests.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "access_token", "access_token": user_token},
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        page_token = result.get("access_token")
        
        if page_token:
            logger.info(f"Successfully obtained page token for page {page_id}")
            return page_token
        else:
            raise Exception(f"No access_token found in response for page {page_id}")
            
    except Exception as e:
        logger.error(f"Failed to get page token for page {page_id}: {e}")
        raise

def update_database_tokens(page_tokens):
    """Update database with new page tokens."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update page_access_token (Scotweb CLAN)
                if 'scotweb_clan' in page_tokens:
                    cursor.execute("""
                        UPDATE platform_credentials 
                        SET credential_value = %s, updated_at = NOW(), last_refreshed_at = NOW()
                        WHERE credential_key = 'page_access_token' AND platform_id = (
                            SELECT id FROM platforms WHERE name = 'facebook'
                        )
                    """, (page_tokens['scotweb_clan'],))
                    logger.info("Updated page_access_token in database")
                
                # Update page_access_token_2 (CLAN by Scotweb)
                if 'clan_by_scotweb' in page_tokens:
                    cursor.execute("""
                        UPDATE platform_credentials 
                        SET credential_value = %s, updated_at = NOW(), last_refreshed_at = NOW()
                        WHERE credential_key = 'page_access_token_2' AND platform_id = (
                            SELECT id FROM platforms WHERE name = 'facebook'
                        )
                    """, (page_tokens['clan_by_scotweb'],))
                    logger.info("Updated page_access_token_2 in database")
                
                conn.commit()
                logger.info("Database tokens updated successfully")
                
    except Exception as e:
        logger.error(f"Failed to update database tokens: {e}")
        raise

def get_current_user_token():
    """Get current user token from database."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # First check what credentials exist
                cursor.execute("""
                    SELECT credential_key, credential_value 
                    FROM platform_credentials 
                    WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                
                all_creds = cursor.fetchall()
                logger.info(f"Found {len(all_creds)} Facebook credentials in database")
                for cred in all_creds:
                    logger.info(f"  {cred['credential_key']}: {cred['credential_value'][:20]}...")
                
                # Now get the user token specifically
                cursor.execute("""
                    SELECT credential_value 
                    FROM platform_credentials 
                    WHERE credential_key = 'user_access_token' 
                    AND platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                
                result = cursor.fetchone()
                if result and result['credential_value']:
                    logger.info(f"Found user access token: {result['credential_value'][:20]}...")
                    return result['credential_value']
                else:
                    raise Exception("No active user access token found in database")
                    
    except Exception as e:
        logger.error(f"Failed to get current user token: {e}")
        raise

def refresh_facebook_tokens():
    """Main function to refresh all Facebook tokens."""
    try:
        logger.info("Starting Facebook token refresh process")
        
        # Get current user token
        user_token = get_current_user_token()
        logger.info("Retrieved current user token from database")
        
        # Get long-lived user token
        long_lived_token = get_long_lived_user_token(
            FACEBOOK_APP_ID, 
            FACEBOOK_APP_SECRET, 
            user_token
        )
        
        # Get page tokens for both pages
        page_tokens = {}
        
        for page_name, page_id in PAGE_IDS.items():
            try:
                page_token = get_page_token_from_user_token(long_lived_token, page_id)
                page_tokens[page_name] = page_token
                logger.info(f"Successfully obtained token for {page_name} (ID: {page_id})")
            except Exception as e:
                logger.error(f"Failed to get token for {page_name}: {e}")
                # Continue with other pages even if one fails
        
        if not page_tokens:
            raise Exception("No page tokens were successfully obtained")
        
        # Update database
        update_database_tokens(page_tokens)
        
        logger.info("Facebook token refresh completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Facebook token refresh failed: {e}")
        return False

def test_posting_to_pages():
    """Test posting to both pages to verify tokens work."""
    try:
        logger.info("Testing posting to both Facebook pages")
        
        # Get current page tokens from database
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT credential_key, credential_value 
                    FROM platform_credentials 
                    WHERE credential_key IN ('page_access_token', 'page_access_token_2')
                    AND platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                
                tokens = {row['credential_key']: row['credential_value'] for row in cursor.fetchall()}
        
        # Test post content
        test_message = f"🔧 Token refresh test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Test posting to both pages
        for page_name, page_id in PAGE_IDS.items():
            token_key = 'page_access_token' if page_name == 'scotweb_clan' else 'page_access_token_2'
            page_token = tokens.get(token_key)
            
            if not page_token:
                logger.error(f"No token found for {page_name}")
                continue
            
            try:
                # Post test message
                response = requests.post(
                    f"{GRAPH_API_BASE}/{page_id}/feed",
                    data={
                        "message": test_message,
                        "access_token": page_token
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    post_id = result.get('id')
                    logger.info(f"✅ Test post successful for {page_name} (Post ID: {post_id})")
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"❌ Test post failed for {page_name}: {response.status_code} - {error_msg}")
                    
            except Exception as e:
                logger.error(f"❌ Test post error for {page_name}: {e}")
        
        logger.info("Test posting completed")
        
    except Exception as e:
        logger.error(f"Failed to test posting: {e}")

if __name__ == "__main__":
    # Check if we have required environment variables
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        logger.error("FACEBOOK_APP_ID and FACEBOOK_APP_SECRET environment variables are required")
        sys.exit(1)
    
    # Refresh tokens
    success = refresh_facebook_tokens()
    
    if success:
        # Test posting to both pages
        test_posting_to_pages()
        logger.info("Facebook token refresh and testing completed successfully")
    else:
        logger.error("Facebook token refresh failed")
        sys.exit(1)
