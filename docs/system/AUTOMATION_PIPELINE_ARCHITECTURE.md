# Automation Pipeline Architecture - Complete Framework

**Date:** 2025-01-XX  
**Purpose:** Comprehensive architectural framework for automated multi-channel publication pipeline  
**Status:** Blueprint for Implementation

---

## Executive Summary

This document defines the complete architectural structure for an automated publication pipeline that:
- Supports all post types (themed, recipe, profile, weekly_word, weekly_phrase, weekly_insult)
- Publishes to multiple channels (blog, Facebook, Instagram, Twitter, Newsletter)
- Includes review gates and manual intervention
- Ensures interoperability and robust reliability

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Calendar Scheduling Layer                     │
│  (JSON-backed cyclic system via utils/calendar_resolver.py)      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Post Type Classification                       │
│  (config/post_type_substages.py + config/post_type_schema.py)   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Channel Assignment Engine                      │
│  (post_type_channel_config table + calendar_item_channels)      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Output Channel Stage Resolution                │
│  (config/output_channel_stages.py - stages per post+channel)    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Production Pipeline                           │
│  (Automation Engine: channel-specific stages/substages)         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Review Gate System                            │
│  (post_approval table + approval workflow)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Publication Scheduler                         │
│  (scheduled_publications table + background jobs)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Channel Publisher                       │
│  (blog, facebook, instagram, twitter, newsletter)                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Publication Status Tracking                   │
│  (post_publication_status table)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Data Model Architecture

### 1.1 Core Tables

#### `post_type_channel_config`
**Purpose:** Defines default channel assignments for each post type

```sql
CREATE TABLE post_type_channel_config (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,           -- 'themed', 'recipe', 'weekly_word', etc.
    channel VARCHAR(50) NOT NULL,              -- 'blog', 'facebook', 'instagram', 'newsletter', 'twitter'
    is_primary BOOLEAN DEFAULT FALSE,         -- Is this the primary channel?
    is_required BOOLEAN DEFAULT TRUE,         -- Must this channel be used?
    publication_delay_hours INTEGER DEFAULT 0, -- Delay after primary channel (0 = simultaneous)
    publication_time TIME,                    -- Override default time for this channel
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(post_type, channel),
    CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter'))
);

-- Indexes
CREATE INDEX idx_post_type_channel_config_post_type ON post_type_channel_config(post_type);
CREATE INDEX idx_post_type_channel_config_channel ON post_type_channel_config(channel);
CREATE INDEX idx_post_type_channel_config_active ON post_type_channel_config(is_active);
```

**Default Data:**
```sql
INSERT INTO post_type_channel_config (post_type, channel, is_primary, is_required, publication_delay_hours) VALUES
    -- Themed posts: Blog primary, Facebook required, Newsletter optional
    ('themed', 'blog', TRUE, TRUE, 0),
    ('themed', 'facebook', FALSE, TRUE, 2),      -- 2 hours after blog
    ('themed', 'newsletter', FALSE, FALSE, 0),    -- Same time as blog
    
    -- Recipe posts: Blog primary, Facebook required
    ('recipe', 'blog', TRUE, TRUE, 0),
    ('recipe', 'facebook', FALSE, TRUE, 2),
    
    -- Weekly word: Facebook primary, Instagram required, NO blog
    ('weekly_word', 'facebook', TRUE, TRUE, 0),
    ('weekly_word', 'instagram', FALSE, TRUE, 0),
    
    -- Weekly phrase: Facebook primary, Twitter required, NO blog
    ('weekly_phrase', 'facebook', TRUE, TRUE, 0),
    ('weekly_phrase', 'twitter', FALSE, TRUE, 0),
    
    -- Weekly insult: Facebook primary, Twitter required, NO blog
    ('weekly_insult', 'facebook', TRUE, TRUE, 0),
    ('weekly_insult', 'twitter', FALSE, TRUE, 0),
    
    -- Product profiles: Blog primary, Facebook + Instagram required
    ('profile_product', 'blog', TRUE, TRUE, 0),
    ('profile_product', 'facebook', FALSE, TRUE, 2),
    ('profile_product', 'instagram', FALSE, TRUE, 2),
    
    -- Surname profiles: Blog only
    ('profile_surname', 'blog', TRUE, TRUE, 0);
```

