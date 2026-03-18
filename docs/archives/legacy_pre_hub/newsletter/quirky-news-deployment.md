# Round Scotland Component - Deployment Summary

## Deployment Status: ✅ COMPLETE

All components have been successfully deployed to the database.

## Completed Steps

### 1. Database Migrations ✅
All three migrations have been successfully run:
- ✅ `add_quirky_news_source_fields.sql` - Extended `newsletter_snapshot_source` table
- ✅ `add_quirky_news_fields.sql` - Extended `newsletter_source_item` table  
- ✅ `create_weekly_highlights_tables.sql` - Created `weekly_highlights` and `weekly_highlights_items` tables

### 2. Source Seeding ✅
8 Scottish weekly newspaper sources have been inserted:
- Oban Times (ID: 18) - Argyll & Bute
- Stornoway Gazette (ID: 19) - Western Isles
- Shetland Times (ID: 20) - Shetland
- Orkney Today (ID: 21) - Orkney
- Perthshire Advertiser (ID: 22) - Perthshire
- Fife Today (ID: 23) - Fife
- Dundee Courier (ID: 24) - Dundee & Angus
- Aberdeen Press and Journal (ID: 25) - Aberdeen & Aberdeenshire

**Note**: All sources are currently **disabled** (`enabled=false`) for initial testing.

## Next Steps for Testing

### 1. Enable Test Sources
Via the UI at `/newsletter/sources` or directly in the database:
```sql
UPDATE newsletter_snapshot_source 
SET enabled = true 
WHERE id IN (18, 19, 20, 21, 22, 23, 24, 25);
```

Or enable just 1-2 sources for initial testing:
```sql
UPDATE newsletter_snapshot_source 
SET enabled = true 
WHERE id IN (18, 19);  -- Oban Times and Stornoway Gazette
```

### 2. Run Prefetch Job
Fetch articles from enabled sources:
```bash
python3 blog-core/newsletter/jobs/prefetch_sources.py
```

This will:
- Fetch articles from enabled sources
- Extract images from article pages
- Apply heuristic scoring
- Store articles in `newsletter_source_item`

### 3. Run Classification Job
Classify articles for quirkiness:
```bash
python3 blog-core/newsletter/jobs/classify_quirky_news.py
```

This will:
- Select candidates (heuristic_score >= 3.0)
- Classify with LLM (quirky/not_quirky)
- Assign quirky scores (0-100)
- Perform safety checks

### 4. Create Test Newsletter Issue
Create a new newsletter issue via the UI or API. The system will automatically:
- Select weekly highlights for the Round Scotland component
- Create `weekly_highlights` record linked to the issue
- Create `weekly_highlights_items` records

### 5. Run Summarization Job
Generate summaries for selected highlights:
```bash
python3 blog-core/newsletter/jobs/summarize_weekly_highlights.py --issue-id <issue_id>
```

This will generate:
- Internal titles
- Newsletter summaries (2-3 sentences)
- Social media summaries (1-2 sentences)
- Location and source labels

### 6. Test UI Components

**Round Scotland Editor**:
- Navigate to `/newsletter/issue/<issue_id>/round-scotland`
- Review selected highlights
- Edit individual items
- Browse candidate pool
- Select images for stories

**Snapshot Block Editor**:
- Navigate to issue editor
- Open snapshot block
- Click "Generate" for Round Scotland component
- Review selected items
- Compile all three components (News, Events, Round Scotland)

**Newsletter Preview**:
- Preview the issue to see Round Scotland section rendered
- Verify formatting and content

### 7. Test Social Media Export
Export highlights for social media:
```python
from newsletter.services.social_export_service import export_weekly_highlights_social

# Export as JSON
result = export_weekly_highlights_social(issue_id=23, format='json')

# Export as CSV
csv_data = export_weekly_highlights_social(issue_id=23, format='csv')

# Export for Facebook
fb_posts = export_weekly_highlights_social(issue_id=23, format='facebook')
```

### 8. Monitor Pipeline Health
Check pipeline statistics:
```python
from newsletter.services.monitoring_service import get_pipeline_stats, check_alerts

# Get stats
stats = get_pipeline_stats(days_back=7)
print(stats)

# Check for alerts
alerts = check_alerts()
for alert in alerts:
    print(f"{alert['level']}: {alert['message']}")
```

## Configuration

Current configuration in `blog-core/newsletter/config/quirky_news_config.py`:
- Heuristic score threshold: 3.0
- LLM quirky score threshold: 60
- Max items per week: 8
- Max items per region: 2
- Image extraction: Enabled

Adjust these values based on testing results.

## Troubleshooting

### No Articles Classified
- Check that sources are enabled
- Verify prefetch job ran successfully
- Check heuristic scores (need >= 3.0)
- Verify LLM service is accessible

### No Weekly Highlights Selected
- Check that articles have `llm_class = 'quirky'`
- Verify `llm_quirky_score >= 60`
- Check date range (articles must be within last 7 days)
- Review diversity rules (may be too restrictive)

### Images Not Extracted
- Check network connectivity
- Verify article URLs are accessible
- Check timeout settings
- Review domain filtering logic

## Production Readiness

Before enabling in production:
1. ✅ Test with 1-2 sources first
2. ✅ Verify classification accuracy
3. ✅ Review selected highlights quality
4. ✅ Test image extraction and serving
5. ✅ Verify social media export formats
6. ✅ Set up monitoring and alerts
7. ✅ Schedule batch jobs (classification, summarization)

## Files Reference

- **Migrations**: `migrations/add_quirky_news_*.sql`
- **Discovery Script**: `blog-core/newsletter/sources/discovery/scottish_newspapers.py`
- **Seed Script**: `blog-core/newsletter/sources/discovery/seed_discovered_sources.py`
- **Manual Sources**: `data/scottish_newspaper_sources_manual.json`
- **Configuration**: `blog-core/newsletter/config/quirky_news_config.py`
- **Documentation**: `docs/newsletter/quirky-news-*.md`

