-- =====================================================
-- DAILY PRODUCT POSTS - Database Schema
-- Pathfinder project for automated daily Facebook posts
-- =====================================================

-- Products table - Store Clan.com product information
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clan_product_id VARCHAR(100) UNIQUE NOT NULL,  -- Clan.com product ID
    name VARCHAR(255) NOT NULL,                    -- Product name
    description TEXT,                              -- Product description
    category VARCHAR(100),                         -- Product category
    price DECIMAL(10,2),                          -- Product price
    image_url VARCHAR(500),                       -- Product image URL
    product_url VARCHAR(500),                     -- Clan.com product URL
    is_active BOOLEAN DEFAULT true,               -- Whether product is available
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily posts table - Track what was posted when
CREATE TABLE IF NOT EXISTS daily_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    post_date DATE NOT NULL,                      -- Date the post was made
    content_text TEXT NOT NULL,                   -- Generated post content
    content_type VARCHAR(50) DEFAULT 'feature',   -- 'feature', 'benefit', 'story'
    platform VARCHAR(50) DEFAULT 'facebook',      -- Platform posted to
    facebook_post_id VARCHAR(100),                -- Facebook post ID if posted
    status VARCHAR(20) DEFAULT 'draft',           -- 'draft', 'posted', 'scheduled'
    posted_at TIMESTAMP,                          -- When it was actually posted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post performance table - Basic engagement metrics
CREATE TABLE IF NOT EXISTS post_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_post_id INTEGER REFERENCES daily_posts(id),
    likes_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    reach_count INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2),                 -- Calculated engagement rate
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product content templates - Simple templates for different content types
CREATE TABLE IF NOT EXISTS product_content_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name VARCHAR(100) NOT NULL,          -- Template name
    content_type VARCHAR(50) NOT NULL,            -- 'feature', 'benefit', 'story'
    template_prompt TEXT NOT NULL,                -- LLM prompt template
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default content templates
INSERT INTO product_content_templates (template_name, content_type, template_prompt) VALUES
('Feature Focus', 'feature', 'Create an engaging Facebook post about this Clan.com product, focusing on its key features and specifications. Keep it under 200 characters, include 3-5 relevant hashtags, and make it sound exciting and authentic. Product: {product_name} - {product_description} - Price: {product_price}'),
('Benefit Focus', 'benefit', 'Create an engaging Facebook post about this Clan.com product, focusing on the benefits and value it provides to customers. Keep it under 200 characters, include 3-5 relevant hashtags, and make it sound compelling and customer-focused. Product: {product_name} - {product_description} - Price: {product_price}'),
('Story Focus', 'story', 'Create an engaging Facebook post about this Clan.com product, telling a story about its heritage, craftsmanship, or how it fits into Scottish culture. Keep it under 200 characters, include 3-5 relevant hashtags, and make it emotional and storytelling-focused. Product: {product_name} - {product_description} - Price: {product_price}');

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_clan_id ON products(clan_product_id);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_daily_posts_date ON daily_posts(post_date);
CREATE INDEX IF NOT EXISTS idx_daily_posts_status ON daily_posts(status);
CREATE INDEX IF NOT EXISTS idx_post_performance_post_id ON post_performance(daily_post_id);
