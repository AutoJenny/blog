-- Migration: Add recipe_category to calendar_recipes table
-- Purpose: Enable filtering by recipe type (soups, mains, desserts, drinks, etc.)
-- Date: 2025-01-XX

ALTER TABLE calendar_recipes 
ADD COLUMN IF NOT EXISTS recipe_category VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_calendar_recipes_category ON calendar_recipes(recipe_category) WHERE recipe_category IS NOT NULL;

COMMENT ON COLUMN calendar_recipes.recipe_category IS 'Recipe category for filtering: soups, mains, desserts, drinks, breads, preserves, snacks';

