# HEADER STRUCTURE ANALYSIS

## THE PROBLEM

The header template `blog_pipeline_header.html` is ONE SINGLE INCLUDE, but the TOP TWO LINES are conditionally rendered and may not appear if variables are missing.

## HEADER STRUCTURE (4 ROWS)

1. **ROW 1: `main-title-line`** (Lines 6-48)
   - Contains: Title prefix, week info, theme, post type badge, taxonomy, content type
   - **CONDITIONAL**: Requires `post_type` to be defined
   - **CONDITIONAL**: Week info requires JavaScript to populate
   - **CONDITIONAL**: Theme requires `post_type` and JavaScript

2. **ROW 2: `post-details-line`** (Lines 50-58)
   - Contains: Status, Created date, Updated date
   - **CONDITIONAL**: Requires `post_status`, `post_created`, `post_updated` variables
   - Will show "Unknown" if variables missing but WILL STILL DISPLAY

3. **ROW 3: `main-stages-line`** (Lines 60-132)
   - Contains: Main navigation buttons (Calendar, Planning, Authoring, Imaging, Header)
   - **ALWAYS DISPLAYS** - No conditionals

4. **ROW 4: `sub-stages-line`** (Lines 134-277)
   - Contains: Sub-stage navigation buttons
   - **CONDITIONAL**: Requires `currentStage` to be set via JavaScript
   - But will still display (just may not highlight correctly)

## ROOT CAUSE

The TOP TWO ROWS are being hidden or not rendered because:

1. **Missing `post_type` variable** - If `post_type` is not defined, the entire `main-title-line` conditional block (lines 11-47) won't render properly
2. **JavaScript not populating week info** - The week info is populated by JavaScript, but if the elements don't exist or JavaScript fails, they won't show
3. **CSS might be hiding empty elements** - If the title elements are empty, they might collapse or be hidden

## THE FIX

The header template needs to be modified so that:
1. The top two rows ALWAYS display, even if variables are missing
2. Show placeholders/defaults instead of hiding completely
3. Ensure JavaScript can always find the elements to populate

## TEMPLATES AFFECTED

ALL templates that include the header but don't pass `post_type` will have missing top rows.

