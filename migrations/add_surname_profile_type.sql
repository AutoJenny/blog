-- Migration: Add 'surname' to profile_type constraints
-- Purpose: Support surname profiles in calendar_profile_sequence and post tables
-- Date: 2025-12-01

BEGIN;

-- Update calendar_profile_sequence constraint
ALTER TABLE calendar_profile_sequence 
DROP CONSTRAINT IF EXISTS calendar_profile_sequence_profile_type_check;

ALTER TABLE calendar_profile_sequence 
ADD CONSTRAINT calendar_profile_sequence_profile_type_check 
CHECK (profile_type IN ('product', 'category', 'surname'));

-- Update post table constraint
ALTER TABLE post 
DROP CONSTRAINT IF EXISTS post_profile_type_check;

ALTER TABLE post 
ADD CONSTRAINT post_profile_type_check 
CHECK (profile_type IN ('product', 'category', 'surname', NULL));

-- Update calendar_category_cycles constraint to include profile_surname
ALTER TABLE calendar_category_cycles 
DROP CONSTRAINT IF EXISTS calendar_category_cycles_category_check;

ALTER TABLE calendar_category_cycles 
ADD CONSTRAINT calendar_category_cycles_category_check 
CHECK (category IN (
    'theme', 'recipe', 'profile_product', 'profile_category', 'profile_surname',
    'weekly_word', 'weekly_phrase'
));

-- Add profile_surname to calendar_category_cycles if not exists
INSERT INTO calendar_category_cycles (category) VALUES ('profile_surname')
ON CONFLICT (category) DO NOTHING;

COMMIT;

