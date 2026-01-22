-- Migration: Create KB Topic Rota System tables
-- Date: 2026-01-22
-- Purpose: Store discovered topics from KB clustering, similarity matrix, weekly rota schedule, and aggregated content

-- Table 1: kb_topics
-- Stores discovered topics from KB clustering
CREATE TABLE IF NOT EXISTS kb_topics (
    id SERIAL PRIMARY KEY,
    topic_name TEXT NOT NULL,
    topic_description TEXT,
    topic_keywords TEXT[],  -- Array of keywords extracted from cluster
    cluster_id INTEGER,  -- Original cluster ID from clustering run
    embedding_vector REAL[],  -- Topic centroid embedding (1024 dims)
    article_ids INTEGER[],  -- Articles that belong to this topic
    category_ids INTEGER[],  -- Categories this topic spans
    topic_type VARCHAR(50),  -- 'practical', 'historical', 'cultural', 'design', 'product', etc.
    priority INTEGER DEFAULT 0,  -- For rota ordering
    is_active BOOLEAN DEFAULT TRUE,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT  -- Manual notes/refinements
);

CREATE INDEX IF NOT EXISTS idx_kb_topics_active ON kb_topics(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_kb_topics_priority ON kb_topics(priority, is_active);
CREATE INDEX IF NOT EXISTS idx_kb_topics_article_ids ON kb_topics USING GIN(article_ids);
CREATE INDEX IF NOT EXISTS idx_kb_topics_category_ids ON kb_topics USING GIN(category_ids);
CREATE INDEX IF NOT EXISTS idx_kb_topics_topic_type ON kb_topics(topic_type) WHERE topic_type IS NOT NULL;

COMMENT ON TABLE kb_topics IS 'Stores discovered topics from KB clustering for weekly social media rota';
COMMENT ON COLUMN kb_topics.topic_name IS 'Abstract topic name (e.g., "Tartan Design Principles")';
COMMENT ON COLUMN kb_topics.topic_keywords IS 'Array of keywords extracted from cluster articles';
COMMENT ON COLUMN kb_topics.cluster_id IS 'Original cluster ID from clustering algorithm';
COMMENT ON COLUMN kb_topics.embedding_vector IS 'Topic centroid embedding (1024 dimensions from e5-large-v2)';
COMMENT ON COLUMN kb_topics.article_ids IS 'Array of KB article IDs that belong to this topic';
COMMENT ON COLUMN kb_topics.category_ids IS 'Array of category IDs this topic spans';
COMMENT ON COLUMN kb_topics.topic_type IS 'Type classification: practical, historical, cultural, design, product, etc.';

-- Table 2: kb_topic_similarity
-- Pre-computed similarity between topics (for diversity)
CREATE TABLE IF NOT EXISTS kb_topic_similarity (
    topic1_id INTEGER REFERENCES kb_topics(id) ON DELETE CASCADE,
    topic2_id INTEGER REFERENCES kb_topics(id) ON DELETE CASCADE,
    similarity_score DECIMAL(4,3) NOT NULL,  -- 0.0 to 1.0 (cosine similarity)
    distance DECIMAL(8,4),  -- L2 distance between embeddings
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (topic1_id, topic2_id),
    CHECK (topic1_id < topic2_id)  -- Ensure one direction only
);

CREATE INDEX IF NOT EXISTS idx_topic_similarity_score ON kb_topic_similarity(similarity_score);
CREATE INDEX IF NOT EXISTS idx_topic_similarity_topic1 ON kb_topic_similarity(topic1_id);
CREATE INDEX IF NOT EXISTS idx_topic_similarity_topic2 ON kb_topic_similarity(topic2_id);

COMMENT ON TABLE kb_topic_similarity IS 'Pre-computed pairwise similarity between topics for diversity scheduling';
COMMENT ON COLUMN kb_topic_similarity.similarity_score IS 'Cosine similarity between topic embeddings (0.0 to 1.0)';
COMMENT ON COLUMN kb_topic_similarity.distance IS 'L2 distance between topic embeddings';

-- Table 3: kb_topic_rota
-- Weekly schedule of topics
CREATE TABLE IF NOT EXISTS kb_topic_rota (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES kb_topics(id) ON DELETE SET NULL,
    scheduled_week INTEGER NOT NULL,  -- ISO week number
    scheduled_year INTEGER NOT NULL,
    scheduled_date DATE,  -- First day of week (Monday)
    diversity_score DECIMAL(4,3),  -- How diverse from recent topics (0.0 to 1.0)
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled, ready, published, skipped
    content_summary TEXT,  -- Aggregated content preview
    source_article_ids INTEGER[],  -- Which articles were aggregated
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scheduled_year, scheduled_week)
);

