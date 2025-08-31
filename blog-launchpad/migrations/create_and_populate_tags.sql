-- Create and populate Scottish/Heritage tags for posts
-- These tags will be used for OG tags and social media sharing

-- Insert relevant tags
INSERT INTO tag (name, slug, description) VALUES
('Scottish Heritage', 'scottish-heritage', 'Scottish cultural heritage and traditions'),
('Highland Culture', 'highland-culture', 'Highland Scottish culture and customs'),
('Tartan', 'tartan', 'Scottish tartan patterns and history'),
('Celtic Traditions', 'celtic-traditions', 'Ancient Celtic customs and beliefs'),
('Scottish History', 'scottish-history', 'Historical events and figures in Scotland'),
('Clan System', 'clan-system', 'Scottish clan structure and heritage'),
('Traditional Dress', 'traditional-dress', 'Traditional Scottish clothing and kilts'),
('Scottish Literature', 'scottish-literature', 'Scottish writing and storytelling'),
('Folk Traditions', 'folk-traditions', 'Scottish folk customs and practices'),
('Cultural Identity', 'cultural-identity', 'Scottish national and cultural identity');

-- Populate meta_tags field for posts based on their content
UPDATE post SET meta_tags = 'Scottish Heritage, Highland Culture, Traditional Dress' WHERE slug = 'kilt-evolution';
UPDATE post SET meta_tags = 'Tartan, Celtic Traditions, Cultural Identity' WHERE slug = 'english-tartans';
UPDATE post SET meta_tags = 'Scottish Heritage, Folk Traditions, Cultural Identity' WHERE slug = 'hand-fasting-1';
UPDATE post SET meta_tags = 'Scottish Heritage, Traditional Dress, Highland Culture' WHERE slug = 'kilts-for-weddings';
UPDATE post SET meta_tags = 'Scottish Literature, Folk Traditions, Cultural Identity' WHERE slug = 'the-art-of-scottish-storytelling-oral-traditions-and-modern-literature-53';

-- For posts without specific tags, add general Scottish heritage tags
UPDATE post SET meta_tags = 'Scottish Heritage, Celtic Traditions, Cultural Identity' 
WHERE meta_tags IS NULL OR meta_tags = '';

-- Show the results
SELECT p.id, p.title, p.meta_tags, 
       CASE WHEN LENGTH(p.meta_tags) > 50 THEN LEFT(p.meta_tags, 50) || '...' ELSE p.meta_tags END as tags_preview
FROM post p 
WHERE p.status != 'deleted' 
ORDER BY p.id;



