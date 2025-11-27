# Quirky Scottish News Integration - Implementation Documentation

## Overview

The "Round Scotland" component extends the existing newsletter snapshot block with a third section featuring quirky, light-hearted local news stories from Scottish weekly newspapers. This system automatically discovers sources, classifies articles, selects highlights, and integrates them into the newsletter workflow.

## Architecture

### Components

1. **Source Discovery**: Discovers Scottish weekly newspapers from Wikipedia
2. **Image Extraction**: Extracts images from article pages with captions/credits
3. **Heuristic Scoring**: Pre-filters articles using keyword and section-based rules
4. **LLM Classification**: Classifies articles as quirky/not_quirky with scoring
5. **Weekly Selection**: Selects diverse highlights with regional constraints
6. **Summarization**: Generates newsletter and social media summaries
7. **UI Integration**: Extends snapshot block editor and adds Round Scotland editor
8. **Social Export**: Exports highlights for social media posting
9. **Monitoring**: Tracks pipeline health and alerts on issues

### Database Schema

#### Extended Tables

**newsletter_snapshot_source**:
- `region` (VARCHAR): Geographic region
- `preferred_sections` (TEXT[]): Preferred content sections
- `excluded_sections` (TEXT[]): Excluded content sections
- `access_mode` (VARCHAR): rss_only|html_list_only|api|blocked
- `discovery_notes` (TEXT): Notes from discovery process

**newsletter_source_item**:
- `heuristic_score` (NUMERIC): Pre-filtering score
- `heuristic_flags` (JSONB): Matching keywords/sections
- `llm_class` (VARCHAR): quirky|not_quirky|uncertain
- `llm_quirky_score` (INTEGER): 0-100 quirky score
- `llm_summary_raw` (TEXT): Raw LLM summary
- `safety_flag` (VARCHAR): Safety classification
- `selected_for_highlights` (BOOLEAN): Whether selected for highlights
- `available_images` (JSONB): Array of extracted images

#### New Tables

**weekly_highlights**:
- `id` (SERIAL): Primary key
- `issue_id` (INTEGER): Linked newsletter issue
- `week_start` (DATE): Week start date
- `week_end` (DATE): Week end date
- `created_at` (TIMESTAMPTZ): Creation timestamp

**weekly_highlights_items**:
- `id` (SERIAL): Primary key
- `weekly_highlights_id` (INTEGER): Parent highlights set
- `article_id` (INTEGER): Source article reference
- `position` (INTEGER): Display order
- `title_internal` (TEXT): Internal title
- `summary_newsletter` (TEXT): Newsletter summary
- `summary_social` (TEXT): Social media summary
- `location_label` (VARCHAR): Location display label
- `source_label` (VARCHAR): Source display label
- `permalink` (TEXT): Article permalink
- `selected_image_url` (TEXT): Selected image URL
- `selected_image_caption` (TEXT): Image caption
- `selected_image_credit` (TEXT): Image credit
- `remote_image_url` (TEXT): Remote-served image URL

## Services

### Image Extraction Service

**File**: `blog-core/newsletter/services/image_extraction_service.py`

Extracts images from article HTML pages:
- Filters to same-domain images only
- Extracts captions and credits
- Stores in `available_images` JSONB field
- Handles timeouts and errors gracefully

### Heuristic Scoring Service

**File**: `blog-core/newsletter/services/heuristic_scoring.py`

Pre-filters articles using:
- Section-based weighting (preferred/excluded sections)
- Keyword-based weighting (positive/negative keywords)
- Returns score and matching flags

### Quirky Classification Service

**File**: `blog-core/newsletter/services/quirky_classification_service.py`

Uses LLM to:
- Classify as quirky/not_quirky/uncertain
- Assign 0-100 quirky score
- Generate neutral summary
- Perform safety check

### Weekly Highlights Selection Service

**File**: `blog-core/newsletter/services/weekly_highlights_selection.py`

Selects highlights with:
- Candidate filtering (quirky score threshold, safety flags)
- Diversity rules (max per region, max total)
- Greedy selection algorithm

### Summarization Service

**File**: `blog-core/newsletter/services/quirky_summarization_service.py`

Generates:
- Internal title
- Newsletter summary (2-3 sentences)
- Social media summary (1-2 sentences)
- Location and source labels

