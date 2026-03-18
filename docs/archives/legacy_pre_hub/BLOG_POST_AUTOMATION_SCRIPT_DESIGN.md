# Blog Post Automation Scripts - Design Document

**Date:** 2026-01-19  
**Purpose:** Detailed design for automation scripts to create and process blog posts to 'ready' status

---

## Overview

Two scripts are needed to automate blog post creation and workflow execution:

1. **`scripts/automated_blog_post_creator.py`** - Creates posts from calendar schedule
2. **`scripts/automated_blog_post_workflow.py`** - Executes workflow stages automatically

---

## Script 1: Automated Blog Post Creator

### Purpose
Create blog posts (themed, recipe, profiles) 1 week in advance based on calendar schedule.

### Structure (Based on `automated_weekly_content_creator.py`)

```python
#!/usr/bin/env python3
"""
Automated Blog Post Creator
Creates post records for blog posts (themed, recipe, profiles) 1 week in advance
Runs daily to check for upcoming blog posts and create draft posts
"""

import os
import sys
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.calendar_resolver import resolve_item_for_week
from blueprints.post_type_config import get_publication_day_for_post_type

logger = logging.getLogger(__name__)

class BlogPostCreator:
    def __init__(self):
        self.db_manager = db_manager
    
    def get_upcoming_weeks(self, days_ahead: int = 7) -> List[tuple]:
        """Get list of (year, week_number) tuples for upcoming weeks"""
        # Same as weekly content creator
    
    def check_existing_post(self, category: str, item_id: int, year: int, week_number: int) -> Optional[int]:
        """
        Check if a post already exists for this calendar item/week
        Returns post_id if exists, None otherwise
        """
        # Query calendar_week_posts_v2 or calendar_week_items
        # Check for existing post linked to this item/week
    
    def create_themed_post(self, theme_item: Dict, year: int, week_number: int) -> Optional[int]:
        """
        Create a themed post from calendar theme
        Returns post_id or None
        """
        # 1. Check if post exists
        # 2. Create post record (status='draft')
        # 3. Set idea_seed in post_development
        # 4. Schedule in calendar_week_items
        # 5. Return post_id
    
    def create_recipe_post(self, recipe_item: Dict, year: int, week_number: int) -> Optional[int]:
        """
        Create a recipe post from calendar recipe
        Returns post_id or None
        """
        # Similar to themed but with recipe_week_number
    
    def create_product_profile_post(self, profile_item: Dict, year: int, week_number: int) -> Optional[int]:
        """
        Create a product profile post
        Returns post_id or None
        """
        # Similar but with profile_product_id
    
    def create_surname_profile_post(self, profile_item: Dict, year: int, week_number: int) -> Optional[int]:
        """
        Create a surname profile post
        Returns post_id or None
        """
        # Similar but with profile_category_id
    
    def create_blog_posts(self, days_ahead: int = 7) -> Dict[str, int]:
        """
        Main function to create blog posts for upcoming weeks
        """
        stats = {
            'weeks_checked': 0,
            'items_found': 0,
            'posts_created': 0,
            'posts_skipped': 0,
            'errors': 0
        }
        
        # Get upcoming weeks
        # For each week:
        #   - Resolve theme (if exists)
        #   - Resolve recipe (if exists)
        #   - Resolve product profile (if exists)
        #   - Resolve surname profile (if exists)
        #   - Create posts for each found item
        #   - Update stats
        
        return stats
```

### Key Functions

