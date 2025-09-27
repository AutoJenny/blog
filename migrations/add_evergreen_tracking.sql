-- Add evergreen content tracking to calendar_ideas table
ALTER TABLE calendar_ideas ADD COLUMN is_evergreen BOOLEAN DEFAULT FALSE;
ALTER TABLE calendar_ideas ADD COLUMN evergreen_frequency VARCHAR(20) DEFAULT 'low-frequency';
ALTER TABLE calendar_ideas ADD COLUMN last_used_date DATE;
ALTER TABLE calendar_ideas ADD COLUMN usage_count INTEGER DEFAULT 0;
ALTER TABLE calendar_ideas ADD COLUMN evergreen_notes TEXT;

-- Add evergreen frequency categories
INSERT INTO calendar_categories (name, description, color, icon) VALUES
('Evergreen', 'Content that can be reused throughout the year', '#10b981', 'refresh'),
('High-Frequency', 'Can be used multiple times per year', '#3b82f6', 'repeat'),
('Medium-Frequency', 'Use 2-3 times per year', '#f59e0b', 'clock'),
('Low-Frequency', 'Use once per year', '#8b5cf6', 'calendar'),
('One-Time', 'Use once, then archive', '#ef4444', 'archive');

-- Add index for evergreen content queries
CREATE INDEX idx_calendar_ideas_evergreen ON calendar_ideas(is_evergreen, evergreen_frequency);
CREATE INDEX idx_calendar_ideas_last_used ON calendar_ideas(last_used_date);