### Social Export Service

**File**: `blog-core/newsletter/services/social_export_service.py`

Exports highlights in formats:
- JSON: Structured data
- CSV: Spreadsheet format
- Facebook: Formatted posts
- Instagram: Captions with hashtags
- Twitter: 280-char tweets

### Monitoring Service

**File**: `blog-core/newsletter/services/monitoring_service.py`

Tracks:
- Articles ingested per source
- Classification success rates
- Weekly highlights counts
- LLM error rates
- Generates alerts for issues

## Jobs

### Classify Quirky News

**File**: `blog-core/newsletter/jobs/classify_quirky_news.py`

Batch job that:
- Selects candidates (heuristic_score >= threshold, not yet classified)
- Processes in batches of 10
- Updates database with classification results

### Summarize Weekly Highlights

**File**: `blog-core/newsletter/jobs/summarize_weekly_highlights.py`

Batch job that:
- Processes all items in a weekly_highlights set
- Calls summarization service for each
- Handles errors gracefully

## API Endpoints

### Snapshot Generation

- `GET /newsletter/issue/<issue_id>/block/<block_id>/generate-round-scotland`
  - Fetches/creates weekly highlights for issue
  - Returns formatted items for display

- `POST /newsletter/issue/<issue_id>/block/<block_id>/compile-snapshot`
  - Compiles all three components (news, events, round_scotland)
  - Generates three paragraphs using LLM

### Round Scotland Editor

- `GET /newsletter/issue/<issue_id>/round-scotland`
  - Overview page with selected highlights

- `GET /newsletter/issue/<issue_id>/round-scotland/item/<item_id>/edit`
  - Edit individual highlight item

- `POST /newsletter/issue/<issue_id>/round-scotland/item/<item_id>/update`
  - Update highlight item

- `POST /newsletter/issue/<issue_id>/round-scotland/item/<item_id>/remove`
  - Remove item from highlights

- `GET /newsletter/issue/<issue_id>/round-scotland/candidates`
  - Browse candidate pool

## Configuration

**File**: `blog-core/newsletter/config/quirky_news_config.py`

Configurable parameters:
- `HEURISTIC_SCORE_THRESHOLD`: Minimum heuristic score (default: 3.0)
- `LLM_QUIRKY_SCORE_THRESHOLD`: Minimum quirky score (default: 60)
- `MAX_ITEMS_PER_WEEK`: Maximum total items (default: 8)
- `MAX_ITEMS_PER_REGION`: Maximum per region (default: 2)
- `EXCLUDED_SAFETY_FLAGS`: Safety flags to exclude
- `IMAGE_EXTRACTION_ENABLED`: Enable/disable image extraction
- `CLASSIFICATION_BATCH_SIZE`: Batch size for classification (default: 10)

## Workflow

1. **Source Discovery**: Run discovery script to find Scottish newspapers
2. **Source Seeding**: Insert discovered sources into database
3. **Daily Ingestion**: Prefetch job fetches articles, extracts images, applies heuristic scoring
4. **Classification**: Batch job classifies articles with LLM
5. **Issue Creation**: Weekly highlights automatically selected when issue created
6. **Summarization**: Batch job generates summaries for selected highlights
7. **Editorial Review**: Editor reviews and adjusts highlights via Round Scotland editor
8. **Snapshot Compilation**: Editor compiles all three snapshot components
9. **Social Export**: Export highlights for social media posting

## Troubleshooting

### No Articles Classified

- Check heuristic scores: Articles need score >= 3.0 to proceed
- Check LLM service: Verify LLM API is accessible
- Check classification job: Ensure job is running

### Low Weekly Highlights Count

- Check candidate pool: Verify articles with quirky_score >= 60 exist
- Check diversity rules: May be too restrictive (max_per_region)
- Check date range: Ensure articles are within last 7 days

### Image Extraction Failing

- Check network access: Verify can reach article URLs
- Check timeout settings: May need to increase timeout
- Check domain filtering: Ensure images are from same domain

### LLM Errors

- Check API credentials: Verify LLM service credentials
- Check rate limits: May be hitting rate limits
- Check prompt format: Verify prompt structure is correct

## File Size Enforcement

All files are kept under 400-500 lines:
- Services split into focused modules
- Templates use partials for reusability
- Complex logic extracted to helper functions

