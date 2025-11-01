-- Weekly Social Focus Migration
-- Creates table for weekly social media content focus schedule
-- Each day of the week has a defined social focus, format, purpose, and example

CREATE TABLE weekly_social_focus (
    id SERIAL PRIMARY KEY,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7), -- 1=Monday, 7=Sunday
    social_focus VARCHAR(255) NOT NULL,  -- The main theme/focus (avoiding "theme" keyword)
    format VARCHAR(255),                 -- e.g., "Carousel Post + Story", "Single Post or Reel"
    purpose TEXT,                        -- Why this focus for this day
    example TEXT,                        -- Example content/emoji/reference
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(day_of_week)                  -- Only one focus per day
);

-- Create index for quick day lookups
CREATE INDEX idx_weekly_social_focus_day ON weekly_social_focus(day_of_week);
CREATE INDEX idx_weekly_social_focus_active ON weekly_social_focus(is_active) WHERE is_active = TRUE;

-- Seed data from CSV
INSERT INTO weekly_social_focus (day_of_week, social_focus, format, purpose, example) VALUES
(1, 'From the Blog', 'Carousel Post + Story', 'Drives traffic to your blog; sets the week''s tone', '7 Things You Didn''t Know About Highland Dress 👘 — full story on clan.com/blog'),
(2, 'Tartan Tuesday', 'Single Post or Reel', 'Educate + inspire; connects visual pattern to heritage', 'MacLeod Modern — bold yellow checks that echo the Isle of Lewis sunlight ☀️'),
(3, 'Workshop Wednesday', 'Reel or 3-image carousel', 'Show craftsmanship + authenticity', 'This week in the mill: cutting cloth for a modern kilt in MacKenzie tartan 🇸🇨'),
(4, 'Throwback Thursday', 'Single Post', 'Build authority + heritage tone', 'A glimpse of 19th-century Highland games at Braemar…'),
(5, 'Family Friday', 'Carousel or Post', 'Connect heritage to individual pride', 'Clan Fraser — From the Lovat estates to Outlander fame…'),
(6, 'Product Spotlight', 'Reel or Post', 'Soft-sell commerce; link to shop', '"Made in Scotland, worn worldwide — lambswool scarves in your clan tartan."'),
(7, 'Scotland Today', 'Post or Story', 'Broaden appeal; emotional/aspirational close', 'Autumn arrives over Glencoe 🍂 — where will your tartan take you next?');