#### `create_themed_post()`
```python
def create_themed_post(self, theme_item: Dict, year: int, week_number: int) -> Optional[int]:
    """
    Create themed post from calendar theme
    """
    theme_id = theme_item['id']
    theme_title = theme_item.get('theme_title', '')
    
    # Check if post exists
    existing_post_id = self.check_existing_post('theme', theme_id, year, week_number)
    if existing_post_id:
        return existing_post_id
    
    # Create post
    slug = self.generate_slug(theme_title)
    with self.db_manager.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO post (title, slug, status, created_at, updated_at)
            VALUES (%s, %s, 'draft', NOW(), NOW())
            RETURNING id
        """, (theme_title, slug))
        post_id = cursor.fetchone()['id']
        
        # Set idea_seed
        cursor.execute("""
            INSERT INTO post_development (post_id, idea_seed, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (post_id) DO UPDATE SET idea_seed = EXCLUDED.idea_seed
        """, (post_id, theme_title))
        
        # Get publication day from config
        from blueprints.post_type_config import get_publication_day_for_post_type
        themed_config = get_publication_day_for_post_type('themed', cursor)
        default_weekday = themed_config['day'] if themed_config else 3  # Wednesday
        
        # Schedule in calendar_week_items
        cursor.execute("""
            INSERT INTO calendar_week_items (
                item_type, item_id, year, week_number, weekday,
                scheduled_date, scheduled_at, is_active, is_selected, 
                priority, metadata, created_at, updated_at
            ) VALUES (
                'profile', %s, %s, %s, %s,
                NULL, NOW(), TRUE, FALSE, 'normal', '{}'::jsonb, NOW(), NOW()
            )
            ON CONFLICT (year, week_number, item_type, item_id) DO UPDATE SET
                weekday = EXCLUDED.weekday,
                updated_at = NOW()
        """, (post_id, year, week_number, default_weekday))
        
        return post_id
```

#### `create_recipe_post()`
```python
def create_recipe_post(self, recipe_item: Dict, year: int, week_number: int) -> Optional[int]:
    """
    Create recipe post from calendar recipe
    """
    recipe_id = recipe_item['id']
    recipe_title = recipe_item.get('recipe_title', '')
    recipe_week_number = recipe_item.get('recipe_week_number', 1)
    
    # Check if post exists
    existing_post_id = self.check_existing_post('recipe', recipe_id, year, week_number)
    if existing_post_id:
        return existing_post_id
    
    # Create post with recipe_week_number
    slug = self.generate_slug(recipe_title)
    with self.db_manager.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO post (title, slug, status, recipe_week_number, created_at, updated_at)
            VALUES (%s, %s, 'draft', %s, NOW(), NOW())
            RETURNING id
        """, (recipe_title, slug, recipe_week_number))
        post_id = cursor.fetchone()['id']
        
        # Get publication day from config
        from blueprints.post_type_config import get_publication_day_for_post_type
        recipe_config = get_publication_day_for_post_type('recipe', cursor)
        default_weekday = recipe_config['day'] if recipe_config else 1  # Monday
        
        # Schedule in calendar_week_items
        cursor.execute("""
            INSERT INTO calendar_week_items (
                item_type, item_id, year, week_number, weekday,
                scheduled_date, scheduled_at, is_active, is_selected,
                priority, metadata, created_at, updated_at
            ) VALUES (
                'profile', %s, %s, %s, %s,
                NULL, NOW(), TRUE, FALSE, 'normal', '{}'::jsonb, NOW(), NOW()
            )
            ON CONFLICT (year, week_number, item_type, item_id) DO UPDATE SET
                weekday = EXCLUDED.weekday,
                updated_at = NOW()
        """, (post_id, year, week_number, default_weekday))
        
        return post_id
```

### Integration Points

**Calendar Resolution:**
- Use `resolve_item_for_week(category, year, week_number)` for each post type
- Categories: 'theme', 'recipe', 'profile_product', 'profile_surname'

**Post Creation:**
- Use similar pattern to `confirm_calendar_idea()` in `blueprints/planning_api_posts.py`
- Create post with `status='draft'`
- Set `idea_seed` in `post_development`
- Schedule in `calendar_week_items`

**Publication Day/Time:**
- Use `get_publication_day_for_post_type()` from `blueprints/post_type_config.py`
- Fallback to defaults: themed=Wednesday, recipe=Monday, profile=Thursday

---

## Script 2: Automated Blog Post Workflow Executor

### Purpose
Execute all automatable workflow stages for draft blog posts, progressing them to 'ready' status.

### Structure (Based on `automated_weekly_content_workflow.py`)

