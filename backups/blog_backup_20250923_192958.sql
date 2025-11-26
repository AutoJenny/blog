-- Database backup created on 2025-09-23T19:29:58.144454
-- Blog project backup

-- Table: category
DROP TABLE IF EXISTS category CASCADE;
CREATE TABLE category (
    id integer NOT NULL DEFAULT nextval('category_id_seq'::regclass),
    name character varying NOT NULL,
    slug character varying NOT NULL,
    description text
);

-- Table: channel_requirements
DROP TABLE IF EXISTS channel_requirements CASCADE;
CREATE TABLE channel_requirements (
    id integer NOT NULL DEFAULT nextval('channel_requirements_id_seq'::regclass),
    platform_id integer NOT NULL,
    channel_type_id integer NOT NULL,
    requirement_category character varying NOT NULL,
    requirement_key character varying NOT NULL,
    requirement_value text NOT NULL,
    description text,
    is_required boolean DEFAULT true,
    validation_rules jsonb,
    unit character varying,
    min_value text,
    max_value text,
    display_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    content_length text,
    final_instruction text
);

-- Data for table: channel_requirements
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');
INSERT INTO channel_requirements VALUES ('id', 'platform_id', 'channel_type_id', 'requirement_category', 'requirement_key', 'requirement_value', 'description', 'is_required', 'validation_rules', 'unit', 'min_value', 'max_value', 'display_order', 'is_active', 'created_at', 'updated_at', 'content_length', 'final_instruction');

