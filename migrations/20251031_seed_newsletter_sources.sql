-- Seed initial newsletter sources based on planning discussion
-- These are the recommended sources for Scotland-focused newsletter content
-- Updated 2025-10-31 after validation testing

-- Weather & seasonality sources
-- NOTE: Met Office warnings RSS only works when active warnings exist (often empty/malformed)
-- Alternative: Use BBC Scotland weather page HTML scraping or Met Office DataPoint API
INSERT INTO newsletter_snapshot_source (name, base_url, type, enabled, created_at, updated_at)
VALUES 
    ('Met Office Scotland Warnings', 'https://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/Scotland', 'rss', false, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Mainstream news sources (VERIFIED WORKING)
INSERT INTO newsletter_snapshot_source (name, base_url, type, enabled, created_at, updated_at)
VALUES 
    ('BBC Scotland', 'https://feeds.bbci.co.uk/news/scotland/rss.xml', 'rss', true, NOW(), NOW()),
    ('The Scotsman', 'https://www.scotsman.com/rss', 'rss', true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Communities & culture (Reddit)
-- NOTE: /r/Highlands subreddit does not exist (404), disabled
INSERT INTO newsletter_snapshot_source (name, base_url, type, enabled, api_key_ref, created_at, updated_at)
VALUES 
    ('Reddit /r/Scotland', 'https://www.reddit.com/r/Scotland/', 'reddit', true, 'REDDIT_CLIENT_ID', NOW(), NOW()),
    ('Reddit /r/Highlands', 'https://www.reddit.com/r/Highlands/', 'reddit', false, 'REDDIT_CLIENT_ID', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Events calendars (What's On)
-- NOTE: 
--   - Historic Environment Scotland: VERIFIED (18 events detected)
--   - National Museums Scotland: Accessible but may need custom selectors for events
--   - National Galleries Scotland: 403 Forbidden (may need cookies/user-agent)
--   - VisitScotland: Accessible but may need custom selectors for events
INSERT INTO newsletter_snapshot_source (name, base_url, type, enabled, created_at, updated_at)
VALUES 
    ('Historic Environment Scotland - What''s On', 'https://www.historicenvironment.scot/whats-on/', 'html', true, NOW(), NOW()),
    ('National Museums Scotland - Events', 'https://www.nms.ac.uk/whats-on/', 'html', true, NOW(), NOW()),
    ('National Galleries Scotland - Exhibitions', 'https://www.nationalgalleries.org/whats-on/exhibitions', 'html', false, NOW(), NOW()),
    ('VisitScotland Events', 'https://www.visitscotland.com/events/', 'html', true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Heritage & seasonal
-- NOTE: rsghga.org domain does not resolve - disabled until alternative found
INSERT INTO newsletter_snapshot_source (name, base_url, type, enabled, created_at, updated_at)
VALUES 
    ('Royal Scottish Highland Games Association', 'https://www.rsghga.org/', 'html', false, NOW(), NOW())
ON CONFLICT DO NOTHING;