---

#### `calendar_item_channels`
**Purpose:** Per-item channel assignments (overrides defaults)

```sql
CREATE TABLE calendar_item_channels (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,            -- 'theme', 'recipe', 'weekly_word', etc.
    item_id INTEGER NOT NULL,                  -- ID of the calendar item
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL,              -- 'blog', 'facebook', 'instagram', etc.
    is_override BOOLEAN DEFAULT FALSE,         -- Is this an override of default?
    scheduled_date DATE,                        -- Override scheduled date
    scheduled_time TIME,                        -- Override scheduled time
    status VARCHAR(50) DEFAULT 'pending',       -- 'pending', 'approved', 'published', 'failed', 'skipped'
    publication_id INTEGER,                     -- FK to post_publication_status.id
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(category, item_id, year, week_number, channel),
    CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')),
    CHECK (status IN ('pending', 'approved', 'published', 'failed', 'skipped'))
);

-- Indexes
CREATE INDEX idx_calendar_item_channels_item ON calendar_item_channels(category, item_id, year, week_number);
CREATE INDEX idx_calendar_item_channels_status ON calendar_item_channels(status);
CREATE INDEX idx_calendar_item_channels_scheduled ON calendar_item_channels(scheduled_date, scheduled_time);
```

---

#### `post_approval`
**Purpose:** Review gate and approval tracking

```sql
CREATE TABLE post_approval (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    stage VARCHAR(50) NOT NULL,                -- 'planning', 'authoring', 'imaging', 'header', 'final'
    substage VARCHAR(50),                       -- Optional: specific substage
    approval_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'changes_requested'
    approver_id INTEGER,                         -- User ID (if user system exists)
    approval_notes TEXT,                        -- Comments from approver
    requested_changes TEXT,                     -- If changes_requested
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(post_id, stage, substage),
    CHECK (approval_status IN ('pending', 'approved', 'rejected', 'changes_requested')),
    CHECK (stage IN ('calendar', 'planning', 'research', 'authoring', 'imaging', 'header', 'final'))
);

-- Indexes
CREATE INDEX idx_post_approval_post ON post_approval(post_id);
CREATE INDEX idx_post_approval_status ON post_approval(approval_status);
CREATE INDEX idx_post_approval_stage ON post_approval(stage);
```

---

#### `scheduled_publications`
**Purpose:** Scheduled publication tracking

```sql
CREATE TABLE scheduled_publications (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL,              -- 'blog', 'facebook', 'instagram', etc.
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    scheduled_datetime TIMESTAMP NOT NULL,     -- Computed: scheduled_date + scheduled_time
    status VARCHAR(50) DEFAULT 'scheduled',    -- 'scheduled', 'processing', 'published', 'failed', 'cancelled'
    publication_id INTEGER,                    -- FK to post_publication_status.id
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')),
    CHECK (status IN ('scheduled', 'processing', 'published', 'failed', 'cancelled'))
);

-- Indexes
CREATE INDEX idx_scheduled_publications_datetime ON scheduled_publications(scheduled_datetime);
CREATE INDEX idx_scheduled_publications_status ON scheduled_publications(status);
CREATE INDEX idx_scheduled_publications_post ON scheduled_publications(post_id);
CREATE INDEX idx_scheduled_publications_channel ON scheduled_publications(channel);
```

---

#### `post_publication_status`
**Purpose:** Track publication status per channel

```sql
CREATE TABLE post_publication_status (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL,              -- 'blog', 'facebook', 'instagram', etc.
    status VARCHAR(50) DEFAULT 'not_published', -- 'not_published', 'scheduled', 'published', 'failed'
    external_id VARCHAR(255),                  -- ID from external platform (e.g., Facebook post ID)
    external_url TEXT,                         -- URL of published content
    published_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB,                            -- Platform-specific metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(post_id, channel),
    CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')),
    CHECK (status IN ('not_published', 'scheduled', 'published', 'failed'))
);

-- Indexes
CREATE INDEX idx_post_publication_status_post ON post_publication_status(post_id);
CREATE INDEX idx_post_publication_status_channel ON post_publication_status(channel);
CREATE INDEX idx_post_publication_status_status ON post_publication_status(status);
```

