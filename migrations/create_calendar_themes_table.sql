-- Create separate calendar_themes table
-- Themes are completely separate from ideas - they are week-wide concepts, not content ideas

CREATE TABLE IF NOT EXISTS calendar_themes (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52 (perpetual week this theme belongs to)
    theme_title VARCHAR(255) NOT NULL,
    theme_description TEXT,
    seasonal_context TEXT,
    priority VARCHAR(20) DEFAULT 'random' CHECK (priority IN ('random', 'mandatory')),
    tags JSONB,
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    is_evergreen BOOLEAN DEFAULT FALSE,
    evergreen_frequency VARCHAR(20) DEFAULT 'low-frequency',
    last_used_date DATE,
    usage_count INTEGER DEFAULT 0,
    evergreen_notes TEXT,
    sources JSONB DEFAULT '[]'::jsonb,
    important_notes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_calendar_themes_week_number ON calendar_themes(week_number);
CREATE INDEX IF NOT EXISTS idx_calendar_themes_priority ON calendar_themes(priority);
CREATE INDEX IF NOT EXISTS idx_calendar_themes_evergreen ON calendar_themes(is_evergreen);

-- Migrate existing themes from calendar_ideas
-- Use dynamic SQL to handle optional columns
DO $$
DECLARE
    has_sources BOOLEAN;
    has_important_notes BOOLEAN;
    sql_text TEXT;
BEGIN
    -- Check if columns exist
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'calendar_ideas' AND column_name = 'sources'
    ) INTO has_sources;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'calendar_ideas' AND column_name = 'important_notes'
    ) INTO has_important_notes;
    
    -- Build dynamic SQL based on column existence
    sql_text := 'INSERT INTO calendar_themes (
        id, week_number, theme_title, theme_description, seasonal_context,
        priority, tags, is_recurring, can_span_weeks, max_weeks,
        is_evergreen, evergreen_frequency, last_used_date, usage_count,
        evergreen_notes, sources, important_notes, created_at, updated_at
    )
    SELECT 
        ci.id,
        ci.week_number,
        ci.idea_title,
        ci.idea_description,
        ci.seasonal_context,
        COALESCE(ci.priority::text, ''random''),
        ci.tags,
        COALESCE(ci.is_recurring, TRUE),
        COALESCE(ci.can_span_weeks, FALSE),
        COALESCE(ci.max_weeks, 1),
        COALESCE(ci.is_evergreen, FALSE),
        COALESCE(ci.evergreen_frequency, ''low-frequency''),
        ci.last_used_date,
        COALESCE(ci.usage_count, 0),
        ci.evergreen_notes,';
    
    IF has_sources THEN
        sql_text := sql_text || ' COALESCE(ci.sources, ''[]''::jsonb),';
    ELSE
        sql_text := sql_text || ' ''[]''::jsonb,';
    END IF;
    
    IF has_important_notes THEN
        sql_text := sql_text || ' COALESCE(ci.important_notes, ''[]''::jsonb),';
    ELSE
        sql_text := sql_text || ' ''[]''::jsonb,';
    END IF;
    
    sql_text := sql_text || ' ci.created_at,
        ci.updated_at
    FROM calendar_ideas ci
    WHERE ci.item_classification = ''theme''
    ON CONFLICT (id) DO NOTHING';
    
    EXECUTE sql_text;
END $$;

-- Update calendar_schedule to reference calendar_themes instead of calendar_ideas for themes
-- Keep idea_id for backwards compatibility but add theme_id
ALTER TABLE calendar_schedule ADD COLUMN IF NOT EXISTS theme_id INTEGER REFERENCES calendar_themes(id) ON DELETE SET NULL;

-- Copy theme references from idea_id to theme_id where appropriate
UPDATE calendar_schedule cs
SET theme_id = cs.idea_id
WHERE cs.idea_id IN (SELECT id FROM calendar_themes)
  AND cs.theme_id IS NULL;

-- Add comment
COMMENT ON TABLE calendar_themes IS 'Week-wide themes (concepts) that are completely separate from calendar_ideas (content ideas)';

