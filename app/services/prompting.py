"""

# Auto-generated from blueprints/planning.py
# Module: services/prompting.py

def build_section_specific_prompt(post_title, section_title, section_description, all_sections, expanded_idea=None):
    """Build prompt for generating section-specific topics"""
    
    # Build other sections context for negative instructions
    other_sections = []
    for i, section in enumerate(all_sections):
        other_title = section.get('title') or section.get('theme', f'Section {i+1}')
        other_desc = section.get('description', '')
        if other_title != section_title:  # Exclude current section
            other_sections.append(f"- {other_title}: {other_desc}")
    
    other_sections_text = "\n".join(other_sections) if other_sections else "None"
    
    # Build expanded idea context
    idea_context = ""
    if expanded_idea:
        try:
            if isinstance(expanded_idea, str):
                idea_data = json.loads(expanded_idea)
            else:
                idea_data = expanded_idea
            
            idea_context = f"""

def build_allocation_data(all_allocations, section_structure):
    """Build final allocation data structure"""
    
    # Group allocations by section
    section_groups = {}
    for allocation in all_allocations:
        section_code = allocation['section_code']
        if section_code not in section_groups:
            section_groups[section_code] = []
        section_groups[section_code].append(allocation['topic_title'])
    
    # Build allocation data
    allocation_data = {
        'allocations': [],
        'metadata': {
            'total_topics_allocated': len(all_allocations),
            'unallocated_topics': [],
            'allocation_method': 'individual_iterative'
        }
    }
    
    # Process all sections from structure, not just those with topics
    for i, section_data in enumerate(section_structure['sections']):
        section_order = i + 1
        section_code = f"{{S{str(section_order).zfill(2)}}}"
        
        # Get topics for this section (empty list if none)
        topic_list = section_groups.get(section_code, [])
        
        # Handle both new format (title) and old format (theme)
        section_theme = section_data.get('title') or section_data.get('theme', f'Section {section_order}')
        
        allocation_data['allocations'].append({
            'section_id': f'section_{section_order}',
            'section_theme': section_theme,
            'topics': topic_list,
            'allocation_reason': f'Topics allocated to {section_theme} based on individual thematic analysis'
        })
    
    return allocation_data