```python
#!/usr/bin/env python3
"""
Automated Blog Post Workflow Executor
Runs workflow stages for draft blog posts
Executes all automatable substages based on post type
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from config.post_type_substages import POST_TYPE_SUBSTAGES
from blueprints.automation_core import execute_substage
from utils.taxonomy_helpers import get_post_type

logger = logging.getLogger(__name__)

class BlogPostWorkflowExecutor:
    def __init__(self):
        self.db_manager = db_manager
        
    def get_draft_blog_posts(self) -> List[Dict]:
        """
        Get draft blog posts that need workflow execution
        Only gets posts that haven't been published yet
        """
        # Query post table for status='draft'
        # Filter by post types: themed, recipe, profile
        # Exclude deleted posts
    
    def get_post_substages(self, post_type: str) -> Dict[str, List[str]]:
        """
        Get list of substages for a post type from config
        """
        # Load from config/post_type_substages.py
    
    def check_stage_complete(self, post_id: int, stage: str, substage: str) -> bool:
        """
        Check if a stage/substage is already complete
        """
        # Check database for required data
        # For example: taxonomy complete = content_type_id is set
    
    def check_review_gate(self, post_id: int, stage: str, substage: str) -> bool:
        """
        Check if this stage requires review before proceeding
        """
        # Check post.approval_required_stages JSONB array
        # Or check post.status for 'needs_review'
        # Return True if review needed, False if can proceed
    
    def execute_substage_for_post(self, post_id: int, stage: str, substage: str) -> Dict[str, any]:
        """
        Execute a single substage for a post
        """
        # Call blueprints/automation_core.py::execute_substage()
        # Handle errors
        # Return success status
    
    def execute_workflow_for_post(self, post_id: int, post_type: str) -> Dict[str, any]:
        """
        Execute all automatable stages for a post
        """
        results = {
            'post_id': post_id,
            'post_type': post_type,
            'stages_completed': [],
            'stages_skipped': [],
            'stages_failed': [],
            'review_gates_hit': [],
            'final_status': 'draft'
        }
        
        # Get substages for post type
        # For each stage/substage:
        #   - Check if already complete
        #   - Check review gate
        #   - Execute if automatable
        #   - Update results
        
        # If all automatable stages complete:
        #   - Update status to 'ready'
        
        return results
    
    def execute_workflows(self, limit: int = 10) -> Dict[str, int]:
        """
        Main function to execute workflows for draft posts
        """
        stats = {
            'posts_processed': 0,
            'posts_completed': 0,
            'posts_needs_review': 0,
            'posts_failed': 0,
            'errors': 0
        }
        
        # Get draft posts
        # For each post:
        #   - Determine post type
        #   - Execute workflow
        #   - Update stats
        
        return stats
```

### Key Functions

#### `check_stage_complete()`
```python
def check_stage_complete(self, post_id: int, stage: str, substage: str) -> bool:
    """
    Check if stage/substage is complete by checking database
    """
    with self.db_manager.get_cursor() as cursor:
        if stage == 'planning' and substage == 'taxonomy':
            # Check if content_type_id is set
            cursor.execute("SELECT content_type_id FROM post WHERE id = %s", (post_id,))
            result = cursor.fetchone()
            return result and result.get('content_type_id') is not None
        
        elif stage == 'planning' and substage == 'topic_brainstorming':
            # Check if topics exist in post_development
            cursor.execute("""
                SELECT topic_allocation FROM post_development WHERE post_id = %s
            """, (post_id,))
            result = cursor.fetchone()
            return result and result.get('topic_allocation') is not None
        
        elif stage == 'authoring' and substage == 'drafting':
            # Check if sections have draft content
            cursor.execute("""
                SELECT COUNT(*) FROM post_section 
                WHERE post_id = %s AND draft IS NOT NULL AND draft != ''
            """, (post_id,))
            result = cursor.fetchone()
            return result and result[0] > 0
        
        # Add more checks for other stages...
        
    return False
```