CREATE INDEX IF NOT EXISTS idx_rota_year_week ON kb_topic_rota(scheduled_year, scheduled_week);
CREATE INDEX IF NOT EXISTS idx_rota_status ON kb_topic_rota(status);
CREATE INDEX IF NOT EXISTS idx_rota_date ON kb_topic_rota(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_rota_topic ON kb_topic_rota(topic_id) WHERE topic_id IS NOT NULL;

COMMENT ON TABLE kb_topic_rota IS 'Weekly schedule of topics for social media content';
COMMENT ON COLUMN kb_topic_rota.scheduled_week IS 'ISO week number (1-53)';
COMMENT ON COLUMN kb_topic_rota.scheduled_date IS 'First day of week (Monday)';
COMMENT ON COLUMN kb_topic_rota.diversity_score IS 'Diversity score from recent topics (higher = more diverse)';
COMMENT ON COLUMN kb_topic_rota.status IS 'Status: scheduled, ready, published, skipped';

-- Table 4: kb_rota_history
-- Track what's been posted for diversity tracking
CREATE TABLE IF NOT EXISTS kb_rota_history (
    id SERIAL PRIMARY KEY,
    rota_id INTEGER REFERENCES kb_topic_rota(id) ON DELETE SET NULL,
    topic_id INTEGER REFERENCES kb_topics(id) ON DELETE SET NULL,
    posted_date DATE,
    diversity_score DECIMAL(4,3),
    similarity_to_previous DECIMAL(4,3),  -- Similarity to previous week
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rota_history_date ON kb_rota_history(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_rota_history_topic ON kb_rota_history(topic_id);
CREATE INDEX IF NOT EXISTS idx_rota_history_rota ON kb_rota_history(rota_id) WHERE rota_id IS NOT NULL;

COMMENT ON TABLE kb_rota_history IS 'History of posted topics for diversity calculations';
COMMENT ON COLUMN kb_rota_history.posted_date IS 'Date when topic was posted';
COMMENT ON COLUMN kb_rota_history.similarity_to_previous IS 'Similarity score to previous week topic';

-- Table 5: kb_topic_content
-- Stores aggregated content for each topic (for social media production)
CREATE TABLE IF NOT EXISTS kb_topic_content (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES kb_topics(id) ON DELETE CASCADE,
    rota_id INTEGER REFERENCES kb_topic_rota(id) ON DELETE CASCADE,
    aggregated_text TEXT NOT NULL,  -- Combined content from multiple articles
    source_article_ids INTEGER[] NOT NULL,  -- Which articles contributed
    source_chunk_ids INTEGER[],  -- Specific chunks used
    content_hash TEXT,  -- Hash for change detection
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_topic_content_topic ON kb_topic_content(topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_content_rota ON kb_topic_content(rota_id) WHERE rota_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_topic_content_hash ON kb_topic_content(content_hash) WHERE content_hash IS NOT NULL;

COMMENT ON TABLE kb_topic_content IS 'Aggregated content from multiple KB articles for each topic';
COMMENT ON COLUMN kb_topic_content.aggregated_text IS 'Combined text content from multiple articles';
COMMENT ON COLUMN kb_topic_content.source_article_ids IS 'Array of KB article IDs that contributed content';
COMMENT ON COLUMN kb_topic_content.source_chunk_ids IS 'Array of content_chunks.id that were used';
COMMENT ON COLUMN kb_topic_content.content_hash IS 'Hash of content for change detection';
