# Source Distinction: Local Weekly vs National Newspapers

## Problem Identified

The Round Scotland component is designed for **local weekly newspapers only**, but the queries were including articles from **national newspapers** (BBC Scotland, The Herald, The Scotsman).

## Database Distinction

Sources are distinguished by the `region` field in `newsletter_snapshot_source`:

- **Local Weekly Newspapers**: Have `region` set (e.g., "Argyll & Bute", "Western Isles", "Fife")
- **National Newspapers**: Have `region = NULL` (BBC Scotland, The Herald, The Scotsman)

## Required Filter

All queries for quirky news classification, candidates, and selection MUST filter to only sources with a region:

```sql
AND ns.region IS NOT NULL
```

This ensures only local weekly newspapers are processed.

## Affected Queries

1. **Classification Job** (`classify_quirky_news.py`): Must join with source table and filter by region
2. **Candidates Query** (`newsletter_round_scotland.py`): Already joins but needs region filter
3. **Weekly Highlights Selection** (`weekly_highlights_selection.py`): Already joins but needs region filter
4. **Heuristic Scoring** (`scoring.py`): Should only apply to local sources

## National Newspapers Purpose

National newspapers (BBC Scotland, The Herald, The Scotsman) are used for:
- Regular news section in snapshot block
- General Scottish news coverage
- NOT for quirky local news

They should remain enabled and continue to feed the regular news pipeline.