#### `execute_workflow_for_post()`
```python
def execute_workflow_for_post(self, post_id: int, post_type: str) -> Dict[str, any]:
    """
    Execute all automatable stages for a post
    """
    results = {
        'post_id': post_id,
        'post_type': post_type,
        'stages_completed': [],
        'stages_skipped': [],
        'stages_failed': [],
        'review_gates_hit': [],
        'final_status': 'draft'
    }
    
    # Get substages for post type
    substages_config = POST_TYPE_SUBSTAGES.get(post_type, {})
    
    # Define automatable stages (can be configured)
    automatable_stages = {
        'planning': ['taxonomy', 'topic_brainstorming', 'section_structure', 
                     'topic_allocation', 'section_titling'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'seo_meta']
    }
    
    # Review gate stages (require manual approval)
    review_gate_stages = {
        'planning': ['section_structure'],  # Verify structure
        'authoring': ['drafting'],  # Verify content quality
        'header': ['header_image']  # Verify image quality
    }
    
    # Execute stages in order
    for stage, substages in substages_config.items():
        if stage not in automatable_stages:
            continue  # Skip non-automatable stages (e.g., research)
        
        for substage in substages:
            if substage not in automatable_stages[stage]:
                continue  # Skip non-automatable substages
            
            # Check if already complete
            if self.check_stage_complete(post_id, stage, substage):
                results['stages_skipped'].append(f"{stage}.{substage}")
                continue
            
            # Check review gate
            if stage in review_gate_stages and substage in review_gate_stages[stage]:
                # Check if already approved
                if not self.is_stage_approved(post_id, stage, substage):
                    results['review_gates_hit'].append(f"{stage}.{substage}")
                    logger.info(f"Review gate hit for {post_id}: {stage}.{substage}")
                    break  # Stop automation at review gate
            
            # Execute substage
            try:
                result = self.execute_substage_for_post(post_id, stage, substage)
                if result.get('success'):
                    results['stages_completed'].append(f"{stage}.{substage}")
                    logger.info(f"Completed {stage}.{substage} for post {post_id}")
                else:
                    results['stages_failed'].append(f"{stage}.{substage}")
                    logger.error(f"Failed {stage}.{substage} for post {post_id}: {result.get('error')}")
                    # Continue with next stage even if one fails
            except Exception as e:
                logger.error(f"Error executing {stage}.{substage} for post {post_id}: {e}")
                results['stages_failed'].append(f"{stage}.{substage}")
    
    # Determine final status
    if results['review_gates_hit']:
        # Update status to 'needs_review'
        self.update_post_status(post_id, 'needs_review')
        results['final_status'] = 'needs_review'
    elif not results['stages_failed']:
        # All automatable stages complete
        self.update_post_status(post_id, 'ready')
        results['final_status'] = 'ready'
    else:
        # Some stages failed, keep as draft
        results['final_status'] = 'draft'
    
    return results
```

### Integration Points

**Substage Execution:**
- Use `blueprints/automation_core.py::execute_substage(stage, substage, post_id, data)`
- Same API used by one-click publication system

**Post Type Detection:**
- Use `utils/taxonomy_helpers::get_post_type(post_id)`
- Returns: 'themed', 'recipe', 'profile', etc.

**Stage Configuration:**
- Load from `config/post_type_substages.py`
- Defines which substages exist for each post type

**Review Gates:**
- Check `post.approval_required_stages` JSONB array
- Or use `post.status = 'needs_review'`
- Pause automation when review gate hit

---

## Review Gate System Design

### Option A: Status-Based (Recommended)

**Post Status Values:**
- `'draft'` - Created, automation running
- `'in_progress'` - Automation actively processing
- `'needs_review'` - At review gate, waiting for approval
- `'ready'` - All automated stages complete, ready for publication
- `'published'` - Published

**Implementation:**
```python
# In automation script
if review_gate_hit:
    cursor.execute("""
        UPDATE post 
        SET status = 'needs_review',
            updated_at = NOW()
        WHERE id = %s
    """, (post_id,))
    # Stop automation for this post
```

