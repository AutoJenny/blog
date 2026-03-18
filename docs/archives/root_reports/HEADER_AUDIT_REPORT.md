# HEADER AUDIT REPORT
## Comprehensive Audit of blog_pipeline_header.html Include

### SUMMARY
**CRITICAL FINDING**: Most templates HAVE the header include, but many routes are NOT passing the required variables (`post_type`, `post_title`, `post_status`, etc.) which causes the header to not display properly or show incomplete information.

### Templates WITH Header Include (✓) - VERIFIED
**AUTHORING STAGE:**
1. ✓ `templates/authoring/sections/drafting.html` - Line 21
2. ✓ `templates/authoring/sections/image_concepts.html` - Line 34
3. ✓ `templates/authoring/sections/image_prompts.html` - Line 34 (FIXED - now passes all required vars)
4. ✓ `templates/authoring/sections/image_captions.html` - Line 30
5. ✓ `templates/authoring/sections/image_generation.html` - Line 27
6. ✓ `templates/authoring/sections/ideas_to_include.html` - Line 14
7. ✓ `templates/authoring/sections/author_first_drafts_deprecated.html` - Line 169

**PLANNING STAGE:**
8. ✓ `templates/planning/calendar.html` - Line 13
9. ✓ `templates/planning/calendar/view.html` - Has include
10. ✓ `templates/planning/calendar/week_view.html` - Has include
11. ✓ `templates/planning/calendar/taxonomy.html` - Has include
12. ✓ `templates/planning/calendar/ideas.html` - Has include
13. ✓ `templates/planning/calendar/ideas_week.html` - Has include
14. ✓ `templates/planning/calendar/product_data_review.html` - Has include
15. ✓ `templates/planning/concept/brainstorm.html` - Has include
16. ✓ `templates/planning/concept/section_structure.html` - Has include
17. ✓ `templates/planning/concept/topic_allocation.html` - Has include
18. ✓ `templates/planning/concept/titling.html` - Has include
19. ✓ `templates/planning/concept/section_content_mapping.html` - Has include
20. ✓ `templates/planning/concept/topic_refinement.html` - Line 13
21. ✓ `templates/planning/concept/sections.html` - Line 13
22. ✓ `templates/planning/concept/outline.html` - Line 13
23. ✓ `templates/planning/research/sources.html` - Line 13

**IMAGING STAGE:**
24. ✓ `templates/imaging/sections/image_generation.html` - Has include
25. ✓ `templates/imaging/sections/photo_selection.html` - Has include
26. ✓ `templates/imaging/sections/optimise.html` - Line 34

**HEADER STAGE:**
27. ✓ `templates/header/title_summary.html` - Has include
28. ✓ `templates/header/header_image.html` - Has include
29. ✓ `templates/header/seo_meta.html` - Has include
30. ✓ `templates/header/final_review.html` - Has include
31. ✓ `templates/header/publishing_details.html` - Has include

**RECIPES:**
32. ✓ `templates/recipes/image_style_prompt.html` - Line 20

### Templates MISSING Header Include (✗)
1. ✗ `templates/planning/concept/grouping.html` - **MISSING** - No include found, but this template may be deprecated (no route found that renders it)

### ROOT CAUSE ANALYSIS

**THE REAL PROBLEM IS NOT MISSING INCLUDES - IT'S MISSING VARIABLES!**

Most templates HAVE the header include, but the routes rendering them are NOT passing all required variables. When variables are missing:
- Header may not display week context
- Navigation may not highlight correctly
- Post details may show "Unknown"
- Week information may not appear

### Required Variables for Header (ALL MUST BE PASSED)
1. `post_id` - **REQUIRED** - For all navigation links
2. `post_type` - **REQUIRED** - For navigation logic and conditional display
3. `post_title` - **RECOMMENDED** - For header title display
4. `post_status` - **RECOMMENDED** - For status display
5. `post_created` - **RECOMMENDED** - For created date display
6. `post_updated` - **RECOMMENDED** - For updated date display
7. `content_type_name` - **RECOMMENDED** - For category banner
8. `year` and `week` - **REQUIRED FOR WEEK CONTEXT** - For week display in header

### Routes That Need Variable Fixes

**AUTHORING ROUTES:**
- ✓ `authoring_api_imaging.py::authoring_sections_image_prompts` - **FIXED** - Now passes all required vars
- ✗ `authoring_api_imaging.py::authoring_sections_image_concepts` - May be missing some vars
- ✗ `authoring_api_imaging.py::authoring_sections_image_captions` - May be missing some vars
- ✗ `authoring.py::authoring_sections_drafting` - Check if all vars passed

**PLANNING ROUTES:**
- ✗ `planning_concept.py` - Multiple routes may be missing vars
- ✗ `planning_calendar.py` - Multiple routes may be missing vars
- ✗ `planning_calendar_product_data_review.py` - May be missing vars

**IMAGING ROUTES:**
- ✗ `imaging_routes.py` - Check all routes pass required vars

**HEADER ROUTES:**
- ✗ `header.py` - Check all routes pass required vars

### ACTION ITEMS

1. **IMMEDIATE**: Fix `image_prompts` route - **DONE** ✓
2. **URGENT**: Audit and fix ALL routes to pass required header variables
3. **URGENT**: Add header include to `grouping.html` if it's still in use
4. **ONGOING**: Ensure all new routes pass all required header variables

### STANDARD PATTERN FOR ROUTES

Every route that renders a template with the header should follow this pattern:

```python
# Get post details
cursor.execute("""
    SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
           p.content_type_id, content_type.illustration_method
    FROM post p
    LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
    WHERE p.id = %s
""", (target_post_id,))
post = cursor.fetchone()

# Get post_type
from utils.taxonomy_helpers import get_post_type
post_type = get_post_type(target_post_id)

# Get content_type_name
cursor.execute("""
    SELECT ti.display_name as content_type_name
    FROM post p
    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
    WHERE p.id = %s
""", (target_post_id,))
result = cursor.fetchone()
content_type_name = result.get('content_type_name') if result else None

# Render template with ALL required variables
return render_template('template.html',
    post_id=post_id,
    post=post,
    post_type=post_type,
    post_title=post.get('title'),
    post_status=post.get('status'),
    post_created=post.get('created_at'),
    post_updated=post.get('updated_at'),
    content_type_name=content_type_name,
    year=year,  # If available
    week=week,  # If available
    # ... other template-specific vars
)
```

