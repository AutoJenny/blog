"""

# Auto-generated from blueprints/planning.py
# Module: services/allocation.py

def allocate_missing_topics(missing_topics, section_structure, post_id):
    """Allocate missing topics using LLM with simplified prompt"""
    try:
        # Create section codes mapping
        section_codes = {}
        for i, section in enumerate(section_structure.get('sections', []), 1):
            section_codes[f'S{i:02d}'] = section.get('theme', f'Section {i}')
        
        # Simplified prompt for missing topics only
        prompt = f"""You are a Scottish heritage content specialist. Allocate these {len(missing_topics)} missing topics to the most appropriate sections.


def merge_allocations(original_allocation, retry_allocation):
    """Merge original allocation with retry allocation"""
    try:
        merged = original_allocation.copy()
        
        # Create a map of section_id to allocation for easy lookup
        section_map = {}
        for allocation in merged['allocations']:
            section_map[allocation['section_id']] = allocation
        
        # Add retry topics to existing sections
        for retry_alloc in retry_allocation['allocations']:
            section_id = retry_alloc['section_id']
            if section_id in section_map:
                # Add topics to existing section
                section_map[section_id]['topics'].extend(retry_alloc['topics'])
            else:
                # Add new section
                merged['allocations'].append(retry_alloc)
        
        # Update totals
        merged['total_topics'] = sum(len(alloc['topics']) for alloc in merged['allocations'])
        merged['allocated_topics'] = merged['total_topics']
        merged['style'] = 'merged'
        
        logger.info(f"Merged allocation: {merged}")
        return merged
        
    except Exception as e:
        logger.error(f"Error merging allocations: {e}")
        return original_allocation


def allocate_global(scores_matrix, sections_data, capacities):
    """
    Two-phase deterministic assignment:
    A) Coverage pass: give each section 1 idea (best available) if capacity>0
    B) Best-remaining: sort all (idea,section) pairs by score desc and fill until capacities exhausted
    """
    ideas = list(scores_matrix.keys())
    assignment = {}  # idea -> section
    remaining_cap = capacities.copy()
    
    # Helper: pick best unassigned idea for a section
    def best_for_section(section_id):
        best_i = None
        best_s = -1
        for iid in ideas:
            if iid in assignment:
                continue
            sc = scores_matrix[iid][section_id]
            if sc > best_s or (sc == best_s and (best_i is None or iid < best_i)):
                best_s = sc
                best_i = iid
        return best_i, best_s
    
    # A) Coverage pass
    for section in sections_data:
        section_id = section.get('id', f"S{sections_data.index(section)+1:02d}")
        if remaining_cap.get(section_id, 0) <= 0:
            continue
        iid, sc = best_for_section(section_id)
        if iid is not None:
            assignment[iid] = section_id
            remaining_cap[section_id] -= 1
    
    # B) Best-remaining pairs
    pairs = []
    for iid in ideas:
        for section in sections_data:
            section_id = section.get('id', f"S{sections_data.index(section)+1:02d}")
            pairs.append((scores_matrix[iid][section_id], section_id, iid))
    
    # Sort by score desc, then section_id asc, then idea_id asc (deterministic)
    pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
    
    for score, section_id, iid in pairs:
        if iid in assignment:
            continue
        if remaining_cap.get(section_id, 0) <= 0:
            continue
        assignment[iid] = section_id
        remaining_cap[section_id] -= 1
        # Stop early if all assigned
        if len(assignment) == len(ideas):
            break
    
    # Final sanity check
    if len(assignment) != len(ideas):
        logger.error(f"Not all ideas assigned: {len(assignment)}/{len(ideas)}")
    
    for section_id, cap in remaining_cap.items():
        if cap < 0:
            logger.error(f"Capacity underflow for {section_id}: {cap}")
    
    return assignment


