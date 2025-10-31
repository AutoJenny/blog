# Changelog

## 2025-10-31

- Week View: Added filters (Blog Themes, Events, Syndication) and integrated Facebook Product syndication schedule rendering per weekday with time.
- Week View: Introduced a single week-wide Blog Themes row above the grid with left-aligned titles.
- Week View: Added calendar day numbers to the right of each day header (Mon–Sun).
- Scheduling: Added backfill and purge endpoints to normalize and hard-delete legacy/inactive schedule rows; `get_schedules` now filters `is_active = true`.