---

### 1.2 Extended Post Table Fields

**Add to existing `post` table:**
```sql
ALTER TABLE post ADD COLUMN IF NOT EXISTS post_type VARCHAR(50);
ALTER TABLE post ADD COLUMN IF NOT EXISTS publication_date DATE;
ALTER TABLE post ADD COLUMN IF NOT EXISTS publication_time TIME;
ALTER TABLE post ADD COLUMN IF NOT EXISTS automation_mode VARCHAR(50) DEFAULT 'auto'; -- 'auto', 'manual', 'paused'
ALTER TABLE post ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT TRUE;
ALTER TABLE post ADD COLUMN IF NOT EXISTS approval_required_stages TEXT[]; -- Array of stages requiring approval

-- Indexes
CREATE INDEX IF NOT EXISTS idx_post_post_type ON post(post_type);
CREATE INDEX IF NOT EXISTS idx_post_publication_datetime ON post(publication_date, publication_time);
CREATE INDEX IF NOT EXISTS idx_post_automation_mode ON post(automation_mode);
```

---

## 2. API Contract Architecture

### 2.1 Channel Assignment API

**Module:** `utils/channel_assignment.py`

```python
"""
Channel Assignment Engine
Determines which channels a post type should publish to
"""

def get_channels_for_post_type(post_type: str) -> List[Dict[str, Any]]:
    """
    Get default channel configuration for a post type.
    
    Returns:
        [
            {
                'channel': 'blog',
                'is_primary': True,
                'is_required': True,
                'publication_delay_hours': 0
            },
            ...
        ]
    """
    pass

def get_channels_for_item(category: str, item_id: int, year: int, week: int) -> List[str]:
    """
    Get actual channels for a calendar item (with overrides).
    
    Returns: ['blog', 'facebook', 'instagram']
    """
    pass

def assign_channels_to_item(category: str, item_id: int, year: int, week: int, 
                            channels: List[str], is_override: bool = False) -> bool:
    """
    Assign channels to a calendar item (override defaults).
    """
    pass
```

---

### 2.2 Production Pipeline API

**Module:** `blueprints/automation_core.py`

**Endpoints:**
```python
# Execute substage
POST /launchpad/one-click-publication/api/execute-substage/<stage>/<substage>
Body: {
    "post_id": int,
    "output": "blog",  # Optional: output channel
    "options": dict
}

# Get pipeline status
GET /launchpad/one-click-publication/api/pipeline-status/<post_id>?output=blog
Response: {
    "post_id": int,
    "post_type": str,
    "stages": {
        "calendar": {"status": "completed", "substages": [...]},
        "planning": {"status": "in_progress", "substages": [...]},
        ...
    }
}

# Skip substage
POST /launchpad/one-click-publication/api/skip-substage/<post_id>
Body: {
    "stage": str,
    "substage": str,
    "output": "blog",  # Optional: output channel
    "reason": str
}

# Pause/Resume
POST /launchpad/one-click-publication/api/pause-post/<post_id>
POST /launchpad/one-click-publication/api/resume-post/<post_id>

# Get pipeline for output channel
GET /launchpad/one-click-publication/api/pipeline/<post_id>?output=facebook
Response: {
    "post_id": int,
    "post_type": "weekly_word",
    "output_channel": "facebook",
    "stages": {
        "content": {"substages": [...]},
        "imaging": {"substages": [...]},
        "publish": {"substages": [...]}
    }
}
```

---

### 2.3 Review Gate API

**Module:** `blueprints/publication_approval.py`

**Endpoints:**
```python
# Request approval
POST /api/publication/approval/request/<post_id>
Body: {
    "stage": str,
    "substage": str (optional)
}

# Approve
POST /api/publication/approval/approve/<post_id>
Body: {
    "stage": str,
    "substage": str (optional),
    "notes": str
}

# Reject
POST /api/publication/approval/reject/<post_id>
Body: {
    "stage": str,
    "substage": str (optional),
    "reason": str,
    "requested_changes": str
}

# Get approval status
GET /api/publication/approval/status/<post_id>
Response: {
    "post_id": int,
    "approvals": [
        {
            "stage": "planning",
            "substage": "ideas",
            "status": "approved",
            "approved_at": "2025-01-15T10:00:00Z"
        },
        ...
    ]
}
```

