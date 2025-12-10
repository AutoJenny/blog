-- Migration: Create calendar_ideas view pointing to calendar_ideas_deprecated
-- Date: 2025-12-10
-- Purpose: Provide backward compatibility for code referencing calendar_ideas

-- Drop view if it exists
DROP VIEW IF EXISTS calendar_ideas;

-- Create view pointing to deprecated table
CREATE VIEW calendar_ideas AS
SELECT * FROM calendar_ideas_deprecated;

-- Add comment
COMMENT ON VIEW calendar_ideas IS 
'View providing backward compatibility for calendar_ideas_deprecated table. 
The actual table is calendar_ideas_deprecated, but code references calendar_ideas.';

