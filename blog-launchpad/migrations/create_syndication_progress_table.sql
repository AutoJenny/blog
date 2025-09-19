-- =====================================================
-- SYNDICATION PROGRESS TRACKING TABLE
-- =====================================================
-- This table tracks which blog post sections have been processed
-- for syndication across different platforms and channel types.
-- It enables automated selection of the next unprocessed section.

CREATE TABLE IF NOT EXISTS syndication_progress (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    channel_type_id INTEGER NOT NULL,
    process_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- Ensure unique combination of post, section, platform, and channel
    UNIQUE(post_id, section_id, platform_id, channel_type_id)
    
    -- Foreign key constraints (if tables exist)
    -- FOREIGN KEY (post_id) REFERENCES blog_posts(id),
    -- FOREIGN KEY (section_id) REFERENCES post_section(id),
    -- FOREIGN KEY (platform_id) REFERENCES platforms(id),
    -- FOREIGN KEY (channel_type_id) REFERENCES channel_types(id),
    -- FOREIGN KEY (process_id) REFERENCES content_processes(id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Index for finding next unprocessed section
CREATE INDEX idx_syndication_progress_status_platform_channel 
ON syndication_progress(status, platform_id, channel_type_id);

-- Index for finding sections by post
CREATE INDEX idx_syndication_progress_post_section 
ON syndication_progress(post_id, section_id);

-- Index for finding sections by platform/channel
CREATE INDEX idx_syndication_progress_platform_channel 
ON syndication_progress(platform_id, channel_type_id);

-- Index for finding completed sections
CREATE INDEX idx_syndication_progress_completed 
ON syndication_progress(completed_at) WHERE completed_at IS NOT NULL;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE syndication_progress IS 'Tracks syndication progress for each blog post section across platforms and channels';
COMMENT ON COLUMN syndication_progress.post_id IS 'ID of the blog post';
COMMENT ON COLUMN syndication_progress.section_id IS 'ID of the specific section within the post';
COMMENT ON COLUMN syndication_progress.platform_id IS 'Platform ID (Facebook, Twitter, etc.)';
COMMENT ON COLUMN syndication_progress.channel_type_id IS 'Channel type ID (feed_post, story_post, etc.)';
COMMENT ON COLUMN syndication_progress.process_id IS 'Process ID used for syndication';
COMMENT ON COLUMN syndication_progress.status IS 'Current status: pending, processing, completed, failed';
COMMENT ON COLUMN syndication_progress.completed_at IS 'Timestamp when syndication was completed';
COMMENT ON COLUMN syndication_progress.error_message IS 'Error message if status is failed';

-- =====================================================
-- SAMPLE DATA (for testing)
-- =====================================================

-- Insert sample progress entries for testing
-- (These will be created automatically by the system)
INSERT INTO syndication_progress (post_id, section_id, platform_id, channel_type_id, process_id, status) VALUES
(1, 1, 1, 1, 1, 'completed'),
(1, 2, 1, 1, 1, 'pending'),
(1, 3, 1, 1, 1, 'pending'),
(2, 1, 1, 1, 1, 'completed'),
(2, 2, 1, 1, 1, 'completed'),
(2, 3, 1, 1, 1, 'pending')
ON CONFLICT (post_id, section_id, platform_id, channel_type_id) DO NOTHING;