---

### 2.4 Publication Scheduler API

**Module:** `blueprints/publication_scheduler.py`

**Endpoints:**
```python
# Schedule publication
POST /api/publication/schedule/<post_id>
Body: {
    "channels": ["blog", "facebook"],  # Optional: defaults to post_type config
    "publication_date": "2025-01-20",
    "publication_time": "14:00:00",
    "delay_hours": {}  # Optional: {"facebook": 2}
}

# Get scheduled publications
GET /api/publication/scheduled
Query: ?date=2025-01-20&channel=blog&status=scheduled

# Cancel scheduled publication
POST /api/publication/schedule/cancel/<scheduled_id>

# Publish now (bypass schedule)
POST /api/publication/publish-now/<post_id>
Body: {
    "channels": ["blog", "facebook"]  # Optional: defaults to all assigned
}
```

---

### 2.5 Multi-Channel Publisher API

**Module:** `blueprints/publication_multi_channel.py`

**Endpoints:**
```python
# Publish to channels
POST /api/publication/publish/<post_id>
Body: {
    "channels": ["blog", "facebook", "instagram"],  # Optional
    "force": false  # Bypass approval if true
}

# Get publication status
GET /api/publication/status/<post_id>
Response: {
    "post_id": int,
    "channels": {
        "blog": {
            "status": "published",
            "external_url": "https://...",
            "published_at": "2025-01-15T14:00:00Z"
        },
        "facebook": {
            "status": "scheduled",
            "scheduled_at": "2025-01-15T16:00:00Z"
        },
        ...
    }
}

# Retry failed publication
POST /api/publication/retry/<post_id>
Body: {
    "channel": "facebook"
}
```

---

## 3. Workflow Definition Architecture

### 3.1 Output Channel Stage Configuration (NEW)

**File:** `config/output_channel_stages.py` (NEW)

**Purpose:** Defines stages/substages per (post_type, output_channel) combination

```python
"""
Output Channel Stage Configuration
Defines stages/substages per (post_type, output_channel) combination
"""

OUTPUT_CHANNEL_STAGES = {
    # Blog outputs (full pipelines - fallback to post_type_substages.py)
    ('themed', 'blog'): {
        'use_post_type_config': True,  # Use config/post_type_substages.py
        'stages': None  # Inherit from post_type_substages
    },
    ('recipe', 'blog'): {
        'use_post_type_config': True
    },
    
    # Social media outputs (minimal pipelines)
    ('weekly_word', 'facebook'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_facebook', 'add_hashtags'],
            'imaging': ['optimize_for_facebook'],
            'publish': ['publish_to_facebook']
        }
    },
    ('weekly_word', 'instagram'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_instagram', 'create_caption'],
            'imaging': ['optimize_for_instagram', 'create_carousel'],
            'publish': ['publish_to_instagram']
        }
    },
    
    # Syndicated outputs (reuse blog content)
    ('themed', 'facebook'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
        }
    }
}

def get_stages_for_output(post_type: str, output_channel: str) -> dict:
    """
    Get stages/substages for a (post_type, output_channel) combination.
    
    Falls back to post_type only if no channel-specific config exists.
    """
    key = (post_type, output_channel)
    if key in OUTPUT_CHANNEL_STAGES:
        config = OUTPUT_CHANNEL_STAGES[key]
        if config.get('use_post_type_config'):
            # Fallback to post_type_substages.py
            from config.post_type_substages import get_substages_for_post_type
            return get_substages_for_post_type(post_type)
        return config
    
    # Default: use post_type config for blog, minimal for social media
    if output_channel == 'blog':
        from config.post_type_substages import get_substages_for_post_type
        return get_substages_for_post_type(post_type)
    
    # For social media, return minimal default
    return get_minimal_social_media_pipeline(post_type, output_channel)
```

---

### 3.2 Post Type Workflow Configuration

**File:** `config/post_type_workflows.py` (or use existing `config/post_type_substages.py`)

