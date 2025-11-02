# Changelog

## 2025-11-XX - Newsletter Event Management

### Event Classification & Management
- **Event Recurrence Classification**: Added LLM-based classification system to identify annual vs one-off events
  - Enhanced prompt to emphasize festivals are annual events
  - Added heuristic pre-check: any event with "festival" in title = annual
  - Added known annual event keywords (hogmanay, celtic connections, royal highland show, etc.)
  - Classification filter added to Events Synopsis page with visual badges
  - Manual override capability on event detail page

### Event Editing & Deletion
- **Inline Editing**: Added direct editing capabilities on event detail page
  - Title: Click-to-edit with full-width input
  - Description: Textarea editing with Save/Cancel
  - Date Text: Raw date text field editing
  - Event Date: Inline date picker
  - Location: Inline text input
  - All edits save to both database columns and raw_data JSON
- **Delete Functionality**: Added delete button with confirmation dialog
  - Checks for soft delete column first, falls back to hard delete
  - Redirects to events list after successful deletion
- **API Endpoints**: 
  - `POST /newsletter/events/<id>/update` - Update any event field
  - `DELETE /newsletter/events/<id>` - Delete event (soft or hard delete)
  - `POST /newsletter/events/<id>/recurrence-type` - Update classification manually

### Database Schema
- **Event Recurrence Type**: Added `event_recurrence_type` column to `newsletter_source_item` table
  - Values: `'annual'`, `'one_off'`, or `NULL` (unclassified)
  - Indexed for efficient filtering
  - Migration: `migrations/add_event_recurrence_type.sql`

### Classification Service
- Created `event_classification_service.py` with LLM-based classification
- Includes heuristic fallback for known annual events
- Batch classification script: `classify_all_events.py`

### Technical Improvements
- Fixed missing `db_manager` imports in event update/delete routes
- Improved event detail service to include recurrence type in queries
- Enhanced event filtering to catch false positives (newsletter signups, accommodation listings, recurring patterns)

## 2025-11-01 (continued - evening)

- Section Titling: Fixed bug where only first section received title/description - now generates for all sections
- Section Titling: Enhanced LLM prompt to explicitly list all sections with themes and topics
- Section Titling: Added validation to ensure LLM generates exactly the correct number of section titles
- Section Titling: Fixed section matching logic bug that was overwriting outer loop variable
- Section Titling: Added direct writes to post_section table in addition to post_development.sections
- Idea Expansion: Enhanced Important Notes highlighting in prompt with mandatory requirements and explicit instructions
- Idea Expansion: Improved theme data fetching to handle cases where theme selected for week before post creation

## 2025-11-01 (continued)

- Page Headers: Replaced post ID display with date span, week number, and selected theme across all blog pipeline pages
- Page Headers: Added fallback logic to fetch theme from week schedule when post schedule doesn't include theme
- Page Headers: Removed stage prefix (Planning/Calendar) from header - now shows only week info and theme
- API: Updated planning_api_posts to include selected_theme_title in schedule responses
- UI: Added CSS styling for new header elements (prefix, week info, separator, theme)

## 2025-11-01

- Week View Navigation: Added localStorage persistence for calendar week view (remembers selected week/year across sessions).
- Week View Navigation: Added "This week" button to quickly jump to the current week.
- Week View Navigation: Replaced week number input with month/week picker interface showing all weeks organized by month with date ranges.
- Theme Selection: Fixed theme selection persistence on ideas week page - themes now save to calendar_schedule when selected.
- Theme Display: Fixed calendar week view to correctly show selected themes using idea_id from calendar_schedule.
- Idea Modal: Added delete button to unified idea/theme/event modal (only visible when editing existing items).
- API: Added DELETE endpoint for calendar events.
- API: Updated calendar_schedule endpoint to include idea_id in responses.

## 2025-10-31

- Week View: Added filters (Blog Themes, Events, Syndication) and integrated Facebook Product syndication schedule rendering per weekday with time.
- Week View: Introduced a single week-wide Blog Themes row above the grid with left-aligned titles.
- Week View: Added calendar day numbers to the right of each day header (Mon–Sun).
- Scheduling: Added backfill and purge endpoints to normalize and hard-delete legacy/inactive schedule rows; `get_schedules` now filters `is_active = true`.


