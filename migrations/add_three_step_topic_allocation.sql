-- Database Migration: Add 3-step topic allocation fields to post_development table
-- Date: 2025-01-29
-- Purpose: Support new 3-step topic allocation process

-- Step 1: Section Structure Design
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS section_structure JSON;
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS structure_design_at TIMESTAMP;

-- Step 2: Topic Allocation  
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS topic_allocation JSON;
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS allocation_completed_at TIMESTAMP;

-- Step 3: Topic Refinement
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS refined_topics JSON;
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS refinement_completed_at TIMESTAMP;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_post_development_structure_design_at ON post_development(structure_design_at);
CREATE INDEX IF NOT EXISTS idx_post_development_allocation_completed_at ON post_development(allocation_completed_at);
CREATE INDEX IF NOT EXISTS idx_post_development_refinement_completed_at ON post_development(refinement_completed_at);