```python
"""
Post Type Workflow Definitions
Defines the complete pipeline for each post type
"""

POST_TYPE_WORKFLOWS = {
    'themed': {
        'stages': ['calendar', 'planning', 'research', 'authoring', 'imaging', 'header'],
        'requires_approval': ['planning', 'authoring', 'header', 'final'],
        'default_channels': ['blog', 'facebook', 'newsletter'],
        'automation_enabled': True
    },
    'recipe': {
        'stages': ['planning', 'authoring', 'imaging', 'header'],
        'requires_approval': ['authoring', 'header', 'final'],
        'default_channels': ['blog', 'facebook'],
        'automation_enabled': True
    },
    'weekly_word': {
        'stages': ['calendar', 'header'],  # Minimal pipeline
        'requires_approval': ['final'],
        'default_channels': ['facebook', 'instagram'],
        'automation_enabled': True
    },
    'weekly_phrase': {
        'stages': ['calendar', 'header'],
        'requires_approval': ['final'],
        'default_channels': ['facebook', 'twitter'],
        'automation_enabled': True
    },
    'weekly_insult': {
        'stages': ['calendar', 'header'],
        'requires_approval': ['final'],
        'default_channels': ['facebook', 'twitter'],
        'automation_enabled': True
    },
    'profile_product': {
        'stages': ['planning', 'authoring', 'imaging', 'header'],
        'requires_approval': ['authoring', 'header', 'final'],
        'default_channels': ['blog', 'facebook', 'instagram'],
        'automation_enabled': True
    },
    'profile_surname': {
        'stages': ['planning', 'authoring', 'imaging', 'header'],
        'requires_approval': ['authoring', 'header', 'final'],
        'default_channels': ['blog'],
        'automation_enabled': True
    }
}
```

---

### 3.2 Stage Execution Contract

**Pattern:** Each stage execution function follows this contract:

```python
def execute_<stage>_<substage>(post_id: int, options: dict = None) -> dict:
    """
    Execute a substage for a post.
    
    Contract:
    - Input: post_id, optional options dict
    - Output: {
        "success": bool,
        "data": dict,  # Stage-specific data
        "next_stage": str,  # Optional: auto-advance to next stage
        "requires_approval": bool,  # Does this require approval?
        "errors": list  # If success=False
    }
    - Side effects: Updates post_development, post_section, etc.
    - Idempotent: Safe to call multiple times
    - Error handling: Returns error dict, doesn't raise
    """
    pass
```

---

## 4. Review Gate Architecture

### 4.1 Approval Flow

```
┌─────────────────┐
│  Stage Complete │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Requires Approval?       │
│ (Check post_type config) │
└────────┬─────────────────┘
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Pending │ │ Auto-Advance │
│ Approval │ │ to Next      │
└────┬─────┘ └──────────────┘
     │
     ▼
┌─────────────────┐
│ User Reviews    │
│ (Dashboard UI)   │
└────────┬─────────┘
     │
     ▼
┌─────────────────┐
│ Approved?       │
└────────┬─────────┘
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Advance │ │ Request      │
│ to Next │ │ Changes      │
└─────────┘ └──────────────┘
```

### 4.2 Approval Check Function

```python
def check_approval_required(post_id: int, stage: str, substage: str = None) -> bool:
    """
    Check if approval is required before proceeding.
    
    Logic:
    1. Check post.requires_approval (global flag)
    2. Check post_type_workflows[post_type]['requires_approval'] (stage list)
    3. Check post_approval table for existing approval
    4. Return True if approval needed and not yet approved
    """
    pass

def can_proceed_to_next_stage(post_id: int, stage: str) -> bool:
    """
    Check if post can proceed to next stage.
    
    Logic:
    1. Current stage must be complete
    2. If approval required, must be approved
    3. No blocking errors
    """
    pass
```

---

## 5. Publication Scheduler Architecture

### 5.1 Scheduling Logic

```python
def schedule_publication(post_id: int, channels: List[str] = None) -> dict:
    """
    Schedule publication for a post.
    
    Logic:
    1. Get post_type
    2. Get channels (from param or post_type_channel_config)
    3. Get publication_date/time from post table
    4. For each channel:
       a. Calculate scheduled_datetime (accounting for delays)
       b. Create scheduled_publications entry
       c. Create post_publication_status entry (status='scheduled')
    5. Return schedule details
    """
    pass
```

