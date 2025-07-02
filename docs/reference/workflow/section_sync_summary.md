# Section Synchronization - Quick Reference

## Overview

The section synchronization system maintains data consistency between two complementary fields:

- **`post_development.section_headings`** (Master): JSON array for LLM actions and workflow planning
- **`post_section.section_heading`** (Individual): Text strings for UI management

## Key Points

### Architecture
- **Master Field**: `post_development.section_headings` - authoritative source
- **Individual Fields**: `post_section.section_heading` - derived for UI
- **Sync Direction**: Primary: post_development → post_section (automatic)
- **Sync Direction**: Secondary: post_section → post_development (optional)

### Data Format
```json
[
  {
    "order": 1,
    "heading": "Introduction",
    "description": "Overview",
    "status": "draft"
  }
]
```

### API Endpoint
```bash
# Manual sync (troubleshooting)
curl -X POST "http://localhost:5000/api/workflow/posts/{post_id}/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "both"}'
```

### Database Triggers
- **Primary**: `trigger_sync_section_headings` (post_development → post_section)
- **Secondary**: `trigger_sync_sections_to_headings_*` (post_section → post_development)

## Best Practices

1. **Always use `post_development.section_headings` as master source**
2. **Let automatic sync handle `post_section` updates**
3. **Use manual sync only for troubleshooting**
4. **Validate JSON format before updates**

## Troubleshooting

### Sync Not Working
```bash
# Check triggers
psql -d blog -c "\d+ post_development"

# Test manual sync
curl -X POST "http://localhost:5000/api/workflow/posts/1/sync-sections" \
  -d '{"direction": "to_sections"}'
```

### Data Inconsistency
```bash
# Force sync both directions
curl -X POST "http://localhost:5000/api/workflow/posts/1/sync-sections" \
  -d '{"direction": "both"}'
```

## References

- [Full Documentation](section_synchronization.md)
- [Section Workflow](sections.md)
- [Database Schema](../../database/schema.md)

---

**Note**: This system ensures LLM actions can work with the master field while UI sections remain manageable through individual records. 