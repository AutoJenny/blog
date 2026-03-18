# Calendar Scheduling - Operational Guide

This document provides operational guidance for maintaining the JSON-backed calendar scheduling system in production environments.

## Overview

The calendar scheduling system uses pre-computed JSON files to serve fast display views. This document explains:

- How frequently JSON should be rebuilt
- Where to store backups
- How to detect stale JSON
- What logs/errors matter
- Live environment considerations

---

## JSON File Maintenance

### Rebuild Frequency

**Recommended Schedule:**

1. **After Base List Changes**
   - Whenever items are added, removed, or reordered via list management APIs
   - Rebuild affected category/year immediately
   - Example: After reordering themes, rebuild `theme_2025.json` and `theme_2026.json`

2. **After Override Changes**
   - System uses Permanent Sequence Model (no overrides currently)
   - All changes go through base list management APIs
   - JSON rebuilds are automatic after list changes

3. **Proactive Year Generation**
   - Generate next year's JSON in December (before it's needed)
   - Generate 2-3 years ahead for long-term planning
   - Example cron: `0 2 1 12 *` (December 1st at 2 AM)

4. **Periodic Full Rebuild**
   - Weekly rebuild of current year + next year (safety measure)
   - Example cron: `0 3 * * 0` (Sunday at 3 AM)

### Rebuild Commands

```bash
# Rebuild current year (all categories)
python scripts/build_calendar_schedules.py --year 2025

# Rebuild specific category for current year
python scripts/build_calendar_schedules.py --year 2025 --category theme

# Rebuild multiple years
python scripts/build_calendar_schedules.py --year 2025 --extra-years 2

# Rebuild via override endpoint (includes overrides)
curl -X POST http://localhost:5000/planning/api/calendar/override/rebuild-year \
  -H "Content-Type: application/json" \
  -d '{"year": 2025}'
```

---

## Backup Strategy

### What to Backup

1. **JSON Schedule Files**
   - Location: `data/calendar/schedule/*.json`
   - Frequency: Before major rebuilds or monthly
   - Retention: Keep last 3 months

2. **Database Tables**
   - `calendar_week_overrides` (override data)
   - `calendar_category_cycles` (cycle configuration)
   - Base list tables (themes, recipes, profiles, ideas)

### Backup Commands

```bash
# Backup JSON files
tar -czf calendar_schedules_backup_$(date +%Y%m%d).tar.gz data/calendar/schedule/

# Backup override table
pg_dump -t calendar_week_overrides your_database > calendar_overrides_$(date +%Y%m%d).sql

# Backup cycle configuration
pg_dump -t calendar_category_cycles your_database > calendar_cycles_$(date +%Y%m%d).sql
```

### Restore Procedure

```bash
# Restore JSON files
tar -xzf calendar_schedules_backup_YYYYMMDD.tar.gz

# Restore override table
psql your_database < calendar_overrides_YYYYMMDD.sql

# After restore, rebuild JSON to ensure consistency
python scripts/build_calendar_schedules.py --year 2025
```

---

## Detecting Stale JSON

### Indicators of Stale JSON

1. **Missing Files**
   - Check for missing `{category}_{year}.json` files
   - Script: `find data/calendar/schedule -name "*.json" | wc -l` (should be 7 categories × N years)

2. **Outdated `generated_at` Timestamps**
   - JSON files include `generated_at` field
   - Compare to last base list change timestamp
   - Script: `grep -r "generated_at" data/calendar/schedule/ | sort`

3. **Mismatch with Database**
   - Compare JSON item counts to database counts
   - Example: If theme list has 12 items but JSON shows 11, rebuild needed

4. **User Reports**
   - Users seeing incorrect items in calendar view
   - Items appearing in wrong weeks

### Detection Script

```bash
#!/bin/bash
# check_stale_json.sh

YEAR=$(date +%Y)
CATEGORIES=("theme" "recipe" "profile_product" "profile_surname" "weekly_word" "weekly_phrase" "weekly_insult")

for category in "${CATEGORIES[@]}"; do
    file="data/calendar/schedule/${category}_${YEAR}.json"
    if [ ! -f "$file" ]; then
        echo "MISSING: $file"
    else
        # Check if file is older than 7 days
        if [ $(find "$file" -mtime +7) ]; then
            echo "STALE: $file (older than 7 days)"
        fi
    fi
done
```

---

## Logging and Monitoring

### Important Log Messages

**Builder Logs:**
- `Wrote schedule JSON: category=X year=Y` - Successful generation
- `Base list is empty for category=X` - Warning (expected for some categories)
- `Error loading base list for category=X` - Error (investigate)
- `Failed to rebuild JSON` - Error (check permissions, disk space)

**Display API Logs:**
- `Schedule JSON not found for category=X year=Y` - Missing file (rebuild needed)
- `Error reading schedule JSON` - Corrupt file (restore from backup)
- `Schedule JSON has unexpected format` - Schema mismatch (rebuild needed)

**Override API Logs:**
- `Rebuilt JSON for category=X year=Y after override change` - Successful
- `Override set successfully but JSON rebuild failed` - Warning (manual rebuild needed)

### Monitoring Recommendations

1. **File Existence Checks**
   - Monitor for missing JSON files (especially current year)
   - Alert if any category/year combination is missing

2. **File Age Checks**
   - Alert if JSON files are older than 30 days (may be stale)
   - Exception: Past years can be older

