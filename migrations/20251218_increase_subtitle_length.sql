-- Increase subtitle column length from 200 to 300 characters
-- This allows for expanded descriptive subtitles (2-4 sentences)

ALTER TABLE post 
ALTER COLUMN subtitle TYPE VARCHAR(300);
