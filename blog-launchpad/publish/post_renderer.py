"""
Post Renderer
Renders post HTML for preview and publishing.
Single source of truth for post HTML rendering.

This module is INDEPENDENT of Flask's app.py - it uses its own Jinja2 environment.
This ensures the publication process doesn't depend on app.py.
"""

import logging
import os
import re
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Create standalone Jinja2 environment - INDEPENDENT of Flask
# This ensures publication process doesn't depend on app.py
# Template is at blog/templates/launchpad/clan_post_raw.html
# post_renderer.py is at blog-launchpad/publish/post_renderer.py
# So we need to go up to blog/ then into templates/launchpad/
_current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_templates_dir = os.path.join(_current_dir, 'templates', 'launchpad')
_jinja_env = Environment(loader=FileSystemLoader(_templates_dir))
_jinja_env.trim_blocks = True
_jinja_env.lstrip_blocks = True

# Register filters
def strip_html_doc(content):
    """Strip HTML document tags and return just the content"""
    if not content:
        return content
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
    if content.strip().startswith('<html'):
        match = re.match(r'^<html[^>]*>(.*?)</html>', content, flags=re.DOTALL)
        if match:
            content = match.group(1)
    if content.strip().startswith('<head'):
        content = re.sub(r'^<head[^>]*>.*?</head>', '', content, flags=re.DOTALL)
    if content.strip().startswith('<body'):
        match = re.match(r'^<body[^>]*>(.*?)</body>', content, flags=re.DOTALL)
        if match:
            content = match.group(1)
    return content.strip()

def strip_h2_headings(content):
    """Strip H2 headings and their content from HTML."""
    if not content:
        return content
    content = re.sub(r'<h2[^>]*>.*?</h2>', '', content, flags=re.IGNORECASE | re.DOTALL)
    return content

def is_recipe_section(value):
    """Check if a section_type value indicates a recipe section."""
    if not value:
        return False
    return str(value).startswith('recipe_')

# Register filters and test
_jinja_env.filters['strip_html_doc'] = strip_html_doc
_jinja_env.filters['strip_h2_headings'] = strip_h2_headings
_jinja_env.tests['is_recipe_section'] = is_recipe_section

# Load template once
_template = _jinja_env.get_template('clan_post_raw.html')


def render_post_html(post, sections, image_replacements=None):
    """
    Single source of truth for post HTML rendering.
    
    This function is INDEPENDENT of Flask's app.py - it uses its own Jinja2 environment.
    This ensures the publication process doesn't depend on app.py.
    
    Args:
        post: Post data dict
        sections: List of section dicts
        image_replacements: Dict mapping local paths to CDN URLs (optional)
                          Only used for published version
    
    Returns:
        HTML string ready for preview or publication
    """
    # Use standalone Jinja2 environment - NO dependency on Flask's app.py
    html = _template.render(post=post, sections=sections)
    
    # ONLY apply image replacements if provided (for publishing)
    if image_replacements:
        logger.info(f'Applying {len(image_replacements)} image replacements...')
        
        # Create a comprehensive path mapping
        path_mapping = {}
        for local_path, cdn_url in image_replacements.items():
            # Add the exact path as found in image_replacements
            path_mapping[local_path] = cdn_url
            
            # Also add variations that might appear in the HTML
            if local_path.startswith('/static/'):
                # Keep the original path
                path_mapping[local_path] = cdn_url
                
                # Add the path without /static/ prefix (in case HTML uses relative paths)
                relative_path = local_path[7:]  # Remove '/static/' prefix
                path_mapping[relative_path] = cdn_url
                logger.info(f"Added relative path mapping: {relative_path} -> {cdn_url}")
        
        # Replace all paths in the HTML content
        replacements_made = 0
        for local_path, cdn_url in path_mapping.items():
            # For Photo-harvesting URLs, we need to match the base URL without query params
            if local_path.startswith(('http://', 'https://')):
                # Extract base URL (without query parameters) for matching
                from urllib.parse import urlparse
                base_url = urlparse(local_path).scheme + '://' + urlparse(local_path).netloc + urlparse(local_path).path
                
                # Find all src attributes with this base URL (with any query params)
                pattern = re.compile(r'src="(' + re.escape(base_url) + r'[^"]*)"')
                matches = pattern.findall(html)
                if matches:
                    for match in set(matches):  # Use set to avoid duplicate replacements
                        html = html.replace(f'src="{match}"', f'src="{cdn_url}"')
                        replacements_made += 1
                        logger.info(f"Replaced Photo-harvesting src (base URL match): {match[:80]}... -> {cdn_url}")
            else:
                # For local paths, use exact matching
                # Replace src attributes
                if f'src="{local_path}"' in html:
                    html = html.replace(f'src="{local_path}"', f'src="{cdn_url}"')
                    replacements_made += 1
                    logger.info(f"Replaced src: {local_path} -> {cdn_url}")
                # Replace href attributes  
                if f'href="{local_path}"' in html:
                    html = html.replace(f'href="{local_path}"', f'href="{cdn_url}"')
                    replacements_made += 1
                    logger.info(f"Replaced href: {local_path} -> {cdn_url}")
                # Replace any other occurrences (but count them)
                if local_path in html and local_path not in cdn_url:
                    before_count = html.count(local_path)
                    html = html.replace(local_path, cdn_url)
                    after_count = html.count(local_path)
                    if after_count < before_count:
                        replacements_made += (before_count - after_count)
                        logger.info(f"Replaced {before_count - after_count} occurrences: {local_path} -> {cdn_url}")
        
        logger.info(f"✅ Applied {replacements_made} image path replacements")
    
    # Post-process HTML to add inline styles to recipe section elements
    # This ensures styling survives even if clan.com strips the <style> block
    html = _add_inline_styles_to_recipe_elements(html)
    
    return html