3. **Error Rate Monitoring**
   - Track 404s on display API (missing JSON)
   - Track 500s on builder/override endpoints

4. **Performance Monitoring**
   - Display API should respond in < 100ms (JSON read)
   - Builder should complete in < 5 seconds per category/year

---

## Live Environment Considerations

### Deployment Checklist

Before deploying changes:

1. **Backup Current JSON Files**
   ```bash
   tar -czf pre_deploy_backup_$(date +%Y%m%d).tar.gz data/calendar/schedule/
   ```

2. **Test Builder Locally**
   ```bash
   python scripts/build_calendar_schedules.py --year 2025 --base-dir /tmp/test_schedule
   ```

3. **Verify JSON Format**
   - Check one file matches expected schema
   - Validate with JSON schema validator if available

4. **Deploy Code Changes**
   - Deploy builder, display API, override API changes

5. **Rebuild Production JSON**
   ```bash
   python scripts/build_calendar_schedules.py --year 2025
   python scripts/build_calendar_schedules.py --year 2026
   ```

6. **Verify Display**
   - Load scheduling page
   - Check current week displays correctly
   - Test navigation buttons

### Zero-Downtime Deployment

The system is designed for zero-downtime:

1. **JSON Files are Read-Only at Runtime**
   - Display API only reads JSON
   - No locks or transactions needed

2. **Rebuild Process**
   - Builder writes to temporary file
   - Atomic rename (if supported) or overwrite
   - Display API continues serving old file during rebuild

3. **Override Changes**
   - Override API updates DB first
   - Then rebuilds JSON
   - Brief window where override exists but JSON not updated (acceptable)

### Rollback Procedure

If issues occur:

1. **Restore JSON Files**
   ```bash
   tar -xzf pre_deploy_backup_YYYYMMDD.tar.gz
   ```

2. **Restore Database (if needed)**
   ```bash
   psql your_database < calendar_overrides_YYYYMMDD.sql
   ```

3. **Revert Code Changes**
   - Deploy previous version
   - Restart application

---

## Troubleshooting

### Common Issues

**Issue: Display shows empty weeks**

- **Cause**: Missing or empty JSON files
- **Fix**: Rebuild JSON for affected category/year
- **Prevention**: Monitor file existence

**Issue: Items appear in wrong weeks**

- **Cause**: Stale JSON (base list changed but JSON not rebuilt)
- **Fix**: Rebuild JSON for affected category/year
- **Prevention**: Auto-rebuild after list changes

**Issue: Override not appearing**

- **Cause**: JSON rebuild failed after override set
- **Fix**: Manually rebuild: `POST /planning/api/calendar/override/rebuild-year`
- **Prevention**: Monitor override API logs for rebuild failures

**Issue: Builder fails with permission error**

- **Cause**: Insufficient write permissions on `data/calendar/schedule/`
- **Fix**: `chmod -R 755 data/calendar/schedule/`
- **Prevention**: Set correct permissions in deployment

**Issue: JSON file is corrupt**

- **Cause**: Disk error, interrupted write, or manual edit
- **Fix**: Restore from backup, then rebuild
- **Prevention**: Regular backups, validate JSON after write

### Diagnostic Commands

```bash
# Check JSON file count
find data/calendar/schedule -name "*.json" | wc -l

# Check file sizes (should be > 0)
find data/calendar/schedule -name "*.json" -size 0

# Validate JSON syntax
find data/calendar/schedule -name "*.json" -exec python3 -m json.tool {} \; > /dev/null

# Check last modification times
find data/calendar/schedule -name "*.json" -exec ls -lh {} \;

# Count overrides per year
psql your_database -c "SELECT year, COUNT(*) FROM calendar_week_overrides GROUP BY year;"
```

---

## Performance Tuning

### JSON File Size

- Typical file size: 5-20 KB per category/year
- 7 categories × 3 years = ~21 files = ~210-420 KB total
- Negligible memory footprint

### Builder Performance

- Single category/year: < 1 second
- All categories for one year: < 5 seconds
- All categories for 3 years: < 15 seconds

### Display API Performance

- JSON read + merge: < 50ms
- Network transfer: < 100ms (depends on file size)
- Total response time: < 200ms (target)

### Optimization Tips

1. **Pre-generate Years**
   - Generate 2-3 years ahead
   - Reduces on-demand rebuilds

2. **Cache JSON in Memory (Optional)**
   - If serving high traffic, consider in-memory cache
   - TTL: 5-10 minutes (balance freshness vs performance)

3. **CDN for JSON (Optional)**
   - If JSON files are large or traffic is high
   - Not typically needed for internal admin tools

---

## Security Considerations

### File Permissions

```bash
# Recommended permissions
chmod 644 data/calendar/schedule/*.json  # Read-only for web server
chmod 755 data/calendar/schedule/         # Directory executable
```

### Access Control

- Display API: Public (read-only)
- Builder script: Admin/automated only
- Override API: Admin only (requires authentication)

### Input Validation

- Builder validates all inputs (category, year, weeks)
- Display API validates query parameters
- Override API validates item_id exists before setting

---

## Related Documentation

- `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md` - JSON schema specification
- `docs/CALENDAR_SCHEDULING_BUILDER.md` - Builder usage guide
- `docs/CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` - System architecture
- `docs/CALENDAR_SCHEDULING_NEW_PARADIGM.md` - Design overview

---

*Last updated: 2025-12-03*

