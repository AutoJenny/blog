#!/usr/bin/env python3
"""
Refactor tool v2: splits monolithic planning.py into small modules by responsibility.
Uses a simpler approach with manual function grouping.
"""

import os, shutil, sys

SRC = "blueprints/planning.py"
OUTDIR = "app"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Read the original file
code = read_file(SRC)

# Extract imports and header
lines = code.splitlines()
import_lines = []
header_lines = []
in_imports = True

for line in lines:
    if in_imports and (line.startswith('import ') or line.startswith('from ') or line.strip() == '' or line.startswith('"""') or line.startswith("'''")):
        if line.strip():
            import_lines.append(line)
        else:
            import_lines.append(line)
    elif line.strip() == '':
        if in_imports:
            import_lines.append(line)
        else:
            header_lines.append(line)
    else:
        in_imports = False
        header_lines.append(line)

# Create the header for all modules
header = '\n'.join(import_lines) + '\n\n'

# Function groups (manually defined based on analysis)
function_groups = {
    'routes/calendar.py': [
        'api_calendar_weeks', 'api_calendar_ideas', 'api_calendar_events',
        'api_calendar_schedule', 'api_calendar_schedule_create', 'api_calendar_categories',
        'api_calendar_category_create', 'api_calendar_category_update', 'api_calendar_category_delete',
        'api_calendar_evergreen', 'api_calendar_evergreen_usage_report', 'api_calendar_ideas_for_week'
    ],
    'routes/misc.py': [
        'api_posts', 'get_post_data', 'api_update_field', 'api_post_progress',
        'get_step_config', 'get_providers', 'get_actions', 'get_system_prompts',
        'execute_action', 'run_llm', 'start_ollama', 'api_calendar_idea_create',
        'api_calendar_idea_update', 'api_calendar_idea_delete', 'api_calendar_event_create',
        'api_calendar_event_update', 'api_calendar_event_delete', 'api_calendar_schedule_update',
        'api_calendar_schedule_delete'
    ],
    'planning/views.py': [
        'planning_dashboard', 'planning_post_overview', 'planning_idea', 'planning_research',
        'planning_structure', 'planning_calendar', 'planning_calendar_view', 'categories_manage',
        'planning_calendar_ideas', 'planning_concept', 'planning_concept_brainstorm',
        'planning_concept_section_structure', 'planning_concept_topic_allocation',
        'planning_concept_topic_refinement', 'planning_concept_grouping', 'planning_concept_titling',
        'planning_concept_sections', 'planning_concept_outline', 'test_authoring_preview',
        'planning_research_sources', 'planning_research_visuals', 'planning_research_prompts',
        'planning_research_verification', 'planning_old_interface'
    ],
    'services/llm.py': [
        'LLMService', 'run_llm'
    ],
    'services/allocation.py': [
        'allocate_missing_topics', 'merge_allocations', 'allocate_global'
    ],
    'services/validation.py': [
        'validate_section_structure', 'validate_topic_allocation', 'canonicalize_sections',
        'validate_scores', 'compute_capacities'
    ],
    'services/parsing.py': [
        'parse_brainstorm_topics', 'validate_topic'
    ],
    'services/prompting.py': [
        'build_section_specific_prompt', 'build_allocation_data'
    ],
    'repositories/posts.py': [
        'get_post_data', 'save_section_structure', 'save_topic_allocation', 'load_topic_allocation'
    ],
    'repositories/config.py': [
        'get_step_config', 'get_system_prompts', 'get_providers', 'get_actions', 'get_section_keywords'
    ]
}

# Extract functions manually
def extract_function(func_name, code):
    """Extract a function by name from code"""
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

# Create output directory
if os.path.exists(OUTDIR):
    shutil.rmtree(OUTDIR)

# Create modules
for module_path, functions in function_groups.items():
    content = header
    content += f"# Auto-generated from {SRC}\n"
    content += f"# Module: {module_path}\n\n"
    
    for func_name in functions:
        func_code = extract_function(func_name, code)
        if func_code:
            content += func_code + '\n\n'
        else:
            content += f"# Function {func_name} not found\n\n"
    
    write_file(os.path.join(OUTDIR, module_path), content)

# Create __init__.py files
for subdir in ['routes', 'planning', 'services', 'repositories']:
    write_file(os.path.join(OUTDIR, subdir, '__init__.py'), '')

print("Refactor v2 complete.")
for module_path, functions in function_groups.items():
    print(f"- app/{module_path}: {len(functions)} functions")
