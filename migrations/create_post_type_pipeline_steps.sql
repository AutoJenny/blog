-- Migration: Create post_type_pipeline_steps table
-- Purpose: Store pipeline step configurations for different post types
-- Date: 2025-01-XX

CREATE TABLE IF NOT EXISTS post_type_pipeline_steps (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    step_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    step_label VARCHAR(255),
    run_function VARCHAR(255),
    complete_event VARCHAR(100),
    prompt_category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_type, step_id)
);

CREATE INDEX IF NOT EXISTS idx_post_type_pipeline_steps_post_type 
ON post_type_pipeline_steps(post_type, step_order) 
WHERE is_active = TRUE;

COMMENT ON TABLE post_type_pipeline_steps IS 'Pipeline step configurations for different post types';
COMMENT ON COLUMN post_type_pipeline_steps.post_type IS 'Post type: themed, recipe, profile';
COMMENT ON COLUMN post_type_pipeline_steps.step_id IS 'Unique step identifier';
COMMENT ON COLUMN post_type_pipeline_steps.step_order IS 'Order of step in pipeline';
COMMENT ON COLUMN post_type_pipeline_steps.step_label IS 'Display label for the step';
COMMENT ON COLUMN post_type_pipeline_steps.run_function IS 'JavaScript function name to run';
COMMENT ON COLUMN post_type_pipeline_steps.complete_event IS 'Event name for completion notification';

-- Insert themed post pipeline steps
INSERT INTO post_type_pipeline_steps (post_type, step_id, step_order, step_label, run_function, complete_event) VALUES
    ('themed', 'week-ideas', 1, 'Calendar — Week Ideas', 'runWeekIdeas', NULL),
    ('themed', 'taxonomy', 2, 'Planning — Taxonomy', 'runTaxonomy', NULL),
    ('themed', 'idea-generation', 3, 'Planning — Idea Generation', 'runIdeaGeneration', NULL),
    ('themed', 'topic-brainstorming', 4, 'Planning — Topic Brainstorming', 'runTopicBrainstorming', NULL),
    ('themed', 'section-structure-design', 5, 'Planning — Section Structure', 'runSectionStructure', NULL),
    ('themed', 'section-ideas', 6, 'Planning — Section Ideas', 'runSectionIdeas', NULL),
    ('themed', 'section-titling', 7, 'Planning — Section Titling', 'runSectionTitling', NULL),
    ('themed', 'drafting', 8, 'Authoring — Drafting', 'runDrafting', NULL),
    ('themed', 'image-concepts', 9, 'Authoring — Image Concepts', 'runImageConcepts', NULL),
    ('themed', 'image-prompts', 10, 'Authoring — Image Prompts', 'runImagePrompts', NULL),
    ('themed', 'image-captions', 11, 'Authoring — Image Captions', 'runImageCaptions', NULL),
    ('themed', 'image-generation', 12, 'Imaging — Image Generation', 'runImageGeneration', 'image_generation_complete'),
    ('themed', 'optimise', 13, 'Imaging — Optimise', 'runImageOptimise', 'image_optimise_complete'),
    ('themed', 'header-title-summary', 14, 'Header — Title & Summary', 'runHeaderTitleSummary', 'header_title_summary_complete'),
    ('themed', 'header-image-prompt', 15, 'Header Image — Prompt', 'runHeaderImagePrompt', 'header_image_prompt_complete'),
    ('themed', 'header-image-details', 16, 'Header Image — Captions/Alt', 'runHeaderImageDetails', 'header_image_details_complete'),
    ('themed', 'header-image-generate', 17, 'Header Image — Image', 'runHeaderImageGenerate', 'header_image_generated'),
    ('themed', 'header-image-optimise', 18, 'Header Image — Optimise', 'runHeaderImageOptimize', 'header_image_optimized'),
    ('themed', 'header-seo-meta', 19, 'Header — SEO & Meta', 'runHeaderSeoMeta', 'header_seo_meta_complete'),
    ('themed', 'final-review', 20, 'Final Review — Preview', 'runFinalReview', NULL)
ON CONFLICT (post_type, step_id) DO UPDATE SET
    step_order = EXCLUDED.step_order,
    step_label = EXCLUDED.step_label,
    run_function = EXCLUDED.run_function,
    complete_event = EXCLUDED.complete_event,
    updated_at = NOW();

