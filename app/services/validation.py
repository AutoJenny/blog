"""

# Auto-generated from blueprints/planning.py
# Module: services/validation.py

def validate_section_structure(structure_data):
    """Validate section structure format"""
    try:
        # Handle both array format (new) and object with sections (old)
        if isinstance(structure_data, list):
            sections = structure_data
        elif isinstance(structure_data, dict):
            sections = structure_data.get('sections', [])
        else:
            return False
        
        if len(sections) != 7:
            return False
        
        for section in sections:
            # New format fields (title instead of theme)
            required_fields = ['section_code', 'title', 'description']
            if not all(field in section for field in required_fields):
                return False
            
            # Validate section codes
            if not section['section_code'].startswith('S'):
                return False
        
        return True
    except:
        return False


def validate_topic_allocation(allocation_data, original_topics):
    """Validate topic allocation format"""
    try:
        if not isinstance(allocation_data, dict):
            logger.error("Allocation data is not a dict")
            return False
        
        allocations = allocation_data.get('allocations', [])
        if not allocations:
            logger.error("No allocations found in data")
            return False
        
        # Check that all topics are allocated
        allocated_topics = []
        for allocation in allocations:
            if not isinstance(allocation, dict):
                logger.error(f"Allocation is not a dict: {allocation}")
                return False
            required_fields = ['section_id', 'section_theme', 'topics', 'allocation_reason']
            if not all(field in allocation for field in required_fields):
                logger.error(f"Missing required fields in allocation: {allocation}")
                return False
            allocated_topics.extend(allocation.get('topics', []))
        
        # Verify all original topics are allocated
        original_titles = [topic.get('title', topic) if isinstance(topic, dict) else topic for topic in original_topics]
        
        # Check that we have the right number of topics
        if len(set(allocated_topics)) != len(original_titles):
            logger.error(f"Topic count mismatch: allocated={len(set(allocated_topics))}, original={len(original_titles)}")
            logger.error(f"Allocated topics: {set(allocated_topics)}")
            logger.error(f"Original topics: {original_titles}")
            
            # Find missing topics
            allocated_set = set(allocated_topics)
            original_set = set(original_titles)
            missing_topics = original_set - allocated_set
            logger.error(f"Missing topics: {missing_topics}")
            return False
        
        # Check that all original topics are present in allocated topics
        allocated_set = set(allocated_topics)
        original_set = set(original_titles)
        if allocated_set != original_set:
            logger.error(f"Topic mismatch: allocated={allocated_set}, original={original_set}")
            return False
        
        return True
    except:
        return False


def canonicalize_sections(section_structure):
    """Step 1: Canonicalize sections into machine-ready criteria"""
    
    # Build sections text for canonicalization
    sections_text = ""
    sections = section_structure.get('sections', [])
    
    for i, section in enumerate(sections):
        section_code = f"S{str(i+1).zfill(2)}"
        section_title = section.get('title') or section.get('theme', f'Section {i+1}')
        section_description = section.get('description', 'No description available')
        
        sections_text += f"\n{section_code}: {section_title}\n"
        sections_text += f"Description: {section_description}\n"
    
    canonicalize_prompt = f"""Normalize these sections for allocation. For each section, create a compact classifier profile.


def validate_scores(scoring_data, expected_idea_id):
    """Validate LLM scores and return clean score dictionary"""
    
    VALID_SECTIONS = ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07']
    
    # Basic validation
    if scoring_data.get("idea_id") != expected_idea_id:
        logger.warning(f"idea_id mismatch: expected {expected_idea_id}, got {scoring_data.get('idea_id')}")
    
    scores = scoring_data.get("scores", [])
    if not isinstance(scores, list) or len(scores) != 7:
        logger.error(f"Invalid scores format for {expected_idea_id}")
        return None
    
    # Build score dictionary
    by_id = {}
    seen = set()
    for row in scores:
        sid = row.get("section_id")
        fs = row.get("fit_score")
        if sid not in VALID_SECTIONS:
            logger.error(f"Invalid section_id {sid} for {expected_idea_id}")
            return None
        if not isinstance(fs, int) or not (0 <= fs <= 100):
            logger.error(f"Invalid fit_score {fs} for {expected_idea_id}")
            return None
        if sid in seen:
            logger.error(f"Duplicate section {sid} for {expected_idea_id}")
            return None
        seen.add(sid)
        by_id[sid] = fs
    
    if len(by_id) != 7:
        logger.error(f"Missing scores for {expected_idea_id}")
        return None
    
    return by_id


def compute_capacities(n_ideas, sections_data):
    """Compute balanced capacities for each section"""
    base = n_ideas // 7
    rem = n_ideas % 7
    caps = {}
    
    # Deterministic order: as provided
    for idx, section in enumerate(sections_data):
        section_id = section.get('id', f"S{idx+1:02d}")
        caps[section_id] = base + (1 if idx < rem else 0)
    
    # Ensure at least 1 capacity per section when possible
    if n_ideas >= 7:
        for idx, section in enumerate(sections_data):
            section_id = section.get('id', f"S{idx+1:02d}")
            if caps[section_id] == 0:
                caps[section_id] = 1
        
        # Rebalance capacities to keep sum == N
        total = sum(caps.values())
        while total > n_ideas:
            # Reduce from sections with largest caps (>1), highest sid last
            for idx in reversed(range(len(sections_data))):
                section_id = sections_data[idx].get('id', f"S{idx+1:02d}")
                if caps[section_id] > 1:
                    caps[section_id] -= 1
                    total -= 1
                    if total == n_ideas:
                        break
    
    return caps


