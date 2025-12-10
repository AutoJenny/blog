-- Migration: Add content_format column to post_type_channel_config
-- Date: 2025-12-10
-- Purpose: Support three-level hierarchy: Post Type → Channel → Content Format

-- Step 1: Create table if it doesn't exist, or alter if it does
DO $$
BEGIN
    -- Check if table exists
    IF NOT EXISTS (SELECT FROM information_schema.tables 
                   WHERE table_schema = 'public' 
                   AND table_name = 'post_type_channel_config') THEN
        -- Create table with content_format from the start
        CREATE TABLE post_type_channel_config (
            id SERIAL PRIMARY KEY,
            post_type VARCHAR(50) NOT NULL,
            channel VARCHAR(50) NOT NULL,
            content_format VARCHAR(50) NOT NULL DEFAULT 'article',
            is_primary BOOLEAN DEFAULT FALSE,
            is_required BOOLEAN DEFAULT TRUE,
            publication_delay_hours INTEGER DEFAULT 0,
            publication_time TIME,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(post_type, channel, content_format),
            CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')),
            CHECK (content_format IN (
                'article', 'recipe', 'profile', 
                'word_of_day', 'phrase_of_day', 'insult_of_day',
                'syndication', 'product', 'carousel', 'roundup'
            ))
        );
        
        -- Create indexes
        CREATE INDEX idx_post_type_channel_config_post_type 
            ON post_type_channel_config(post_type);
        CREATE INDEX idx_post_type_channel_config_channel 
            ON post_type_channel_config(channel);
        CREATE INDEX idx_post_type_channel_config_active 
            ON post_type_channel_config(is_active);
        CREATE INDEX idx_post_type_channel_config_format 
            ON post_type_channel_config(content_format);
    ELSE
        -- Table exists, add content_format column
        IF NOT EXISTS (SELECT FROM information_schema.columns 
                       WHERE table_schema = 'public' 
                       AND table_name = 'post_type_channel_config' 
                       AND column_name = 'content_format') THEN
            -- Add content_format column with default
            ALTER TABLE post_type_channel_config 
            ADD COLUMN content_format VARCHAR(50) NOT NULL DEFAULT 'article';
            
            -- Drop old unique constraint if it exists (without content_format)
            ALTER TABLE post_type_channel_config 
            DROP CONSTRAINT IF EXISTS post_type_channel_config_post_type_channel_key;
            
            -- Add new unique constraint with content_format
            ALTER TABLE post_type_channel_config 
            ADD CONSTRAINT post_type_channel_config_post_type_channel_format_key 
            UNIQUE (post_type, channel, content_format);
            
            -- Add check constraint for content_format
            ALTER TABLE post_type_channel_config 
            ADD CONSTRAINT post_type_channel_config_content_format_check 
            CHECK (content_format IN (
                'article', 'recipe', 'profile', 
                'word_of_day', 'phrase_of_day', 'insult_of_day',
                'syndication', 'product', 'carousel', 'roundup'
            ));
            
            -- Create index on content_format
            CREATE INDEX IF NOT EXISTS idx_post_type_channel_config_format 
            ON post_type_channel_config(content_format);
            
            -- Update existing rows with appropriate defaults
            -- Blog posts default to 'article'
            UPDATE post_type_channel_config 
            SET content_format = 'article' 
            WHERE channel = 'blog' AND content_format = 'article';
            
            -- Social media posts default to 'syndication' (for blog-derived content)
            UPDATE post_type_channel_config 
            SET content_format = 'syndication' 
            WHERE channel IN ('facebook', 'instagram', 'twitter', 'newsletter') 
            AND content_format = 'article';
        END IF;
    END IF;
END $$;

-- Step 2: Populate default data (only if table is empty or new rows needed)
-- This uses INSERT ... ON CONFLICT to avoid duplicates

INSERT INTO post_type_channel_config (post_type, channel, content_format, is_primary, is_required, publication_delay_hours) 
VALUES
    -- Themed posts
    ('themed', 'blog', 'article', TRUE, TRUE, 0),
    ('themed', 'facebook', 'syndication', FALSE, TRUE, 2),
    ('themed', 'newsletter', 'syndication', FALSE, FALSE, 0),
    
    -- Recipe posts
    ('recipe', 'blog', 'recipe', TRUE, TRUE, 0),
    ('recipe', 'facebook', 'recipe', FALSE, TRUE, 2),
    
    -- Weekly word
    ('weekly_word', 'facebook', 'word_of_day', TRUE, TRUE, 0),
    ('weekly_word', 'instagram', 'word_of_day', FALSE, TRUE, 0),
    
    -- Weekly phrase
    ('weekly_phrase', 'facebook', 'phrase_of_day', TRUE, TRUE, 0),
    ('weekly_phrase', 'twitter', 'phrase_of_day', FALSE, TRUE, 0),
    
    -- Weekly insult
    ('weekly_insult', 'facebook', 'insult_of_day', TRUE, TRUE, 0),
    ('weekly_insult', 'twitter', 'insult_of_day', FALSE, TRUE, 0),
    
    -- Product profiles
    ('profile_product', 'blog', 'profile', TRUE, TRUE, 0),
    ('profile_product', 'facebook', 'syndication', FALSE, TRUE, 2),
    ('profile_product', 'instagram', 'carousel', FALSE, TRUE, 2),
    
    -- Surname profiles
    ('profile_surname', 'blog', 'profile', TRUE, TRUE, 0)
ON CONFLICT (post_type, channel, content_format) 
DO UPDATE SET 
    is_primary = EXCLUDED.is_primary,
    is_required = EXCLUDED.is_required,
    publication_delay_hours = EXCLUDED.publication_delay_hours,
    updated_at = NOW();

-- Step 3: Add comment for documentation
COMMENT ON TABLE post_type_channel_config IS 
'Defines channel assignments and content formats for each post type. 
Three-level hierarchy: Post Type → Channel → Content Format.
Example: recipe → facebook → recipe (recipe-specific Facebook format)';

COMMENT ON COLUMN post_type_channel_config.content_format IS 
'Content format/type within the channel. Examples: 
- Blog: article, recipe, profile, word_of_day
- Facebook: recipe, word_of_day, syndication, product
- Instagram: word_of_day, carousel, syndication
- Twitter: word_of_day, phrase_of_day, syndication
- Newsletter: syndication, roundup';

