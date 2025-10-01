#!/usr/bin/env python3
"""
Fix extracted modules by adding proper imports and blueprint decorators
"""

import os

def fix_module(file_path, module_type, blueprint_name, url_prefix):
    """Fix a module by adding proper imports and decorators"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract the module name from the path
    module_name = os.path.basename(file_path).replace('.py', '')
    
    # Create the header with imports
    header = f'''"""
{module_type.title()} module
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from config.database import db_manager
import logging
from datetime import datetime, date
import json
import requests

logger = logging.getLogger(__name__)

# Create {blueprint_name} blueprint
{blueprint_name} = Blueprint('{blueprint_name}', __name__, url_prefix='{url_prefix}')

'''
    
    # Add route decorators to functions
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('def ') and not line.strip().startswith('def __'):
            # Extract function name
            func_name = line.split('(')[0].replace('def ', '').strip()
            
            # Add route decorator
            if func_name.startswith('api_'):
                route_path = f"/{func_name.replace('api_', '').replace('_', '-')}"
                new_lines.append(f"@{blueprint_name}.route('{route_path}')")
            elif func_name.startswith('planning_'):
                route_path = f"/{func_name.replace('planning_', '').replace('_', '-')}"
                new_lines.append(f"@{blueprint_name}.route('{route_path}')")
            else:
                route_path = f"/{func_name.replace('_', '-')}"
                new_lines.append(f"@{blueprint_name}.route('{route_path}')")
        
        new_lines.append(line)
    
    # Combine header with fixed content
    fixed_content = header + '\n'.join(new_lines)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(fixed_content)

# Fix all modules
modules_to_fix = [
    ('app/routes/calendar.py', 'Calendar API routes', 'calendar_bp', '/api/calendar'),
    ('app/routes/misc.py', 'Miscellaneous API routes', 'misc_bp', '/api'),
    ('app/planning/views.py', 'Planning views', 'planning_bp', '/planning'),
    ('app/services/llm.py', 'LLM services', 'llm_bp', '/api/llm'),
    ('app/services/allocation.py', 'Allocation services', 'allocation_bp', '/api/allocation'),
    ('app/services/validation.py', 'Validation services', 'validation_bp', '/api/validation'),
    ('app/services/parsing.py', 'Parsing services', 'parsing_bp', '/api/parsing'),
    ('app/services/prompting.py', 'Prompting services', 'prompting_bp', '/api/prompting'),
    ('app/repositories/posts.py', 'Post repository', 'posts_bp', '/api/posts'),
    ('app/repositories/config.py', 'Config repository', 'config_bp', '/api/config'),
]

for file_path, module_type, blueprint_name, url_prefix in modules_to_fix:
    if os.path.exists(file_path):
        print(f"Fixing {file_path}...")
        fix_module(file_path, module_type, blueprint_name, url_prefix)
        print(f"✅ Fixed {file_path}")

print("All modules fixed!")
