-- Migration: Create Knowledge Base tables
-- Purpose: Store CLAN Knowledge Base categories and articles locally
-- Date: 2025-11-11

BEGIN;

-- Knowledge Base Categories Table
CREATE TABLE IF NOT EXISTS clan_kb_categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    url_key TEXT,
    meta_title TEXT,
    meta_keywords TEXT,
    meta_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    parent_id INTEGER REFERENCES clan_kb_categories(id) ON DELETE SET NULL,
    path TEXT,
    level INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0,
    children_count INTEGER DEFAULT 0,
    clan_created_at TIMESTAMP,
    clan_updated_at TIMESTAMP,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for clan_kb_categories
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_parent_id ON clan_kb_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_url_key ON clan_kb_categories(url_key);
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_is_active ON clan_kb_categories(is_active);
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_path ON clan_kb_categories(path);

-- Knowledge Base Articles Table
CREATE TABLE IF NOT EXISTS clan_kb_articles (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES clan_kb_categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    url_key TEXT,
    feature_image TEXT,
    feature_image_local TEXT,
    short_text TEXT,
    text TEXT,
    meta_title TEXT,
    meta_keywords TEXT,
    meta_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    user_id INTEGER,
    user_name TEXT,
    votes_sum DECIMAL(10,2),
    votes_num INTEGER DEFAULT 0,
    rating DECIMAL(3,2),
    position INTEGER DEFAULT 0,
    clan_created_at TIMESTAMP,
    clan_updated_at TIMESTAMP,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_content_change_at TIMESTAMP,
    article_content_hash TEXT
);

-- Indexes for clan_kb_articles
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_category_id ON clan_kb_articles(category_id);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_url_key ON clan_kb_articles(url_key);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_is_active ON clan_kb_articles(is_active);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_updated_at ON clan_kb_articles(clan_updated_at);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_position ON clan_kb_articles(category_id, position);

-- Full-text search index (for PostgreSQL full-text search - available as alternative to vector search)
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_text_fts ON clan_kb_articles USING GIN(to_tsvector('english', text));

-- Index for change detection queries
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_content_change 
ON clan_kb_articles(last_content_change_at) 
WHERE last_content_change_at IS NOT NULL;

-- Add comments
COMMENT ON TABLE clan_kb_categories IS 'Knowledge Base category hierarchy from CLAN.com';
COMMENT ON TABLE clan_kb_articles IS 'Knowledge Base articles from CLAN.com';
COMMENT ON COLUMN clan_kb_articles.article_content_hash IS 'SHA-256 hash of name, url_key, text, short_text, feature_image for change detection';
COMMENT ON COLUMN clan_kb_articles.last_content_change_at IS 'Timestamp when article content actually changed (detected via hash comparison)';
COMMENT ON COLUMN clan_kb_articles.feature_image_local IS 'Local path to cached feature image (downloaded from feature_image URL)';

COMMIT;