### 5.2 Background Job

**File:** `scripts/scheduled_publisher.py`

```python
"""
Background job that runs every minute to check for scheduled publications.
"""

def process_scheduled_publications():
    """
    Main loop:
    1. Query scheduled_publications WHERE scheduled_datetime <= NOW() AND status='scheduled'
    2. For each:
       a. Update status to 'processing'
       b. Check approval (if required)
       c. Call appropriate publisher function
       d. Update status to 'published' or 'failed'
       e. Update post_publication_status
    """
    pass
```

---

## 6. Multi-Channel Publisher Architecture

### 6.1 Publisher Interface

**Module:** `utils/channel_publishers.py`

```python
class ChannelPublisher(ABC):
    """Base class for all channel publishers"""
    
    @abstractmethod
    def publish(self, post_id: int, content: dict) -> dict:
        """
        Publish content to channel.
        
        Returns:
            {
                "success": bool,
                "external_id": str,
                "external_url": str,
                "error": str
            }
        """
        pass
    
    @abstractmethod
    def validate(self, post_id: int) -> dict:
        """Validate content before publishing"""
        pass

class BlogPublisher(ChannelPublisher):
    """Publishes to clan.com blog"""
    pass

class FacebookPublisher(ChannelPublisher):
    """Publishes to Facebook"""
    pass

class InstagramPublisher(ChannelPublisher):
    """Publishes to Instagram"""
    pass

class TwitterPublisher(ChannelPublisher):
    """Publishes to Twitter"""
    pass

class NewsletterPublisher(ChannelPublisher):
    """Publishes to newsletter"""
    pass
```

### 6.2 Unified Publisher

```python
def publish_to_channels(post_id: int, channels: List[str] = None, 
                       force: bool = False) -> dict:
    """
    Publish post to multiple channels.
    
    Logic:
    1. Get channels (from param or post_type_channel_config)
    2. For each channel:
       a. Validate content (if not force)
       b. Check approval (if required and not force)
       c. Get appropriate publisher
       d. Call publisher.publish()
       e. Update post_publication_status
       f. Handle delays (if configured)
    3. Return aggregated results
    """
    pass
```

---

## 7. Error Handling & Reliability Patterns

### 7.1 Retry Logic

```python
def publish_with_retry(post_id: int, channel: str, max_retries: int = 3) -> dict:
    """
    Publish with automatic retry on failure.
    
    Logic:
    1. Attempt publish
    2. If failure:
       a. Increment retry_count in post_publication_status
       b. If retry_count < max_retries:
          - Wait (exponential backoff)
          - Retry
       c. If retry_count >= max_retries:
          - Mark as failed
          - Log error
          - Notify user
    """
    pass
```

### 7.2 Error Tracking

```python
# All publisher functions should:
# 1. Log errors to post_publication_status.error_message
# 2. Update status to 'failed'
# 3. Increment retry_count
# 4. Raise structured exceptions (not generic)
```

### 7.3 State Consistency

```python
def ensure_state_consistency(post_id: int) -> dict:
    """
    Check and fix state inconsistencies.
    
    Checks:
    1. scheduled_publications.status matches post_publication_status.status
    2. post.status matches pipeline progress
    3. approval status matches stage requirements
    4. Fix any inconsistencies found
    """
    pass
```

---

## 8. Integration Points

### 8.1 Calendar → Pipeline

**Integration:** `blueprints/automation_calendar.py`

```python
def get_next_up_item() -> dict:
    """
    Get next item from calendar for automation.
    
    Logic:
    1. Use utils/calendar_resolver.py to get current week
    2. Resolve items for current week
    3. Filter by post_type (if needed)
    4. Check if post already exists
    5. Return item with post_id (if exists) or None
    """
    pass
```

### 8.2 Pipeline → Publication

**Integration:** `blueprints/automation_core.py`

```python
def on_pipeline_complete(post_id: int):
    """
    Called when pipeline completes.
    
    Logic:
    1. Check if approval required
    2. If approved (or not required):
       a. Get channels from post_type_channel_config
       b. Schedule publication
       c. Update post status
    """
    pass
```