-- Insert recipe post pipeline steps (simplified to use existing authoring workflow)
INSERT INTO post_type_pipeline_steps (post_type, step_id, step_order, step_label, run_function, complete_event, prompt_category) VALUES
    ('recipe', 'recipe-selection', 1, 'Recipe — Selection', 'runRecipeSelection', NULL, 'recipe'),
    ('recipe', 'recipe-research', 2, 'Research — Recipe Context', 'runRecipeResearch', NULL, 'recipe'),
    ('recipe', 'drafting', 3, 'Authoring — Drafting', 'runDrafting', NULL, 'recipe'),
    ('recipe', 'image-concepts', 4, 'Authoring — Image Concepts', 'runImageConcepts', NULL, 'recipe'),
    ('recipe', 'image-prompts', 5, 'Authoring — Image Prompts', 'runImagePrompts', NULL, 'recipe'),
    ('recipe', 'image-captions', 6, 'Authoring — Image Captions', 'runImageCaptions', NULL, 'recipe'),
    ('recipe', 'image-generation', 7, 'Imaging — Image Generation', 'runImageGeneration', 'image_generation_complete', 'recipe'),
    ('recipe', 'optimise', 8, 'Imaging — Optimise', 'runImageOptimise', 'image_optimise_complete', 'recipe'),
    ('recipe', 'header-title-summary', 9, 'Header — Title & Summary', 'runHeaderTitleSummary', 'header_title_summary_complete', NULL),
    ('recipe', 'header-image-prompt', 10, 'Header Image — Prompt', 'runHeaderImagePrompt', 'header_image_prompt_complete', NULL),
    ('recipe', 'header-image-details', 11, 'Header Image — Captions/Alt', 'runHeaderImageDetails', 'header_image_details_complete', NULL),
    ('recipe', 'header-image-generate', 12, 'Header Image — Image', 'runHeaderImageGenerate', 'header_image_generated', NULL),
    ('recipe', 'header-image-optimise', 13, 'Header Image — Optimise', 'runHeaderImageOptimize', 'header_image_optimized', NULL),
    ('recipe', 'header-seo-meta', 14, 'Header — SEO & Meta', 'runHeaderSeoMeta', 'header_seo_meta_complete', NULL),
    ('recipe', 'final-review', 15, 'Final Review — Preview', 'runFinalReview', NULL, NULL)
ON CONFLICT (post_type, step_id) DO UPDATE SET
    step_order = EXCLUDED.step_order,
    step_label = EXCLUDED.step_label,
    run_function = EXCLUDED.run_function,
    complete_event = EXCLUDED.complete_event,
    prompt_category = EXCLUDED.prompt_category,
    updated_at = NOW();

-- Insert profile post pipeline steps
INSERT INTO post_type_pipeline_steps (post_type, step_id, step_order, step_label, run_function, complete_event, prompt_category) VALUES
    ('profile', 'profile-selection', 1, 'Profile — Selection', 'runProfileSelection', NULL, 'profile'),
    ('profile', 'profile-data-sync', 2, 'Data Sync — Product Information', 'runProfileDataSync', NULL, 'profile'),
    ('profile', 'profile-sections', 3, 'Profile — Sections', 'runProfileSections', NULL, 'profile'),
    ('profile', 'profile-image-concepts', 4, 'Profile — Image Concepts', 'runProfileImageConcepts', NULL, 'profile'),
    ('profile', 'profile-image-prompts', 5, 'Profile — Image Prompts', 'runProfileImagePrompts', NULL, 'profile'),
    ('profile', 'profile-image-generation', 6, 'Profile — Image Generation', 'runProfileImageGeneration', 'image_generation_complete', 'profile'),
    ('profile', 'profile-image-optimise', 7, 'Profile — Image Optimise', 'runProfileImageOptimise', 'image_optimise_complete', 'profile'),
    ('profile', 'header-title-summary', 8, 'Header — Title & Summary', 'runHeaderTitleSummary', 'header_title_summary_complete', NULL),
    ('profile', 'header-image-prompt', 9, 'Header Image — Prompt', 'runHeaderImagePrompt', 'header_image_prompt_complete', NULL),
    ('profile', 'header-image-details', 10, 'Header Image — Captions/Alt', 'runHeaderImageDetails', 'header_image_details_complete', NULL),
    ('profile', 'header-image-generate', 11, 'Header Image — Image', 'runHeaderImageGenerate', 'header_image_generated', NULL),
    ('profile', 'header-image-optimise', 12, 'Header Image — Optimise', 'runHeaderImageOptimize', 'header_image_optimized', NULL),
    ('profile', 'header-seo-meta', 13, 'Header — SEO & Meta', 'runHeaderSeoMeta', 'header_seo_meta_complete', NULL),
    ('profile', 'final-review', 14, 'Final Review — Preview', 'runFinalReview', NULL, NULL)
ON CONFLICT (post_type, step_id) DO UPDATE SET
    step_order = EXCLUDED.step_order,
    step_label = EXCLUDED.step_label,
    run_function = EXCLUDED.run_function,
    complete_event = EXCLUDED.complete_event,
    prompt_category = EXCLUDED.prompt_category,
    updated_at = NOW();

