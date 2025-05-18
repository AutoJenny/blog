-- Drop existing tables if they exist
DROP TABLE IF EXISTS workflow_status CASCADE;
DROP TABLE IF EXISTS post_categories CASCADE;
DROP TABLE IF EXISTS post_tags CASCADE;
DROP TABLE IF EXISTS post_section CASCADE;
DROP TABLE IF EXISTS post_development CASCADE;
DROP TABLE IF EXISTS llm_action_history CASCADE;
DROP TABLE IF EXISTS llm_action CASCADE;
DROP TABLE IF EXISTS llm_interaction CASCADE;
DROP TABLE IF EXISTS llm_prompt CASCADE;
DROP TABLE IF EXISTS llm_config CASCADE;
DROP TABLE IF EXISTS image_prompt_example CASCADE;
DROP TABLE IF EXISTS image_setting CASCADE;
DROP TABLE IF EXISTS image_style CASCADE;
DROP TABLE IF EXISTS image_format CASCADE;
DROP TABLE IF EXISTS image CASCADE;
DROP TABLE IF EXISTS post CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS tag CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- Create enum types
CREATE TYPE workflow_stage AS ENUM ('idea', 'research', 'outlining', 'authoring', 'images', 'metadata', 'review', 'publishing', 'updates', 'syndication');
CREATE TYPE post_status AS ENUM ('draft', 'in_process', 'published', 'archived');

-- Create tables
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE image (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    path VARCHAR(255) NOT NULL UNIQUE,
    alt_text VARCHAR(255),
    caption TEXT,
    image_prompt TEXT,
    notes TEXT,
    image_metadata JSONB,
    watermarked BOOLEAN DEFAULT FALSE,
    watermarked_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE post (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    content TEXT,
    summary TEXT,
    published BOOLEAN DEFAULT FALSE,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    header_image_id INTEGER REFERENCES image(id),
    llm_metadata JSONB,
    seo_metadata JSONB,
    syndication_status JSONB,
    status post_status DEFAULT 'draft' NOT NULL,
    conclusion TEXT,
    footer TEXT
);

CREATE TABLE post_categories (
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES category(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, category_id)
);

CREATE TABLE post_tags (
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

CREATE TABLE post_section (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) NOT NULL,
    section_order INTEGER,
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
    image_prompt_example_id INTEGER,
    generated_image_url VARCHAR(512),
    image_generation_metadata JSONB,
    image_id INTEGER REFERENCES image(id)
);

CREATE TABLE post_development (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) UNIQUE NOT NULL,
    basic_idea TEXT,
    provisional_title TEXT,
    idea_scope TEXT,
    topics_to_cover TEXT,
    interesting_facts TEXT,
    tartans_products TEXT,
    section_planning TEXT,
    section_headings TEXT,
    section_order TEXT,
    main_title TEXT,
    subtitle TEXT,
    intro_blurb TEXT,
    conclusion TEXT,
    basic_metadata TEXT,
    tags TEXT,
    categories TEXT,
    image_captions TEXT,
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
    engagement_tracking TEXT
);

CREATE TABLE llm_prompt (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    system_prompt TEXT,
    parameters JSONB,
    "order" INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE llm_interaction (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER REFERENCES llm_prompt(id),
    input_text TEXT NOT NULL,
    output_text TEXT,
    parameters_used JSONB,
    interaction_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE llm_config (
    id SERIAL PRIMARY KEY,
    provider_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    api_base VARCHAR(200) NOT NULL,
    auth_token VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE llm_action (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(128) NOT NULL,
    prompt_template TEXT NOT NULL,
    prompt_template_id INTEGER REFERENCES llm_prompt(id) NOT NULL,
    llm_model VARCHAR(128) NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    "order" INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE llm_action_history (
    id SERIAL PRIMARY KEY,
    action_id INTEGER REFERENCES llm_action(id) NOT NULL,
    post_id INTEGER REFERENCES post(id) NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE image_style (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE image_format (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    width INTEGER,
    height INTEGER,
    steps INTEGER,
    guidance_scale FLOAT,
    extra_settings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE image_setting (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    style_id INTEGER REFERENCES image_style(id) NOT NULL,
    format_id INTEGER REFERENCES image_format(id) NOT NULL,
    width INTEGER,
    height INTEGER,
    steps INTEGER,
    guidance_scale FLOAT,
    extra_settings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE image_prompt_example (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    style_id INTEGER REFERENCES image_style(id) NOT NULL,
    format_id INTEGER REFERENCES image_format(id) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    image_setting_id INTEGER REFERENCES image_setting(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workflow_status (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) UNIQUE NOT NULL,
    conceptualisation VARCHAR(32) DEFAULT 'not_started',
    authoring VARCHAR(32) DEFAULT 'not_started',
    meta_status VARCHAR(32) DEFAULT 'not_started',
    images VARCHAR(32) DEFAULT 'not_started',
    validation VARCHAR(32) DEFAULT 'not_started',
    publishing VARCHAR(32) DEFAULT 'not_started',
    syndication VARCHAR(32) DEFAULT 'not_started',
    log TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_post_slug ON post(slug);
CREATE INDEX idx_post_created ON post(created_at);
CREATE INDEX idx_post_status ON post(status);
CREATE INDEX idx_image_path ON image(path);
CREATE INDEX idx_llm_action_field ON llm_action(field_name);
CREATE INDEX idx_llm_action_history_status ON llm_action_history(status);
CREATE INDEX idx_workflow_status_post ON workflow_status(post_id);

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_post_updated_at
    BEFORE UPDATE ON post
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_image_updated_at
    BEFORE UPDATE ON image
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_config_updated_at
    BEFORE UPDATE ON llm_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_action_updated_at
    BEFORE UPDATE ON llm_action
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_updated_at
    BEFORE UPDATE ON "user"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_image_style_updated_at
    BEFORE UPDATE ON image_style
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_image_format_updated_at
    BEFORE UPDATE ON image_format
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_image_setting_updated_at
    BEFORE UPDATE ON image_setting
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_image_prompt_example_updated_at
    BEFORE UPDATE ON image_prompt_example
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 