### 8.3 Publication → Status Tracking

**Integration:** All publisher functions update `post_publication_status`

---

## 9. Configuration Management

### 9.1 Centralized Config

**File:** `config/publication_config.py`

```python
"""
Centralized publication configuration
"""

# Review gate settings
REVIEW_GATES_ENABLED = True
REQUIRE_APPROVAL_BY_DEFAULT = True

# Scheduling settings
SCHEDULER_ENABLED = True
SCHEDULER_CHECK_INTERVAL_SECONDS = 60

# Retry settings
MAX_PUBLICATION_RETRIES = 3
RETRY_BACKOFF_SECONDS = [60, 300, 900]  # 1min, 5min, 15min

# Channel settings
CHANNEL_API_TIMEOUT_SECONDS = 30
CHANNEL_RATE_LIMIT_DELAY_SECONDS = 1
```

---

## 10. Testing & Validation Framework

### 10.1 Unit Test Structure

```python
# tests/test_channel_assignment.py
def test_get_channels_for_post_type()
def test_get_channels_for_item()
def test_override_channels()

# tests/test_publication_scheduler.py
def test_schedule_publication()
def test_calculate_delayed_publication_time()
def test_process_scheduled_publications()

# tests/test_multi_channel_publisher.py
def test_publish_to_channels()
def test_retry_logic()
def test_error_handling()
```

### 10.2 Integration Test Structure

```python
# tests/integration/test_full_pipeline.py
def test_themed_post_full_pipeline()
def test_weekly_word_minimal_pipeline()
def test_multi_channel_publication()
```

---

## 11. Implementation Checklist

### Phase 1: Data Model
- [ ] Create `post_type_channel_config` table
- [ ] Create `calendar_item_channels` table
- [ ] Create `post_approval` table
- [ ] Create `scheduled_publications` table
- [ ] Create `post_publication_status` table
- [ ] Add fields to `post` table
- [ ] Populate default channel configs

### Phase 2: Core APIs
- [ ] Implement `utils/channel_assignment.py`
- [ ] Implement `blueprints/publication_approval.py`
- [ ] Implement `blueprints/publication_scheduler.py`
- [ ] Implement `blueprints/publication_multi_channel.py`

### Phase 3: Publishers
- [ ] Implement `BlogPublisher` (extend existing)
- [ ] Implement `FacebookPublisher` (extend existing)
- [ ] Implement `InstagramPublisher` (new)
- [ ] Implement `TwitterPublisher` (new)
- [ ] Implement `NewsletterPublisher` (integrate existing)

### Phase 4: Automation Integration
- [ ] Update `automation_core.py` to support all stages
- [ ] Add weekly content types to `post_type_substages.py`
- [ ] Fix calendar sync in `automation_calendar.py`
- [ ] Implement review gate checks in pipeline

### Phase 5: Background Jobs
- [ ] Implement `scripts/scheduled_publisher.py`
- [ ] Set up cron/task queue
- [ ] Implement retry logic
- [ ] Implement error notifications

### Phase 6: Testing
- [ ] Unit tests for all modules
- [ ] Integration tests for full pipeline
- [ ] End-to-end tests for each post type
- [ ] Load testing for scheduler

---

## 12. Documentation Requirements

- [ ] API documentation for all endpoints
- [ ] Database schema documentation
- [ ] Workflow diagrams for each post type
- [ ] Channel assignment decision tree
- [ ] Error handling guide
- [ ] Deployment guide
- [ ] Operations manual

---

## Summary

This architecture provides:

✅ **Clear Data Models** - All tables defined with relationships  
✅ **API Contracts** - Well-defined interfaces between components  
✅ **Workflow Definitions** - Complete pipeline for each post type  
✅ **Channel Assignment Framework** - Rules and override mechanisms  
✅ **Review Gate Architecture** - Approval workflow system  
✅ **Error Handling Patterns** - Retry logic and state consistency  
✅ **Integration Points** - How components connect  
✅ **Testing Framework** - Unit and integration test structure  

**Status:** Ready for implementation with clear guidelines and contracts.

