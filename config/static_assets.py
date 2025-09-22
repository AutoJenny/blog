# config/static_assets.py
"""
Static Assets Configuration and Management
Handles static asset organization and serving for the unified application
"""

import os
from flask import url_for

class StaticAssetsManager:
    """Manages static assets for the unified application"""
    
    def __init__(self, app=None):
        self.app = app
        self.asset_map = {
            'css': {
                'main': 'css/dist/main.css',
                'llm_actions': 'css/llm-actions.css',
                'launchpad': 'css/launchpad.css',
                'post_sections': 'css/post-sections.css',
                'post_info': 'css/post-info.css',
                'images': 'css/images.css',
                'clan_api': 'css/clan-api.css',
                'workflow_nav': 'css/nav.dist.css'
            },
            'js': {
                'main': 'js/main.js',
                'llm_actions': 'js/llm-actions.js',
                'launchpad': 'js/launchpad.js',
                'post_sections': 'js/post-sections.js',
                'post_info': 'js/post-info.js',
                'images': 'js/images.js',
                'clan_api': 'js/clan-api.js',
                'workflow_nav': 'js/workflow-nav.js'
            },
            'images': {
                'brand_logo': 'images/site/brand-logo.png',
                'header': 'images/site/header.jpg',
                'footer': 'images/site/footer.jpg',
                'clan_watermark': 'images/site/clan-watermark.png'
            }
        }
    
    def get_asset_url(self, asset_type, asset_name):
        """Get URL for a specific asset"""
        if asset_type in self.asset_map and asset_name in self.asset_map[asset_type]:
            return url_for('static', filename=self.asset_map[asset_type][asset_name])
        return None
    
    def get_css_assets(self, blueprint_name=None):
        """Get CSS assets for a specific blueprint or all"""
        css_assets = []
        
        if blueprint_name:
            # Get blueprint-specific CSS
            blueprint_css = {
                'core': ['main', 'workflow_nav'],
                'launchpad': ['main', 'launchpad'],
                'llm_actions': ['main', 'llm_actions'],
                'post_sections': ['main', 'post_sections'],
                'post_info': ['main', 'post_info'],
                'images': ['main', 'images'],
                'clan_api': ['main', 'clan_api']
            }
            
            if blueprint_name in blueprint_css:
                for css_name in blueprint_css[blueprint_name]:
                    if css_name in self.asset_map['css']:
                        css_assets.append(self.asset_map['css'][css_name])
        else:
            # Get all CSS assets
            css_assets = list(self.asset_map['css'].values())
        
        return css_assets
    
    def get_js_assets(self, blueprint_name=None):
        """Get JavaScript assets for a specific blueprint or all"""
        js_assets = []
        
        if blueprint_name:
            # Get blueprint-specific JS
            blueprint_js = {
                'core': ['main', 'workflow_nav'],
                'launchpad': ['main', 'launchpad'],
                'llm_actions': ['main', 'llm_actions'],
                'post_sections': ['main', 'post_sections'],
                'post_info': ['main', 'post_info'],
                'images': ['main', 'images'],
                'clan_api': ['main', 'clan_api']
            }
            
            if blueprint_name in blueprint_js:
                for js_name in blueprint_js[blueprint_name]:
                    if js_name in self.asset_map['js']:
                        js_assets.append(self.asset_map['js'][js_name])
        else:
            # Get all JS assets
            js_assets = list(self.asset_map['js'].values())
        
        return js_assets
    
    def get_image_url(self, image_name):
        """Get URL for a specific image"""
        if image_name in self.asset_map['images']:
            return url_for('static', filename=self.asset_map['images'][image_name])
        return None
    
    def get_blueprint_assets(self, blueprint_name):
        """Get all assets for a specific blueprint"""
        return {
            'css': self.get_css_assets(blueprint_name),
            'js': self.get_js_assets(blueprint_name),
            'images': self.asset_map['images']
        }

# Global instance
static_assets = StaticAssetsManager()
