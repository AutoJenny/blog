# Complete Guide: Populating Local Sources for Round Scotland

## Summary

You now have local weekly newspaper sources enabled and articles being processed. Here's what was done and how to use it.

## What Was Done

### 1. Enabled Local Sources ✅
- Enabled 8 local weekly newspaper sources:
  - Oban Times (Argyll & Bute)
  - Stornoway Gazette (Western Isles)
  - Shetland Times (Shetland)
  - Orkney Today (Orkney)
  - Fife Today (Fife)
  - Dundee Courier (Dundee & Angus)
  - Aberdeen Press and Journal (Aberdeen & Aberdeenshire)
  - Perthshire Advertiser (Perthshire)

### 2. Fixed Source Distinction ✅
- All queries now filter to only local sources (`region IS NOT NULL`)
- National newspapers (BBC Scotland, The Herald, The Scotsman) are excluded from quirky news processing

### 3. Fixed Heuristic Scoring ✅
- Updated `store_source_items()` to save `heuristic_score` and `heuristic_flags`
- Fixed `get_source_config()` to handle dict-like database rows
- Re-scored existing articles (95 articles, 22 with scores > 0, 1 above threshold)

### 4. Ran Classification ✅
- 1 article classified as quirky (score: 85)
- Article: "'Beating heart of the community' celebrates 20 years..." from Oban Times

## Current Status

- **Total articles from local sources**: 95
- **Articles with heuristic scores > 0**: 22
- **Articles above threshold (>= 3.0)**: 1
- **Articles classified as quirky**: 1

## How to Populate More Articles

### Step 1: Fetch New Articles
```bash
cd /Users/autojenny/Documents/projects/blog
python3 blog-core/newsletter/jobs/prefetch_sources.py
```

This will:
- Fetch new articles from enabled local sources
- Apply heuristic scoring automatically
- Store articles with heuristic scores

### Step 2: Re-score Existing Articles (if needed)
If you want to re-score articles that were fetched before heuristic scoring was fixed:

```bash
python3 scripts/rescore_local_articles.py
```

### Step 3: Classify Articles
```bash
python3 blog-core/newsletter/jobs/classify_quirky_news.py
```

This processes articles with `heuristic_score >= 3.0` and classifies them as quirky/not_quirky.

### Step 4: View Candidates
Navigate to:
```
http://localhost:5000/newsletter/issue/23/round-scotland/candidates
```

You should now see the quirky article(s) available for selection.

## Troubleshooting

### No Articles Showing in Candidates

1. **Check heuristic scores**:
```python
import sys
sys.path.insert(0, 'blog-core')
from config.database import db_manager

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('''
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN heuristic_score >= 3.0 THEN 1 END) as above_threshold
            FROM newsletter_source_item nsi
            INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
            WHERE ns.region IS NOT NULL
            AND nsi.category = 'news'
        ''')
        print(cur.fetchone())
```

2. **Check classified articles**:
```python
cur.execute('''
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN llm_class = 'quirky' THEN 1 END) as quirky
    FROM newsletter_source_item nsi
    INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
    WHERE ns.region IS NOT NULL
    AND nsi.category = 'news'
''')
print(cur.fetchone())
```

3. **Check date range**: Articles must be within last 14 days (configurable in classification job)

### Low Number of Quirky Articles

- The heuristic threshold (3.0) is intentionally high to filter out non-quirky content
- Only articles with strong quirky indicators (festivals, community events, local celebrations) will pass
- This ensures quality over quantity

### Sources Not Fetching

- Check source URLs are accessible
- Verify sources are enabled: `SELECT name, enabled FROM newsletter_snapshot_source WHERE region IS NOT NULL`
- Review prefetch job logs for errors

## Next Steps

1. **Enable more sources**: Add more local weekly newspapers from the discovery script
2. **Adjust thresholds**: Modify heuristic threshold in `blog-core/newsletter/config/quirky_news_config.py`
3. **Run regularly**: Set up a cron job to run prefetch and classification daily
4. **Select highlights**: Use the Round Scotland editor to select articles for the newsletter

## Files Modified

- `blog-core/newsletter/jobs/prefetch_sources.py` - Fixed import path
- `blog-core/newsletter/jobs/classify_quirky_news.py` - Fixed import path, added region filter
- `blog-core/newsletter/services/scoring.py` - Added region check for heuristic scoring
- `blog-core/newsletter/services/weekly_highlights_selection.py` - Added region filter
- `blog-core/newsletter/db/queries_sources.py` - Fixed get_source_config, added heuristic fields to INSERT
- `blueprints/newsletter_round_scotland.py` - Added region filter to candidates query
- `scripts/rescore_local_articles.py` - New script to re-score existing articles