-- Table: channel_types
DROP TABLE IF EXISTS channel_types CASCADE;
CREATE TABLE channel_types (
    id integer NOT NULL DEFAULT nextval('channel_types_id_seq'::regclass),
    name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    content_type character varying NOT NULL,
    media_support ARRAY,
    default_priority integer DEFAULT 0,
    is_active boolean DEFAULT true,
    display_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: channel_types
INSERT INTO channel_types VALUES ('id', 'name', 'display_name', 'description', 'content_type', 'media_support', 'default_priority', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO channel_types VALUES ('id', 'name', 'display_name', 'description', 'content_type', 'media_support', 'default_priority', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO channel_types VALUES ('id', 'name', 'display_name', 'description', 'content_type', 'media_support', 'default_priority', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO channel_types VALUES ('id', 'name', 'display_name', 'description', 'content_type', 'media_support', 'default_priority', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO channel_types VALUES ('id', 'name', 'display_name', 'description', 'content_type', 'media_support', 'default_priority', 'is_active', 'display_order', 'created_at', 'updated_at');

-- Table: clan_cache_metadata
DROP TABLE IF EXISTS clan_cache_metadata CASCADE;
CREATE TABLE clan_cache_metadata (
    key text NOT NULL,
    value text,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: clan_cache_metadata
INSERT INTO clan_cache_metadata VALUES ('key', 'value', 'last_updated');
INSERT INTO clan_cache_metadata VALUES ('key', 'value', 'last_updated');

-- Table: clan_categories
DROP TABLE IF EXISTS clan_categories CASCADE;
CREATE TABLE clan_categories (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    level integer DEFAULT 0,
    parent_id integer,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: clan_categories
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');
INSERT INTO clan_categories VALUES ('id', 'name', 'description', 'level', 'parent_id', 'last_updated');

-- Table: clan_products
DROP TABLE IF EXISTS clan_products CASCADE;
CREATE TABLE clan_products (
    id integer NOT NULL,
    name text NOT NULL,
    sku text NOT NULL,
    price text,
    image_url text,
    url text,
    description text,
    category_ids jsonb,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    has_detailed_data boolean DEFAULT true,
    printable_design_type character varying
);

-- Data for table: clan_products
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');
INSERT INTO clan_products VALUES ('id', 'name', 'sku', 'price', 'image_url', 'url', 'description', 'category_ids', 'last_updated', 'has_detailed_data', 'printable_design_type');

-- Table: config_categories
DROP TABLE IF EXISTS config_categories CASCADE;
CREATE TABLE config_categories (
    id integer NOT NULL DEFAULT nextval('config_categories_id_seq'::regclass),
    name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    display_order integer DEFAULT 0,
    color_theme character varying DEFAULT 'primary'::character varying,
    icon_class character varying,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: config_categories
INSERT INTO config_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO config_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO config_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO config_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO config_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');

-- Table: content_priorities
DROP TABLE IF EXISTS content_priorities CASCADE;
CREATE TABLE content_priorities (
    id integer NOT NULL DEFAULT nextval('content_priorities_id_seq'::regclass),
    content_type character varying NOT NULL,
    content_id integer NOT NULL,
    priority_score numeric NOT NULL DEFAULT 0,
    priority_factors jsonb,
    last_calculated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    next_calculation_at timestamp without time zone,
    calculation_version character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: content_priorities
INSERT INTO content_priorities VALUES ('id', 'content_type', 'content_id', 'priority_score', 'priority_factors', 'last_calculated_at', 'next_calculation_at', 'calculation_version', 'created_at', 'updated_at');
INSERT INTO content_priorities VALUES ('id', 'content_type', 'content_id', 'priority_score', 'priority_factors', 'last_calculated_at', 'next_calculation_at', 'calculation_version', 'created_at', 'updated_at');
INSERT INTO content_priorities VALUES ('id', 'content_type', 'content_id', 'priority_score', 'priority_factors', 'last_calculated_at', 'next_calculation_at', 'calculation_version', 'created_at', 'updated_at');
INSERT INTO content_priorities VALUES ('id', 'content_type', 'content_id', 'priority_score', 'priority_factors', 'last_calculated_at', 'next_calculation_at', 'calculation_version', 'created_at', 'updated_at');
INSERT INTO content_priorities VALUES ('id', 'content_type', 'content_id', 'priority_score', 'priority_factors', 'last_calculated_at', 'next_calculation_at', 'calculation_version', 'created_at', 'updated_at');

-- Table: content_processes
DROP TABLE IF EXISTS content_processes CASCADE;
CREATE TABLE content_processes (
    id integer NOT NULL DEFAULT nextval('content_processes_id_seq'::regclass),
    platform_id integer NOT NULL,
    channel_type_id integer NOT NULL,
    process_name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    development_status character varying DEFAULT 'not_started'::character varying,
    priority integer DEFAULT 0,
    is_active boolean DEFAULT true,
    estimated_completion_date date,
    actual_completion_date date,
    development_notes text,
    last_activity_at timestamp without time zone,
    total_executions integer DEFAULT 0,
    success_rate_percentage numeric,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: content_processes
INSERT INTO content_processes VALUES ('id', 'platform_id', 'channel_type_id', 'process_name', 'display_name', 'description', 'development_status', 'priority', 'is_active', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'total_executions', 'success_rate_percentage', 'created_at', 'updated_at');
INSERT INTO content_processes VALUES ('id', 'platform_id', 'channel_type_id', 'process_name', 'display_name', 'description', 'development_status', 'priority', 'is_active', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'total_executions', 'success_rate_percentage', 'created_at', 'updated_at');
INSERT INTO content_processes VALUES ('id', 'platform_id', 'channel_type_id', 'process_name', 'display_name', 'description', 'development_status', 'priority', 'is_active', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'total_executions', 'success_rate_percentage', 'created_at', 'updated_at');
INSERT INTO content_processes VALUES ('id', 'platform_id', 'channel_type_id', 'process_name', 'display_name', 'description', 'development_status', 'priority', 'is_active', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'total_executions', 'success_rate_percentage', 'created_at', 'updated_at');
INSERT INTO content_processes VALUES ('id', 'platform_id', 'channel_type_id', 'process_name', 'display_name', 'description', 'development_status', 'priority', 'is_active', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'total_executions', 'success_rate_percentage', 'created_at', 'updated_at');

-- Table: credential_channels
DROP TABLE IF EXISTS credential_channels CASCADE;
CREATE TABLE credential_channels (
    id integer NOT NULL DEFAULT nextval('credential_channels_id_seq'::regclass),
    name character varying NOT NULL,
    description text,
    base_url character varying,
    icon_class character varying,
    color character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: credential_channels
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');
INSERT INTO credential_channels VALUES ('id', 'name', 'description', 'base_url', 'icon_class', 'color', 'created_at', 'updated_at');

-- Table: credential_services
DROP TABLE IF EXISTS credential_services CASCADE;
CREATE TABLE credential_services (
    id integer NOT NULL DEFAULT nextval('credential_services_id_seq'::regclass),
    channel_id integer,
    name character varying NOT NULL,
    description text,
    service_url character varying,
    api_endpoints jsonb,
    required_fields jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: credential_services
INSERT INTO credential_services VALUES ('id', 'channel_id', 'name', 'description', 'service_url', 'api_endpoints', 'required_fields', 'created_at', 'updated_at');
INSERT INTO credential_services VALUES ('id', 'channel_id', 'name', 'description', 'service_url', 'api_endpoints', 'required_fields', 'created_at', 'updated_at');
INSERT INTO credential_services VALUES ('id', 'channel_id', 'name', 'description', 'service_url', 'api_endpoints', 'required_fields', 'created_at', 'updated_at');
INSERT INTO credential_services VALUES ('id', 'channel_id', 'name', 'description', 'service_url', 'api_endpoints', 'required_fields', 'created_at', 'updated_at');
INSERT INTO credential_services VALUES ('id', 'channel_id', 'name', 'description', 'service_url', 'api_endpoints', 'required_fields', 'created_at', 'updated_at');

-- Table: credential_usage_history
DROP TABLE IF EXISTS credential_usage_history CASCADE;
CREATE TABLE credential_usage_history (
    id integer NOT NULL DEFAULT nextval('credential_usage_history_id_seq'::regclass),
    credential_id integer,
    action character varying NOT NULL,
    details jsonb,
    ip_address inet,
    user_agent text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: credential_usage_history
INSERT INTO credential_usage_history VALUES ('id', 'credential_id', 'action', 'details', 'ip_address', 'user_agent', 'created_at');

-- Table: credentials
DROP TABLE IF EXISTS credentials CASCADE;
CREATE TABLE credentials (
    id integer NOT NULL DEFAULT nextval('credentials_id_seq'::regclass),
    channel_id integer,
    service_id integer,
    name character varying NOT NULL,
    description text,
    credential_type USER-DEFINED NOT NULL,
    status USER-DEFINED DEFAULT 'active'::credential_status,
    api_key character varying,
    username character varying,
    password character varying,
    oauth_token text,
    bearer_token text,
    refresh_token text,
    token_expires_at timestamp without time zone,
    metadata jsonb,
    last_used_at timestamp without time zone,
    last_verified_at timestamp without time zone,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: credentials
INSERT INTO credentials VALUES ('id', 'channel_id', 'service_id', 'name', 'description', 'credential_type', 'status', 'api_key', 'username', 'password', 'oauth_token', 'bearer_token', 'refresh_token', 'token_expires_at', 'metadata', 'last_used_at', 'last_verified_at', 'error_message', 'created_at', 'updated_at');

-- Table: daily_posts
DROP TABLE IF EXISTS daily_posts CASCADE;
CREATE TABLE daily_posts (
    id integer NOT NULL DEFAULT nextval('daily_posts_id_seq'::regclass),
    product_id integer,
    post_date date NOT NULL,
    content_text text NOT NULL,
    content_type character varying DEFAULT 'feature'::character varying,
    platform character varying DEFAULT 'facebook'::character varying,
    facebook_post_id character varying,
    status character varying DEFAULT 'draft'::character varying,
    posted_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: daily_posts
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');
INSERT INTO daily_posts VALUES ('id', 'product_id', 'post_date', 'content_text', 'content_type', 'platform', 'facebook_post_id', 'status', 'posted_at', 'created_at');

-- Table: daily_posts_schedule
DROP TABLE IF EXISTS daily_posts_schedule CASCADE;
CREATE TABLE daily_posts_schedule (
    id integer NOT NULL DEFAULT nextval('daily_posts_schedule_id_seq'::regclass),
    time time without time zone NOT NULL DEFAULT '17:00:00'::time without time zone,
    timezone character varying NOT NULL DEFAULT 'GMT'::character varying,
    days jsonb NOT NULL DEFAULT '[]'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    name character varying DEFAULT 'Default Schedule'::character varying,
    display_order integer DEFAULT 0,
    platform character varying DEFAULT 'facebook'::character varying,
    channel_type character varying DEFAULT 'feed_post'::character varying,
    content_type character varying DEFAULT 'product'::character varying
);

-- Data for table: daily_posts_schedule
INSERT INTO daily_posts_schedule VALUES ('id', 'time', 'timezone', 'days', 'is_active', 'created_at', 'updated_at', 'name', 'display_order', 'platform', 'channel_type', 'content_type');
INSERT INTO daily_posts_schedule VALUES ('id', 'time', 'timezone', 'days', 'is_active', 'created_at', 'updated_at', 'name', 'display_order', 'platform', 'channel_type', 'content_type');
INSERT INTO daily_posts_schedule VALUES ('id', 'time', 'timezone', 'days', 'is_active', 'created_at', 'updated_at', 'name', 'display_order', 'platform', 'channel_type', 'content_type');
INSERT INTO daily_posts_schedule VALUES ('id', 'time', 'timezone', 'days', 'is_active', 'created_at', 'updated_at', 'name', 'display_order', 'platform', 'channel_type', 'content_type');

-- Table: image
DROP TABLE IF EXISTS image CASCADE;
CREATE TABLE image (
    id integer NOT NULL DEFAULT nextval('image_id_seq'::regclass),
    filename character varying NOT NULL,
    original_filename character varying,
    path character varying NOT NULL,
    alt_text character varying,
    caption text,
    image_prompt text,
    notes text,
    image_metadata jsonb,
    watermarked boolean DEFAULT false,
    watermarked_path character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: image
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');
INSERT INTO image VALUES ('id', 'filename', 'original_filename', 'path', 'alt_text', 'caption', 'image_prompt', 'notes', 'image_metadata', 'watermarked', 'watermarked_path', 'created_at', 'updated_at');

-- Table: image_format
DROP TABLE IF EXISTS image_format CASCADE;
CREATE TABLE image_format (
    id integer NOT NULL DEFAULT nextval('image_format_id_seq'::regclass),
    title character varying NOT NULL,
    description character varying,
    width integer,
    height integer,
    steps integer,
    guidance_scale double precision,
    extra_settings text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: image_format
INSERT INTO image_format VALUES ('id', 'title', 'description', 'width', 'height', 'steps', 'guidance_scale', 'extra_settings', 'created_at', 'updated_at');

-- Table: image_processing_jobs
DROP TABLE IF EXISTS image_processing_jobs CASCADE;
CREATE TABLE image_processing_jobs (
    id integer NOT NULL DEFAULT nextval('image_processing_jobs_id_seq'::regclass),
    post_id integer NOT NULL,
    job_type character varying NOT NULL,
    status character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    total_images integer DEFAULT 0,
    processed_images integer DEFAULT 0,
    settings jsonb
);

-- Data for table: image_processing_jobs
INSERT INTO image_processing_jobs VALUES ('id', 'post_id', 'job_type', 'status', 'created_at', 'started_at', 'completed_at', 'total_images', 'processed_images', 'settings');
INSERT INTO image_processing_jobs VALUES ('id', 'post_id', 'job_type', 'status', 'created_at', 'started_at', 'completed_at', 'total_images', 'processed_images', 'settings');
INSERT INTO image_processing_jobs VALUES ('id', 'post_id', 'job_type', 'status', 'created_at', 'started_at', 'completed_at', 'total_images', 'processed_images', 'settings');
INSERT INTO image_processing_jobs VALUES ('id', 'post_id', 'job_type', 'status', 'created_at', 'started_at', 'completed_at', 'total_images', 'processed_images', 'settings');
INSERT INTO image_processing_jobs VALUES ('id', 'post_id', 'job_type', 'status', 'created_at', 'started_at', 'completed_at', 'total_images', 'processed_images', 'settings');

-- Table: image_processing_status
DROP TABLE IF EXISTS image_processing_status CASCADE;
CREATE TABLE image_processing_status (
    id integer NOT NULL DEFAULT nextval('image_processing_status_id_seq'::regclass),
    image_id character varying NOT NULL,
    post_id integer NOT NULL,
    image_type character varying NOT NULL,
    section_id integer,
    current_step character varying,
    pipeline_status character varying,
    processing_job_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);

-- Data for table: image_processing_status
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');
INSERT INTO image_processing_status VALUES ('id', 'image_id', 'post_id', 'image_type', 'section_id', 'current_step', 'pipeline_status', 'processing_job_id', 'created_at', 'updated_at');

-- Table: image_processing_steps
DROP TABLE IF EXISTS image_processing_steps CASCADE;
CREATE TABLE image_processing_steps (
    id integer NOT NULL DEFAULT nextval('image_processing_steps_id_seq'::regclass),
    job_id integer,
    step_name character varying NOT NULL,
    status character varying NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    progress integer DEFAULT 0,
    error_message text
);

-- Data for table: image_processing_steps
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');
INSERT INTO image_processing_steps VALUES ('id', 'job_id', 'step_name', 'status', 'started_at', 'completed_at', 'progress', 'error_message');

-- Table: image_prompt_example
DROP TABLE IF EXISTS image_prompt_example CASCADE;
CREATE TABLE image_prompt_example (
    id integer NOT NULL DEFAULT nextval('image_prompt_example_id_seq'::regclass),
    description text NOT NULL,
    style_id integer NOT NULL,
    format_id integer NOT NULL,
    provider character varying NOT NULL,
    image_setting_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: image_setting
DROP TABLE IF EXISTS image_setting CASCADE;
CREATE TABLE image_setting (
    id integer NOT NULL DEFAULT nextval('image_setting_id_seq'::regclass),
    name character varying NOT NULL,
    style_id integer NOT NULL,
    format_id integer NOT NULL,
    width integer,
    height integer,
    steps integer,
    guidance_scale double precision,
    extra_settings text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: image_setting
INSERT INTO image_setting VALUES ('id', 'name', 'style_id', 'format_id', 'width', 'height', 'steps', 'guidance_scale', 'extra_settings', 'created_at', 'updated_at');

-- Table: image_style
DROP TABLE IF EXISTS image_style CASCADE;
CREATE TABLE image_style (
    id integer NOT NULL DEFAULT nextval('image_style_id_seq'::regclass),
    title character varying NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: image_style
INSERT INTO image_style VALUES ('id', 'title', 'description', 'created_at', 'updated_at');

-- Table: images
DROP TABLE IF EXISTS images CASCADE;
CREATE TABLE images (
    id integer NOT NULL DEFAULT nextval('images_id_seq'::regclass),
    filename character varying NOT NULL,
    original_filename character varying,
    file_path character varying NOT NULL,
    file_size integer,
    mime_type character varying,
    width integer,
    height integer,
    alt_text text,
    caption text,
    image_prompt text,
    notes text,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: llm_action
DROP TABLE IF EXISTS llm_action CASCADE;
CREATE TABLE llm_action (
    id integer NOT NULL DEFAULT nextval('llm_action_id_seq'::regclass),
    field_name character varying NOT NULL,
    prompt_template text NOT NULL,
    prompt_template_id integer NOT NULL,
    llm_model character varying NOT NULL,
    temperature double precision DEFAULT 0.7,
    max_tokens integer DEFAULT 1000,
    order integer NOT NULL DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    provider_id integer NOT NULL,
    timeout integer DEFAULT 60
);

-- Data for table: llm_action
INSERT INTO llm_action VALUES ('id', 'field_name', 'prompt_template', 'prompt_template_id', 'llm_model', 'temperature', 'max_tokens', 'order', 'created_at', 'updated_at', 'provider_id', 'timeout');
INSERT INTO llm_action VALUES ('id', 'field_name', 'prompt_template', 'prompt_template_id', 'llm_model', 'temperature', 'max_tokens', 'order', 'created_at', 'updated_at', 'provider_id', 'timeout');

-- Table: llm_action_history
DROP TABLE IF EXISTS llm_action_history CASCADE;
CREATE TABLE llm_action_history (
    id integer NOT NULL DEFAULT nextval('llm_action_history_id_seq'::regclass),
    action_id integer NOT NULL,
    post_id integer NOT NULL,
    input_text text NOT NULL,
    output_text text,
    status character varying DEFAULT 'pending'::character varying,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: llm_config
DROP TABLE IF EXISTS llm_config CASCADE;
CREATE TABLE llm_config (
    id integer NOT NULL DEFAULT nextval('llm_config_id_seq'::regclass),
    provider_type character varying NOT NULL,
    model_name character varying NOT NULL,
    api_base character varying NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: llm_config
INSERT INTO llm_config VALUES ('id', 'provider_type', 'model_name', 'api_base', 'is_active', 'created_at', 'updated_at');
INSERT INTO llm_config VALUES ('id', 'provider_type', 'model_name', 'api_base', 'is_active', 'created_at', 'updated_at');

-- Table: llm_format_template
DROP TABLE IF EXISTS llm_format_template CASCADE;
CREATE TABLE llm_format_template (
    id integer NOT NULL DEFAULT nextval('llm_format_template_id_seq'::regclass),
    name character varying NOT NULL,
    format_type character varying NOT NULL,
    format_spec text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: llm_format_template
INSERT INTO llm_format_template VALUES ('id', 'name', 'format_type', 'format_spec', 'created_at', 'updated_at');
INSERT INTO llm_format_template VALUES ('id', 'name', 'format_type', 'format_spec', 'created_at', 'updated_at');
INSERT INTO llm_format_template VALUES ('id', 'name', 'format_type', 'format_spec', 'created_at', 'updated_at');
INSERT INTO llm_format_template VALUES ('id', 'name', 'format_type', 'format_spec', 'created_at', 'updated_at');
INSERT INTO llm_format_template VALUES ('id', 'name', 'format_type', 'format_spec', 'created_at', 'updated_at');

-- Table: llm_interaction
DROP TABLE IF EXISTS llm_interaction CASCADE;
CREATE TABLE llm_interaction (
    id integer NOT NULL DEFAULT nextval('llm_interaction_id_seq'::regclass),
    prompt_id integer,
    input_text text NOT NULL,
    output_text text,
    parameters_used jsonb,
    interaction_metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    publication_status character varying DEFAULT 'draft'::character varying,
    ready_for_publication boolean DEFAULT false,
    publication_notes text,
    last_modified_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: llm_interaction
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');
INSERT INTO llm_interaction VALUES ('id', 'prompt_id', 'input_text', 'output_text', 'parameters_used', 'interaction_metadata', 'created_at', 'publication_status', 'ready_for_publication', 'publication_notes', 'last_modified_at');

-- Table: llm_model
DROP TABLE IF EXISTS llm_model CASCADE;
CREATE TABLE llm_model (
    id integer NOT NULL DEFAULT nextval('llm_model_id_seq'::regclass),
    name character varying NOT NULL,
    provider_id integer NOT NULL,
    description text,
    strengths text,
    weaknesses text,
    api_params jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: llm_model
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');
INSERT INTO llm_model VALUES ('id', 'name', 'provider_id', 'description', 'strengths', 'weaknesses', 'api_params', 'created_at', 'updated_at');

-- Table: llm_prompt
DROP TABLE IF EXISTS llm_prompt CASCADE;
CREATE TABLE llm_prompt (
    id integer NOT NULL DEFAULT nextval('llm_prompt_id_seq'::regclass),
    name character varying NOT NULL,
    description text,
    prompt_text text,
    system_prompt text,
    parameters jsonb,
    order integer NOT NULL DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    part_ids jsonb DEFAULT '[]'::jsonb,
    prompt_json jsonb,
    step_id integer
);

-- Data for table: llm_prompt
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');
INSERT INTO llm_prompt VALUES ('id', 'name', 'description', 'prompt_text', 'system_prompt', 'parameters', 'order', 'created_at', 'updated_at', 'part_ids', 'prompt_json', 'step_id');

-- Table: llm_prompt_part
DROP TABLE IF EXISTS llm_prompt_part CASCADE;
CREATE TABLE llm_prompt_part (
    id integer NOT NULL DEFAULT nextval('llm_prompt_part_id_seq'::regclass),
    type character varying NOT NULL,
    content text NOT NULL,
    tags ARRAY,
    order integer NOT NULL DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    name character varying,
    action_id integer,
    description text
);

-- Data for table: llm_prompt_part
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');
INSERT INTO llm_prompt_part VALUES ('id', 'type', 'content', 'tags', 'order', 'created_at', 'updated_at', 'name', 'action_id', 'description');

-- Table: llm_provider
DROP TABLE IF EXISTS llm_provider CASCADE;
CREATE TABLE llm_provider (
    id integer NOT NULL DEFAULT nextval('llm_provider_id_seq'::regclass),
    name character varying NOT NULL,
    type character varying NOT NULL DEFAULT 'local'::character varying,
    api_url text,
    auth_token text,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: llm_provider
INSERT INTO llm_provider VALUES ('id', 'name', 'type', 'api_url', 'auth_token', 'description', 'created_at', 'updated_at');
INSERT INTO llm_provider VALUES ('id', 'name', 'type', 'api_url', 'auth_token', 'description', 'created_at', 'updated_at');
INSERT INTO llm_provider VALUES ('id', 'name', 'type', 'api_url', 'auth_token', 'description', 'created_at', 'updated_at');
INSERT INTO llm_provider VALUES ('id', 'name', 'type', 'api_url', 'auth_token', 'description', 'created_at', 'updated_at');
INSERT INTO llm_provider VALUES ('id', 'name', 'type', 'api_url', 'auth_token', 'description', 'created_at', 'updated_at');

-- Table: platform_capabilities
DROP TABLE IF EXISTS platform_capabilities CASCADE;
CREATE TABLE platform_capabilities (
    id integer NOT NULL DEFAULT nextval('platform_capabilities_id_seq'::regclass),
    platform_id integer NOT NULL,
    capability_type character varying NOT NULL,
    capability_name character varying NOT NULL,
    capability_value text NOT NULL,
    description text,
    unit character varying,
    min_value text,
    max_value text,
    validation_rules jsonb,
    is_active boolean DEFAULT true,
    display_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: platform_capabilities
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');
INSERT INTO platform_capabilities VALUES ('id', 'platform_id', 'capability_type', 'capability_name', 'capability_value', 'description', 'unit', 'min_value', 'max_value', 'validation_rules', 'is_active', 'display_order', 'created_at', 'updated_at');

-- Table: platform_channel_support
DROP TABLE IF EXISTS platform_channel_support CASCADE;
CREATE TABLE platform_channel_support (
    id integer NOT NULL DEFAULT nextval('platform_channel_support_id_seq'::regclass),
    platform_id integer NOT NULL,
    channel_type_id integer NOT NULL,
    is_supported boolean DEFAULT true,
    status character varying DEFAULT 'active'::character varying,
    development_status character varying DEFAULT 'not_started'::character varying,
    priority integer DEFAULT 0,
    notes text,
    estimated_completion_date date,
    actual_completion_date date,
    development_notes text,
    last_activity_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: platform_channel_support
INSERT INTO platform_channel_support VALUES ('id', 'platform_id', 'channel_type_id', 'is_supported', 'status', 'development_status', 'priority', 'notes', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'created_at', 'updated_at');
INSERT INTO platform_channel_support VALUES ('id', 'platform_id', 'channel_type_id', 'is_supported', 'status', 'development_status', 'priority', 'notes', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'created_at', 'updated_at');
INSERT INTO platform_channel_support VALUES ('id', 'platform_id', 'channel_type_id', 'is_supported', 'status', 'development_status', 'priority', 'notes', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'created_at', 'updated_at');
INSERT INTO platform_channel_support VALUES ('id', 'platform_id', 'channel_type_id', 'is_supported', 'status', 'development_status', 'priority', 'notes', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'last_activity_at', 'created_at', 'updated_at');

-- Table: platform_credentials
DROP TABLE IF EXISTS platform_credentials CASCADE;
CREATE TABLE platform_credentials (
    id integer NOT NULL DEFAULT nextval('platform_credentials_id_seq'::regclass),
    platform_id integer NOT NULL,
    credential_type character varying NOT NULL,
    credential_key character varying NOT NULL,
    credential_value text NOT NULL,
    is_encrypted boolean DEFAULT false,
    is_active boolean DEFAULT true,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: platform_credentials
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');
INSERT INTO platform_credentials VALUES ('id', 'platform_id', 'credential_type', 'credential_key', 'credential_value', 'is_encrypted', 'is_active', 'expires_at', 'created_at', 'updated_at');

-- Table: platforms
DROP TABLE IF EXISTS platforms CASCADE;
CREATE TABLE platforms (
    id integer NOT NULL DEFAULT nextval('platforms_id_seq'::regclass),
    name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    status character varying DEFAULT 'active'::character varying,
    priority integer DEFAULT 0,
    website_url character varying,
    api_documentation_url character varying,
    logo_url character varying,
    development_status character varying DEFAULT 'not_started'::character varying,
    is_featured boolean DEFAULT false,
    menu_priority integer DEFAULT 0,
    is_visible_in_ui boolean DEFAULT true,
    last_activity_at timestamp without time zone,
    last_post_at timestamp without time zone,
    last_api_call_at timestamp without time zone,
    total_posts_count integer DEFAULT 0,
    success_rate_percentage numeric,
    average_response_time_ms integer,
    estimated_completion_date date,
    actual_completion_date date,
    development_notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: platforms
INSERT INTO platforms VALUES ('id', 'name', 'display_name', 'description', 'status', 'priority', 'website_url', 'api_documentation_url', 'logo_url', 'development_status', 'is_featured', 'menu_priority', 'is_visible_in_ui', 'last_activity_at', 'last_post_at', 'last_api_call_at', 'total_posts_count', 'success_rate_percentage', 'average_response_time_ms', 'estimated_completion_date', 'actual_completion_date', 'development_notes', 'created_at', 'updated_at');

-- Table: post
DROP TABLE IF EXISTS post CASCADE;
CREATE TABLE post (
    id integer NOT NULL DEFAULT nextval('post_id_seq'::regclass),
    title character varying NOT NULL,
    slug character varying NOT NULL,
    summary text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    header_image_id integer,
    status USER-DEFINED NOT NULL DEFAULT 'draft'::post_status,
    substage_id integer,
    subtitle character varying,
    title_choices text,
    header_image_caption text,
    header_image_title text,
    header_image_width integer,
    header_image_height integer,
    cross_promotion_category_id integer,
    cross_promotion_category_title text,
    cross_promotion_product_id integer,
    cross_promotion_product_title text,
    clan_post_id integer,
    clan_last_attempt timestamp without time zone,
    clan_error text,
    clan_uploaded_url text,
    cross_promotion_category_position integer,
    cross_promotion_product_position integer,
    cross_promotion_category_widget_html text,
    cross_promotion_product_widget_html text,
    meta_title character varying,
    meta_description text,
    meta_image character varying,
    meta_type character varying DEFAULT 'article'::character varying,
    meta_site_name character varying DEFAULT 'Clan.com Blog'::character varying,
    meta_tags character varying
);

-- Data for table: post
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');
INSERT INTO post VALUES ('id', 'title', 'slug', 'summary', 'created_at', 'updated_at', 'header_image_id', 'status', 'substage_id', 'subtitle', 'title_choices', 'header_image_caption', 'header_image_title', 'header_image_width', 'header_image_height', 'cross_promotion_category_id', 'cross_promotion_category_title', 'cross_promotion_product_id', 'cross_promotion_product_title', 'clan_post_id', 'clan_last_attempt', 'clan_error', 'clan_uploaded_url', 'cross_promotion_category_position', 'cross_promotion_product_position', 'cross_promotion_category_widget_html', 'cross_promotion_product_widget_html', 'meta_title', 'meta_description', 'meta_image', 'meta_type', 'meta_site_name', 'meta_tags');

-- Table: post_categories
DROP TABLE IF EXISTS post_categories CASCADE;
CREATE TABLE post_categories (
    post_id integer NOT NULL,
    category_id integer NOT NULL
);

-- Table: post_development
DROP TABLE IF EXISTS post_development CASCADE;
CREATE TABLE post_development (
    id integer NOT NULL DEFAULT nextval('post_development_id_seq'::regclass),
    post_id integer NOT NULL,
    basic_idea text,
    provisional_title text,
    idea_scope text,
    topics_to_cover text,
    interesting_facts text,
    section_headings text,
    section_order text,
    main_title text,
    intro_blurb text,
    seo_optimization text,
    summary text,
    idea_seed text,
    provisional_title_primary text,
    concepts text,
    facts text,
    outline text,
    allocated_facts text,
    sections text,
    title_order text,
    expanded_idea text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    image_montage_concept text,
    image_montage_prompt text,
    image_captions text
);

-- Data for table: post_development
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');
INSERT INTO post_development VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at', 'image_montage_concept', 'image_montage_prompt', 'image_captions');

-- Table: post_development_backup_20250804_080448
DROP TABLE IF EXISTS post_development_backup_20250804_080448 CASCADE;
CREATE TABLE post_development_backup_20250804_080448 (
    id integer,
    post_id integer,
    basic_idea text,
    provisional_title text,
    idea_scope text,
    topics_to_cover text,
    interesting_facts text,
    tartans_products text,
    section_planning text,
    section_headings text,
    section_order text,
    main_title text,
    subtitle text,
    intro_blurb text,
    conclusion text,
    basic_metadata text,
    tags text,
    categories text,
    image_captions text,
    seo_optimization text,
    self_review text,
    peer_review text,
    final_check text,
    scheduling text,
    deployment text,
    verification text,
    feedback_collection text,
    content_updates text,
    version_control text,
    platform_selection text,
    content_adaptation text,
    distribution text,
    engagement_tracking text,
    summary text,
    idea_seed text,
    provisional_title_primary text,
    concepts text,
    facts text,
    outline text,
    allocated_facts text,
    sections text,
    title_order text,
    expanded_idea text,
    updated_at timestamp without time zone
);

-- Data for table: post_development_backup_20250804_080448
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');
INSERT INTO post_development_backup_20250804_080448 VALUES ('id', 'post_id', 'basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'tartans_products', 'section_planning', 'section_headings', 'section_order', 'main_title', 'subtitle', 'intro_blurb', 'conclusion', 'basic_metadata', 'tags', 'categories', 'image_captions', 'seo_optimization', 'self_review', 'peer_review', 'final_check', 'scheduling', 'deployment', 'verification', 'feedback_collection', 'content_updates', 'version_control', 'platform_selection', 'content_adaptation', 'distribution', 'engagement_tracking', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'updated_at');

-- Table: post_images
DROP TABLE IF EXISTS post_images CASCADE;
CREATE TABLE post_images (
    id integer NOT NULL DEFAULT nextval('post_images_id_seq'::regclass),
    post_id integer,
    image_id integer,
    image_type character varying NOT NULL,
    section_id integer,
    sort_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: post_performance
DROP TABLE IF EXISTS post_performance CASCADE;
CREATE TABLE post_performance (
    id integer NOT NULL DEFAULT nextval('post_performance_id_seq'::regclass),
    daily_post_id integer,
    likes_count integer DEFAULT 0,
    shares_count integer DEFAULT 0,
    comments_count integer DEFAULT 0,
    reach_count integer DEFAULT 0,
    engagement_rate numeric,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: post_section
DROP TABLE IF EXISTS post_section CASCADE;
CREATE TABLE post_section (
    id integer NOT NULL DEFAULT nextval('post_section_id_seq'::regclass),
    post_id integer NOT NULL,
    section_order integer,
    section_heading text,
    ideas_to_include text,
    facts_to_include text,
    highlighting text,
    image_concepts text,
    image_prompts text,
    image_meta_descriptions text,
    image_captions text,
    section_description text,
    status text DEFAULT 'draft'::text,
    polished text,
    draft text,
    image_filename character varying,
    image_generated_at timestamp without time zone,
    image_title text,
    image_width integer,
    image_height integer
);

-- Data for table: post_section
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');
INSERT INTO post_section VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'highlighting', 'image_concepts', 'image_prompts', 'image_meta_descriptions', 'image_captions', 'section_description', 'status', 'polished', 'draft', 'image_filename', 'image_generated_at', 'image_title', 'image_width', 'image_height');

-- Table: post_section_backup_20250109
DROP TABLE IF EXISTS post_section_backup_20250109 CASCADE;
CREATE TABLE post_section_backup_20250109 (
    id integer,
    post_id integer,
    section_order integer,
    section_heading text,
    ideas_to_include text,
    facts_to_include text,
    first_draft text,
    uk_british text,
    highlighting text,
    image_concepts text,
    image_prompts text,
    generation text,
    optimization text,
    watermarking text,
    image_meta_descriptions text,
    image_captions text,
    image_prompt_example_id integer,
    generated_image_url character varying,
    image_generation_metadata jsonb,
    image_id integer,
    section_description text,
    status text
);

-- Data for table: post_section_backup_20250109
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');
INSERT INTO post_section_backup_20250109 VALUES ('id', 'post_id', 'section_order', 'section_heading', 'ideas_to_include', 'facts_to_include', 'first_draft', 'uk_british', 'highlighting', 'image_concepts', 'image_prompts', 'generation', 'optimization', 'watermarking', 'image_meta_descriptions', 'image_captions', 'image_prompt_example_id', 'generated_image_url', 'image_generation_metadata', 'image_id', 'section_description', 'status');

-- Table: post_section_elements
DROP TABLE IF EXISTS post_section_elements CASCADE;
CREATE TABLE post_section_elements (
    id integer NOT NULL DEFAULT nextval('post_section_elements_id_seq'::regclass),
    post_id integer NOT NULL,
    section_id integer NOT NULL,
    element_type character varying NOT NULL,
    element_text text NOT NULL,
    element_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: post_tags
DROP TABLE IF EXISTS post_tags CASCADE;
CREATE TABLE post_tags (
    post_id integer NOT NULL,
    tag_id integer NOT NULL
);

-- Table: post_workflow_stage
DROP TABLE IF EXISTS post_workflow_stage CASCADE;
CREATE TABLE post_workflow_stage (
    id integer NOT NULL DEFAULT nextval('post_workflow_stage_id_seq'::regclass),
    post_id integer,
    stage_id integer,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    status character varying,
    input_field character varying,
    output_field character varying
);

-- Data for table: post_workflow_stage
INSERT INTO post_workflow_stage VALUES ('id', 'post_id', 'stage_id', 'started_at', 'completed_at', 'status', 'input_field', 'output_field');
INSERT INTO post_workflow_stage VALUES ('id', 'post_id', 'stage_id', 'started_at', 'completed_at', 'status', 'input_field', 'output_field');

-- Table: post_workflow_step_action
DROP TABLE IF EXISTS post_workflow_step_action CASCADE;
CREATE TABLE post_workflow_step_action (
    id integer NOT NULL DEFAULT nextval('post_workflow_step_action_id_seq'::regclass),
    post_id integer,
    step_id integer,
    action_id integer,
    input_field character varying,
    output_field character varying,
    button_label text,
    button_order integer DEFAULT 0
);

-- Data for table: post_workflow_step_action
INSERT INTO post_workflow_step_action VALUES ('id', 'post_id', 'step_id', 'action_id', 'input_field', 'output_field', 'button_label', 'button_order');

-- Table: post_workflow_sub_stage
DROP TABLE IF EXISTS post_workflow_sub_stage CASCADE;
CREATE TABLE post_workflow_sub_stage (
    id integer NOT NULL DEFAULT nextval('post_workflow_sub_stage_id_seq'::regclass),
    post_workflow_stage_id integer,
    sub_stage_id integer,
    content text,
    status character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes text
);

-- Table: posting_queue
DROP TABLE IF EXISTS posting_queue CASCADE;
CREATE TABLE posting_queue (
    id integer NOT NULL DEFAULT nextval('posting_queue_id_seq'::regclass),
    product_id integer,
    scheduled_date date,
    scheduled_time time without time zone,
    schedule_name character varying,
    timezone character varying,
    generated_content text,
    queue_order integer DEFAULT 0,
    status character varying DEFAULT 'ready'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    platform character varying DEFAULT 'facebook'::character varying,
    channel_type character varying DEFAULT 'feed_post'::character varying,
    content_type character varying DEFAULT 'product'::character varying,
    scheduled_timestamp timestamp without time zone,
    platform_post_id character varying,
    error_message text,
    section_id integer,
    product_name character varying,
    sku character varying,
    price numeric,
    product_image character varying,
    post_id integer,
    post_title character varying,
    section_title character varying
);

-- Data for table: posting_queue
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');
INSERT INTO posting_queue VALUES ('id', 'product_id', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'generated_content', 'queue_order', 'status', 'created_at', 'updated_at', 'platform', 'channel_type', 'content_type', 'scheduled_timestamp', 'platform_post_id', 'error_message', 'section_id', 'product_name', 'sku', 'price', 'product_image', 'post_id', 'post_title', 'section_title');

-- Table: priority_factors
DROP TABLE IF EXISTS priority_factors CASCADE;
CREATE TABLE priority_factors (
    id integer NOT NULL DEFAULT nextval('priority_factors_id_seq'::regclass),
    factor_name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    factor_type character varying NOT NULL,
    weight numeric NOT NULL DEFAULT 1.0,
    calculation_formula text,
    is_active boolean DEFAULT true,
    is_configurable boolean DEFAULT true,
    min_value numeric,
    max_value numeric,
    default_value numeric,
    unit character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: priority_factors
INSERT INTO priority_factors VALUES ('id', 'factor_name', 'display_name', 'description', 'factor_type', 'weight', 'calculation_formula', 'is_active', 'is_configurable', 'min_value', 'max_value', 'default_value', 'unit', 'created_at', 'updated_at');
INSERT INTO priority_factors VALUES ('id', 'factor_name', 'display_name', 'description', 'factor_type', 'weight', 'calculation_formula', 'is_active', 'is_configurable', 'min_value', 'max_value', 'default_value', 'unit', 'created_at', 'updated_at');
INSERT INTO priority_factors VALUES ('id', 'factor_name', 'display_name', 'description', 'factor_type', 'weight', 'calculation_formula', 'is_active', 'is_configurable', 'min_value', 'max_value', 'default_value', 'unit', 'created_at', 'updated_at');
INSERT INTO priority_factors VALUES ('id', 'factor_name', 'display_name', 'description', 'factor_type', 'weight', 'calculation_formula', 'is_active', 'is_configurable', 'min_value', 'max_value', 'default_value', 'unit', 'created_at', 'updated_at');
INSERT INTO priority_factors VALUES ('id', 'factor_name', 'display_name', 'description', 'factor_type', 'weight', 'calculation_formula', 'is_active', 'is_configurable', 'min_value', 'max_value', 'default_value', 'unit', 'created_at', 'updated_at');
INSERT INTO priority_factors VALUES ('id', 'factor_name', 'display_name', 'description', 'factor_type', 'weight', 'calculation_formula', 'is_active', 'is_configurable', 'min_value', 'max_value', 'default_value', 'unit', 'created_at', 'updated_at');

-- Table: process_configurations
DROP TABLE IF EXISTS process_configurations CASCADE;
CREATE TABLE process_configurations (
    id integer NOT NULL DEFAULT nextval('process_configurations_id_seq'::regclass),
    process_id integer NOT NULL,
    config_category character varying NOT NULL,
    config_key character varying NOT NULL,
    config_value text NOT NULL,
    description text,
    display_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    validation_rules jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: process_configurations
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');
INSERT INTO process_configurations VALUES ('id', 'process_id', 'config_category', 'config_key', 'config_value', 'description', 'display_order', 'is_active', 'validation_rules', 'created_at', 'updated_at');

-- Table: product_content_templates
DROP TABLE IF EXISTS product_content_templates CASCADE;
CREATE TABLE product_content_templates (
    id integer NOT NULL DEFAULT nextval('product_content_templates_id_seq'::regclass),
    template_name character varying NOT NULL,
    content_type character varying NOT NULL,
    template_prompt text NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: product_content_templates
INSERT INTO product_content_templates VALUES ('id', 'template_name', 'content_type', 'template_prompt', 'is_active', 'created_at');
INSERT INTO product_content_templates VALUES ('id', 'template_name', 'content_type', 'template_prompt', 'is_active', 'created_at');
INSERT INTO product_content_templates VALUES ('id', 'template_name', 'content_type', 'template_prompt', 'is_active', 'created_at');

-- Table: requirement_categories
DROP TABLE IF EXISTS requirement_categories CASCADE;
CREATE TABLE requirement_categories (
    id integer NOT NULL DEFAULT nextval('requirement_categories_id_seq'::regclass),
    name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    display_order integer DEFAULT 0,
    color_theme character varying DEFAULT 'primary'::character varying,
    icon_class character varying,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: requirement_categories
INSERT INTO requirement_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO requirement_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO requirement_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO requirement_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');
INSERT INTO requirement_categories VALUES ('id', 'name', 'display_name', 'description', 'display_order', 'color_theme', 'icon_class', 'is_active', 'created_at');

-- Table: section_image_mappings
DROP TABLE IF EXISTS section_image_mappings CASCADE;
CREATE TABLE section_image_mappings (
    id integer NOT NULL DEFAULT nextval('section_image_mappings_id_seq'::regclass),
    post_id integer NOT NULL,
    section_id integer NOT NULL,
    local_image_path text NOT NULL,
    clan_uploaded_url text NOT NULL,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    image_filename text,
    image_size_bytes bigint,
    image_dimensions text
);

-- Data for table: section_image_mappings
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');
INSERT INTO section_image_mappings VALUES ('id', 'post_id', 'section_id', 'local_image_path', 'clan_uploaded_url', 'uploaded_at', 'image_filename', 'image_size_bytes', 'image_dimensions');

-- Table: substage_action_default
DROP TABLE IF EXISTS substage_action_default CASCADE;
CREATE TABLE substage_action_default (
    id integer NOT NULL DEFAULT nextval('substage_action_default_id_seq'::regclass),
    substage character varying NOT NULL,
    action_id integer
);

-- Table: syndication_progress
DROP TABLE IF EXISTS syndication_progress CASCADE;
CREATE TABLE syndication_progress (
    id integer NOT NULL DEFAULT nextval('syndication_progress_id_seq'::regclass),
    post_id integer NOT NULL,
    section_id integer NOT NULL,
    platform_id integer NOT NULL,
    channel_type_id integer NOT NULL,
    process_id integer NOT NULL,
    status character varying NOT NULL DEFAULT 'pending'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    error_message text
);

-- Data for table: syndication_progress
INSERT INTO syndication_progress VALUES ('id', 'post_id', 'section_id', 'platform_id', 'channel_type_id', 'process_id', 'status', 'created_at', 'updated_at', 'completed_at', 'error_message');
INSERT INTO syndication_progress VALUES ('id', 'post_id', 'section_id', 'platform_id', 'channel_type_id', 'process_id', 'status', 'created_at', 'updated_at', 'completed_at', 'error_message');
INSERT INTO syndication_progress VALUES ('id', 'post_id', 'section_id', 'platform_id', 'channel_type_id', 'process_id', 'status', 'created_at', 'updated_at', 'completed_at', 'error_message');
INSERT INTO syndication_progress VALUES ('id', 'post_id', 'section_id', 'platform_id', 'channel_type_id', 'process_id', 'status', 'created_at', 'updated_at', 'completed_at', 'error_message');
INSERT INTO syndication_progress VALUES ('id', 'post_id', 'section_id', 'platform_id', 'channel_type_id', 'process_id', 'status', 'created_at', 'updated_at', 'completed_at', 'error_message');
INSERT INTO syndication_progress VALUES ('id', 'post_id', 'section_id', 'platform_id', 'channel_type_id', 'process_id', 'status', 'created_at', 'updated_at', 'completed_at', 'error_message');

-- Table: tag
DROP TABLE IF EXISTS tag CASCADE;
CREATE TABLE tag (
    id integer NOT NULL DEFAULT nextval('tag_id_seq'::regclass),
    name character varying NOT NULL,
    slug character varying NOT NULL,
    description text
);

-- Data for table: tag
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');
INSERT INTO tag VALUES ('id', 'name', 'slug', 'description');

-- Table: ui_display_rules
DROP TABLE IF EXISTS ui_display_rules CASCADE;
CREATE TABLE ui_display_rules (
    id integer NOT NULL DEFAULT nextval('ui_display_rules_id_seq'::regclass),
    rule_name character varying NOT NULL,
    description text,
    rule_type character varying NOT NULL,
    target_type character varying NOT NULL,
    target_id integer,
    condition_expression text,
    is_active boolean DEFAULT true,
    priority integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: ui_display_rules
INSERT INTO ui_display_rules VALUES ('id', 'rule_name', 'description', 'rule_type', 'target_type', 'target_id', 'condition_expression', 'is_active', 'priority', 'created_at', 'updated_at');
INSERT INTO ui_display_rules VALUES ('id', 'rule_name', 'description', 'rule_type', 'target_type', 'target_id', 'condition_expression', 'is_active', 'priority', 'created_at', 'updated_at');
INSERT INTO ui_display_rules VALUES ('id', 'rule_name', 'description', 'rule_type', 'target_type', 'target_id', 'condition_expression', 'is_active', 'priority', 'created_at', 'updated_at');
INSERT INTO ui_display_rules VALUES ('id', 'rule_name', 'description', 'rule_type', 'target_type', 'target_id', 'condition_expression', 'is_active', 'priority', 'created_at', 'updated_at');
INSERT INTO ui_display_rules VALUES ('id', 'rule_name', 'description', 'rule_type', 'target_type', 'target_id', 'condition_expression', 'is_active', 'priority', 'created_at', 'updated_at');
INSERT INTO ui_display_rules VALUES ('id', 'rule_name', 'description', 'rule_type', 'target_type', 'target_id', 'condition_expression', 'is_active', 'priority', 'created_at', 'updated_at');

-- Table: ui_menu_items
DROP TABLE IF EXISTS ui_menu_items CASCADE;
CREATE TABLE ui_menu_items (
    id integer NOT NULL DEFAULT nextval('ui_menu_items_id_seq'::regclass),
    name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    menu_type character varying NOT NULL,
    parent_menu_id integer,
    section_id integer,
    url_pattern character varying,
    icon_class character varying,
    display_order integer DEFAULT 0,
    is_visible boolean DEFAULT true,
    is_active boolean DEFAULT true,
    requires_permission character varying,
    badge_text character varying,
    badge_color character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: ui_menu_items
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');
INSERT INTO ui_menu_items VALUES ('id', 'name', 'display_name', 'description', 'menu_type', 'parent_menu_id', 'section_id', 'url_pattern', 'icon_class', 'display_order', 'is_visible', 'is_active', 'requires_permission', 'badge_text', 'badge_color', 'created_at', 'updated_at');

-- Table: ui_sections
DROP TABLE IF EXISTS ui_sections CASCADE;
CREATE TABLE ui_sections (
    id integer NOT NULL DEFAULT nextval('ui_sections_id_seq'::regclass),
    name character varying NOT NULL,
    display_name character varying NOT NULL,
    description text,
    section_type character varying NOT NULL,
    parent_section_id integer,
    display_order integer DEFAULT 0,
    is_visible boolean DEFAULT true,
    is_collapsible boolean DEFAULT true,
    default_collapsed boolean DEFAULT false,
    color_theme character varying,
    icon_class character varying,
    css_classes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: ui_sections
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');
INSERT INTO ui_sections VALUES ('id', 'name', 'display_name', 'description', 'section_type', 'parent_section_id', 'display_order', 'is_visible', 'is_collapsible', 'default_collapsed', 'color_theme', 'icon_class', 'css_classes', 'created_at', 'updated_at');

-- Table: ui_session_state
DROP TABLE IF EXISTS ui_session_state CASCADE;
CREATE TABLE ui_session_state (
    id integer NOT NULL DEFAULT nextval('ui_session_state_id_seq'::regclass),
    session_id character varying NOT NULL,
    user_id integer,
    state_key character varying NOT NULL,
    state_value text,
    state_type character varying NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: ui_session_state
INSERT INTO ui_session_state VALUES ('id', 'session_id', 'user_id', 'state_key', 'state_value', 'state_type', 'expires_at', 'created_at', 'updated_at');
INSERT INTO ui_session_state VALUES ('id', 'session_id', 'user_id', 'state_key', 'state_value', 'state_type', 'expires_at', 'created_at', 'updated_at');
INSERT INTO ui_session_state VALUES ('id', 'session_id', 'user_id', 'state_key', 'state_value', 'state_type', 'expires_at', 'created_at', 'updated_at');
INSERT INTO ui_session_state VALUES ('id', 'session_id', 'user_id', 'state_key', 'state_value', 'state_type', 'expires_at', 'created_at', 'updated_at');
INSERT INTO ui_session_state VALUES ('id', 'session_id', 'user_id', 'state_key', 'state_value', 'state_type', 'expires_at', 'created_at', 'updated_at');

-- Table: ui_user_preferences
DROP TABLE IF EXISTS ui_user_preferences CASCADE;
CREATE TABLE ui_user_preferences (
    id integer NOT NULL DEFAULT nextval('ui_user_preferences_id_seq'::regclass),
    user_id integer NOT NULL,
    preference_key character varying NOT NULL,
    preference_value text,
    preference_type character varying NOT NULL,
    category character varying,
    is_global boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: ui_user_preferences
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');
INSERT INTO ui_user_preferences VALUES ('id', 'user_id', 'preference_key', 'preference_value', 'preference_type', 'category', 'is_global', 'created_at', 'updated_at');

-- Table: user
DROP TABLE IF EXISTS user CASCADE;
CREATE TABLE user (
    id integer NOT NULL DEFAULT nextval('user_id_seq'::regclass),
    username character varying NOT NULL,
    email character varying NOT NULL,
    password_hash character varying,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: user
INSERT INTO user VALUES ('user');

-- Table: workflow
DROP TABLE IF EXISTS workflow CASCADE;
CREATE TABLE workflow (
    id integer NOT NULL DEFAULT nextval('workflow_id_seq'::regclass),
    post_id integer NOT NULL,
    stage_id integer NOT NULL,
    status USER-DEFINED NOT NULL DEFAULT 'draft'::workflow_status_enum,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: workflow
INSERT INTO workflow VALUES ('id', 'post_id', 'stage_id', 'status', 'created', 'updated');

-- Table: workflow_field_mapping
DROP TABLE IF EXISTS workflow_field_mapping CASCADE;
CREATE TABLE workflow_field_mapping (
    id integer NOT NULL DEFAULT nextval('workflow_field_mapping_id_seq'::regclass),
    field_name text NOT NULL,
    stage_id integer,
    substage_id integer,
    order_index integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    workflow_step_id integer,
    field_type character varying,
    table_name character varying,
    column_name character varying,
    display_name character varying,
    is_required boolean DEFAULT false,
    default_value text,
    validation_rules jsonb
);

-- Data for table: workflow_field_mapping
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');
INSERT INTO workflow_field_mapping VALUES ('id', 'field_name', 'stage_id', 'substage_id', 'order_index', 'created_at', 'updated_at', 'workflow_step_id', 'field_type', 'table_name', 'column_name', 'display_name', 'is_required', 'default_value', 'validation_rules');

-- Table: workflow_field_mappings
DROP TABLE IF EXISTS workflow_field_mappings CASCADE;
CREATE TABLE workflow_field_mappings (
    id integer NOT NULL DEFAULT nextval('workflow_field_mappings_id_seq'::regclass),
    step_id integer NOT NULL,
    field_name text NOT NULL,
    mapped_field text NOT NULL,
    section text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    table_name character varying NOT NULL DEFAULT 'post_development'::character varying
);

-- Data for table: workflow_field_mappings
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');
INSERT INTO workflow_field_mappings VALUES ('id', 'step_id', 'field_name', 'mapped_field', 'section', 'created_at', 'updated_at', 'table_name');

-- Table: workflow_format_template
DROP TABLE IF EXISTS workflow_format_template CASCADE;
CREATE TABLE workflow_format_template (
    id integer NOT NULL DEFAULT nextval('workflow_format_template_id_seq'::regclass),
    name character varying NOT NULL,
    description text,
    fields jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    llm_instructions text
);

-- Data for table: workflow_format_template
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');
INSERT INTO workflow_format_template VALUES ('id', 'name', 'description', 'fields', 'created_at', 'updated_at', 'llm_instructions');

-- Table: workflow_post_format
DROP TABLE IF EXISTS workflow_post_format CASCADE;
CREATE TABLE workflow_post_format (
    id integer NOT NULL DEFAULT nextval('workflow_post_format_id_seq'::regclass),
    post_id integer NOT NULL,
    template_id integer NOT NULL,
    data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: workflow_stage_entity
DROP TABLE IF EXISTS workflow_stage_entity CASCADE;
CREATE TABLE workflow_stage_entity (
    id integer NOT NULL DEFAULT nextval('workflow_stage_entity_id_seq'::regclass),
    name character varying NOT NULL,
    description text,
    stage_order integer NOT NULL
);

-- Data for table: workflow_stage_entity
INSERT INTO workflow_stage_entity VALUES ('id', 'name', 'description', 'stage_order');
INSERT INTO workflow_stage_entity VALUES ('id', 'name', 'description', 'stage_order');
INSERT INTO workflow_stage_entity VALUES ('id', 'name', 'description', 'stage_order');
INSERT INTO workflow_stage_entity VALUES ('id', 'name', 'description', 'stage_order');

-- Table: workflow_stage_format
DROP TABLE IF EXISTS workflow_stage_format CASCADE;
CREATE TABLE workflow_stage_format (
    id integer NOT NULL DEFAULT nextval('workflow_stage_format_id_seq'::regclass),
    stage_id integer NOT NULL,
    template_id integer NOT NULL,
    config jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: workflow_step_context_config
DROP TABLE IF EXISTS workflow_step_context_config CASCADE;
CREATE TABLE workflow_step_context_config (
    id integer NOT NULL DEFAULT nextval('workflow_step_context_config_id_seq'::regclass),
    step_id integer NOT NULL,
    config jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);

-- Data for table: workflow_step_context_config
INSERT INTO workflow_step_context_config VALUES ('id', 'step_id', 'config', 'created_at');

-- Table: workflow_step_entity
DROP TABLE IF EXISTS workflow_step_entity CASCADE;
CREATE TABLE workflow_step_entity (
    id integer NOT NULL DEFAULT nextval('workflow_step_entity_id_seq'::regclass),
    sub_stage_id integer,
    name character varying NOT NULL,
    description text,
    step_order integer NOT NULL,
    config jsonb DEFAULT '{}'::jsonb,
    default_input_format_id integer,
    default_output_format_id integer
);

-- Data for table: workflow_step_entity
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');
INSERT INTO workflow_step_entity VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config', 'default_input_format_id', 'default_output_format_id');

-- Table: workflow_step_entity_backup
DROP TABLE IF EXISTS workflow_step_entity_backup CASCADE;
CREATE TABLE workflow_step_entity_backup (
    id integer,
    sub_stage_id integer,
    name character varying,
    description text,
    step_order integer,
    config jsonb
);

-- Data for table: workflow_step_entity_backup
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');
INSERT INTO workflow_step_entity_backup VALUES ('id', 'sub_stage_id', 'name', 'description', 'step_order', 'config');

-- Table: workflow_step_format
DROP TABLE IF EXISTS workflow_step_format CASCADE;
CREATE TABLE workflow_step_format (
    id integer NOT NULL DEFAULT nextval('workflow_step_format_id_seq'::regclass),
    step_id integer NOT NULL,
    post_id integer NOT NULL,
    input_format_id integer,
    output_format_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Table: workflow_step_input
DROP TABLE IF EXISTS workflow_step_input CASCADE;
CREATE TABLE workflow_step_input (
    id integer NOT NULL DEFAULT nextval('workflow_step_input_id_seq'::regclass),
    step_id integer NOT NULL,
    post_id integer NOT NULL,
    input_id text NOT NULL,
    field_name text NOT NULL
);

-- Table: workflow_step_prompt
DROP TABLE IF EXISTS workflow_step_prompt CASCADE;
CREATE TABLE workflow_step_prompt (
    id integer NOT NULL DEFAULT nextval('workflow_step_prompt_id_seq'::regclass),
    step_id integer NOT NULL,
    system_prompt_id integer,
    task_prompt_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: workflow_step_prompt
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');
INSERT INTO workflow_step_prompt VALUES ('id', 'step_id', 'system_prompt_id', 'task_prompt_id', 'created_at', 'updated_at');

-- Table: workflow_steps
DROP TABLE IF EXISTS workflow_steps CASCADE;
CREATE TABLE workflow_steps (
    id integer NOT NULL DEFAULT nextval('workflow_steps_id_seq'::regclass),
    post_workflow_sub_stage_id integer,
    step_order integer NOT NULL,
    name character varying NOT NULL,
    description text,
    llm_action_id integer,
    input_field character varying,
    output_field character varying,
    status character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes text
);

-- Table: workflow_sub_stage_entity
DROP TABLE IF EXISTS workflow_sub_stage_entity CASCADE;
CREATE TABLE workflow_sub_stage_entity (
    id integer NOT NULL DEFAULT nextval('workflow_sub_stage_entity_id_seq'::regclass),
    stage_id integer,
    name character varying NOT NULL,
    description text,
    sub_stage_order integer NOT NULL
);

-- Data for table: workflow_sub_stage_entity
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');
INSERT INTO workflow_sub_stage_entity VALUES ('id', 'stage_id', 'name', 'description', 'sub_stage_order');

-- Table: workflow_table_preferences
DROP TABLE IF EXISTS workflow_table_preferences CASCADE;
CREATE TABLE workflow_table_preferences (
    id integer NOT NULL DEFAULT nextval('workflow_table_preferences_id_seq'::regclass),
    step_id integer NOT NULL,
    section character varying NOT NULL,
    preferred_table character varying NOT NULL,
    user_id integer DEFAULT 1,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Data for table: workflow_table_preferences
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');
INSERT INTO workflow_table_preferences VALUES ('id', 'step_id', 'section', 'preferred_table', 'user_id', 'created_at', 'updated_at');