**Approval:**
```python
# Manual approval (via UI or API)
cursor.execute("""
    UPDATE post 
    SET status = 'in_progress',  -- Resume automation
        updated_at = NOW()
    WHERE id = %s
""", (post_id,))
```

### Option B: JSONB Array

**Post Field:**
```sql
ALTER TABLE post ADD COLUMN approval_required_stages JSONB DEFAULT '[]';
```

**Usage:**
```python
# Set review gate
approval_stages = ['planning.section_structure', 'authoring.drafting']
cursor.execute("""
    UPDATE post 
    SET approval_required_stages = %s::jsonb
    WHERE id = %s
""", (json.dumps(approval_stages), post_id))

# Check review gate
if f"{stage}.{substage}" in approval_required_stages:
    # Check if approved
    if not is_stage_approved(post_id, stage, substage):
        # Pause automation
```

**Recommended**: Option A (Status-Based) - simpler, no schema changes needed

---

## Background Monitor Integration

### Update `scripts/background_posting_monitor.sh`

Add steps after existing weekly content and product post steps:

```bash
# Step 7: Create blog posts (1 week in advance)
log "Creating blog posts..."
PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_blog_post_creator.py" >> "$LOG_FILE" 2>&1 || log "Warning: automated_blog_post_creator.py exited with error (continuing)"

# Step 8: Execute workflow for draft blog posts
log "Executing blog post workflows..."
PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_blog_post_workflow.py" >> "$LOG_FILE" 2>&1 || log "Warning: automated_blog_post_workflow.py exited with error (continuing)"
```

---

## Error Handling

### Duplicate Prevention
- Check for existing posts before creating
- Use database unique constraints
- Handle constraint violations gracefully

### Failure Recovery
- Log all errors
- Continue processing other posts if one fails
- Retry failed stages (optional, with max retries)

### Status Tracking
- Update post status appropriately
- Log progress for each stage
- Provide detailed error messages

---

## Testing Strategy

### Unit Tests
- Test post creation for each type
- Test workflow execution for each stage
- Test review gate logic
- Test duplicate prevention

### Integration Tests
- Test full workflow from creation to ready
- Test with real calendar data
- Test error scenarios
- Test review gate workflow

### Manual Testing
- Run scripts manually
- Verify posts created correctly
- Verify workflow executes correctly
- Verify review gates work

---

## Success Criteria

### Post Creation
- ✅ Posts created 1 week in advance
- ✅ All post types supported
- ✅ Proper calendar scheduling
- ✅ No duplicates created

### Workflow Execution
- ✅ All automatable stages execute
- ✅ Posts reach 'ready' status
- ✅ Review gates respected
- ✅ Errors handled gracefully

### Integration
- ✅ Background monitor integration
- ✅ Logging and monitoring
- ✅ Error recovery
- ✅ Status tracking

---

## Implementation Order

### Phase 1: Post Creator (Priority 1)
1. Create `automated_blog_post_creator.py`
2. Implement `create_themed_post()`
3. Implement `create_recipe_post()`
4. Implement `create_product_profile_post()`
5. Implement `create_surname_profile_post()`
6. Test with real calendar data

### Phase 2: Workflow Executor (Priority 2)
1. Create `automated_blog_post_workflow.py`
2. Implement stage completion detection
3. Implement substage execution
4. Implement review gate logic
5. Test workflow execution

### Phase 3: Integration (Priority 3)
1. Add to background monitor
2. Test end-to-end
3. Monitor and refine
4. Document usage

---

## Files to Create

1. `scripts/automated_blog_post_creator.py` - Post creation script
2. `scripts/automated_blog_post_workflow.py` - Workflow execution script
3. `docs/BLOG_POST_AUTOMATION_IMPLEMENTATION.md` - Implementation guide (future)

## Files to Update

1. `scripts/background_posting_monitor.sh` - Add new steps
2. `docs/BLOG_POST_AUTOMATION_GOALS.md` - Update with implementation status

---

**Last Updated:** 2026-01-19
