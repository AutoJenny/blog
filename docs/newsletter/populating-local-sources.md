# How to Populate Local Weekly Newspaper Sources

## Overview

To populate the Round Scotland component with quirky local news, you need to:
1. Enable local weekly newspaper sources
2. Run the prefetch job to fetch articles
3. Run the classification job to identify quirky articles

## Step 1: Enable Local Sources

Local weekly newspaper sources are currently **disabled** by default. You need to enable them.

### Option A: Via SQL

```sql
-- Enable all local weekly newspapers
UPDATE newsletter_snapshot_source 
SET enabled = true 
WHERE region IS NOT NULL;

-- Or enable specific ones
UPDATE newsletter_snapshot_source 
SET enabled = true 
WHERE name IN ('Oban Times', 'Stornoway Gazette', 'Shetland Times');
```

### Option B: Via Python Script

```python
import sys
sys.path.insert(0, 'blog-core')
from config.database import db_manager

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        # Enable all local sources
        cur.execute("""
            UPDATE newsletter_snapshot_source 
            SET enabled = true 
            WHERE region IS NOT NULL
        """)
        conn.commit()
        print("Local sources enabled")
```

### Option C: Via UI

Navigate to `/newsletter/sources` and enable the local weekly newspapers manually.

## Step 2: Run Prefetch Job

The prefetch job fetches articles from all enabled sources and applies heuristic scoring.

```bash
cd /Users/autojenny/Documents/projects/blog
python3 blog-core/newsletter/jobs/prefetch_sources.py
```

This will:
- Fetch articles from enabled local sources
- Extract images from article pages
- Apply heuristic scoring (only to local sources)
- Store articles in `newsletter_source_item`

## Step 3: Run Classification Job

The classification job processes articles that passed heuristic filtering and classifies them as quirky/not_quirky.

```bash
python3 blog-core/newsletter/jobs/classify_quirky_news.py
```

This will:
- Select candidates (heuristic_score >= 3.0, from local sources only)
- Classify with LLM (quirky/not_quirky with 0-100 score)
- Perform safety checks
- Update articles with classification results

## Step 4: Verify

Check that articles are being processed:

```python
import sys
sys.path.insert(0, 'blog-core')
from config.database import db_manager

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        # Check articles from local sources
        cur.execute("""
            SELECT COUNT(*) as total
            FROM newsletter_source_item nsi
            INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
            WHERE ns.region IS NOT NULL
            AND nsi.category = 'news'
        """)
        total = cur.fetchone()['total']
        print(f'Total articles from local sources: {total}')
        
        # Check classified articles
        cur.execute("""
            SELECT COUNT(*) as total
            FROM newsletter_source_item nsi
            INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
            WHERE ns.region IS NOT NULL
            AND nsi.llm_class = 'quirky'
        """)
        quirky = cur.fetchone()['total']
        print(f'Quirky articles: {quirky}')
```

## Troubleshooting

### No Articles Fetched

- Check that sources are enabled: `SELECT name, enabled FROM newsletter_snapshot_source WHERE region IS NOT NULL`
- Check source URLs are accessible
- Review prefetch job logs for errors

### No Articles Classified

- Check heuristic scores: Articles need `heuristic_score >= 3.0` to proceed
- Verify LLM service is accessible
- Check classification job logs

### No Candidates Showing

- Ensure articles have `llm_class = 'quirky'` and `llm_quirky_score >= 60`
- Check date range (articles must be within last 14 days by default)
- Verify sources have `region IS NOT NULL`

