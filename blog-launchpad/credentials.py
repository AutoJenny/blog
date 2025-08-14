#!/usr/bin/env python3
"""
Simple credentials manager for Clan.com API
"""

import os

def get_clan_credentials():
    """Get Clan.com API credentials from environment or config file"""
    
    # Try environment variables first
    api_key = os.getenv('CLAN_API_KEY')
    api_user = os.getenv('CLAN_API_USER', 'blog')
    api_base_url = os.getenv('CLAN_API_BASE_URL', 'https://clan.com/clan/blog_api/')
    
    # If no API key in environment, try to load from config file
    if not api_key:
        config_file = os.path.join(os.path.dirname(__file__), '.clan_credentials')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == 'CLAN_API_KEY':
                                    api_key = value.strip()
                                elif key.strip() == 'CLAN_API_USER':
                                    api_user = value.strip()
                                elif key.strip() == 'CLAN_API_BASE_URL':
                                    api_base_url = value.strip()
            except Exception as e:
                print(f"Error reading credentials file: {e}")
    
    return {
        'api_key': api_key,
        'api_user': api_user,
        'api_base_url': api_base_url
    }

def set_credentials(api_key, api_user='blog', api_base_url='https://clan.com/clan/blog_api/'):
    """Set credentials in environment variables"""
    os.environ['CLAN_API_KEY'] = api_key
    os.environ['CLAN_API_USER'] = api_user
    os.environ['CLAN_API_BASE_URL'] = api_base_url