def _add_inline_styles_to_recipe_elements(html):
    """
    Add inline styles to recipe section elements to ensure styling survives
    even if clan.com strips the <style> block.
    """
    import re
    
    # Inline style for ingredient amounts
    ingredient_amount_style = "font-family: 'Courier New', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic;"
    
    # Inline styles for method step time and temperature
    step_time_style = "font-family: 'Courier New', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic; margin-right: 0.75rem;"
    step_temperature_style = "font-family: 'Courier New', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic;"
    
    # Inline style for variant and serving descriptions
    variant_description_style = "font-family: 'Courier New', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic; margin-bottom: 0.5rem;"
    
    # Add inline styles to ingredient-amount spans
    # Pattern: <span class="ingredient-amount"> or <span class="... ingredient-amount ...">
    pattern = re.compile(r'<span([^>]*class="[^"]*ingredient-amount[^"]*"[^>]*)>', re.IGNORECASE)
    def add_ingredient_style(match):
        attrs = match.group(1)
        if 'style=' not in attrs:
            return f'<span{attrs} style="{ingredient_amount_style}">'
        return match.group(0)
    html = pattern.sub(add_ingredient_style, html)
    
    # Add inline styles to step-time spans
    pattern = re.compile(r'<span([^>]*class="[^"]*step-time[^"]*"[^>]*)>', re.IGNORECASE)
    def add_step_time_style(match):
        attrs = match.group(1)
        if 'style=' not in attrs:
            return f'<span{attrs} style="{step_time_style}">'
        return match.group(0)
    html = pattern.sub(add_step_time_style, html)
    
    # Add inline styles to step-temperature spans
    pattern = re.compile(r'<span([^>]*class="[^"]*step-temperature[^"]*"[^>]*)>', re.IGNORECASE)
    def add_step_temp_style(match):
        attrs = match.group(1)
        if 'style=' not in attrs:
            return f'<span{attrs} style="{step_temperature_style}">'
        return match.group(0)
    html = pattern.sub(add_step_temp_style, html)
    
    # Add inline styles to variant-description paragraphs
    pattern = re.compile(r'<p([^>]*class="[^"]*variant-description[^"]*"[^>]*)>', re.IGNORECASE)
    def add_variant_desc_style(match):
        attrs = match.group(1)
        if 'style=' not in attrs:
            return f'<p{attrs} style="{variant_description_style}">'
        return match.group(0)
    html = pattern.sub(add_variant_desc_style, html)
    
    # Add inline styles to serving-description paragraphs
    pattern = re.compile(r'<p([^>]*class="[^"]*serving-description[^"]*"[^>]*)>', re.IGNORECASE)
    def add_serving_desc_style(match):
        attrs = match.group(1)
        if 'style=' not in attrs:
            return f'<p{attrs} style="{variant_description_style}">'
        return match.group(0)
    html = pattern.sub(add_serving_desc_style, html)
    
    logger.info("✅ Added inline styles to recipe section elements")
    
    return html

