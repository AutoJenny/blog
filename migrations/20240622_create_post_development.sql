-- Create post_development table
CREATE TABLE IF NOT EXISTS post_development (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) NOT NULL,
    idea_seed TEXT,
    expanded_idea TEXT,
    provisional_title TEXT,
    idea_scope TEXT,
    topics_to_cover TEXT,
    interesting_facts TEXT,
    tartans_products TEXT,
    section_planning TEXT,
    section_headings TEXT,
    section_order TEXT,
    section_heading TEXT,
    ideas_to_include TEXT,
    facts_to_include TEXT,
    first_draft TEXT,
    uk_british TEXT,
    highlighting TEXT,
    image_concepts TEXT,
    image_prompts TEXT,
    generation TEXT,
    optimization TEXT,
    watermarking TEXT,
    image_meta_descriptions TEXT,
    image_captions TEXT,
    main_title TEXT,
    subtitle TEXT,
    intro_blurb TEXT,
    conclusion TEXT,
    basic_metadata TEXT,
    tags TEXT,
    categories TEXT,
    seo_optimization TEXT,
    self_review TEXT,
    peer_review TEXT,
    final_check TEXT,
    scheduling TEXT,
    deployment TEXT,
    verification TEXT,
    feedback_collection TEXT,
    content_updates TEXT,
    version_control TEXT,
    platform_selection TEXT,
    content_adaptation TEXT,
    distribution TEXT,
    engagement_tracking TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_post_development UNIQUE (post_id)
);

-- Create indexes for performance
CREATE INDEX idx_post_development_post_id ON post_development(post_id);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_post_development_updated_at
    BEFORE UPDATE ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 