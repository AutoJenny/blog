# Source Distinction Fix - Implementation Report

## Issue Identified

The Round Scotland component was incorrectly processing articles from **national newspapers** (BBC Scotland, The Herald, The Scotsman) in addition to **local weekly newspapers**. This was a fundamental design flaw that needed immediate correction.

## Root Cause

All queries for quirky news classification, candidate selection, and weekly highlights were filtering only by `category = 'news'` without distinguishing between:
- **National newspapers**: Have `region = NULL` in `newsletter_snapshot_source`
- **Local weekly newspapers**: Have `region` set (e.g., "Argyll & Bute", "Fife")

## Database Schema

The distinction is already in place via the `region` field:

**National Newspapers** (region = NULL):
- BBC Scotland
- The Herald  
- The Scotsman
- Met Office Scotland

**Local Weekly Newspapers** (region set):
- Oban Times (Argyll & Bute)
- Stornoway Gazette (Western Isles)
- Shetland Times (Shetland)
- Orkney Today (Orkney)
- Fife Today (Fife)
- Dundee Courier (Dundee & Angus)
- Aberdeen Press and Journal (Aberdeen & Aberdeenshire)
- Perthshire Advertiser (Perthshire)

## Fixes Applied

### 1. Classification Job (`classify_quirky_news.py`)
**Before**: Processed all news articles regardless of source type
**After**: Only processes articles from sources with `region IS NOT NULL`

```sql
INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
WHERE ...
AND ns.region IS NOT NULL  -- Only local weekly newspapers
```

### 2. Candidates Query (`newsletter_round_scotland.py`)
**Before**: LEFT JOIN allowed national sources through
**After**: INNER JOIN with `region IS NOT NULL` filter

### 3. Weekly Highlights Selection (`weekly_highlights_selection.py`)
**Before**: LEFT JOIN allowed national sources through
**After**: INNER JOIN with `region IS NOT NULL` filter

### 4. Heuristic Scoring (`scoring.py`)
**Before**: Applied to all news articles
**After**: Only applies to sources with `region` set (local weeklies)

## Impact

- **National newspapers** continue to work normally for regular news section
- **Local weekly newspapers** are now exclusively used for Round Scotland component
- No data loss - distinction was already in database, just not enforced in queries

## Verification

Run this query to verify only local sources are processed:

```sql
SELECT DISTINCT ns.name, ns.region
FROM newsletter_source_item nsi
INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
WHERE nsi.llm_class = 'quirky'
AND ns.region IS NOT NULL;
```

All results should have a region set.

## Next Steps

1. Enable local weekly newspaper sources (currently disabled for testing)
2. Run prefetch job to fetch articles from local sources
3. Run classification job - it will now only process local sources
4. Verify candidates page shows only local newspaper articles

