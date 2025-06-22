-- Add updated_at column to post_development table
ALTER TABLE post_development ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP; 