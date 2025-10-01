#!/usr/bin/env python3
"""
Fixed refactor tool: properly extracts functions with correct imports and syntax
"""

import os, shutil, sys, re

SRC = "blueprints/planning.py"
OUTDIR = "app"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def extract_function(func_name, code):
    """Extract a function by name from code with proper formatting"""
    lines = code.splitlines()
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith(f'def {func_name}(') or line.strip().startswith(f'class {func_name}('):
            start_line = i
            break
    
    if start_line is None:
        return None
    
    # Find the end of the function
    indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
    end_line = start_line + 1
    
    while end_line < len(lines):
        line = lines[end_line]
        if line.strip() == '':
            end_line += 1
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent_level and line.strip():
            break
        end_line += 1
    
    return '\n'.join(lines[start_line:end_line])

# Read the original file
code = read_file(SRC)

# Extract imports from the original file
import_lines = []
for line in code.splitlines():
    if line.strip().startswith(('import ', 'from ')) or line.strip() == '':
        if line.strip():
            import_lines.append(line)
        else:
            import_lines.append(line)
    elif line.strip():
        break

# Create the header for all modules
header = '\n'.join(import_lines) + '\n\n'

# Function groups with proper route decorators
function_groups = {
    'routes/calendar.py': {
        'functions': [
            'api_calendar_weeks', 'api_calendar_ideas', 'api_calendar_events',
            'api_calendar_schedule', 'api_calendar_schedule_create', 'api_calendar_categories',
            'api_calendar_category_create', 'api_calendar_category_update', 'api_calendar_category_delete',
            'api_calendar_evergreen', 'api_calendar_evergreen_usage_report', 'api_calendar_ideas_for_week'
        ],
        'blueprint_name': 'calendar_bp',
        'url_prefix': '/api/calendar'
    },
    'routes/misc.py': {
        'functions': [
            'api_posts', 'get_post_data', 'api_update_field', 'api_post_progress',
            'get_step_config', 'get_providers', 'get_actions', 'get_system_prompts',
            'execute_action', 'run_llm', 'start_ollama', 'api_calendar_idea_create',
            'api_calendar_idea_update', 'api_calendar_idea_delete', 'api_calendar_event_create',
            'api_calendar_event_update', 'api_calendar_event_delete', 'api_calendar_schedule_update',
            'api_calendar_schedule_delete'
        ],
        'blueprint_name': 'misc_bp',
        'url_prefix': '/api'
    },
    'planning/views.py': {
        'functions': [
            'planning_dashboard', 'planning_post_overview', 'planning_idea', 'planning_research',
            'planning_structure', 'planning_calendar', 'planning_calendar_view', 'categories_manage',
            'planning_calendar_ideas', 'planning_concept', 'planning_concept_brainstorm',
            'planning_concept_section_structure', 'planning_concept_topic_allocation',
            'planning_concept_topic_refinement', 'planning_concept_grouping', 'planning_concept_titling',
            'planning_concept_sections', 'planning_concept_outline', 'test_authoring_preview',
            'planning_research_sources', 'planning_research_visuals', 'planning_research_prompts',
            'planning_research_verification', 'planning_old_interface'
        ],
        'blueprint_name': 'planning_bp',
        'url_prefix': '/planning'
    },
    'services/llm.py': {
        'functions': ['LLMService', 'run_llm'],
        'blueprint_name': 'llm_bp',
        'url_prefix': '/api/llm'
    },
    'services/allocation.py': {
        'functions': ['allocate_missing_topics', 'merge_allocations', 'allocate_global'],
        'blueprint_name': 'allocation_bp',
        'url_prefix': '/api/allocation'
    },
    'services/validation.py': {
        'functions': ['validate_section_structure', 'validate_topic_allocation', 'canonicalize_sections', 'validate_scores', 'compute_capacities'],
        'blueprint_name': 'validation_bp',
        'url_prefix': '/api/validation'
    },
    'services/parsing.py': {
        'functions': ['parse_brainstorm_topics', 'validate_topic'],
        'blueprint_name': 'parsing_bp',
        'url_prefix': '/api/parsing'
    },
    'services/prompting.py': {
        'functions': ['build_section_specific_prompt', 'build_allocation_data'],
        'blueprint_name': 'prompting_bp',
        'url_prefix': '/api/prompting'
    },
    'repositories/posts.py': {
        'functions': ['get_post_data', 'save_section_structure', 'save_topic_allocation', 'load_topic_allocation'],
        'blueprint_name': 'posts_bp',
        'url_prefix': '/api/posts'
    },
    'repositories/config.py': {
        'functions': ['get_step_config', 'get_system_prompts', 'get_providers', 'get_actions', 'get_section_keywords'],
        'blueprint_name': 'config_bp',
        'url_prefix': '/api/config'
    }
}

# Create output directory
if os.path.exists(OUTDIR):
    shutil.rmtree(OUTDIR)

# Create modules
for module_path, config in function_groups.items():
    functions = config['functions']
    blueprint_name = config['blueprint_name']
    url_prefix = config['url_prefix']
    
    content = header
    content += f"# Auto-generated from {SRC}\n"
    content += f"# Module: {module_path}\n\n"
    
    # Add blueprint creation
    content += f"from flask import Blueprint\n\n"
    content += f"# Create {blueprint_name} blueprint\n"
    content += f"{blueprint_name} = Blueprint('{blueprint_name}', __name__, url_prefix='{url_prefix}')\n\n"
    
    for func_name in functions:
        func_code = extract_function(func_name, code)
        if func_code:
            # Add route decorator for functions that need it
            if func_name.startswith('api_') or func_name.startswith('planning_'):
                route_path = f"/{func_name.replace('api_', '').replace('planning_', '').replace('_', '-')}"
                content += f"@{blueprint_name}.route('{route_path}')\n"
            
            content += func_code + '\n\n'
        else:
            content += f"# Function {func_name} not found\n\n"
    
    write_file(os.path.join(OUTDIR, module_path), content)

# Create __init__.py files
for subdir in ['routes', 'planning', 'services', 'repositories']:
    write_file(os.path.join(OUTDIR, subdir, '__init__.py'), '')

print("Fixed refactor complete.")
for module_path, config in function_groups.items():
    print(f"- app/{module_path}: {len(config['functions'])} functions")
