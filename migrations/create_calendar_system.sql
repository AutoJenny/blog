-- Calendar System Migration
-- Creates tables for perpetual calendar with seasonal ideas and one-off events

-- 1. Calendar Weeks Master Reference
CREATE TABLE calendar_weeks (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52
    year INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    month_name VARCHAR(10) NOT NULL, -- Jan, Feb, Mar, etc.
    is_current_week BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_number, year)
);

-- 2. Calendar Ideas (Perpetual - repeats every year)
CREATE TABLE calendar_ideas (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52 (perpetual)
    idea_title VARCHAR(255) NOT NULL,
    idea_description TEXT,
    seasonal_context TEXT, -- "Spring gardening", "Holiday baking", etc.
    content_type VARCHAR(50), -- "tutorial", "guide", "list", "review"
    priority INTEGER DEFAULT 1, -- 1-5 scale
    tags JSONB, -- ["gardening", "seasonal", "beginner"]
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE, -- For series
    max_weeks INTEGER DEFAULT 1, -- Maximum weeks for series
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Calendar Events (One-off events for specific years)
CREATE TABLE calendar_events (
    id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    event_description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    week_number INTEGER, -- Calculated from start_date
    year INTEGER NOT NULL,
    content_type VARCHAR(50),
    priority INTEGER DEFAULT 1,
    tags JSONB,
    is_recurring BOOLEAN DEFAULT FALSE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Calendar Schedule (Actual scheduling for each year)
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    idea_id INTEGER REFERENCES calendar_ideas(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES post(id) ON DELETE SET NULL, -- If converted to actual post
    status VARCHAR(20) DEFAULT 'planned', -- planned, in_progress, published, cancelled
    scheduled_date DATE,
    notes TEXT,
    is_override BOOLEAN DEFAULT FALSE, -- Override for specific year
    original_idea_id INTEGER REFERENCES calendar_ideas(id), -- If this is an override
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (idea_id IS NOT NULL OR event_id IS NOT NULL) -- Must have one or the other
);

-- 5. Calendar Categories
CREATE TABLE calendar_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50), -- Icon class or name
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Link ideas to categories (many-to-many)
CREATE TABLE calendar_idea_categories (
    idea_id INTEGER REFERENCES calendar_ideas(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES calendar_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (idea_id, category_id)
);

-- 7. Link events to categories (many-to-many)
CREATE TABLE calendar_event_categories (
    event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES calendar_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, category_id)
);

-- Indexes for performance
CREATE INDEX idx_calendar_weeks_year_week ON calendar_weeks(year, week_number);
CREATE INDEX idx_calendar_ideas_week ON calendar_ideas(week_number);
CREATE INDEX idx_calendar_events_year_week ON calendar_events(year, week_number);
CREATE INDEX idx_calendar_schedule_year_week ON calendar_schedule(year, week_number);
CREATE INDEX idx_calendar_schedule_status ON calendar_schedule(status);

-- Insert default categories
INSERT INTO calendar_categories (name, description, color, icon) VALUES
('Gardening', 'Plant care, growing tips, seasonal gardening', '#10b981', 'seedling'),
('Cooking', 'Recipes, cooking techniques, food preparation', '#f59e0b', 'utensils'),
('Holidays', 'Seasonal celebrations, traditions, special events', '#ef4444', 'gift'),
('Tutorials', 'How-to guides, step-by-step instructions', '#3b82f6', 'book-open'),
('Reviews', 'Product reviews, recommendations, comparisons', '#8b5cf6', 'star'),
('Lists', 'Top 10 lists, checklists, roundups', '#06b6d4', 'list'),
('Seasonal', 'Weather-related, time-sensitive content', '#84cc16', 'sun'),
('General', 'General blog content, miscellaneous topics', '#6b7280', 'file-text');

-- Insert sample calendar weeks for 2025 (we can generate more years as needed)
-- This will be populated by a function or script
