--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: post_status; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.post_status AS ENUM (
    'draft',
    'in_process',
    'published',
    'archived',
    'deleted'
);


ALTER TYPE public.post_status OWNER TO nickfiddes;

--
-- Name: poststatus; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.poststatus AS ENUM (
    'draft',
    'in_process',
    'published',
    'archived'
);


ALTER TYPE public.poststatus OWNER TO nickfiddes;

--
-- Name: prompt_part_type; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.prompt_part_type AS ENUM (
    'system',
    'style',
    'instructions',
    'user',
    'assistant',
    'other'
);


ALTER TYPE public.prompt_part_type OWNER TO nickfiddes;

--
-- Name: prompt_role_type; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.prompt_role_type AS ENUM (
    'system',
    'user',
    'assistant',
    'tool',
    'function',
    'other'
);


ALTER TYPE public.prompt_role_type OWNER TO nickfiddes;

--
-- Name: provider_type_enum; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.provider_type_enum AS ENUM (
    'openai',
    'ollama',
    'other'
);


ALTER TYPE public.provider_type_enum OWNER TO nickfiddes;

--
-- Name: workflow_status_enum; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.workflow_status_enum AS ENUM (
    'draft',
    'published',
    'review',
    'deleted'
);


ALTER TYPE public.workflow_status_enum OWNER TO nickfiddes;

--
-- Name: workflowstage; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.workflowstage AS ENUM (
    'idea',
    'research',
    'outlining',
    'authoring',
    'images',
    'metadata',
    'review',
    'publishing',
    'updates',
    'syndication'
);


ALTER TYPE public.workflowstage OWNER TO nickfiddes;

--
-- Name: rollback_format_migration(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.rollback_format_migration() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- This function can be used to rollback the migration if needed
    -- It would recreate the old table structure and migrate data back
    RAISE NOTICE 'Rollback function created - use with caution';
END;
$$;


ALTER FUNCTION public.rollback_format_migration() OWNER TO nickfiddes;

--
-- Name: rollback_workflow_post_format(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.rollback_workflow_post_format() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DROP TABLE IF EXISTS workflow_post_format CASCADE;
END;
$$;


ALTER FUNCTION public.rollback_workflow_post_format() OWNER TO nickfiddes;

--
-- Name: rollback_workflow_stage_format(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.rollback_workflow_stage_format() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DROP TABLE IF EXISTS workflow_stage_format CASCADE;
END;
$$;


ALTER FUNCTION public.rollback_workflow_stage_format() OWNER TO nickfiddes;

--
-- Name: sync_section_headings_to_sections(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.sync_section_headings_to_sections() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    section_data JSONB;
    section_item JSONB;
    section_id INTEGER;
    i INTEGER := 0;
BEGIN
    -- Remove the "no change" check to ensure trigger always fires
    -- This ensures sync happens even if the value appears unchanged
    
    -- Parse the section_headings JSON
    IF NEW.section_headings IS NULL OR NEW.section_headings = '' THEN
        -- Clear all sections for this post
        DELETE FROM post_section WHERE post_id = NEW.post_id;
        RETURN NEW;
    END IF;
    
    BEGIN
        section_data := NEW.section_headings::JSONB;
    EXCEPTION WHEN OTHERS THEN
        -- Handle invalid JSON - log error but don't fail
        RAISE WARNING 'Invalid JSON in section_headings for post %: %', NEW.post_id, NEW.section_headings;
        RETURN NEW;
    END;
    
    -- Process each section in the array
    FOR section_item IN SELECT * FROM jsonb_array_elements(section_data)
    LOOP
        i := i + 1;
        
        -- Extract section data
        DECLARE
            heading TEXT;
            description TEXT;
            section_status TEXT;
        BEGIN
            -- Handle different JSON formats
            IF jsonb_typeof(section_item) = 'string' THEN
                heading := section_item::TEXT;
                description := '';
                section_status := 'draft';
            ELSE
                heading := COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i);
                description := COALESCE(section_item->>'description', '');
                section_status := COALESCE(section_item->>'status', 'draft');
            END IF;
            
            -- Find existing section or create new one
            SELECT id INTO section_id 
            FROM post_section 
            WHERE post_id = NEW.post_id AND section_order = i;
            
            IF section_id IS NULL THEN
                -- Create new section
                INSERT INTO post_section (
                    post_id, section_order, section_heading, 
                    section_description, status
                ) VALUES (
                    NEW.post_id, i, heading, description, section_status
                );
            ELSE
                -- Update existing section
                UPDATE post_section 
                SET section_heading = heading,
                    section_description = description,
                    status = section_status
                WHERE id = section_id;
            END IF;
        END;
    END LOOP;
    
    -- Remove sections that are no longer in the list
    DELETE FROM post_section 
    WHERE post_id = NEW.post_id AND section_order > i;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.sync_section_headings_to_sections() OWNER TO nickfiddes;

--
-- Name: sync_sections_to_section_headings(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.sync_sections_to_section_headings() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    section_headings_json JSONB;
    section_record RECORD;
    recursion_guard TEXT;
BEGIN
    -- Recursion guard: only run if not set by the primary trigger
    BEGIN
        SELECT current_setting('section_sync.in_progress', true) INTO recursion_guard;
    EXCEPTION WHEN OTHERS THEN
        recursion_guard := NULL;
    END;
    IF recursion_guard = '1' THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    -- Build JSON array from current sections
    section_headings_json := '[]'::JSONB;
    
    FOR section_record IN 
        SELECT section_order, section_heading, section_description, status
        FROM post_section 
        WHERE post_id = COALESCE(NEW.post_id, OLD.post_id)
        ORDER BY section_order
    LOOP
        section_headings_json := section_headings_json || jsonb_build_object(
            'order', section_record.section_order,
            'heading', section_record.section_heading,
            'description', COALESCE(section_record.section_description, ''),
            'status', COALESCE(section_record.status, 'draft')
        );
    END LOOP;
    
    -- Update post_development
    UPDATE post_development 
    SET section_headings = section_headings_json::TEXT
    WHERE post_id = COALESCE(NEW.post_id, OLD.post_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$;


ALTER FUNCTION public.sync_sections_to_section_headings() OWNER TO nickfiddes;

--
-- Name: update_post_development_updated_at_column(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_post_development_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_post_development_updated_at_column() OWNER TO nickfiddes;

--
-- Name: update_system_prompt_template_updated_at(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_system_prompt_template_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_system_prompt_template_updated_at() OWNER TO nickfiddes;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO nickfiddes;

--
-- Name: update_workflow_field_mapping_updated_at(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_workflow_field_mapping_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_workflow_field_mapping_updated_at() OWNER TO nickfiddes;

--
-- Name: update_workflow_post_format_updated_at(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_workflow_post_format_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_workflow_post_format_updated_at() OWNER TO nickfiddes;

--
-- Name: update_workflow_stage_format_updated_at(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_workflow_stage_format_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_workflow_stage_format_updated_at() OWNER TO nickfiddes;

--
-- Name: update_workflow_step_prompt_updated_at(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_workflow_step_prompt_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_workflow_step_prompt_updated_at() OWNER TO nickfiddes;

--
-- Name: update_workflow_updated_at_column(); Type: FUNCTION; Schema: public; Owner: nickfiddes
--

CREATE FUNCTION public.update_workflow_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_workflow_updated_at_column() OWNER TO nickfiddes;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: category; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.category (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    slug character varying(50) NOT NULL,
    description text
);


ALTER TABLE public.category OWNER TO nickfiddes;

--
-- Name: category_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.category_id_seq OWNER TO nickfiddes;

--
-- Name: category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.category_id_seq OWNED BY public.category.id;


--
-- Name: image; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.image (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255),
    path character varying(255) NOT NULL,
    alt_text character varying(255),
    caption text,
    image_prompt text,
    notes text,
    image_metadata jsonb,
    watermarked boolean DEFAULT false,
    watermarked_path character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.image OWNER TO nickfiddes;

--
-- Name: image_format; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.image_format (
    id integer NOT NULL,
    title character varying(100) NOT NULL,
    description character varying(255),
    width integer,
    height integer,
    steps integer,
    guidance_scale double precision,
    extra_settings text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.image_format OWNER TO nickfiddes;

--
-- Name: image_format_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.image_format_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_format_id_seq OWNER TO nickfiddes;

--
-- Name: image_format_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.image_format_id_seq OWNED BY public.image_format.id;


--
-- Name: image_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_id_seq OWNER TO nickfiddes;

--
-- Name: image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;


--
-- Name: image_prompt_example; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.image_prompt_example (
    id integer NOT NULL,
    description text NOT NULL,
    style_id integer NOT NULL,
    format_id integer NOT NULL,
    provider character varying(50) NOT NULL,
    image_setting_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.image_prompt_example OWNER TO nickfiddes;

--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.image_prompt_example_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_prompt_example_id_seq OWNER TO nickfiddes;

--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.image_prompt_example_id_seq OWNED BY public.image_prompt_example.id;


--
-- Name: image_setting; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.image_setting (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
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


ALTER TABLE public.image_setting OWNER TO nickfiddes;

--
-- Name: image_setting_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.image_setting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_setting_id_seq OWNER TO nickfiddes;

--
-- Name: image_setting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.image_setting_id_seq OWNED BY public.image_setting.id;


--
-- Name: image_style; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.image_style (
    id integer NOT NULL,
    title character varying(100) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.image_style OWNER TO nickfiddes;

--
-- Name: image_style_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.image_style_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_style_id_seq OWNER TO nickfiddes;

--
-- Name: image_style_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.image_style_id_seq OWNED BY public.image_style.id;


--
-- Name: images; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.images (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255),
    file_path character varying(500) NOT NULL,
    file_size integer,
    mime_type character varying(100),
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


ALTER TABLE public.images OWNER TO nickfiddes;

--
-- Name: images_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.images_id_seq OWNER TO nickfiddes;

--
-- Name: images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.images_id_seq OWNED BY public.images.id;


--
-- Name: llm_action; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_action (
    id integer NOT NULL,
    field_name character varying(128) NOT NULL,
    prompt_template text NOT NULL,
    prompt_template_id integer NOT NULL,
    llm_model character varying(128) NOT NULL,
    temperature double precision DEFAULT 0.7,
    max_tokens integer DEFAULT 1000,
    "order" integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    input_field character varying(128),
    output_field character varying(128),
    provider_id integer NOT NULL,
    timeout integer DEFAULT 60
);


ALTER TABLE public.llm_action OWNER TO nickfiddes;

--
-- Name: llm_action_history; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_action_history (
    id integer NOT NULL,
    action_id integer NOT NULL,
    post_id integer NOT NULL,
    input_text text NOT NULL,
    output_text text,
    status character varying(50) DEFAULT 'pending'::character varying,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.llm_action_history OWNER TO nickfiddes;

--
-- Name: llm_action_history_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_action_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_action_history_id_seq OWNER TO nickfiddes;

--
-- Name: llm_action_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_action_history_id_seq OWNED BY public.llm_action_history.id;


--
-- Name: llm_action_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_action_id_seq OWNER TO nickfiddes;

--
-- Name: llm_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_action_id_seq OWNED BY public.llm_action.id;


--
-- Name: llm_config; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_config (
    id integer NOT NULL,
    provider_type character varying(50) NOT NULL,
    model_name character varying(50) NOT NULL,
    api_base character varying(255) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.llm_config OWNER TO nickfiddes;

--
-- Name: llm_config_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_config_id_seq OWNER TO nickfiddes;

--
-- Name: llm_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_config_id_seq OWNED BY public.llm_config.id;


--
-- Name: llm_format_template; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_format_template (
    id integer NOT NULL,
    name character varying(128) NOT NULL,
    format_type character varying(32) NOT NULL,
    format_spec text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT llm_format_template_format_type_check CHECK (((format_type)::text = ANY (ARRAY[('input'::character varying)::text, ('output'::character varying)::text])))
);


ALTER TABLE public.llm_format_template OWNER TO nickfiddes;

--
-- Name: llm_format_template_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_format_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_format_template_id_seq OWNER TO nickfiddes;

--
-- Name: llm_format_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_format_template_id_seq OWNED BY public.llm_format_template.id;


--
-- Name: llm_interaction; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_interaction (
    id integer NOT NULL,
    prompt_id integer,
    input_text text NOT NULL,
    output_text text,
    parameters_used jsonb,
    interaction_metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.llm_interaction OWNER TO nickfiddes;

--
-- Name: llm_interaction_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_interaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_interaction_id_seq OWNER TO nickfiddes;

--
-- Name: llm_interaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_interaction_id_seq OWNED BY public.llm_interaction.id;


--
-- Name: llm_model; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_model (
    id integer NOT NULL,
    name character varying(128) NOT NULL,
    provider_id integer NOT NULL,
    description text,
    strengths text,
    weaknesses text,
    api_params jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.llm_model OWNER TO nickfiddes;

--
-- Name: llm_model_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_model_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_model_id_seq OWNER TO nickfiddes;

--
-- Name: llm_model_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_model_id_seq OWNED BY public.llm_model.id;


--
-- Name: llm_prompt; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_prompt (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    prompt_text text,
    system_prompt text,
    parameters jsonb,
    "order" integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    part_ids jsonb DEFAULT '[]'::jsonb,
    prompt_json jsonb,
    step_id integer
);


ALTER TABLE public.llm_prompt OWNER TO nickfiddes;

--
-- Name: llm_prompt_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_prompt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_prompt_id_seq OWNER TO nickfiddes;

--
-- Name: llm_prompt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_prompt_id_seq OWNED BY public.llm_prompt.id;


--
-- Name: llm_prompt_part; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_prompt_part (
    id integer NOT NULL,
    type character varying(32) NOT NULL,
    content text NOT NULL,
    tags text[],
    "order" integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    name character varying(128),
    action_id integer,
    description text
);


ALTER TABLE public.llm_prompt_part OWNER TO nickfiddes;

--
-- Name: llm_prompt_part_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_prompt_part_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_prompt_part_id_seq OWNER TO nickfiddes;

--
-- Name: llm_prompt_part_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_prompt_part_id_seq OWNED BY public.llm_prompt_part.id;


--
-- Name: llm_provider; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_provider (
    id integer NOT NULL,
    name character varying(128) NOT NULL,
    type character varying(64) DEFAULT 'local'::character varying NOT NULL,
    api_url text,
    auth_token text,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.llm_provider OWNER TO nickfiddes;

--
-- Name: llm_provider_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.llm_provider_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_provider_id_seq OWNER TO nickfiddes;

--
-- Name: llm_provider_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.llm_provider_id_seq OWNED BY public.llm_provider.id;


--
-- Name: post; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    summary text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    header_image_id integer,
    status public.post_status DEFAULT 'draft'::public.post_status NOT NULL,
    substage_id integer,
    subtitle character varying(200),
    title_choices text
);


ALTER TABLE public.post OWNER TO nickfiddes;

--
-- Name: post_categories; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_categories (
    post_id integer NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.post_categories OWNER TO nickfiddes;

--
-- Name: post_development; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_development (
    id integer NOT NULL,
    post_id integer NOT NULL,
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
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.post_development OWNER TO nickfiddes;

--
-- Name: post_development_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_development_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_development_id_seq OWNER TO nickfiddes;

--
-- Name: post_development_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_development_id_seq OWNED BY public.post_development.id;


--
-- Name: post_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_id_seq OWNER TO nickfiddes;

--
-- Name: post_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_id_seq OWNED BY public.post.id;


--
-- Name: post_images; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_images (
    id integer NOT NULL,
    post_id integer,
    image_id integer,
    image_type character varying(50) NOT NULL,
    section_id integer,
    sort_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.post_images OWNER TO nickfiddes;

--
-- Name: post_images_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_images_id_seq OWNER TO nickfiddes;

--
-- Name: post_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_images_id_seq OWNED BY public.post_images.id;


--
-- Name: post_section; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_section (
    id integer NOT NULL,
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
    image_filename character varying(255),
    image_generated_at timestamp without time zone
);


ALTER TABLE public.post_section OWNER TO nickfiddes;

--
-- Name: COLUMN post_section.polished; Type: COMMENT; Schema: public; Owner: nickfiddes
--

COMMENT ON COLUMN public.post_section.polished IS 'Final publication-ready content after unified LLM processing';


--
-- Name: COLUMN post_section.draft; Type: COMMENT; Schema: public; Owner: nickfiddes
--

COMMENT ON COLUMN public.post_section.draft IS 'Initial raw draft content before processing';


--
-- Name: post_section_backup_20250109; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_section_backup_20250109 (
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
    generated_image_url character varying(512),
    image_generation_metadata jsonb,
    image_id integer,
    section_description text,
    status text
);


ALTER TABLE public.post_section_backup_20250109 OWNER TO nickfiddes;

--
-- Name: post_section_elements; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_section_elements (
    id integer NOT NULL,
    post_id integer NOT NULL,
    section_id integer NOT NULL,
    element_type character varying(50) NOT NULL,
    element_text text NOT NULL,
    element_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT post_section_elements_element_type_check CHECK (((element_type)::text = ANY (ARRAY[('fact'::character varying)::text, ('idea'::character varying)::text, ('theme'::character varying)::text])))
);


ALTER TABLE public.post_section_elements OWNER TO nickfiddes;

--
-- Name: post_section_elements_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_section_elements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_section_elements_id_seq OWNER TO nickfiddes;

--
-- Name: post_section_elements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_section_elements_id_seq OWNED BY public.post_section_elements.id;


--
-- Name: post_section_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_section_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_section_id_seq OWNER TO nickfiddes;

--
-- Name: post_section_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_section_id_seq OWNED BY public.post_section.id;


--
-- Name: post_tags; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_tags (
    post_id integer NOT NULL,
    tag_id integer NOT NULL
);


ALTER TABLE public.post_tags OWNER TO nickfiddes;

--
-- Name: post_workflow_stage; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_workflow_stage (
    id integer NOT NULL,
    post_id integer,
    stage_id integer,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    status character varying(32),
    input_field character varying(128),
    output_field character varying(1024)
);


ALTER TABLE public.post_workflow_stage OWNER TO nickfiddes;

--
-- Name: post_workflow_stage_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_workflow_stage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_workflow_stage_id_seq OWNER TO nickfiddes;

--
-- Name: post_workflow_stage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_workflow_stage_id_seq OWNED BY public.post_workflow_stage.id;


--
-- Name: post_workflow_step_action; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_workflow_step_action (
    id integer NOT NULL,
    post_id integer,
    step_id integer,
    action_id integer,
    input_field character varying(128),
    output_field character varying(128),
    button_label text,
    button_order integer DEFAULT 0
);


ALTER TABLE public.post_workflow_step_action OWNER TO nickfiddes;

--
-- Name: post_workflow_step_action_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_workflow_step_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_workflow_step_action_id_seq OWNER TO nickfiddes;

--
-- Name: post_workflow_step_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_workflow_step_action_id_seq OWNED BY public.post_workflow_step_action.id;


--
-- Name: post_workflow_sub_stage; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_workflow_sub_stage (
    id integer NOT NULL,
    post_workflow_stage_id integer,
    sub_stage_id integer,
    content text,
    status character varying(32),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes text
);


ALTER TABLE public.post_workflow_sub_stage OWNER TO nickfiddes;

--
-- Name: post_workflow_sub_stage_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_workflow_sub_stage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_workflow_sub_stage_id_seq OWNER TO nickfiddes;

--
-- Name: post_workflow_sub_stage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_workflow_sub_stage_id_seq OWNED BY public.post_workflow_sub_stage.id;


--
-- Name: substage_action_default; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.substage_action_default (
    id integer NOT NULL,
    substage character varying(64) NOT NULL,
    action_id integer
);


ALTER TABLE public.substage_action_default OWNER TO nickfiddes;

--
-- Name: substage_action_default_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.substage_action_default_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.substage_action_default_id_seq OWNER TO nickfiddes;

--
-- Name: substage_action_default_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.substage_action_default_id_seq OWNED BY public.substage_action_default.id;


--
-- Name: tag; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.tag (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    slug character varying(50) NOT NULL,
    description text
);


ALTER TABLE public.tag OWNER TO nickfiddes;

--
-- Name: tag_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.tag_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tag_id_seq OWNER TO nickfiddes;

--
-- Name: tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.tag_id_seq OWNED BY public.tag.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(128),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public."user" OWNER TO nickfiddes;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO nickfiddes;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: workflow; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow (
    id integer NOT NULL,
    post_id integer NOT NULL,
    stage_id integer NOT NULL,
    status public.workflow_status_enum DEFAULT 'draft'::public.workflow_status_enum NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow OWNER TO nickfiddes;

--
-- Name: workflow_field_mapping; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_field_mapping (
    id integer NOT NULL,
    field_name text NOT NULL,
    stage_id integer,
    substage_id integer,
    order_index integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    workflow_step_id integer,
    field_type character varying(32),
    table_name character varying(64),
    column_name character varying(64),
    display_name character varying(128),
    is_required boolean DEFAULT false,
    default_value text,
    validation_rules jsonb,
    CONSTRAINT workflow_field_mapping_field_type_check CHECK (((field_type)::text = ANY (ARRAY[('input'::character varying)::text, ('output'::character varying)::text])))
);


ALTER TABLE public.workflow_field_mapping OWNER TO nickfiddes;

--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_field_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_field_mapping_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_field_mapping_id_seq OWNED BY public.workflow_field_mapping.id;


--
-- Name: workflow_field_mappings; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_field_mappings (
    id integer NOT NULL,
    step_id integer NOT NULL,
    field_name text NOT NULL,
    mapped_field text NOT NULL,
    section text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow_field_mappings OWNER TO nickfiddes;

--
-- Name: workflow_field_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_field_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_field_mappings_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_field_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_field_mappings_id_seq OWNED BY public.workflow_field_mappings.id;


--
-- Name: workflow_format_template; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_format_template (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    fields jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    llm_instructions text
);


ALTER TABLE public.workflow_format_template OWNER TO nickfiddes;

--
-- Name: workflow_format_template_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_format_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_format_template_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_format_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_format_template_id_seq OWNED BY public.workflow_format_template.id;


--
-- Name: workflow_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_id_seq OWNED BY public.workflow.id;


--
-- Name: workflow_post_format; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_post_format (
    id integer NOT NULL,
    post_id integer NOT NULL,
    template_id integer NOT NULL,
    data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow_post_format OWNER TO nickfiddes;

--
-- Name: workflow_post_format_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_post_format_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_post_format_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_post_format_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_post_format_id_seq OWNED BY public.workflow_post_format.id;


--
-- Name: workflow_stage_entity; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_stage_entity (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    stage_order integer NOT NULL
);


ALTER TABLE public.workflow_stage_entity OWNER TO nickfiddes;

--
-- Name: workflow_stage_entity_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_stage_entity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_stage_entity_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_stage_entity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_stage_entity_id_seq OWNED BY public.workflow_stage_entity.id;


--
-- Name: workflow_stage_format; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_stage_format (
    id integer NOT NULL,
    stage_id integer NOT NULL,
    template_id integer NOT NULL,
    config jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow_stage_format OWNER TO nickfiddes;

--
-- Name: workflow_stage_format_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_stage_format_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_stage_format_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_stage_format_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_stage_format_id_seq OWNED BY public.workflow_stage_format.id;


--
-- Name: workflow_step_context_config; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_step_context_config (
    id integer NOT NULL,
    step_id integer NOT NULL,
    config jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.workflow_step_context_config OWNER TO nickfiddes;

--
-- Name: workflow_step_context_config_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_step_context_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_step_context_config_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_step_context_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_step_context_config_id_seq OWNED BY public.workflow_step_context_config.id;


--
-- Name: workflow_step_entity; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_step_entity (
    id integer NOT NULL,
    sub_stage_id integer,
    name character varying(100) NOT NULL,
    description text,
    step_order integer NOT NULL,
    config jsonb DEFAULT '{}'::jsonb,
    field_name text,
    order_index integer,
    default_input_format_id integer,
    default_output_format_id integer
);


ALTER TABLE public.workflow_step_entity OWNER TO nickfiddes;

--
-- Name: workflow_step_entity_backup; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workflow_step_entity_backup (
    id integer,
    sub_stage_id integer,
    name character varying(100),
    description text,
    step_order integer,
    config jsonb
);


ALTER TABLE public.workflow_step_entity_backup OWNER TO postgres;

--
-- Name: workflow_step_entity_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_step_entity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_step_entity_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_step_entity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_step_entity_id_seq OWNED BY public.workflow_step_entity.id;


--
-- Name: workflow_step_format; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_step_format (
    id integer NOT NULL,
    step_id integer NOT NULL,
    post_id integer NOT NULL,
    input_format_id integer,
    output_format_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow_step_format OWNER TO nickfiddes;

--
-- Name: workflow_step_format_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_step_format_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_step_format_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_step_format_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_step_format_id_seq OWNED BY public.workflow_step_format.id;


--
-- Name: workflow_step_input; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_step_input (
    id integer NOT NULL,
    step_id integer NOT NULL,
    post_id integer NOT NULL,
    input_id text NOT NULL,
    field_name text NOT NULL
);


ALTER TABLE public.workflow_step_input OWNER TO nickfiddes;

--
-- Name: workflow_step_input_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_step_input_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_step_input_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_step_input_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_step_input_id_seq OWNED BY public.workflow_step_input.id;


--
-- Name: workflow_step_prompt; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_step_prompt (
    id integer NOT NULL,
    step_id integer NOT NULL,
    system_prompt_id integer NOT NULL,
    task_prompt_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow_step_prompt OWNER TO nickfiddes;

--
-- Name: workflow_step_prompt_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_step_prompt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_step_prompt_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_step_prompt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_step_prompt_id_seq OWNED BY public.workflow_step_prompt.id;


--
-- Name: workflow_steps; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_steps (
    id integer NOT NULL,
    post_workflow_sub_stage_id integer,
    step_order integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    llm_action_id integer,
    input_field character varying(128),
    output_field character varying(128),
    status character varying(32),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes text
);


ALTER TABLE public.workflow_steps OWNER TO nickfiddes;

--
-- Name: workflow_steps_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_steps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_steps_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_steps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_steps_id_seq OWNED BY public.workflow_steps.id;


--
-- Name: workflow_sub_stage_entity; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_sub_stage_entity (
    id integer NOT NULL,
    stage_id integer,
    name character varying(100) NOT NULL,
    description text,
    sub_stage_order integer NOT NULL
);


ALTER TABLE public.workflow_sub_stage_entity OWNER TO nickfiddes;

--
-- Name: workflow_sub_stage_entity_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_sub_stage_entity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_sub_stage_entity_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_sub_stage_entity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_sub_stage_entity_id_seq OWNED BY public.workflow_sub_stage_entity.id;


--
-- Name: category id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.category ALTER COLUMN id SET DEFAULT nextval('public.category_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: image_format id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_format ALTER COLUMN id SET DEFAULT nextval('public.image_format_id_seq'::regclass);


--
-- Name: image_prompt_example id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_prompt_example ALTER COLUMN id SET DEFAULT nextval('public.image_prompt_example_id_seq'::regclass);


--
-- Name: image_setting id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_setting ALTER COLUMN id SET DEFAULT nextval('public.image_setting_id_seq'::regclass);


--
-- Name: image_style id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_style ALTER COLUMN id SET DEFAULT nextval('public.image_style_id_seq'::regclass);


--
-- Name: images id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.images ALTER COLUMN id SET DEFAULT nextval('public.images_id_seq'::regclass);


--
-- Name: llm_action id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action ALTER COLUMN id SET DEFAULT nextval('public.llm_action_id_seq'::regclass);


--
-- Name: llm_action_history id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action_history ALTER COLUMN id SET DEFAULT nextval('public.llm_action_history_id_seq'::regclass);


--
-- Name: llm_config id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_config ALTER COLUMN id SET DEFAULT nextval('public.llm_config_id_seq'::regclass);


--
-- Name: llm_format_template id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_format_template ALTER COLUMN id SET DEFAULT nextval('public.llm_format_template_id_seq'::regclass);


--
-- Name: llm_interaction id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_interaction ALTER COLUMN id SET DEFAULT nextval('public.llm_interaction_id_seq'::regclass);


--
-- Name: llm_model id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_model ALTER COLUMN id SET DEFAULT nextval('public.llm_model_id_seq'::regclass);


--
-- Name: llm_prompt id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt ALTER COLUMN id SET DEFAULT nextval('public.llm_prompt_id_seq'::regclass);


--
-- Name: llm_prompt_part id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt_part ALTER COLUMN id SET DEFAULT nextval('public.llm_prompt_part_id_seq'::regclass);


--
-- Name: llm_provider id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_provider ALTER COLUMN id SET DEFAULT nextval('public.llm_provider_id_seq'::regclass);


--
-- Name: post id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post ALTER COLUMN id SET DEFAULT nextval('public.post_id_seq'::regclass);


--
-- Name: post_development id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_development ALTER COLUMN id SET DEFAULT nextval('public.post_development_id_seq'::regclass);


--
-- Name: post_images id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_images ALTER COLUMN id SET DEFAULT nextval('public.post_images_id_seq'::regclass);


--
-- Name: post_section id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section ALTER COLUMN id SET DEFAULT nextval('public.post_section_id_seq'::regclass);


--
-- Name: post_section_elements id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section_elements ALTER COLUMN id SET DEFAULT nextval('public.post_section_elements_id_seq'::regclass);


--
-- Name: post_workflow_stage id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_stage ALTER COLUMN id SET DEFAULT nextval('public.post_workflow_stage_id_seq'::regclass);


--
-- Name: post_workflow_step_action id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_step_action ALTER COLUMN id SET DEFAULT nextval('public.post_workflow_step_action_id_seq'::regclass);


--
-- Name: post_workflow_sub_stage id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_sub_stage ALTER COLUMN id SET DEFAULT nextval('public.post_workflow_sub_stage_id_seq'::regclass);


--
-- Name: substage_action_default id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.substage_action_default ALTER COLUMN id SET DEFAULT nextval('public.substage_action_default_id_seq'::regclass);


--
-- Name: tag id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.tag ALTER COLUMN id SET DEFAULT nextval('public.tag_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: workflow id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow ALTER COLUMN id SET DEFAULT nextval('public.workflow_id_seq'::regclass);


--
-- Name: workflow_field_mapping id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mapping ALTER COLUMN id SET DEFAULT nextval('public.workflow_field_mapping_id_seq'::regclass);


--
-- Name: workflow_field_mappings id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mappings ALTER COLUMN id SET DEFAULT nextval('public.workflow_field_mappings_id_seq'::regclass);


--
-- Name: workflow_format_template id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_format_template ALTER COLUMN id SET DEFAULT nextval('public.workflow_format_template_id_seq'::regclass);


--
-- Name: workflow_post_format id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_post_format ALTER COLUMN id SET DEFAULT nextval('public.workflow_post_format_id_seq'::regclass);


--
-- Name: workflow_stage_entity id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_entity ALTER COLUMN id SET DEFAULT nextval('public.workflow_stage_entity_id_seq'::regclass);


--
-- Name: workflow_stage_format id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_format ALTER COLUMN id SET DEFAULT nextval('public.workflow_stage_format_id_seq'::regclass);


--
-- Name: workflow_step_context_config id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_context_config ALTER COLUMN id SET DEFAULT nextval('public.workflow_step_context_config_id_seq'::regclass);


--
-- Name: workflow_step_entity id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity ALTER COLUMN id SET DEFAULT nextval('public.workflow_step_entity_id_seq'::regclass);


--
-- Name: workflow_step_format id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_format ALTER COLUMN id SET DEFAULT nextval('public.workflow_step_format_id_seq'::regclass);


--
-- Name: workflow_step_input id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_input ALTER COLUMN id SET DEFAULT nextval('public.workflow_step_input_id_seq'::regclass);


--
-- Name: workflow_step_prompt id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_prompt ALTER COLUMN id SET DEFAULT nextval('public.workflow_step_prompt_id_seq'::regclass);


--
-- Name: workflow_steps id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_steps ALTER COLUMN id SET DEFAULT nextval('public.workflow_steps_id_seq'::regclass);


--
-- Name: workflow_sub_stage_entity id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity ALTER COLUMN id SET DEFAULT nextval('public.workflow_sub_stage_entity_id_seq'::regclass);


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.category (id, name, slug, description) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.image (id, filename, original_filename, path, alt_text, caption, image_prompt, notes, image_metadata, watermarked, watermarked_path, created_at, updated_at) FROM stdin;
139	kilt-evolution_header.jpg	\N	../../app/static/images/posts/kilt-evolution_header.jpg	Collage of kilt styles over the centuries.	The kilt has evolved constantly from its earliest origins.	Collage representing the evolution of the Scottish kilt through centuries, showing styles from early wraps to modern tailored kilts. Blend historical illustrations and photographic elements. Aspect ratio 16:9.	Initial header concept.	{"notes": "Initial header concept.", "prompt": "Collage representing the evolution of the Scottish kilt through centuries, showing styles from early wraps to modern tailored kilts. Blend historical illustrations and photographic elements. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Collage of kilt styles over the centuries.", "blog_caption": "The kilt has evolved constantly from its earliest origins."}, "description": "Header image", "syndication": {"facebook": {"status": "pending", "caption": "Did you know the kilt evolved significantly over centuries? From the practical 'féileadh mòr' of the Highlands to a symbol of identity and even high fashion, its story is fascinating. Learn more about the evolution of this iconic garment on the blog! [Link Placeholder]"}, "instagram": {"status": "pending", "caption": "From battlefield necessity to global fashion icon! ✨ Explore the incredible journey of the Scottish kilt through the ages. #KiltHistory #ScottishFashion #Tartan #HighlandWear #Scotland #CelticStyle #MenswearEvolution", "hashtags": ["KiltHistory", "ScottishFashion", "Tartan", "HighlandWear", "Scotland", "CelticStyle", "MenswearEvolution"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_header.jpg", "filename_local": "kilt-evolution_header.jpg", "uploaded_path_relative": "/blog/kilt-evolution_header.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.645009	2025-05-18 16:25:20.645013
140	kilt-evolution_early-highland-dress.jpg	\N	../../app/static/images/posts/kilt-evolution_early-highland-dress.jpg	Pictish warrior in tunic and brat cloak on a cliff with standing stones.	Early Highland attire: A Pictish warrior embodying resilience in practical woollen tunic and cloak.	Illustration of an early Highlander (Pict or Gael) pre-16th century, wearing a simple woollen tunic ('léine') and brat cloak fastened with a brooch, standing in a rugged Highland landscape. Focus on practical, layered clothing. Historically accurate. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Illustration of an early Highlander (Pict or Gael) pre-16th century, wearing a simple woollen tunic ('léine') and brat cloak fastened with a brooch, standing in a rugged Highland landscape. Focus on practical, layered clothing. Historically accurate. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Pictish warrior in tunic and brat cloak on a cliff with standing stones.", "blog_caption": "Early Highland attire: A Pictish warrior embodying resilience in practical woollen tunic and cloak."}, "description": "Early Forms of Highland Dress", "syndication": {"facebook": {"status": "pending", "caption": "Journey back before the 16th century! Early Highland attire focused on survival in rugged landscapes, featuring practical woollen tunics (léine) and cloaks (brat). These garments laid the groundwork for later iconic styles. #ScottishHistory #CelticFashion"}, "instagram": {"status": "pending", "caption": "Before the familiar kilt: Early Highland dress prioritized practicality for rugged terrain. Think layered woollen tunics & cloaks! #HighlandHistory #AncientScotland #Picts #Gaels #ScottishClothing #CelticHistory", "hashtags": ["HighlandHistory", "AncientScotland", "Picts", "Gaels", "ScottishClothing", "CelticHistory"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_early-highland-dress.jpg", "filename_local": "kilt-evolution_early-highland-dress.jpg", "uploaded_path_relative": "/blog/kilt-evolution_early-highland-dress.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.66228	2025-05-18 16:25:20.662283
141	kilt-evolution_great-kilt-origins.jpg	\N	../../app/static/images/posts/kilt-evolution_great-kilt-origins.jpg	16th-century Highlander pleating and belting a large féileadh mòr tartan wrap.	The versatile féileadh mòr: A 16th-century Highlander dons the great kilt for protection and practicality.	A 16th-century Highlander in a realistic setting, demonstrating how to pleat and belt the large 'féileadh mòr' (great kilt) made of several yards of tartan cloth. Focus on the process and the versatile nature of the garment. Historical accuracy in clothing and environment. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "A 16th-century Highlander in a realistic setting, demonstrating how to pleat and belt the large 'féileadh mòr' (great kilt) made of several yards of tartan cloth. Focus on the process and the versatile nature of the garment. Historical accuracy in clothing and environment. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "16th-century Highlander pleating and belting a large féileadh mòr tartan wrap.", "blog_caption": "The versatile féileadh mòr: A 16th-century Highlander dons the great kilt for protection and practicality."}, "description": "Origins of the Great Kilt", "syndication": {"facebook": {"status": "pending", "caption": "The original 'Great Kilt' or Féileadh Mòr emerged in the 16th century. This single large piece of tartan was skillfully pleated and belted, serving multiple practical purposes for Highlanders. #ScottishHeritage #KiltEvolution #FeileadhMor"}, "instagram": {"status": "pending", "caption": "Meet the Féileadh Mòr! The 16th-century 'great kilt' was a versatile marvel – cloak by day, blanket by night. #GreatKilt #FeileadhMor #ScottishHistory #TartanTuesday #HighlandDress #Kilt", "hashtags": ["GreatKilt", "FeileadhMor", "ScottishHistory", "TartanTuesday", "HighlandDress", "Kilt"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_great-kilt-origins.jpg", "filename_local": "kilt-evolution_great-kilt-origins.jpg", "uploaded_path_relative": "/blog/kilt-evolution_great-kilt-origins.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.672373	2025-05-18 16:25:20.67238
142	kilt-evolution_great-kilt-significance.jpg	\N	../../app/static/images/posts/kilt-evolution_great-kilt-significance.jpg	17th-century MacLeod chief distributing tartan plaids to clansmen during a gathering.	Tartan as identity: A 17th-century clan chief reinforces kinship through the distribution of plaids.	Illustration depicting a 17th-century Highland clan chief, perhaps MacDonald or Campbell, distributing specific tartan plaids (féileadh mòr) to his loyal clansmen during an outdoor gathering. Emphasize the tartan patterns as symbols of identity and allegiance. Detailed historical attire and setting. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Illustration depicting a 17th-century Highland clan chief, perhaps MacDonald or Campbell, distributing specific tartan plaids (féileadh mòr) to his loyal clansmen during an outdoor gathering. Emphasize the tartan patterns as symbols of identity and allegiance. Detailed historical attire and setting. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "17th-century MacLeod chief distributing tartan plaids to clansmen during a gathering.", "blog_caption": "Tartan as identity: A 17th-century clan chief reinforces kinship through the distribution of plaids."}, "description": "Cultural Significance of the Great Kilt", "syndication": {"facebook": {"status": "pending", "caption": "By the 17th century, tartan evolved into a powerful symbol of clan identity and loyalty. Chiefs distributed specific patterns, reinforcing kinship and social structure within the Highlands. #ScottishHistory #Tartan #ClanLife"}, "instagram": {"status": "pending", "caption": "Tartan wasn't just fabric; it was identity! In the 17th century, specific patterns signified clan allegiance, like visual badges of honour. #ClanTartan #ScottishClans #HighlandCulture #TartanHistory #ScotlandIsNow", "hashtags": ["ClanTartan", "ScottishClans", "HighlandCulture", "TartanHistory", "ScotlandIsNow"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_great-kilt-significance.jpg", "filename_local": "kilt-evolution_great-kilt-significance.jpg", "uploaded_path_relative": "/blog/kilt-evolution_great-kilt-significance.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.68492	2025-05-18 16:25:20.684929
143	kilt-evolution_kilt-adaptations-practicality.jpg	\N	../../app/static/images/posts/kilt-evolution_kilt-adaptations-practicality.jpg	Highland hunter around 1700 tucking the upper part of his féileadh mòr into his belt.	Adapting for action: A Highland hunter modifies the great kilt for greater freedom of movement circa 1700.	Realistic depiction of a Highland hunter or soldier around the late 17th/early 18th century, actively tucking the upper shoulder plaid part of his féileadh mòr into his belt to create a more practical, skirt-like lower half for better movement. Show action or purpose (hunting/marching). Accurate historical detail. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Realistic depiction of a Highland hunter or soldier around the late 17th/early 18th century, actively tucking the upper shoulder plaid part of his féileadh mòr into his belt to create a more practical, skirt-like lower half for better movement. Show action or purpose (hunting/marching). Accurate historical detail. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Highland hunter around 1700 tucking the upper part of his féileadh mòr into his belt.", "blog_caption": "Adapting for action: A Highland hunter modifies the great kilt for greater freedom of movement circa 1700."}, "description": "Adaptations for Practicality", "syndication": {"facebook": {"status": "pending", "caption": "Practicality drives change! As life demanded more dynamic movement, Highlanders began adapting the bulky Féileadh Mòr by tucking the upper plaid, a key step towards the 'small kilt' we know today. #ScottishInnovation #KiltHistory #HighlandDress"}, "instagram": {"status": "pending", "caption": "Adapting for action! Late 17th-century Highlanders started tucking away the top plaid of the great kilt for practicality, paving the way for the modern kilt form. #KiltEvolution #HighlandLife #ScottishHistory #Adaptation #FeileadhMor", "hashtags": ["KiltEvolution", "HighlandLife", "ScottishHistory", "Adaptation", "FeileadhMor"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_kilt-adaptations-practicality.jpg", "filename_local": "kilt-evolution_kilt-adaptations-practicality.jpg", "uploaded_path_relative": "/blog/kilt-evolution_kilt-adaptations-practicality.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.733539	2025-05-18 16:25:20.733566
144	kilt-evolution_small-kilt-emergence.jpg	\N	../../app/static/images/posts/kilt-evolution_small-kilt-emergence.jpg	18th-century ironworker wearing the knee-length féileadh beag (small kilt) while working at a forge.	The birth of the modern kilt: An ironworker demonstrates the practicality of the féileadh beag around 1720.	Scene in an early 18th-century Highland ironworks (around 1720s), showing workers wearing the newly developed 'féileadh beag' (small kilt) – the pre-pleated, knee-length skirt without the shoulder plaid. Focus on the practicality for industrial work, perhaps near a forge or furnace. Link to Thomas Rawlinson's innovation. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Scene in an early 18th-century Highland ironworks (around 1720s), showing workers wearing the newly developed 'féileadh beag' (small kilt) – the pre-pleated, knee-length skirt without the shoulder plaid. Focus on the practicality for industrial work, perhaps near a forge or furnace. Link to Thomas Rawlinson's innovation. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "18th-century ironworker wearing the knee-length féileadh beag (small kilt) while working at a forge.", "blog_caption": "The birth of the modern kilt: An ironworker demonstrates the practicality of the féileadh beag around 1720."}, "description": "Emergence of the Small Kilt", "syndication": {"facebook": {"status": "pending", "caption": "Innovation corner: The early 18th century saw the emergence of the 'Féileadh Beag' (small kilt). Often credited to industrialist Thomas Rawlinson, this separated skirt design offered greater practicality, influencing kilt design forever. #KiltFacts #ScottishHeritage #IndustrialHistory"}, "instagram": {"status": "pending", "caption": "The modern kilt takes shape! Around 1720, the 'Féileadh Beag' or small kilt emerged, separating the pleated skirt from the shoulder plaid – a practical evolution for workers and soldiers. #SmallKilt #FeileadhBeag #KiltHistory #ScottishInnovation #18thCentury", "hashtags": ["SmallKilt", "FeileadhBeag", "KiltHistory", "ScottishInnovation", "18thCentury"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_small-kilt-emergence.jpg", "filename_local": "kilt-evolution_small-kilt-emergence.jpg", "uploaded_path_relative": "/blog/kilt-evolution_small-kilt-emergence.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.7398	2025-05-18 16:25:20.739809
145	kilt-evolution_highland-dress-suppression.jpg	\N	../../app/static/images/posts/kilt-evolution_highland-dress-suppression.jpg	Highland woman secretly weaving tartan by candlelight while Redcoats patrol outside, circa 1760.	Defiance in the shadows: Secretly weaving banned tartan during the Dress Act suppression (1746-1782).	Atmospheric, slightly clandestine scene inside a dimly lit Highland cottage, circa 1760. A determined Highland woman secretly weaves tartan on a small loom by candlelight, while the shadow of a patrolling Redcoat soldier is visible outside the window. Convey resilience and cultural defiance during the Dress Act (1746-1782). Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Atmospheric, slightly clandestine scene inside a dimly lit Highland cottage, circa 1760. A determined Highland woman secretly weaves tartan on a small loom by candlelight, while the shadow of a patrolling Redcoat soldier is visible outside the window. Convey resilience and cultural defiance during the Dress Act (1746-1782). Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Highland woman secretly weaving tartan by candlelight while Redcoats patrol outside, circa 1760.", "blog_caption": "Defiance in the shadows: Secretly weaving banned tartan during the Dress Act suppression (1746-1782)."}, "description": "Suppression of Highland Dress", "syndication": {"facebook": {"status": "pending", "caption": "A dark chapter: The Dress Act (1746-1782) aimed to suppress Highland culture by banning tartan and the kilt following the Jacobite rising. Yet, the spirit endured through acts of quiet defiance and cultural preservation. #WearWhatYouWant #ScottishHistory #CulturalSuppression #Resilience"}, "instagram": {"status": "pending", "caption": "A symbol forbidden! After Culloden, the Dress Act of 1746 banned tartan & kilts. But Highland culture persisted in secret acts of defiance, like weaving by candlelight. #DressAct #HighlandHistory #ScottishResilience #Tartan #Jacobite #ForbiddenFashion", "hashtags": ["DressAct", "HighlandHistory", "ScottishResilience", "Tartan", "Jacobite", "ForbiddenFashion"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_highland-dress-suppression.jpg", "filename_local": "kilt-evolution_highland-dress-suppression.jpg", "uploaded_path_relative": "/blog/kilt-evolution_highland-dress-suppression.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.743851	2025-05-18 16:25:20.74387
146	kilt-evolution_romantic-revival-renaissance.jpg	\N	../../app/static/images/posts/kilt-evolution_romantic-revival-renaissance.jpg	Sir Walter Scott in Royal Stewart tartan leading nobles during King George IV's 1822 Edinburgh visit.	Romantic revival: Sir Walter Scott orchestrates a tartan spectacle for King George IV in 1822 Edinburgh.	Grand, celebratory scene depicting Sir Walter Scott, adorned in prominent Royal Stewart tartan, orchestrating the 1822 visit of King George IV to Edinburgh. Show Lowland nobles, previously dismissive, now wearing kilts and tartan. Highlight the pageantry and romanticism transforming the kilt's image. Accurate depiction of Holyrood Palace or Edinburgh setting. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Grand, celebratory scene depicting Sir Walter Scott, adorned in prominent Royal Stewart tartan, orchestrating the 1822 visit of King George IV to Edinburgh. Show Lowland nobles, previously dismissive, now wearing kilts and tartan. Highlight the pageantry and romanticism transforming the kilt's image. Accurate depiction of Holyrood Palace or Edinburgh setting. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Sir Walter Scott in Royal Stewart tartan leading nobles during King George IV's 1822 Edinburgh visit.", "blog_caption": "Romantic revival: Sir Walter Scott orchestrates a tartan spectacle for King George IV in 1822 Edinburgh."}, "description": "Romantic Revival and Cultural Renaissance", "syndication": {"facebook": {"status": "pending", "caption": "From suppression to spectacle! The late 18th and 19th centuries saw a Romantic revival of Highland culture, heavily influenced by writers like Sir Walter Scott and cemented by King George IV's famous 1822 visit to Edinburgh, where tartan took centre stage. #ScottishRenaissance #KiltHistory #Romanticism #WalterScott"}, "instagram": {"status": "pending", "caption": "Tartan's big comeback! Thanks to Sir Walter Scott & King George IV's 1822 visit, the kilt was reborn in a wave of romantic revival, transforming into a symbol of Scottish identity & pageantry. #TartanRevival #SirWalterScott #RoyalVisit #ScottishRomanticism #KiltStyle", "hashtags": ["TartanRevival", "SirWalterScott", "RoyalVisit", "ScottishRomanticism", "KiltStyle", "19thCentury"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_romantic-revival-renaissance.jpg", "filename_local": "kilt-evolution_romantic-revival-renaissance.jpg", "uploaded_path_relative": "/blog/kilt-evolution_romantic-revival-renaissance.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.750491	2025-05-18 16:25:20.750495
147	kilt-evolution_military-adoption-influence.jpg	\N	../../app/static/images/posts/kilt-evolution_military-adoption-influence.jpg	Black Watch soldier in government sett kilt charging across a WWI battlefield with a bagpiper.	Courage in tartan: A Black Watch soldier embodies the kilt's military legacy during World War I.	Dynamic, gritty scene from a World War I battlefield (e.g., Western Front). A determined Black Watch soldier in his dark Government Sett kilt advances, perhaps alongside a piper. Convey the juxtaposition of traditional Highland dress in modern warfare, emphasizing bravery and regimental pride. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Dynamic, gritty scene from a World War I battlefield (e.g., Western Front). A determined Black Watch soldier in his dark Government Sett kilt advances, perhaps alongside a piper. Convey the juxtaposition of traditional Highland dress in modern warfare, emphasizing bravery and regimental pride. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Black Watch soldier in government sett kilt charging across a WWI battlefield with a bagpiper.", "blog_caption": "Courage in tartan: A Black Watch soldier embodies the kilt's military legacy during World War I."}, "description": "Military Adoption and Global Influence", "syndication": {"facebook": {"status": "pending", "caption": "The kilt went global largely thanks to its adoption by the British Army's Highland regiments. Their distinct tartans and battlefield bravery, from Napoleonic Wars to WWI, made the kilt an internationally recognized symbol. #MilitaryHistory #ScottishRegiments #Kilt #Tartan"}, "instagram": {"status": "pending", "caption": "Courage in tartan! Highland regiments like the Black Watch famously wore kilts into battle, becoming global symbols of Scottish bravery and identity, even on WW1 fields. #HighlandRegiment #BlackWatch #MilitaryKilt #ScottishSoldier #WWI #Courage", "hashtags": ["HighlandRegiment", "BlackWatch", "MilitaryKilt", "ScottishSoldier", "WWI", "Courage"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_military-adoption-influence.jpg", "filename_local": "kilt-evolution_military-adoption-influence.jpg", "uploaded_path_relative": "/blog/kilt-evolution_military-adoption-influence.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.752153	2025-05-18 16:25:20.752156
148	kilt-evolution_formal-everyday-attire.jpg	\N	../../app/static/images/posts/kilt-evolution_formal-everyday-attire.jpg	1950s Scottish wedding scene with groom in Prince Charlie kilt outfit and guests dancing a ceilidh.	From battlefield to ballroom: Kilts become central to 20th-century formal and celebratory wear.	Joyful, slightly nostalgic scene of a Scottish wedding reception or ceilidh in the 1950s/60s. Focus on guests wearing kilts (e.g., Prince Charlie outfits) for formal celebration, dancing, and socializing. Capture the post-war popularization of the kilt for non-military formal events. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "Joyful, slightly nostalgic scene of a Scottish wedding reception or ceilidh in the 1950s/60s. Focus on guests wearing kilts (e.g., Prince Charlie outfits) for formal celebration, dancing, and socializing. Capture the post-war popularization of the kilt for non-military formal events. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "1950s Scottish wedding scene with groom in Prince Charlie kilt outfit and guests dancing a ceilidh.", "blog_caption": "From battlefield to ballroom: Kilts become central to 20th-century formal and celebratory wear."}, "description": "Kilts in Formal and Everyday Attire", "syndication": {"facebook": {"status": "pending", "caption": "The 20th century saw the kilt firmly established as celebratory wear. Popularised by returning soldiers and embraced by the diaspora, it became synonymous with Scottish weddings, formal events, and cultural pride. #ScottishCulture #KiltStyle #20thCenturyFashion"}, "instagram": {"status": "pending", "caption": "From battlefield to ballroom! Post-WWII, the kilt became a staple of formal wear for weddings, ceilidhs, and celebrations, solidifying its place in 20th-century Scottish social life. #KiltOutfit #Ceilidh #ScottishWedding #FormalWear #VintageScotland #PrinceCharlie", "hashtags": ["KiltOutfit", "Ceilidh", "ScottishWedding", "FormalWear", "VintageScotland", "PrinceCharlie"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_formal-everyday-attire.jpg", "filename_local": "kilt-evolution_formal-everyday-attire.jpg", "uploaded_path_relative": "/blog/kilt-evolution_formal-everyday-attire.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.753736	2025-05-18 16:25:20.753738
149	kilt-evolution_modern-innovations-fashion.jpg	\N	../../app/static/images/posts/kilt-evolution_modern-innovations-fashion.jpg	Gender-fluid model on a neon runway wearing a deconstructed, futuristic tartan kilt.	The kilt reimagined: 21st-century fashion fuses tartan tradition with avant-garde and inclusive design.	High-fashion runway scene featuring a model (could be gender-fluid) wearing a modern, avant-garde kilt interpretation. Think unconventional materials (leather, denim, tech fabrics), deconstructed design, or bold contemporary tartan patterns. Emphasize the fusion of tradition and modern fashion trends, challenging norms. Dynamic lighting and runway setting. Aspect ratio 16:9.	\N	{"notes": null, "prompt": "High-fashion runway scene featuring a model (could be gender-fluid) wearing a modern, avant-garde kilt interpretation. Think unconventional materials (leather, denim, tech fabrics), deconstructed design, or bold contemporary tartan patterns. Emphasize the fusion of tradition and modern fashion trends, challenging norms. Dynamic lighting and runway setting. Aspect ratio 16:9.", "status": "approved", "metadata": {"alt": "Gender-fluid model on a neon runway wearing a deconstructed, futuristic tartan kilt.", "blog_caption": "The kilt reimagined: 21st-century fashion fuses tartan tradition with avant-garde and inclusive design."}, "description": "Modern Innovations and Fashion Trends", "syndication": {"facebook": {"status": "pending", "caption": "The kilt continues to evolve! 21st-century fashion embraces the kilt, experimenting with new materials, challenging gender norms, and blending streetwear influences with heritage. What do you think of modern kilt designs? #Kilt #FashionTrends #ScottishStyle #ContemporaryDesign"}, "instagram": {"status": "pending", "caption": "The kilt, but make it fashion! ⚡️ Today's designers reimagine tartan and the kilt form with modern materials, cuts, and a challenge to traditional norms. Tradition meets runway! #ModernKilt #TartanFashion #AvantGarde #ScottishDesign #FashionForward #Inclusivity", "hashtags": ["ModernKilt", "TartanFashion", "AvantGarde", "ScottishDesign", "FashionForward", "Inclusivity", "RunwayStyle"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/kilt-evolution/", "post_slug": "kilt-evolution", "public_url": "https://static.clan.com/media/blog/kilt-evolution_modern-innovations-fashion.jpg", "filename_local": "kilt-evolution_modern-innovations-fashion.jpg", "uploaded_path_relative": "/blog/kilt-evolution_modern-innovations-fashion.jpg"}, "watermark_status": "pending", "generation_status": "complete"}	f	\N	2025-05-18 16:25:20.755153	2025-05-18 16:25:20.755155
150	quaich-traditions_header-collage.jpg	\N	../../app/static/images/posts/quaich-traditions_header-collage.jpg	A collection of various Scottish quaichs from different eras	The Scottish Quaich: A journey through history, tradition, and symbolism.	A collection of various Scottish quaichs from different eras – wood, pewter, silver – arranged artistically on a background of subtle tartan, representing the scope of the article. Soft, inviting lighting. Aspect ratio 16:9.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A collection of various Scottish quaichs from different eras – wood, pewter, silver – arranged artistically on a background of subtle tartan, representing the scope of the article. Soft, inviting lighting. Aspect ratio 16:9.", "status": "pending_review", "metadata": {"alt": "A collection of various Scottish quaichs from different eras", "blog_caption": "The Scottish Quaich: A journey through history, tradition, and symbolism."}, "description": "Header image", "syndication": {"facebook": {"status": "pending", "caption": "What is a Quaich? Discover the story behind Scotland's traditional two-handled 'cup of friendship', a symbol of hospitality and trust for centuries. Learn more on the blog! [Link Placeholder]"}, "instagram": {"status": "pending", "caption": "Slàinte! Exploring the rich history of the Scottish Quaich, the 'cup of friendship'. From clans to kings to modern weddings. #Quaich #ScottishTradition #CupOfFriendship #Celtic #Scotland #History", "hashtags": ["Quaich", "ScottishTradition", "CupOfFriendship", "Celtic", "Scotland", "History", "Pewter", "Silver"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_header-collage.jpg", "filename_local": "quaich-traditions_header-collage.jpg", "uploaded_path_relative": "/blog/quaich-traditions_header-collage.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.756573	2025-05-18 16:25:20.756575
151	quaich-traditions_early-origins-wooden.jpg	\N	../../app/static/images/posts/quaich-traditions_early-origins-wooden.jpg	Early hand-carved wooden quaich by a hearth	A simple wooden quaich reflects early Highland values of peace and trust.	A rustic medieval Scottish setting depicting a simple, hand-carved wooden quaich resting on a rough wooden table near a warm, stone-built hearth. Early Scottish Highlanders gather around in traditional tartan cloaks, symbolically exchanging the quaich to represent friendship, trust, and peace. Include warm, candlelit tones and accurate historical details of Highland clothing and furnishings.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A rustic medieval Scottish setting depicting a simple, hand-carved wooden quaich resting on a rough wooden table near a warm, stone-built hearth. Early Scottish Highlanders gather around in traditional tartan cloaks, symbolically exchanging the quaich to represent friendship, trust, and peace. Include warm, candlelit tones and accurate historical details of Highland clothing and furnishings.", "status": "pending_review", "metadata": {"alt": "Early hand-carved wooden quaich by a hearth", "blog_caption": "A simple wooden quaich reflects early Highland values of peace and trust."}, "description": "Early Origins", "syndication": {"facebook": {"status": "pending", "caption": "The origins of the Quaich lie in medieval Scotland, often crafted from simple wood or horn. Its unique two-handled design was practical - promoting trust during shared drinks. #ScottishHistory #QuaichFacts #CelticTradition"}, "instagram": {"status": "pending", "caption": "Back to basics! Early Scottish quaichs were often carved from wood, symbolising peace & trust. The two handles meant no hidden weapons! #Quaich #MedievalScotland #Woodworking #CelticHistory #ScottishCraft", "hashtags": ["Quaich", "MedievalScotland", "Woodworking", "CelticHistory", "ScottishCraft"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_early-origins-wooden.jpg", "filename_local": "quaich-traditions_early-origins-wooden.jpg", "uploaded_path_relative": "/blog/quaich-traditions_early-origins-wooden.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.757773	2025-05-18 16:25:20.757775
152	quaich-traditions_clan-unity-hospitality.jpg	\N	../../app/static/images/posts/quaich-traditions_clan-unity-hospitality.jpg	Clan chieftain toasts with a quaich at a 17th-century Highland gathering	The quaich: central to clan gatherings, fostering unity and hospitality.	A vibrant scene at a Scottish Highland clan gathering in the 17th century. At its center, a clan chieftain raises an ornately carved wooden quaich in a ceremonial toast surrounded by warriors, elders, and clansfolk in historically accurate clan tartans. Emphasize expressions of unity, pride, and camaraderie, with detailed Highland attire, symbolic banners, and traditional Celtic decor.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A vibrant scene at a Scottish Highland clan gathering in the 17th century. At its center, a clan chieftain raises an ornately carved wooden quaich in a ceremonial toast surrounded by warriors, elders, and clansfolk in historically accurate clan tartans. Emphasize expressions of unity, pride, and camaraderie, with detailed Highland attire, symbolic banners, and traditional Celtic decor.", "status": "pending_review", "metadata": {"alt": "Clan chieftain toasts with a quaich at a 17th-century Highland gathering", "blog_caption": "The quaich: central to clan gatherings, fostering unity and hospitality."}, "description": "Clan Unity and Hospitality", "syndication": {"facebook": {"status": "pending", "caption": "More than just a cup! In clan gatherings, sharing the quaich was a powerful ritual signifying mutual respect, resolving conflicts, and celebrating together. #ScottishTradition #ClanUnity #QuaichHistory"}, "instagram": {"status": "pending", "caption": "A symbol of unity! The quaich was essential at Highland clan gatherings, shared to build trust and celebrate together. #ClanLife #ScottishGathering #Quaich #HighlandCulture #Scotland", "hashtags": ["ClanLife", "ScottishGathering", "Quaich", "HighlandCulture", "Scotland", "Hospitality"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_clan-unity-hospitality.jpg", "filename_local": "quaich-traditions_clan-unity-hospitality.jpg", "uploaded_path_relative": "/blog/quaich-traditions_clan-unity-hospitality.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.759154	2025-05-18 16:25:20.759155
153	quaich-traditions_design-evolution.jpg	\N	../../app/static/images/posts/quaich-traditions_design-evolution.jpg	Collection showing quaich evolution from wood to ornate silver	From simple wood to intricate silver: the evolution of quaich craftsmanship.	A beautifully detailed illustration showcasing the historical progression of Scottish quaich designs from simple wooden and horn quaichs to intricately crafted silver and pewter versions. Depict various examples arranged chronologically on an antique Scottish tartan cloth, clearly highlighting evolving craftsmanship, materials, decorative Celtic motifs, and engraved patterns.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A beautifully detailed illustration showcasing the historical progression of Scottish quaich designs from simple wooden and horn quaichs to intricately crafted silver and pewter versions. Depict various examples arranged chronologically on an antique Scottish tartan cloth, clearly highlighting evolving craftsmanship, materials, decorative Celtic motifs, and engraved patterns.", "status": "pending_review", "metadata": {"alt": "Collection showing quaich evolution from wood to ornate silver", "blog_caption": "From simple wood to intricate silver: the evolution of quaich craftsmanship."}, "description": "Evolution of Design", "syndication": {"facebook": {"status": "pending", "caption": "The design of the quaich tells a story of evolving craftsmanship. Starting with wood, techniques like stave-building emerged, followed by luxurious silver and popular pewter versions, often featuring beautiful Celtic details. #QuaichDesign #ScottishArtisans #CelticDesign"}, "instagram": {"status": "pending", "caption": "Watch the quaich evolve! From humble wood & horn to elegant pewter & stunning silver adorned with Celtic designs. Scottish craftsmanship through the ages. #ScottishCraftsmanship #Quaich #DesignHistory #CelticArt #Pewter #Silver #Scotland", "hashtags": ["ScottishCraftsmanship", "Quaich", "DesignHistory", "CelticArt", "Pewter", "Silver", "Scotland", "Antiques"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_design-evolution.jpg", "filename_local": "quaich-traditions_design-evolution.jpg", "uploaded_path_relative": "/blog/quaich-traditions_design-evolution.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.760527	2025-05-18 16:25:20.760528
154	quaich-traditions_wedding-ceremony.jpg	\N	../../app/static/images/posts/quaich-traditions_wedding-ceremony.jpg	Couple sharing whisky from a quaich during their Scottish wedding	A central part of Scottish weddings, the quaich seals the couple's commitment.	A warmly lit, intimate depiction of a traditional Scottish wedding ceremony set in a rustic Highland chapel or castle. A bride and groom in traditional Scottish wedding attire (kilt and dress) joyfully share whisky from an ornate silver quaich. Family and friends surround them, smiling and celebrating, highlighting the quaich’s role as a symbol of shared joy and commitment.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A warmly lit, intimate depiction of a traditional Scottish wedding ceremony set in a rustic Highland chapel or castle. A bride and groom in traditional Scottish wedding attire (kilt and dress) joyfully share whisky from an ornate silver quaich. Family and friends surround them, smiling and celebrating, highlighting the quaich’s role as a symbol of shared joy and commitment.", "status": "pending_review", "metadata": {"alt": "Couple sharing whisky from a quaich during their Scottish wedding", "blog_caption": "A central part of Scottish weddings, the quaich seals the couple's commitment."}, "description": "The Quaich in Ceremony and Celebration", "syndication": {"facebook": {"status": "pending", "caption": "From weddings and births to farewells, the quaich has long marked significant life events in Scotland, symbolizing shared moments and collective memory. The wedding ceremony is a particularly cherished tradition. #ScottishCustoms #Quaich #LifeEvents #WeddingIdeas"}, "instagram": {"status": "pending", "caption": "Sealing the vows with a sip! The quaich is a beautiful tradition in Scottish weddings, symbolizing the couple's commitment to share life's journey together. ❤️ #ScottishWedding #WeddingTradition #QuaichCeremony #CupOfFriendship #LoveAndWhisky", "hashtags": ["ScottishWedding", "WeddingTradition", "QuaichCeremony", "CupOfFriendship", "LoveAndWhisky", "CelticWedding"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_wedding-ceremony.jpg", "filename_local": "quaich-traditions_wedding-ceremony.jpg", "uploaded_path_relative": "/blog/quaich-traditions_wedding-ceremony.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.761794	2025-05-18 16:25:20.761795
155	quaich-traditions_royal-gift.jpg	\N	../../app/static/images/posts/quaich-traditions_royal-gift.jpg	King James VI presenting an ornate silver quaich as a gift	Royal approval: King James VI gifting a quaich highlights its diplomatic importance.	A historically accurate and majestic scene from the Scottish royal court in the late 16th century, showing King James VI presenting a luxurious, intricately decorated silver quaich as a diplomatic gift to a visiting dignitary. Include richly detailed period costumes, royal regalia, ornate throne setting, and realistic expressions conveying goodwill and diplomacy.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A historically accurate and majestic scene from the Scottish royal court in the late 16th century, showing King James VI presenting a luxurious, intricately decorated silver quaich as a diplomatic gift to a visiting dignitary. Include richly detailed period costumes, royal regalia, ornate throne setting, and realistic expressions conveying goodwill and diplomacy.", "status": "pending_review", "metadata": {"alt": "King James VI presenting an ornate silver quaich as a gift", "blog_caption": "Royal approval: King James VI gifting a quaich highlights its diplomatic importance."}, "description": "Quaich and Royal Connections", "syndication": {"facebook": {"status": "pending", "caption": "The quaich's influence reached the highest courts. King James VI famously gifted quaichs, and later royal visits by Queen Victoria helped solidify its status as a treasured symbol of Scottish heritage recognised by royalty. #ScottishRoyalty #QuaichHistory #HistoricalObjects"}, "instagram": {"status": "pending", "caption": "Fit for a king! 👑 Scottish monarchs like James VI used the quaich as a significant gift, cementing alliances and showcasing Scottish hospitality to royalty and dignitaries. #RoyalScotland #KingJamesVI #Quaich #DiplomaticGift #ScottishHistory #Silverware", "hashtags": ["RoyalScotland", "KingJamesVI", "Quaich", "DiplomaticGift", "ScottishHistory", "Silverware", "16thCentury"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_royal-gift.jpg", "filename_local": "quaich-traditions_royal-gift.jpg", "uploaded_path_relative": "/blog/quaich-traditions_royal-gift.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.763497	2025-05-18 16:25:20.763499
156	quaich-traditions_whisky-pairing.jpg	\N	../../app/static/images/posts/quaich-traditions_whisky-pairing.jpg	Pewter quaich filled with whisky resting on an oak barrel	A perfect pairing: The quaich often held whisky, Scotland's famous spirit.	A cozy, authentic Scottish scene inside a historical whisky distillery tasting room. A polished pewter quaich, prominently placed on an oak barrel, holds golden whisky illuminated warmly by natural window light. Surround it with whisky bottles, barley sheaves, and rustic distillery equipment, highlighting the timeless Scottish pairing of quaich and whisky.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A cozy, authentic Scottish scene inside a historical whisky distillery tasting room. A polished pewter quaich, prominently placed on an oak barrel, holds golden whisky illuminated warmly by natural window light. Surround it with whisky bottles, barley sheaves, and rustic distillery equipment, highlighting the timeless Scottish pairing of quaich and whisky.", "status": "pending_review", "metadata": {"alt": "Pewter quaich filled with whisky resting on an oak barrel", "blog_caption": "A perfect pairing: The quaich often held whisky, Scotland's famous spirit."}, "description": "Quaich Traditions and Whisky", "syndication": {"facebook": {"status": "pending", "caption": "What's traditionally served in a quaich? Often, it's Scotland's national drink – whisky! This pairing enhances the symbolism of warmth and welcome, a tradition often kept alive in distilleries today. #WhiskyFacts #Quaich #ScottishDrinks #Hospitality"}, "instagram": {"status": "pending", "caption": "Name a more iconic duo... 😉 The quaich and Scotch whisky! Sharing a dram from the 'cup of friendship' is a cornerstone of Scottish hospitality. Slàinte! 🥃 #QuaichAndWhisky #ScotchWhisky #ScottishHospitality #WhiskyTasting #Slainte #Scotland #Distillery", "hashtags": ["QuaichAndWhisky", "ScotchWhisky", "ScottishHospitality", "WhiskyTasting", "Slainte", "Scotland", "Distillery", "Pewter"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_whisky-pairing.jpg", "filename_local": "quaich-traditions_whisky-pairing.jpg", "uploaded_path_relative": "/blog/quaich-traditions_whisky-pairing.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.764825	2025-05-18 16:25:20.764827
157	quaich-traditions_decline-revival.jpg	\N	../../app/static/images/posts/quaich-traditions_decline-revival.jpg	Split image showing a stored quaich vs. one used in a modern festival	From quiet preservation during decline to vibrant celebration in its revival.	An evocative illustration symbolizing both cultural decline and revival. On one side, a shadowed Scottish Highland cottage interior with a simple wooden quaich stored carefully on a shelf, symbolizing suppressed cultural traditions during the 18th-century Highland Clearances. On the other, bright revival imagery showcasing Scottish pride with restored quaich traditions amid Highland festivals and celebrations in vivid tartan colors.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "An evocative illustration symbolizing both cultural decline and revival. On one side, a shadowed Scottish Highland cottage interior with a simple wooden quaich stored carefully on a shelf, symbolizing suppressed cultural traditions during the 18th-century Highland Clearances. On the other, bright revival imagery showcasing Scottish pride with restored quaich traditions amid Highland festivals and celebrations in vivid tartan colors.", "status": "pending_review", "metadata": {"alt": "Split image showing a stored quaich vs. one used in a modern festival", "blog_caption": "From quiet preservation during decline to vibrant celebration in its revival."}, "description": "Cultural Decline and Revival", "syndication": {"facebook": {"status": "pending", "caption": "Like many aspects of Highland culture, the quaich faced decline during periods of upheaval. But the tradition was preserved and saw a strong revival, becoming a cherished national symbol once again. #ScottishHeritage #CulturalHistory #Revival"}, "instagram": {"status": "pending", "caption": "A story of resilience! 🔥 Though Highland culture faced suppression, traditions like the quaich persisted quietly, ready for a vibrant revival in later centuries. #CulturalRevival #ScottishResilience #Quaich #HighlandHistory #Jacobite #ScotlandStrong", "hashtags": ["CulturalRevival", "ScottishResilience", "Quaich", "HighlandHistory", "Jacobite", "ScotlandStrong"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_decline-revival.jpg", "filename_local": "quaich-traditions_decline-revival.jpg", "uploaded_path_relative": "/blog/quaich-traditions_decline-revival.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.766249	2025-05-18 16:25:20.766251
158	quaich-traditions_contemporary-culture.jpg	\N	../../app/static/images/posts/quaich-traditions_contemporary-culture.jpg	Modern couple celebrating with a silver quaich at their wedding	The quaich tradition lives on in contemporary Scottish celebrations like weddings.	A cheerful, contemporary Scottish wedding reception scene in a modern venue with subtle traditional touches. A couple dressed in modern formal attire joyfully holds a sleek, polished silver quaich, capturing a modern continuation of the ancient tradition. Guests celebrate in the background, showing the quaich’s enduring symbolism of unity and friendship.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A cheerful, contemporary Scottish wedding reception scene in a modern venue with subtle traditional touches. A couple dressed in modern formal attire joyfully holds a sleek, polished silver quaich, capturing a modern continuation of the ancient tradition. Guests celebrate in the background, showing the quaich’s enduring symbolism of unity and friendship.", "status": "pending_review", "metadata": {"alt": "Modern couple celebrating with a silver quaich at their wedding", "blog_caption": "The quaich tradition lives on in contemporary Scottish celebrations like weddings."}, "description": "The Quaich in Contemporary Scottish Culture", "syndication": {"facebook": {"status": "pending", "caption": "The quaich isn't just history! It's actively used in contemporary Scottish culture, especially weddings, and cherished as gifts and connections to ancestry by Scots around the globe. #LivingTradition #ScottishCultureToday #QuaichLove"}, "instagram": {"status": "pending", "caption": "Tradition endures! The quaich remains a beloved part of modern Scottish life, especially at weddings, anniversaries, and as meaningful gifts connecting Scots worldwide to their heritage. #ModernScotland #ScottishTradition #Quaich #WeddingGift #Heritage #FamilyHeirloom", "hashtags": ["ModernScotland", "ScottishTradition", "Quaich", "WeddingGift", "Heritage", "FamilyHeirloom", "Diaspora"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_contemporary-culture.jpg", "filename_local": "quaich-traditions_contemporary-culture.jpg", "uploaded_path_relative": "/blog/quaich-traditions_contemporary-culture.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.767514	2025-05-18 16:25:20.767515
159	quaich-traditions_modern-diplomacy.jpg	\N	../../app/static/images/posts/quaich-traditions_modern-diplomacy.jpg	Scottish official presenting an engraved quaich to a diplomat	A modern symbol of goodwill: The quaich used in international diplomacy.	A formal diplomatic ceremony at a modern Scottish government building or historic site, showing a Scottish official warmly presenting a gleaming, engraved quaich to an international representative. Capture respectful, friendly interactions, modern business attire, official flags, and expressions conveying genuine goodwill, emphasizing the quaich’s role in contemporary diplomacy.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A formal diplomatic ceremony at a modern Scottish government building or historic site, showing a Scottish official warmly presenting a gleaming, engraved quaich to an international representative. Capture respectful, friendly interactions, modern business attire, official flags, and expressions conveying genuine goodwill, emphasizing the quaich’s role in contemporary diplomacy.", "status": "pending_review", "metadata": {"alt": "Scottish official presenting an engraved quaich to a diplomat", "blog_caption": "A modern symbol of goodwill: The quaich used in international diplomacy."}, "description": "Quaich as a Modern Symbol of Friendship and Diplomacy", "syndication": {"facebook": {"status": "pending", "caption": "From clan symbol to international gesture! The quaich is now frequently used in modern diplomacy by Scottish leaders to represent friendship and build connections across borders. #Symbolism #ScotlandOnTheWorldStage #Diplomacy"}, "instagram": {"status": "pending", "caption": "Scotland's cup of friendship goes global! 🤝 Today, the quaich is often presented as a diplomatic gift, symbolising goodwill, mutual respect, and partnership on the international stage. #ScottishDiplomacy #Quaich #FriendshipCup #InternationalRelations #ScotlandTheWorld", "hashtags": ["ScottishDiplomacy", "Quaich", "FriendshipCup", "InternationalRelations", "ScotlandTheWorld", "GlobalScot"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_modern-diplomacy.jpg", "filename_local": "quaich-traditions_modern-diplomacy.jpg", "uploaded_path_relative": "/blog/quaich-traditions_modern-diplomacy.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.768814	2025-05-18 16:25:20.768816
160	quaich-traditions_collecting-quaichs.jpg	\N	../../app/static/images/posts/quaich-traditions_collecting-quaichs.jpg	Museum display showing a collection of antique and modern quaichs	Prized by collectors: Antique and modern quaichs displayed in a museum setting.	A museum-quality display illustrating various antique and modern quaichs arranged meticulously within a glass showcase in a Scottish cultural heritage museum. Quaichs range from antique silver pieces adorned with intricate Celtic engraving to contemporary minimalist designs, accurately reflecting different historical periods. Include subtle museum lighting to emphasize craftsmanship and cultural value.	Needs final image generation.	{"notes": "Needs final image generation.", "prompt": "A museum-quality display illustrating various antique and modern quaichs arranged meticulously within a glass showcase in a Scottish cultural heritage museum. Quaichs range from antique silver pieces adorned with intricate Celtic engraving to contemporary minimalist designs, accurately reflecting different historical periods. Include subtle museum lighting to emphasize craftsmanship and cultural value.", "status": "pending_review", "metadata": {"alt": "Museum display showing a collection of antique and modern quaichs", "blog_caption": "Prized by collectors: Antique and modern quaichs displayed in a museum setting."}, "description": "Collecting Quaichs", "syndication": {"facebook": {"status": "pending", "caption": "Quaichs are not just functional; they're collectible works of art! From historic silver pieces to contemporary designs, they represent centuries of Scottish craftsmanship and culture. #ScottishCollectibles #Quaich #ArtHistory #Craftsmanship"}, "instagram": {"status": "pending", "caption": "Collecting history! Antique silver quaichs are highly sought after, while modern artisans keep the tradition alive with new designs. A beautiful blend of heritage and craft. #QuaichCollecting #AntiqueSilver #ScottishAntiques #ModernCraft #MuseumDisplay #Collectible", "hashtags": ["QuaichCollecting", "AntiqueSilver", "ScottishAntiques", "ModernCraft", "MuseumDisplay", "Collectible", "CelticArt"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": "https://static.clan.com/media/blog/quaich-traditions_collecting-quaichs.jpg", "filename_local": "quaich-traditions_collecting-quaichs.jpg", "uploaded_path_relative": "/blog/quaich-traditions_collecting-quaichs.jpg"}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.770783	2025-05-18 16:25:20.770784
161	quaich-traditions_enduring-legacy.png	\N	../../app/static/images/posts/quaich-traditions_enduring-legacy.png	Hands of different generations holding a silver quaich against Highland scenery	The enduring power of the quaich, passed through generations.	A visually poetic image symbolizing the enduring legacy and cultural power of the quaich, featuring an elegant silver quaich gently held by hands of different generations—a child’s hand alongside an older adult’s—set against a softly blurred backdrop of Scottish Highlands scenery. This serene image highlights unity, heritage, and continuity through generations.	Needs final image generation for conclusion.	{"notes": "Needs final image generation for conclusion.", "prompt": "A visually poetic image symbolizing the enduring legacy and cultural power of the quaich, featuring an elegant silver quaich gently held by hands of different generations—a child’s hand alongside an older adult’s—set against a softly blurred backdrop of Scottish Highlands scenery. This serene image highlights unity, heritage, and continuity through generations.", "status": "pending_review", "metadata": {"alt": "Hands of different generations holding a silver quaich against Highland scenery", "blog_caption": "The enduring power of the quaich, passed through generations."}, "description": "Conclusion", "syndication": {"facebook": {"status": "pending", "caption": "The quaich's journey reflects Scotland's own story. From practical cup to cherished emblem, it continues to connect generations through its simple, powerful message of unity and goodwill. #ScottishTradition #Quaich #Legacy #Friendship"}, "instagram": {"status": "pending", "caption": "Generations united by tradition. The Scottish quaich endures as a powerful symbol of friendship, hospitality, and cultural continuity. A legacy held in hand. #EnduringLegacy #ScottishHeritage #Quaich #FamilyTradition #Generations #Scotland", "hashtags": ["EnduringLegacy", "ScottishHeritage", "Quaich", "FamilyTradition", "Generations", "Scotland", "Symbol"]}}, "prompt_status": "complete", "source_details": {"local_dir": "/images/posts/quaich-traditions/", "post_slug": "quaich-traditions", "public_url": null, "filename_local": "quaich-traditions_enduring-legacy.png", "uploaded_path_relative": null}, "watermark_status": "pending", "generation_status": "pending"}	f	\N	2025-05-18 16:25:20.772085	2025-05-18 16:25:20.772087
\.


--
-- Data for Name: image_format; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.image_format (id, title, description, width, height, steps, guidance_scale, extra_settings, created_at, updated_at) FROM stdin;
2	Standard 512x512	Standard image format	512	512	20	7.5	\N	2025-07-09 10:38:21.172864	2025-07-09 10:38:21.172864
\.


--
-- Data for Name: image_prompt_example; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.image_prompt_example (id, description, style_id, format_id, provider, image_setting_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: image_setting; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.image_setting (id, name, style_id, format_id, width, height, steps, guidance_scale, extra_settings, created_at, updated_at) FROM stdin;
2	Default Setting	2	2	512	512	20	7.5	\N	2025-07-09 10:38:25.115832	2025-07-09 10:38:25.115832
\.


--
-- Data for Name: image_style; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.image_style (id, title, description, created_at, updated_at) FROM stdin;
2	Default Style	Default image generation style	2025-07-09 10:38:16.836204	2025-07-09 10:38:16.836204
\.


--
-- Data for Name: images; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.images (id, filename, original_filename, file_path, file_size, mime_type, width, height, alt_text, caption, image_prompt, notes, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_action; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_action (id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, "order", created_at, updated_at, input_field, output_field, provider_id, timeout) FROM stdin;
\.


--
-- Data for Name: llm_action_history; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_action_history (id, action_id, post_id, input_text, output_text, status, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_config (id, provider_type, model_name, api_base, is_active, created_at, updated_at) FROM stdin;
1	ollama	llama3.1:70b	http://localhost:11434	f	2025-06-22 15:56:16.610495+01	2025-06-22 15:56:16.610495+01
2	ollama	mistral	http://localhost:11434	t	2025-06-22 16:06:51.931087+01	2025-06-22 16:06:51.931087+01
\.


--
-- Data for Name: llm_format_template; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_format_template (id, name, format_type, format_spec, created_at, updated_at) FROM stdin;
1	Test Format	input	{"type":"object","properties":{"test":"value"}}	2025-06-26 11:11:02.216338	2025-06-26 11:11:02.216338
3	Test Input Format	input	{"type":"object","properties":{"test":{"type":"string","description":"Test input field"}},"required":["test"],"additionalProperties":false}	2025-06-26 11:17:58.404777	2025-06-26 11:17:58.404777
4	Test Output Format	output	{"type":"object","properties":{"result":{"type":"string","description":"Result output field"}},"required":["result"],"additionalProperties":false}	2025-06-26 11:18:03.030131	2025-06-26 11:18:03.030131
7	Test Format	input	{"type": "object", "properties": {"test": {"type": "string"}}}	2025-06-26 12:40:12.171073	2025-06-26 12:40:12.171073
9	Test Input Format	input	{"type": "object", "properties": {"test": {"type": "string"}}}	2025-06-26 12:47:12.63983	2025-06-26 12:47:12.63983
\.


--
-- Data for Name: llm_interaction; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_interaction (id, prompt_id, input_text, output_text, parameters_used, interaction_metadata, created_at) FROM stdin;
\.


--
-- Data for Name: llm_model; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_model (id, name, provider_id, description, strengths, weaknesses, api_params, created_at, updated_at) FROM stdin;
1	mistral	1	Mistral 7B (local)	Fast, low resource, good for general tasks	Not as strong as GPT-4 for reasoning	{"max_tokens": 8192}	2025-05-26 11:02:54.337827	2025-05-26 11:02:54.337827
2	gpt-3.5-turbo	2	OpenAI GPT-3.5 Turbo	Fast, cheap, good for general tasks	Not as strong as GPT-4 for reasoning	{"max_tokens": 16384}	2025-05-26 11:07:20.603016	2025-05-26 11:07:20.603016
3	gpt-4-turbo	2	OpenAI GPT-4 Turbo	Strong reasoning, broad knowledge	Slower, more expensive	{"max_tokens": 128000}	2025-05-26 11:07:20.603016	2025-05-26 11:07:20.603016
4	gpt-4o	2	OpenAI GPT-4o	Fast, multimodal, strong reasoning	New, less tested	{"max_tokens": 128000}	2025-05-26 11:07:20.603016	2025-05-26 11:07:20.603016
5	claude-3-opus-20240229	3	Anthropic Claude 3 Opus	Very strong reasoning, long context	Expensive, slower	{"max_tokens": 200000}	2025-05-26 11:07:20.604904	2025-05-26 11:07:20.604904
6	claude-3-sonnet-20240229	3	Anthropic Claude 3 Sonnet	Strong, fast, cheaper than Opus	Slightly less capable	{"max_tokens": 200000}	2025-05-26 11:07:20.604904	2025-05-26 11:07:20.604904
7	claude-3-haiku-20240307	3	Anthropic Claude 3 Haiku	Fastest, cheapest Claude	Lower reasoning ability	{"max_tokens": 200000}	2025-05-26 11:07:20.604904	2025-05-26 11:07:20.604904
8	gemini-1.5-pro	4	Google Gemini 1.5 Pro	Multimodal, long context	New, less tested	{"max_tokens": 1048576}	2025-05-26 11:07:20.605505	2025-05-26 11:07:20.605505
9	gemini-1.0-pro	4	Google Gemini 1.0 Pro	Good for general tasks	Not as strong as GPT-4	{"max_tokens": 32768}	2025-05-26 11:07:20.605505	2025-05-26 11:07:20.605505
10	llama3.1:70b	1	Llama 3.1 70B (Ollama)	Large, strong reasoning	High resource usage	{"parameter_size": "70.6B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
11	deepseek-coder:latest	1	DeepSeek Coder (Ollama)	Code generation	Small context	{"parameter_size": "1B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
12	nomic-embed-text:latest	1	Nomic Embed Text (Ollama)	Embeddings	Not a chat model	{"parameter_size": "137M"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
13	qwen2.5-coder:1.5b-base	1	Qwen2.5 Coder 1.5B Base (Ollama)	Code, small model	Lower reasoning	{"parameter_size": "1.5B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
14	llama3.1:8b	1	Llama 3.1 8B (Ollama)	Fast, low resource	Lower accuracy	{"parameter_size": "8.0B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
15	qwq:32b	1	QWQ 32B (Ollama)	Large, strong reasoning	High resource usage	{"parameter_size": "32.8B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
16	llama3.2:latest	1	Llama 3.2 (Ollama)	General tasks	Small context	{"parameter_size": "3.2B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
17	qwen2.5:1.5b	1	Qwen2.5 1.5B (Ollama)	Small, fast	Lower reasoning	{"parameter_size": "1.5B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
18	aya:35b	1	Aya 35B (Ollama)	Large, strong reasoning	High resource usage	{"parameter_size": "35.0B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
19	qwen2.5:32b	1	Qwen2.5 32B (Ollama)	Large, strong reasoning	High resource usage	{"parameter_size": "32.8B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
20	llama3:latest	1	Llama 3 (Ollama)	General tasks	Small context	{"parameter_size": "8B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
21	mistral:latest	1	Mistral 7B (Ollama)	Fast, low resource	Lower accuracy	{"parameter_size": "7B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
22	llava:latest	1	Llava (Ollama)	Multimodal	Experimental	{"parameter_size": "7B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
23	mixtral:latest	1	Mixtral (Ollama)	Large, strong reasoning	High resource usage	{"parameter_size": "47B"}	2025-05-26 11:07:20.605884	2025-05-26 11:07:20.605884
\.


--
-- Data for Name: llm_prompt; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_prompt (id, name, description, prompt_text, system_prompt, parameters, "order", created_at, updated_at, part_ids, prompt_json, step_id) FROM stdin;
82	Outline Generator	Generates detailed blog post outline	Generate a detailed blog post outline based on the expanded idea. Do not give an introduction or conclusion. Just provide a list of main sections that appropriately divide up the content into coherent topics. Provide a title; and a description of the section; and some examples of each section's ideal content emphasising both what it should include and also what it should not cover with respect to topics covered in other sections. Your entire response must be a single valid JSON array of section objects. Do not include any text before or after the JSON. Do not include any introductions, explanations, or commentary. Only output the JSON.\n\nEach section object must have this exact format:\n{\n  "title": "Section Title",\n  "description": "Detailed description of what this section should cover",\n  "contents": ["Topic 1", "Topic 2", "Topic 3"]}	\N	{"max_tokens": 2000, "temperature": 0.7}	0	2025-06-25 22:39:03.979897	2025-07-23 20:09:10.425579	[]	{"output_format": "json_array"}	23
97	Summary Generator	Generate a compelling summary for blog posts	Create a concise, engaging summary that captures the essence of the blog post. The summary should be 2-3 sentences and entice readers to continue reading.	\N	\N	100	2025-07-23 15:01:32.238711	2025-07-23 20:10:40.728256	[]	\N	51
71	Scottish CULTURE author	\N	\N	You are an expert in Scottish history, culture, and traditions. You write with precision and clarity. Use short sentences and plain words. Avoid introductions, conclusions, and flourishes. Do not generalize or editorialize. Do not use clichés, metaphors, or vague language. Focus only on verified facts. Be concise. Be direct. Stay strictly on topic.	\N	0	2025-06-25 19:32:40.672345	2025-07-15 22:15:30.007019	[]	\N	16
89	BLOGGING editor 	\N	You are a helpful assistant, expert in social media blogging and online marketing	You are a helpful assistant, expert in social media blogging and online marketing	\N	0	2025-06-30 20:44:26.499603	2025-07-01 08:32:53.909047	[]	\N	52
77	Scottish HISTORY Expert	System prompt for research facts	\N	You are an expert  researcher and author in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism. You hate cliche or bland generalities.  You are known for your very tight and fact-oriented writing style with an economy of short words and sentences.	{"max_tokens": 1000, "temperature": 0.7}	0	2025-06-25 22:39:03.979897	2025-07-07 16:46:51.424238	[]	{"role": "system"}	52
78	FACTS Generator	Generates 50 interesting facts about the topic	Explore all aspects of the topic outlined in the inputs above, and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Do NOT add introductions, conclusions, or commentary of any kind. Just give a list of facts. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50. Add no commentary or formatting first or after the list — just list 50 facts.	\N	{"max_tokens": 2000, "temperature": 0.7}	0	2025-06-25 22:39:03.979897	2025-07-23 20:08:51.869673	[]	{"output_format": "json_array"}	13
49	fifty facts in list	\N	Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism. Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50.	\N	\N	0	2025-05-31 14:57:19.511274	2025-07-23 20:10:52.936411	[]	[{"name": "Scottish cultural expert", "tags": ["Style"], "type": "system", "content": "Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism."}, {"name": "Research 50 ideas", "tags": ["Operation"], "type": "user", "content": "Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50."}]	13
92	B.20.WRITING author section content	\N	All the content above is for CONTEXT only, providing you with the overall content of the article we are writing so that you know of topics to AVOID covering while you focus your writing on the specific section of it detailed below that now follows. You are to write 150–200 words of plain prose (not a list) on the topic set by SECTION_HEADING and SECTION_DESCRIPTION below. Use only the specific ‘ideas to include’.\r\n\r\nIt is vital that you write content that can flow directly from and into other sections.  So do NOT write any introduction or conclusions. Also do not add a heading, commentary, sources, or references. Write as a paragraph that is part of the wider article, so it only deals with on-topic information for this specific section.\r\n\r\nUse UK spellings and idioms. Avoid generalisations, long words, or florid language. Stick to clear, factual, topic-bound writing.		\N	0	2025-07-03 13:21:55.389351	2025-07-17 10:57:51.116798	[]	\N	16
16	Author First Drafts	Generate detailed content for each section of the outline	You are tasked with generating detailed content for a blog post section. \n\nBased on the section heading, description, and ideas to include, create comprehensive content that:\n\n1. Expands on the main points outlined in the ideas\n2. Maintains a clear, engaging writing style\n3. Provides valuable information to readers\n4. Flows naturally from the previous section\n5. Sets up the next section appropriately\n\nSection Heading: [section_heading]\nSection Description: [section_description]\nIdeas to Include: [ideas_to_include]\n\nWrite the content in a way that is informative, engaging, and well-structured. Use clear paragraphs and appropriate transitions between ideas.		\N	3	2025-07-23 18:37:42.901325	2025-07-23 18:37:42.901325	[]	\N	16
69	EXPAND idea to basic paragraph	Task prompt for planning/idea/basic_idea	Expand the input content below into a paragraph-length brief for a long-form blog article:\r\n\r\nThe brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language. \r\n\r\nYour response should:\r\n1. Focus specifically on Scottish cultural and historical aspects\r\n2. Maintain academic accuracy while being accessible\r\n3. Suggest clear angles and themes for development\r\n4. Use UK-British spellings and idioms\r\n5. Return only the expanded brief about {{ idea_seed }}, with no additional commentary or formatting, and no title.	\N	\N	0	2025-06-25 17:20:39.200435	2025-07-23 20:03:30.558207	[]	\N	41
50	Section Creator	\N	You are an expert editorial planner for long-form articles. Your job is to design a clear, engaging, and logically structured set of sections for a new article, based on the provided title, idea, and facts.. Write for a general audience. Ensure the structure is accessible, engaging, and covers all provided themes and facts without overlap. You will be given:\n- A provisional title for broad orientation.\n- A basic idea describing the scope and themes to be explored.\n- A set of interesting facts, each of which must be included in exactly one section.\n\nYour tasks:\n1. Devise and name a coherent, engaging section structure for the article. Each section should have a title and a short description.\n2. Allocate every theme, idea, and fact to exactly one section. No item should be left unassigned or assigned to more than one section.\n3. Output a JSON object with a "sections" array. Each section must include:\n   - "name": Section title\n   - "description": Short summary of the section\n   - "themes": List of assigned themes/ideas (if any)\n   - "facts": List of assigned facts (if any)\n4. If any theme, idea, or fact cannot be assigned, include it in an "unassigned" section at the end of the array.\n\nBe robust: handle any subject matter, and ensure the output is valid JSON.	\N	\N	0	2025-06-05 08:14:33.826018	2025-07-23 20:09:31.528107	[]	[{"name": "Section Creator", "tags": ["Role"], "type": "system", "content": "You are an expert editorial planner for long-form articles. Your job is to design a clear, engaging, and logically structured set of sections for a new article, based on the provided title, idea, and facts."}, {"name": "Section Creator voice", "tags": ["Style"], "type": "system", "content": "Write for a general audience. Ensure the structure is accessible, engaging, and covers all provided themes and facts without overlap."}, {"name": "Section Creator instructions", "tags": ["Operation"], "type": "user", "content": "You will be given:\\n- A provisional title for broad orientation.\\n- A basic idea describing the scope and themes to be explored.\\n- A set of interesting facts, each of which must be included in exactly one section.\\n\\nYour tasks:\\n1. Devise and name a coherent, engaging section structure for the article. Each section should have a title and a short description.\\n2. Allocate every theme, idea, and fact to exactly one section. No item should be left unassigned or assigned to more than one section.\\n3. Output a JSON object with a \\"sections\\" array. Each section must include:\\n   - \\"name\\": Section title\\n   - \\"description\\": Short summary of the section\\n   - \\"themes\\": List of assigned themes/ideas (if any)\\n   - \\"facts\\": List of assigned facts (if any)\\n4. If any theme, idea, or fact cannot be assigned, include it in an \\"unassigned\\" section at the end of the array.\\n\\nBe robust: handle any subject matter, and ensure the output is valid JSON."}, {"name": "Section Creator format", "tags": ["Format"], "type": "user", "content": "Title: {{provisional_title}}\\nBasic Idea: {{basic_idea}}\\nInteresting Facts:\\n{{#each interesting_facts}}\\n- {{this}}\\n{{/each}}"}]	24
48	50 facts	\N	Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism. Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail.	\N	\N	0	2025-05-31 13:36:17.602638	2025-07-23 20:03:09.571629	[]	[{"name": "Scottish cultural expert", "tags": ["Style"], "type": "system", "content": "Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism."}, {"name": "Research 50 ideas", "tags": ["Operation"], "type": "user", "content": "Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail."}]	42
55	Section HEADINGS	Creates a structured outline for blog posts based on title, basic idea, and interesting facts	Review all the content in the inputs above, and consider how to structure this into a blog article with around 5-8 sections. The sections should flow logically and build upon each other to tell a complete story. Create a structured outline for a blog post with the following details:\r\n\r\nPlease provide a JSON array of sections, where each section has:\r\n- title: A clear, engaging section heading\r\n- description: The main theme or focus of this section\r\n\r\nDO NOT include any introduction or conclusions, or comment at all. ONLY title and describe the sections for the article. 	\N	{"idea": "string", "facts": "array", "title": "string"}	1	2025-06-08 09:36:05.838612	2025-07-23 20:10:04.526056	[]	\N	24
57	Scottish Idea Expansion	Expands an idea seed into a Scottish-themed brief	[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting	\N	\N	0	2025-06-09 16:16:45.779501	2025-07-23 20:09:22.693654	[]	\N	32
52	Section Creator as JSON	\N	You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them.\\n\\nReturn ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }.\\n\\nExample output:\\n{\\n  "sections": [\\n    {\\n      "name": "Introduction",\\n      "description": "Overview of the topic",\\n      "themes": ["history", "significance"],\\n      "facts": ["Fact 1", "Fact 2"]\\n    },\\n    {\\n      "name": "Historical Evolution",\\n      "description": "How the topic evolved over time",\\n      "themes": ["evolution", "design"],\\n      "facts": ["Fact 3"]\\n    }\\n  ]\\n}\\n\\nArticle Outline: {{title}}\\nTarget Audience: {{idea}}\\nInteresting Facts:\\n{{#each interesting_facts}}\\n- {{this}}\\n{{/each}}	\N	\N	0	2025-06-06 11:07:38.692983	2025-07-23 20:09:59.043179	[]	[{"name": "Section Creator", "tags": ["Role"], "type": "system", "content": "You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them."}, {"name": "Section Creator - Output JSON", "tags": ["Format"], "type": "user", "content": "Return ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }.\\n\\nExample output:\\n{\\n  \\"sections\\": [\\n    {\\n      \\"name\\": \\"Introduction\\",\\n      \\"description\\": \\"Overview of the topic\\",\\n      \\"themes\\": [\\"history\\", \\"significance\\"],\\n      \\"facts\\": [\\"Fact 1\\", \\"Fact 2\\"]\\n    },\\n    {\\n      \\"name\\": \\"Historical Evolution\\",\\n      \\"description\\": \\"How the topic evolved over time\\",\\n      \\"themes\\": [\\"evolution\\", \\"design\\"],\\n      \\"facts\\": [\\"Fact 3\\"]\\n    }\\n  ]\\n}"}]	24
88	Title/subtitle Generator	Generates alternative titles based on expanded idea	We are creating titles and subtitles for the subject matter above, for a Scottish theme blog. Generate five alternative, arresting, and informative blog (1) post titles; and (2) post subtitles. Return your response as a strict JSON array of strings using <title> and <subtitle> tabs, with no commentary or formatting — just the list of titles and subtitles.	\N	{"max_tokens": 1500, "temperature": 0.7}	0	2025-06-25 22:40:14.560717	2025-07-23 21:19:18.980617	[]	{"input_fields": ["basic_idea"], "output_format": "json_array"}	50
107	Generate INKWASH 2240x1256 image	\N	Generate an intricately detailed scene in the soft, vibrant styles of inkwash and watercolour. Use soft brushstrokes that naturally end before the edges of the canvas, blending the image as a part of the white background paper.		\N	0	2025-07-25 19:26:40.939874	2025-07-27 14:37:55.423366	[]	\N	55
98	Creative IMAGE consultant	\N		You are a Creative IMAGE consultant, an expert in visual content creation and image generation. You specialize in helping users create compelling, high-quality images that enhance their content and engage their audience. You understand various image styles, composition techniques, and can provide detailed guidance on image concepts, prompts, and visual storytelling.	\N	0	2025-07-24 08:43:14.877626	2025-07-24 08:45:17.966845	[]	\N	\N
93	IDEAS to include	\N	We are authoring a blog article which  covers the IDEA SCOPE and BASIC IDEA in the inputs above. Te full piece is organised into SECTION HEADINGS with titles and descriptions provided. Everything above is for wider context only. In this task we are expanding just ONE of the abovee headings. \r\n\r\nEach section should be very distinct from each other. For this task you are dealing ONLY with the topic of the SECTION_HEADING (note singular) and SECTION_DESCRIPTION in the inputs below. Everything below is what you must focus on, taking care not to stray into topics in other headings above.\r\n\r\nYour task is identify and list 8-10 interesting topics or ideas to include in the section described below. These topics or ideas should be of diverse kinds, mostly factual but perhaps including elements of whimsy, \r\n\r\nThis is not a writing exercise, so do not introduce or conclude or use florid prose. Just list topics or ideas in a clear and factual way with sufficient detail for later editors to expand upon.		\N	0	2025-07-07 12:03:03.740857	2025-07-24 08:53:39.07688	[]	\N	43
96	FIX language format & style	\N	Please process the input text above into a coherent section of elegant an unpretentious prose that flows all the ideas together beautifully. Remove any text from the start that sounds like an introduction or at the end like a conclusion, to focus only on the core facts. Also adhere to these specific requirements:\r\n\r\n**Processing Requirements:**\r\n1. **Simplify Language**: Remove flowery language and "fluff" - focus on tight, factual language\r\n2. **Paragraph Structure**: Break into shorter paragraphs of 2-3 sentences each, wrapped in <p> tags\r\n3. **UK British Spelling**: Convert any US spellings to UK British (e.g., color → colour)\r\n4. **Bold Key Terms**: Highlight important terms using <strong> tags for readability\r\n5. **Remove Citations**: Remove any source references in parentheses\r\n\r\n**Output Format:** HTML with proper paragraph tags and bold formatting. Please provide the processed text in clean HTML format with all changes applied.		\N	0	2025-07-09 12:33:32.170818	2025-07-24 11:48:01.041282	[]	\N	49
100	Image prompt optimiser	\N		You are a prompt-optimizer for image generation.	\N	0	2025-07-24 15:39:04.791363	2025-07-24 15:39:04.791363	[]	\N	\N
105	Test Prompt Name	\N	This is a test prompt content		\N	0	2025-07-25 19:24:57.100768	2025-07-25 19:25:10.220953	[]	\N	43
94	Image concept	\N	Your task is distill one single engaging but appropriate image based on the input BELOW to illustrate this specific section of a blog article. The image must have one single clear focussed topic. Describe its main features in depth including layout, key features, and background. Focus on content, not style.\r\n\r\nBe true to historic period, using modern settings for contemporary themes and more romantic settings for older times. AVOID romanticism, cliché or stereotypes.  Avoid multiculturalism unless specifically called for. 		\N	0	2025-07-07 17:08:08.540084	2025-07-28 06:57:46.923278	[]	\N	53
95	Image Concept -> Prompt	\N	Convert the following image concept into a concise, vivid, and fully formed image description prompt for an image generation model. The output MUST include:\r\n\r\n1. A complete and details summary of the visual scene, characters, setting, and mood described, using vivid and visual language suitable for image generation.\r\n2. Tone: aim for literal representation of a single key idea. Avoid romanticism, cliché or stereotypes, and avoid multiculturalism unless specifically called for.\r\n3. Be true to historic period, using modern settings for contemporary themes and more romantic settings for older times.\r\n\r\nOnly return the final prompt string suitable for image generation, NOT explanations. Note that image FORMAT such as style and dimensions is provided to the LLM separately so do NOT include any.  Now, here is the image description to summarise:\r\n		\N	0	2025-07-07 18:19:38.71313	2025-07-27 16:46:32.377911	[]	\N	54
\.


--
-- Data for Name: llm_prompt_part; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_prompt_part (id, type, content, tags, "order", created_at, updated_at, name, action_id, description) FROM stdin;
26	system	Test content	{context,custom}	1	2025-05-27 17:34:51.927527	2025-05-27 17:34:51.927527	Test Part	\N	\N
27	system	Test content	{context,custom}	1	2025-05-27 17:36:25.735135	2025-05-27 17:36:25.735135	UI Test Part	\N	\N
16	system	You are a naming assistant that returns exactly three creative but plausible names for each item provided.	{specimen}	1000	2025-05-26 08:34:59.747679	2025-05-27 07:55:34.216258	SPECIMEN SYSTEM	\N	\N
17	user	Here is a JSON list of items:\\n\\n{\\"animals\\": [\\"dog\\", \\"cat\\", \\"bird\\", \\"hamster\\", \\"lizard\\"]}\\n\\nPlease return a JSON object where each animal has an array of three possible names.	{specimen}	1000	2025-05-26 08:36:08.771728	2025-05-27 08:00:34.170418	SPECIMEN USER	\N	\N
21	system	Here is a JSON list of items:	{format}	50	2025-05-27 08:02:58.7468	2025-05-29 08:44:11.361664	Input JSON list	\N	\N
22	system	Here is a section of text to process:	{format}	50	2025-05-27 08:04:06.164223	2025-05-29 08:44:20.466925	Input TEXT section	\N	\N
24	system	Please return a section of text with NO commentary, annotations, or special markup.	{format}	60	2025-05-27 08:07:03.50217	2025-05-29 08:44:34.84462	Output plain TEXT	\N	\N
28	system	Use the following input content to transform as instructed: [data:FIELDNAME]	{format}	30	2025-05-27 17:43:11.814585	2025-05-29 08:45:00.469648	Use [data:FIELDNAME]	\N	\N
15	system	Return only a valid JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	{format}	80	2025-05-26 07:56:30.930082	2025-05-29 08:45:14.962256	JSON format	\N	\N
29	system	Managing Editor specialising in blog and social media creation, with an academic background in Scottish history and culture.	{role}	1	2025-05-29 08:38:49.803069	2025-05-31 10:50:03.872691	Scottish Blog basis	\N	\N
18	system	Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.	{style}	2	2025-05-26 10:20:26.867218	2025-05-31 10:50:36.179857	Scottish cultural expert	\N	\N
4	user	Traditional Scottish style	{style}	25	2025-05-25 17:32:28.03507	2025-05-31 10:51:23.730128	Scottish style	\N	\N
31	user	Write a short poem	{operation}	25	2025-05-29 14:05:06.207721	2025-05-31 10:51:32.497209	Poem	\N	\N
32	user	Write entirely in French	{style}	20	2025-05-29 14:05:25.466507	2025-05-31 10:51:51.11404	French	\N	\N
33	system	Start every response with "TITLE: NONSENSE"	{role}	20	2025-05-29 14:06:43.34658	2025-05-31 10:52:05.316238	Title Imposer	\N	\N
34	system	Expert in the services and functionality of the CLAN.com web site, which specialises in authentic Scottish heritage products and information.	{role}	3	2025-05-31 10:54:43.999355	2025-05-31 10:54:43.999355	CLAN.com UI & experience	\N	\N
19	user	Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.	{operation}	10	2025-05-26 10:27:05.283848	2025-05-31 10:55:02.915616	idea_seed expansion	\N	\N
36	user	Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50.	{operation}	20	2025-05-31 13:33:29.173341	2025-05-31 14:55:14.562695	Research 50 ideas	\N	\N
23	user	Return ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }.\n\nExample output:\n{\n  "sections": [\n    {\n      "name": "Introduction",\n      "description": "Overview of the topic",\n      "themes": ["history", "significance"],\n      "facts": ["Fact 1", "Fact 2"]\n    },\n    {\n      "name": "Historical Evolution",\n      "description": "How the topic evolved over time",\n      "themes": ["evolution", "design"],\n      "facts": ["Fact 3"]\n    }\n  ]\n}	{format}	35	2025-05-27 08:05:33.661989	2025-06-06 11:05:56.138451	Section Creator - Output JSON 	\N	\N
37	system	You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them.	{role}	30	2025-06-05 08:09:50.261501	2025-06-06 11:04:46.319143	Section Creator	\N	\N
\.


--
-- Data for Name: llm_provider; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_provider (id, name, type, api_url, auth_token, description, created_at, updated_at) FROM stdin;
2	OpenAI	openai	https://api.openai.com/v1	\N	OpenAI API for GPT-3.5, GPT-4, etc.	2025-05-26 11:06:00.780193	2025-05-26 11:06:00.780193
3	Anthropic	other	https://api.anthropic.com/v1	\N	Anthropic Claude API.	2025-05-26 11:06:01.915015	2025-05-26 11:06:01.915015
4	Gemini	other	https://generativelanguage.googleapis.com/v1beta	\N	Google Gemini API.	2025-05-26 11:06:02.450166	2025-05-26 11:06:02.450166
1	Ollama (local)	ollama	http://localhost:11434	\N	Local Ollama server for fast, private inference.	2025-05-26 10:58:23.513987	2025-05-26 10:58:23.513987
5	ollama	local	http://localhost:11434	\N	\N	2025-06-22 16:16:47.612146	2025-06-22 16:16:47.612146
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post (id, title, slug, summary, created_at, updated_at, header_image_id, status, substage_id, subtitle, title_choices) FROM stdin;
2	hand-fasting...	hand-fasting-1	\N	2025-05-04 09:47:22.571191	2025-05-04 16:15:45.445826	\N	draft	1	\N	\N
4	The Evolution of the Modern Scottish Kilt	kilt-evolution	<p>The <b>Scottish kilt</b>, a garment that has become synonymous with Highland culture and Scottish identity, has undergone significant evolution since its inception. From its origins as the <b>'great kilt'</b> or <b>'belted plaid'</b> to the modern form we recognize today, its journey reflects Scotland's rich history of tradition, adaptation, and resilience. This article explores the kilt's transformation through time, examining how historical events, practical needs, and cultural shifts have shaped this iconic symbol of Scottish heritage.</p>\n	2023-10-20 00:00:00	2025-05-18 16:25:20.775043	139	draft	1	\N	\N
5	English tartans	english-tartans	<p><strong>English tartans</strong> have a fascinating trajectory, intertwining with the better-known <strong>Scottish tartan</strong> tradition yet developing a character of their own. Although <strong>tartan</strong> is primarily identified with Scotland, England’s engagement with tartan spans from ancient use of <strong>checkered cloth</strong> by <strong>Celtic</strong> peoples to a modern revival of regional and national patterns. This comprehensive overview examines the emergence and development of tartans in England – from historical origins and regional examples to influences of the <strong>textile industry</strong>, expressions of <strong>national identity</strong>, and contemporary <strong>design movements</strong> – all while preserving every detail of the rich historical narrative.</p>	2025-04-18 00:00:00	2025-05-18 16:25:20.785179	\N	draft	1	\N	\N
6	The Tradition of the Scottish Quaich	quaich-traditions	<p>The <b>quaich</b>, Scotland's cherished <b>"cup of friendship,"</b> holds a special place in Scottish tradition, symbolising hospitality, unity, and trust. Originating centuries ago, its simple yet profound design—a shallow, two-handled bowl—embodies a rich history spanning <b>clan</b> gatherings, ceremonial rituals, royal celebrations, and contemporary <b>weddings</b>. This article explores the evolution of the quaich, delving into its earliest origins, cultural significance, craftsmanship, historical anecdotes, and enduring presence in modern Scottish culture.</p>\n	2023-10-27 00:00:00	2025-05-18 16:25:20.822509	150	draft	1	\N	\N
11	dod hatching...	dod-hatching		2025-05-21 21:59:50.069028	2025-05-21 22:58:29.225706	\N	deleted	1	\N	\N
7	cat torture...	cat-torture		2025-05-21 21:44:07.808692	2025-05-21 22:58:52.977616	\N	deleted	1	\N	\N
10	Test idea for workflow redirect...	test-idea-for-workflow-redirect		2025-05-21 21:58:45.229565	2025-05-21 23:03:36.776851	\N	deleted	1	\N	\N
12	green eggs...	green-eggs		2025-05-21 22:30:01.563795	2025-05-21 23:03:52.645833	\N	deleted	1	\N	\N
8	treacle bending...	treacle-bending		2025-05-21 21:49:33.812708	2025-05-21 23:03:57.595772	\N	deleted	1	\N	\N
9	ankle worship...	ankle-worship		2025-05-21 21:55:27.127066	2025-05-26 19:59:56.038415	\N	deleted	1	\N	\N
13	dog eating...	dog-eating		2025-05-26 20:06:27.151898	2025-05-26 20:12:45.27793	\N	deleted	\N	\N	\N
14	mangle wrangling...	mangle-wrangling		2025-05-26 20:12:36.858356	2025-05-30 17:36:15.223207	\N	deleted	\N	\N	\N
19	story-telling...	story-telling		2025-05-30 19:48:28.625876	2025-05-31 10:29:47.174463	\N	deleted	\N	\N	\N
18	mangle-wrangling...	mangle-wrangling-1		2025-05-30 17:36:54.776857	2025-05-31 10:29:51.808228	\N	deleted	\N	\N	\N
16	dog breakfasts...	dog-breakfasts		2025-05-28 21:11:19.909206	2025-05-31 10:29:55.758615	\N	deleted	\N	\N	\N
15	cream distillation...	cream-distillation		2025-05-27 15:12:33.356259	2025-05-31 10:30:04.106987	\N	deleted	\N	\N	\N
17	gin distillation...	gin-distillation		2025-05-29 18:52:00.672093	2025-05-31 10:30:08.023655	\N	deleted	\N	\N	\N
3	tartan fabrics...	tartan-fabrics		2025-05-26 19:57:47.169588	2025-05-31 10:30:12.461337	\N	deleted	\N	\N	\N
21	kilts for weddings...	kilts-for-weddings		2025-05-31 15:07:56.315652	2025-06-01 08:53:21.567802	\N	draft	\N	\N	\N
20	tartan fabrics from CLAN.com, from stock or woven ...	tartan-fabrics-from-clan-com-from-stock-or-woven		2025-05-31 10:37:23.919744	2025-06-01 10:10:35.043437	\N	deleted	\N	\N	\N
24	test2...	test2		2025-06-01 10:25:59.24337	2025-06-01 11:29:58.053887	\N	deleted	\N	\N	\N
23	test...	test		2025-06-01 10:19:43.207523	2025-06-01 11:30:01.254093	\N	deleted	\N	\N	\N
38	Test Post	test-post	\N	2025-06-25 23:14:45.372138	2025-06-25 23:30:55.134528	\N	deleted	\N	\N	\N
44	Test post for fixing issues...	test-post-for-fixing-issues		2025-07-16 17:14:44.023523	2025-07-16 17:18:35.747755	\N	deleted	\N	\N	\N
40	Test Post	test-post-1751576267	\N	2025-07-03 21:57:47.83635	2025-07-16 17:18:39.660529	\N	deleted	\N	\N	\N
46	tsfaqrqw...	tsfaqrqw		2025-07-16 17:21:21.446197	2025-07-16 17:21:34.079578	\N	deleted	\N	\N	\N
47	qwerqwr...	qwerqwr		2025-07-16 17:21:23.726493	2025-07-16 17:21:37.857642	\N	deleted	\N	\N	\N
52	adff...	adff		2025-07-16 17:24:57.197121	2025-07-16 17:25:57.199821	\N	deleted	\N	\N	\N
51	Test post redirect...	test-post-redirect		2025-07-16 17:24:14.973305	2025-07-16 17:26:00.862708	\N	deleted	\N	\N	\N
50	ewrtet...	ewrtet		2025-07-16 17:23:27.160708	2025-07-16 17:26:05.502484	\N	deleted	\N	\N	\N
49	qwer...	qwer		2025-07-16 17:21:42.946813	2025-07-16 17:26:08.4779	\N	deleted	\N	\N	\N
48	qwerewr...	qwerewr		2025-07-16 17:21:40.72552	2025-07-16 17:26:11.843127	\N	deleted	\N	\N	\N
45	wallpaper hanging...	wallpaper-hanging		2025-07-16 17:18:52.796776	2025-07-17 14:11:11.556805	\N	deleted	\N	\N	\N
22	The Power of Narrative: Scotland's Storytelling Legacy Revealed	story-telling-1		2025-06-01 10:10:53.766198	2025-07-23 16:31:43.91605	\N	deleted	\N	From folklore to contemporary art forms, explore the stories that shaped Scotland's identity.	 [\n{"title": "Whispers from the Past: Unraveling Scotland's Timeless Tales", "subtitle": "Journey through Scotland's ancient storytelling traditions and their enduring impact."},\n{"title": "The Power of Narrative: Scotland's Storytelling Legacy Revealed", "subtitle": "From folklore to contemporary art forms, explore the stories that shaped Scotland's identity."},\n{"title": "Beyond Legends: A Fresh Look at Scottish Storytelling's Evolution", "subtitle": "Discover how Scotland's storytelling has transformed from oral tradition to modern-day expressions."},\n{"title": "Tales of Transformation: Mythology, Folklore, and the Art of Storytelling in Scotland", "subtitle": "Uncover the connections between Scottish mythology, folklore, and the art of storytelling."},\n{"title": "Narrative Threads: Tracing the Influence of Storytelling on Scottish Culture", "subtitle": "Follow the story of Scotland's rich cultural heritage through its captivating tales and traditions."}\n]
1	test	hand-fasting	\N	2025-05-03 16:05:45.941465	2025-07-27 09:37:41.526542	\N	deleted	1	\N	\N
53	The Art of Scottish Storytelling: Oral Traditions and Modern Literature	story-telling-2		2025-07-17 14:11:27.027049	2025-07-29 15:45:33.766016	\N	draft	\N	Discover the captivating tales that have shaped Scotland's unique cultural heritage	 [\n{"title": "The Enchanted Quill: Unraveling Scotland's Magical Story-telling Traditions", "subtitle": "Explore the rich tapestry of Scottish story-telling, from ancient Celtic mythology to modern literary masterpieces."},\n{"title": "From Oral Tradition to Printed Page: The Evolution of Scottish Story-telling", "subtitle": "Trace Scotland's narrative history, from oral folktales and ballads to the works of celebrated authors."},\n{"title": "Mystical Tales and Heroes: A Journey through Scotland's Fascinating Folklore", "subtitle": "Discover the legendary heroes and mythical creatures that inhabit Scotland's story-telling heritage."},\n{"title": "The Power of Story: Preserving Scottish Culture Through Narrative Art", "subtitle": "Explore how story-telling has served as a vital tool for preserving Scotland's cultural traditions and identity."},\n{"title": "Whispers of the Past: The Timeless Allure of Scottish Story-telling", "subtitle": "Step into the world of ancient Celtic tales, medieval ballads, and modern literary gems that continue to captivate readers around the globe."}\n]
\.


--
-- Data for Name: post_categories; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_categories (post_id, category_id) FROM stdin;
\.


--
-- Data for Name: post_development; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_development (id, post_id, basic_idea, provisional_title, idea_scope, topics_to_cover, interesting_facts, tartans_products, section_planning, section_headings, section_order, main_title, subtitle, intro_blurb, conclusion, basic_metadata, tags, categories, image_captions, seo_optimization, self_review, peer_review, final_check, scheduling, deployment, verification, feedback_collection, content_updates, version_control, platform_selection, content_adaptation, distribution, engagement_tracking, summary, idea_seed, provisional_title_primary, concepts, facts, outline, allocated_facts, sections, title_order, expanded_idea, updated_at) FROM stdin;
3	7	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
4	8	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
5	9	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
6	11	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
7	12	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
10	17	TITLE: NONSENSE\n\nDans les alambics de la folie,\nOù la vapeur danse et s'envole,\nLa distillation du gin se déroule,\nUn rituel ancien, une magie qui évolue.\n\nLes baies de genièvre, parfumées et fines,\nSont ajoutées au mélange, un secret divin,\nLe feu crépite, la chaleur monte en spirale,\nEt l'alcool pur se dégage, comme un esprit qui s'envole.\n\nDans les verres froids, le gin sera versé,\nUn breuvage qui réchauffe et fait oublier,\nLes soucis du jour, les nuits sans sommeil,\nTout est oublié, dans ce liquide cristal.	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	gin distillation	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
16	23	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	test	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
9	16	Here's a brief for a long-form blog article based on the idea of "dog breakfasts":\n\n**Title:** "The Unlikely Origins of 'Dog Breakfast': How Scotland's Gastronomic History Shaped a Curious Culinary Tradition"\n\n**Scope and Angle:** This article will delve into the fascinating history behind the Scottish tradition of serving "dog breakfasts" - a hearty, if unconventional, meal typically consisting of leftover food scraps, served to working-class people, particularly in rural areas. While this practice may seem unappetizing or even bizarre to modern readers, our exploration will reveal its roots in Scotland's rich cultural heritage and the country's historical struggles with poverty, food scarcity, and social inequality.\n\n**Tone:** Our tone will be engaging, informative, and respectful, acknowledging the complexities of Scotland's past while avoiding sensationalism or judgment. We'll strive to convey a sense of empathy and understanding for those who relied on dog breakfasts as a means of sustenance, highlighting the resourcefulness and resilience that defined these communities.\n\n**Core Ideas:**\n\n* Explore the etymology of "dog breakfast" and its possible connections to Scottish Gaelic phrases and customs\n* Discuss the historical context in which dog breakfasts emerged, including Scotland's agricultural economy, poverty rates, and limited access to nutritious food\n* Examine the social dynamics surrounding dog breakfasts, including their role in rural communities, workhouses, and other institutions\n* Highlight notable examples of dog breakfasts in Scottish literature, folklore, or oral traditions\n* Reflect on the legacy of dog breakfasts in modern Scotland, considering how this tradition has influenced contemporary attitudes towards food waste, sustainability, and social welfare\n\n**Authenticity and Accuracy:** As a specialist in Scottish history and culture, we'll prioritize academic rigor and attention to detail, ensuring that all claims are supported by credible sources and historical records. By doing so, we'll create an engaging narrative that not only entertains but also educates readers about this lesser-known aspect of Scotland's cultural heritage.	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	dog breakfasts	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
31	5	\N	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Test idea	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-03 20:31:18.088556
32	38		\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Test idea seed	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-03 20:31:18.088556
13	20	I apologize but as your request is not clear enough about what kind of information you want to receive or which aspect(es) from CLAN website services should be included.  Based on the brief provided and considering it doesn’t specify how much detail we need, here's a general guideline based upon data I have above:\n\n**Title - "The Tartan Truth": Unraveling The Myths And Histories Of Scotland's Iconic Fabric" – an informative post on authentic Scottish heritage products and information. This brief outlines the scope, angle (engaging with inquisitive readers), tone(enthusiastic but not overbearing about history or mythology) , core ideas that could be developed into a full article:**\n\n1- **Scope - A comprehensive exploration of tartan fabrics and their histories. Including information on the origin, evolution in time (ancient to modern), common mythologies associated with them(s). Exploring specific design details for different fabric designs from history back to present times when they were made**\n2- **Angle - An engaging approach using academic rigour but still inviting readers. Drawing insights and facts along the way, making sense of tartan stories in detail while maintaining a conversational tone that is easy on the eyes (like walking through an intricate mosaic) – to make this article more than just reading**\n3- **Tone - A friendly yet knowledgeable approach with focus solely around authenticity and significance. Encouraging curiosity about history, culture & fabric while still challenging myths or misconceptions by presenting them in a meaningful way (with examples of clans exclusive patterns) – to make sure readers are not just watching but also experiencing the journey**\n4- **Brief - Suitable for an informative article aimed at encouraging curiosity about history, culture & fabric and its impact on tartan designs. It provides depth into each aspect while keeping it engaging with a conversational tone ensuring reader interaction is both enjoyable (viewing them in new ways) and enticing**\n	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Here is the expanded brief:\n\n**Title:** "The Tartan Truth: Unraveling the Myths and Histories of Scotland's Iconic Fabric"\n\n**Brief:** This article will delve into the fascinating world of tartan fabrics, separating fact from fiction and exploring the rich cultural heritage behind these iconic patterns. Using data from CLAN.com, a reputable source for authentic tartan fabrics, we'll examine the history of tartan in Scotland, from its ancient origins to its modern-day uses. We'll also debunk common myths surrounding tartans, such as the notion that specific patterns are exclusive to certain clans or families. With a focus on accuracy and authenticity, this article will appeal to both history buffs and those with a passing interest in Scottish culture. By exploring the stories behind different tartan designs, we'll reveal the intricate connections between Scotland's past, its people, and their textiles.\n\n**Scope:** This long-form blog post will cover:\n\n* A brief history of tartan in Scotland, including its ancient Celtic roots and evolution over time\n* An examination of common myths and misconceptions surrounding tartans\n* In-depth looks at specific tartan designs, their origins, and associated stories\n* The significance of tartan in Scottish culture, both historically and today\n\n**Angle:** Our approach will be informative yet engaging, blending academic rigor with a conversational tone that invites readers to explore the world of tartans. We'll draw on credible sources, including historical records and expert insights from textile historians.\n\n**Tone:** Friendly, knowledgeable, and enthusiastic – we aim to inspire curiosity about Scottish history and culture while dispelling myths and misconceptions. Our goal is to create a sense of wonder and appreciation for the intricate stories woven into every tartan fabric.\n\nThis brief should provide a solid foundation for crafting an engaging and informative article that explores the captivating world of tartans, revealing their significance in Scotland's rich cultural heritage.	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
8	15	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:\n\n**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"\n\n**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.\n\n**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.\n\n**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.\n\n**Core ideas:**\n\n* Introduce the basics of cream distillation and its role in Scottish whisky production\n* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations\n* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie\n* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers\n* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production\n\n**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	\N	\N	\N	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:\n\n**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"\n\n**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.\n\n**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.\n\n**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.\n\n**Core ideas:**\n\n* Introduce the basics of cream distillation and its role in Scottish whisky production\n* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations\n* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie\n* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers\n* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production\n\n**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	cream distillation	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
2	2	This is a test response for format validation	Tying the Knot: Unraveling Scotland's Ancient Tradition of Hand-Fasting	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Explain the difference between hand-fasting and marriage",\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Analyze the social impact of hand-fasting on women's lives in Scotland's past",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans",\n  "Describe the role of the 'hand-fastening' ritual in Scottish wedding ceremonies",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings",\n  "Discuss the romanticization of hand-fasting in Scottish literature and art",\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Examine the cultural exchange between Scottish and Norse cultures regarding hand-fasting",\n  "Investigate the connection between hand-fasting and Scotland's ancient laws",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Describe the role of the 'priest' or 'officiant' in a traditional hand-fasting ceremony",\n  "Explore the regional variations of hand-fasting practices across Scotland",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Look at how hand-fasting has been used as a symbol of Scottish national identity",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Examine the influence of hand-fasting on modern wedding traditions worldwide",\n  "Investigate the connection between hand-fasting and Scotland's ancient festivals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Discuss the role of family and community in traditional hand-fasting ceremonies",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the historical context of hand-fasting during Scotland's clan wars",\n  "Look at how hand-fasting has been used as a symbol of loyalty and commitment",\n  "Examine the modern relevance of hand-fasting in contemporary relationships",\n  "Discuss the connection between hand-fasting and Scotland's ancient mythology",\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Analyze the cultural significance of hand-fasting in Scotland's Lowland culture",\n  "Describe the historical context of hand-fasting during Scotland's Enlightenment period",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities",\n  "Discuss the symbolism behind the use of specific materials or objects in hand-fasting rituals",\n  "Look at how hand-fasting has been used as a symbol of resistance against oppressive regimes"\n]	\N	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	\N	\N	[]	["Unraveling the Ancient Celtic Roots of Hand-Fasting","The Evolution of Hand-Fasting in Scotland's Historical Landscape","Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting","Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements","A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions","Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies","Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology","Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Write about the history and significance of Scottish kilts	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
14	21	[\n  "Tartan Traditions: A Guide to Wearing Kilts at Scottish Weddings",\n  "Kilted and Married: The History and Significance of Tartan in Scottish Wedding Attire",\n  "The Ultimate Kilt Guide for Grooms: How to Wear Your Heritage with Pride on the Big Day",\n  "Plaid Promises: Uncovering the Cultural Significance of Kilts at Scottish Weddings",\n  "Tying the Knot in Tartan: A Journey Through Scotland's Rich History of Wedding Kilts"\n]	\N	\N	\N	Here are 50 interesting facts about kilts at Scottish weddings:\n\n1. **Tartan origins**: The word "tartan" comes from the French word "tartane," meaning a type of woolen cloth.\n2. **Ancient roots**: The earliest known evidence of tartan patterns dates back to the 3rd century AD, in ancient Celtic art.\n3. **Clans and kinship**: In Scotland, tartan was used to identify specific clans or families, with each having its own unique pattern.\n4. **Wedding tradition**: Kilts have been a part of Scottish wedding attire for centuries, symbolizing family heritage and cultural identity.\n5. **Black Watch**: The Black Watch tartan is one of the most recognizable patterns, originally worn by the 42nd Royal Highland Regiment.\n6. **Regional associations**: Different regions in Scotland have their own unique tartans, such as the Gordon tartan from Aberdeenshire.\n7. **Sporran significance**: A sporran (a pouch worn at the waist) is a traditional part of kilt attire, used to carry personal items and symbolizing prosperity.\n8. **Kilt-making skills**: Traditional kilt-making requires great skill and attention to detail, with each kilt taking around 30-40 hours to complete.\n9. **Woolen heritage**: Kilts are typically made from wool, a nod to Scotland's rich sheep-farming history.\n10. **Tartan registers**: In the 18th century, tartans were formally registered and standardized to prevent imitation and ensure authenticity.\n11. **Kilted heroes**: Famous Scots like Robert Burns and Sir Walter Scott often wore kilts as a symbol of national pride.\n12. **Wedding attire**: Traditionally, the groom's kilt is matched with a sash or plaid (a long piece of fabric) in the same tartan.\n13. **Scottish regiments**: Many Scottish military regiments have their own unique kilts and tartans, such as the Royal Scots Dragoon Guards.\n14. **Cultural revival**: The 19th-century Highland Revival saw a resurgence in interest in traditional Scottish culture, including kilts and tartans.\n15. **Fashion influence**: Kilts have influenced fashion worldwide, with designers incorporating tartan patterns into their collections.\n16. **Wedding party attire**: In traditional Scottish weddings, the entire wedding party (including bridesmaids) may wear matching tartans or kilts.\n17. **Kilt accessories**: Sgian dubh (a small knife), dirks (long knives), and sporrans are common kilt accessories with cultural significance.\n18. **Ancient Celtic art**: Early Celtic art features intricate patterns similar to modern tartan designs.\n19. **Tartan textiles**: Kilts are often made from woven woolen fabric, which can be heavy and warm.\n20. **Kilted athletes**: Scottish athletes have worn kilts as part of their national team uniforms in various sports, including football and rugby.\n21. **Bagpipes and kilts**: The iconic combination of bagpipes and kilts is a staple of Scottish culture and wedding celebrations.\n22. **Wedding ceremony significance**: In traditional Scottish weddings, the kilt is often worn during the ceremony to symbolize family heritage.\n23. **Hand-fasting**: In ancient Celtic tradition, couples were "hand-fast" (married) while wearing matching tartans or kilts.\n24. **Tartan etiquette**: Specific rules govern the wearing of tartans and kilts, including which side to wear a sash or plaid.\n25. **Royal connections**: The British royal family has long been associated with Scottish culture, often wearing kilts on formal occasions.\n26. **Wedding attire evolution**: Modern kilt designs for weddings may incorporate new colors or patterns while maintaining traditional elements.\n27. **Kilt-making techniques**: Traditional kilt-making involves intricate pleating and folding to create the distinctive tartan pattern.\n28. **Historical kilts**: Kilts have been worn in Scotland since at least the 16th century, with early examples featuring more subdued colors.\n29. **Tartan symbolism**: Specific tartans are associated with different values or attributes, such as bravery (Black Watch) or loyalty (Gordon).\n30. **Wedding party kilts**: In some traditional weddings, the entire wedding party wears matching kilts in the same tartan.\n31. **Scottish heritage**: Kilts and tartans serve as a connection to Scotland's rich cultural heritage and history.\n32. **Modern twists**: Contemporary kilt designs may incorporate bold colors or modern patterns while maintaining traditional elements.\n33. **Cultural exchange**: Tartans have been adopted by cultures worldwide, including African and Asian communities.\n34. **Wedding fashion influence**: Kilts have influenced wedding attire globally, with many designers incorporating tartan patterns into their collections.\n35. **Famous kilted figures**: Sir Sean Connery and Billy Connolly are just two famous Scots who often wear kilts on formal occasions.\n36. **Kilted folklore**: In Scottish mythology, kilts were said to have magical properties, offering protection and strength to the wearer.\n37. **Wedding attire for all**: Modern kilt designs cater to a range of styles and preferences, including women's kilts and bespoke designs.\n38. **Tartan in art**: Tartans have been featured in various art forms, from textiles to music and literature.\n39. **Cultural significance**: Kilts serve as an important cultural symbol, representing Scottish heritage and national identity.\n40. **Kilt accessories**: Sashes, sporrans, and sgian dubh are all essential kilt accessories with historical and cultural significance.\n41. **Wedding attire evolution**: Modern kilt designs often blend traditional elements with modern styles and materials.\n42. **Royal tartans**: The British royal family has its own unique tartans, which are reserved for specific occasions.\n43. **Tartan registers**: In the 19th century, tartans were formally registered to standardize patterns and prevent imitation.\n44. **Kilt-making apprenticeships**: Traditional kilt-making skills are passed down through generations via formal apprenticeships.\n45. **Wedding party attire**: In some traditional Scottish weddings, the bride's dress may incorporate matching tartan elements or a sash.\n46. **Famous kilts in literature**: Kilts have been featured prominently in literary works like Sir Walter Scott's novels.\n47. **Tartan textiles**: Modern textile technology has made it possible to create intricate and accurate tartan patterns on various fabrics.\n48. **Kilted music festivals**: Scottish music festivals often feature kilted performers, showcasing traditional culture.\n49. **Cultural traditions**: Kilts are an integral part of Scottish cultural heritage, reflecting the country's rich history and identity.\n50. **Global recognition**: The image of a Scotsman in a kilt is instantly recognizable worldwide, symbolizing Scottish culture and national pride.\n\nThese 50 facts cover a range of topics, from the origins of tartan to modern interpretations of kilts at weddings, while highlighting the cultural significance and symbolism behind this iconic attire.	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	kilts for weddings	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
1	1	This is a test response for format validation	This is a test response for format validation	\N	\N	\N	\N	\N	[{"order": 1, "heading": "The Ancient Kingdoms of Scotland", "description": "A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.", "status": "draft"}, {"order": 2, "heading": "Medieval Scotland: Kingdoms and Feudalism", "description": "An exploration of Scotland's medieval kingdoms, nobility, and feudal system.", "status": "draft"}, {"order": 3, "heading": "The Wars of Scottish Independence", "description": "A detailed account of Scotland's struggles for independence from England, including key battles and figures.", "status": "draft"}, {"order": 4, "heading": "Tartanry and Highland Culture", "description": "An examination of Scotland's iconic tartans, clans, and traditional Highland culture.", "status": "draft"}, {"order": 5, "heading": "Scotland's Contribution to the British Empire", "description": "An exploration of Scotland's role in shaping the British Empire, including key figures and events.", "status": "draft"}, {"order": 6, "heading": "Modern Scotland: Industrialization, Nationalism, and Devolution", "description": "A discussion of Scotland's modern history, including key economic, cultural, and political developments.", "status": "draft"}, {"order": 7, "heading": "Scottish Culture and Identity Today", "description": "An examination of contemporary Scottish culture, including literature, music, art, and festivals.", "status": "draft"}]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Test value	\N	\N	\N	[\n  {\n    "title": "The Ancient Kingdoms of Scotland",\n    "description": "A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.",\n    "contents": [\n      "Pictish culture and society",\n      "The rise of the Dál Riata dynasty",\n      "Viking invasions and their impact on Scotland"\n    ]\n  },\n  {\n    "title": "Medieval Scotland: Kingdoms and Feudalism",\n    "description": "An exploration of Scotland's medieval kingdoms, nobility, and feudal system.",\n    "contents": [\n      "The Kingdom of Alba and the development of Scottish identity",\n      "Feudal relationships between Scottish lords and the monarch",\n      "The role of the Church in medieval Scottish society"\n    ]\n  },\n  {\n    "title": "The Wars of Scottish Independence",\n    "description": "A detailed account of Scotland's struggles for independence from England, including key battles and figures.",\n    "contents": [\n      "The First War of Scottish Independence (1296-1357)",\n      "Robert the Bruce: his life, campaigns, and legacy",\n      "Key battles: Stirling Bridge, Falkirk, Bannockburn"\n    ]\n  },\n  {\n    "title": "Tartanry and Highland Culture",\n    "description": "An examination of Scotland's iconic tartans, clans, and traditional Highland culture.",\n    "contents": [\n      "Origins and meaning of Scottish tartans",\n      "The significance of clan structure and kinship in Highland society",\n      "Traditional Highland music, dance, and art"\n    ]\n  },\n  {\n    "title": "Scotland's Contribution to the British Empire",\n    "description": "An exploration of Scotland's role in shaping the British Empire, including key figures and events.",\n    "contents": [\n      "The 'Darien Scheme' and its impact on Scottish politics",\n      "Scottish explorers: James Bruce and Mungo Park",\n      "Scotland's military contributions to the Napoleonic Wars"\n    ]\n  },\n  {\n    "title": "Modern Scotland: Industrialization, Nationalism, and Devolution",\n    "description": "A discussion of Scotland's modern history, including key economic, cultural, and political developments.",\n    "contents": [\n      "Industrialization and urbanization in Scotland",\n      "The rise of Scottish nationalism and the SNP",\n      "Devolution and the Scottish Parliament"\n    ]\n  },\n  {\n    "title": "Scottish Culture and Identity Today",\n    "description": "An examination of contemporary Scottish culture, including literature, music, art, and festivals.",\n    "contents": [\n      "Modern Scottish literature: authors and themes",\n      "The role of traditional music in modern Scotland",\n      "Celebrations: Hogmanay, Burns Night, Celtic Connections"\n    ]\n  }\n]	\N	Here is the detailed content for each section of the outline, maintaining a consistent style and tone throughout:\n\n```json\n{\n  "The Ancient Kingdoms of Scotland": {\n    "description": "A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.",\n    "contents": [\n      {\n        "title": "Pictish culture and society",\n        "text": "The Picts were a group of people who lived in Scotland during the Late Iron Age and Early Medieval periods. Their name is derived from the Latin word 'picti,' meaning 'painted people.' This refers to their practice of body painting, which was a common custom among many ancient cultures. The Picts left behind a rich legacy of art, including intricate stone carvings and metalwork. Despite their impressive artistic achievements, the Picts left no written records, making it difficult for historians to reconstruct their society with certainty. Nevertheless, archaeological evidence suggests that they were organized into smaller groups or 'nations,' each with its own distinct culture and traditions."\n      },\n      {\n        "title": "The rise of the Dál Riata dynasty",\n        "text": "As the Roman Empire declined, Scotland was invaded by various groups from Ireland. One such group, the Dál Riata, eventually established a powerful dynasty that would shape Scotland's early history. The Dál Riata were skilled warriors and traders who built a strong kingdom in western Scotland. They also developed a system of writing, using an adaptation of the Ogham alphabet to record their language and history. Under the Dál Riata, Scotland began to take on a more distinct identity, with its own culture, laws, and institutions."\n      },\n      {\n        "title": "Viking invasions and their impact on Scotland",\n        "text": "In the late 8th century, Viking raiders from Scandinavia invaded Scotland, bringing destruction and chaos in their wake. The Vikings were skilled warriors who quickly established themselves as a dominant force in Scottish politics. They often fought alongside native Scots against other rival groups, but they also brought their own culture, language, and customs to the region. Despite the disruption caused by the Viking invasions, Scotland's ancient kingdoms would eventually emerge stronger than ever, shaped by the complex interactions between the Picts, Scots, and Vikings."\n    ]\n  },\n  "Medieval Scotland: Kingdoms and Feudalism": {\n    "description": "An exploration of Scotland's medieval kingdoms, nobility, and feudal system.",\n    "contents": [\n      {\n        "title": "The Kingdom of Alba and the development of Scottish identity",\n        "text": "As the Dál Riata dynasty declined, a new kingdom emerged in eastern Scotland: the Kingdom of Alba. The name 'Alba' means 'dawn' or 'white,' reflecting the kingdom's association with light and hope. Under the Kingdom of Alba, Scotland began to take on a more unified identity, with its own monarch, laws, and institutions. This period saw the rise of Scottish nationalism, as Scots sought to assert their independence from neighboring kingdoms."\n      },\n      {\n        "title": "Feudal relationships between Scottish lords and the monarch",\n        "text": "In medieval Scotland, society was organized around a complex system of feudal relationships. Lords owed allegiance to the monarch, who in turn protected them and their lands. In exchange for protection, lords were expected to provide military service, tribute, or other forms of support. This system allowed the Kingdom of Alba to expand its borders through strategic alliances and military campaigns. However, it also created tensions between lords and the monarch, as they jockeyed for power and influence."\n      },\n      {\n        "title": "The role of the Church in medieval Scottish society",\n        "text": "The Christian Church played a central role in medieval Scottish society, providing education, healthcare, and spiritual guidance to the population. The Church also served as a unifying force, binding together disparate groups within Scotland's complex feudal system. Monasteries and abbeys became centers of learning and culture, where monks and scholars preserved ancient knowledge and developed new artistic and literary traditions."\n    ]\n  },\n  "The Wars of Scottish Independence": {\n    "description": "A detailed account of Scotland's struggles for independence from England, including key battles and figures.",\n    "contents": [\n      {\n        "title": "The First War of Scottish Independence (1296-1357)",\n        "text": "In the late 13th century, Edward I of England invaded Scotland, sparking a decades-long conflict that would shape Scotland's history. The war saw numerous battles, including Stirling Bridge and Falkirk, where Scottish forces emerged victorious but ultimately succumbed to English pressure. This period also saw the emergence of key figures like William Wallace and Robert the Bruce, who would become iconic heroes in Scotland's struggle for independence."\n      },\n      {\n        "title": "Robert the Bruce: his life, campaigns, and legacy",\n        "text": "Robert the Bruce was a Scottish nobleman who rose to prominence during the Wars of Scottish Independence. He initially supported English rule but later turned against them, leading the charge at Bannockburn in 1314. This decisive victory marked a turning point in Scotland's struggle for independence, as the country began to assert its sovereignty over England. Bruce's legacy endures to this day, symbolizing Scotland's enduring spirit of resistance and self-determination."\n      },\n      {\n        "title": "Key battles: Stirling Bridge, Falkirk, Bannockburn",\n        "text": "The Wars of Scottish Independence saw numerous pivotal battles, each with its own unique significance. Stirling Bridge was a crucial early victory for the Scots, showcasing their military prowess and strategic thinking. Falkirk marked a turning point in English fortunes, as they regained momentum after initial setbacks. Bannockburn, however, remains Scotland's most iconic battle, where Robert the Bruce led his forces to an historic triumph over the English."\n    ]\n  },\n  "Tartanry and Highland Culture": {\n    "description": "An examination of Scotland's iconic tartans, clans, and traditional Highland culture.",\n    "contents": [\n      {\n        "title": "Origins and meaning of Scottish tartans",\n        "text": "Scottish tartans have a rich history, dating back to the Middle Ages. Originally, these intricate patterns served as markers of clan identity and status. Each tartan was associated with specific regions or families, reflecting their unique cultural heritage. Over time, the significance of tartans has evolved, serving as symbols of national pride and community spirit."\n      },\n      {\n        "title": "The significance of clan structure and kinship in Highland society",\n        "text": "In traditional Highland culture, clans played a central role in defining identity and social hierarchy. Clans were organized around shared ancestry, with each family tracing their lineage back to a common ancestor. This system fostered strong bonds between family members and reinforced the importance of loyalty, honor, and hospitality."\n      },\n      {\n        "title": "Traditional Highland music, dance, and art",\n        "text": "Highland culture is renowned for its rich musical heritage, with traditional instruments like the bagpipes and fiddle dominating Scotland's folk scene. Traditional dances like the ceilidh and Highland fling are still celebrated today, reflecting the country's deep connection to its cultural roots. Scottish art also boasts a stunning array of textiles, metalwork, and other crafts that showcase the region's artistic prowess."\n    ]\n  },\n  "Scotland's Contribution to the British Empire": {\n    "description": "An exploration of Scotland's role in shaping the British Empire, including key figures and events.",\n    "contents": [\n      {\n        "title": "The 'Darien Scheme' and its impact on Scottish politics",\n        "text": "In the early 18th century, Scotland proposed a bold venture to establish a colony in Panama, known as the Darien Scheme. Although the plan ultimately failed, it reflected Scotland's growing ambitions within the British Empire. The failure of the Darien Scheme led to a period of economic hardship and social unrest in Scotland, prompting calls for greater autonomy or even independence from England."\n      },\n      {\n        "title": "Scottish explorers: James Bruce and Mungo Park",\n        "text": "Scotland has produced many notable explorers who contributed significantly to the British Empire's expansion. James Bruce was a renowned geographer and explorer who traveled extensively in Africa, discovering several major rivers. Mungo Park, another prominent Scottish explorer, ventured into West Africa, mapping new territories and encountering diverse cultures."\n      },\n      {\n        "title": "Scotland's military contributions to the Napoleonic Wars",\n        "text": "During the Napoleonic Wars, Scotland played a significant role in British military campaigns. Many Scots served as soldiers or officers in key battles, contributing to crucial victories like Waterloo. This period also saw the rise of Scottish nationalism, as Scots sought greater recognition and influence within the British Empire."\n    ]\n  },\n  "Modern Scotland: Industrialization, Nationalism, and Devolution": {\n    "description": "A discussion of Scotland's modern history, including key economic, cultural, and political developments.",\n    "contents": [\n      {\n        "title": "Industrialization and urbanization in Scotland",\n        "text": "In the 19th century, Scotland underwent rapid industrialization, driven by coal mining, steel production, and textile manufacturing. This led to significant urban growth, as people flocked to cities like Glasgow and Edinburgh for work and opportunities. However, this period also saw the rise of social inequalities and poverty in Scotland."\n      },\n      {\n        "title": "The rise of Scottish nationalism and the SNP",\n        "text": "In the 20th century, Scottish nationalism experienced a resurgence, driven by calls for greater autonomy or independence from England. The Scottish National Party (SNP) emerged as a major force, advocating for devolution and self-governance. This movement has continued to grow in influence, shaping Scotland's politics and identity."\n      },\n      {\n        "title": "Devolution and the Scottish Parliament",\n        "text": "In 1999, Scotland gained its own parliament through the Devolution Act, marking a significant shift in the country's governance. The Scottish Parliament is responsible for making laws on various domestic issues, including healthcare, education, and justice. This has led to increased autonomy for Scotland within the UK, allowing the country to develop its unique policies and priorities."\n    ]\n  },\n  "Scottish Culture and Identity Today": {\n    "description": "An examination of contemporary Scottish culture, including literature, music, art, and festivals.",\n    "contents": [\n      {\n        "title": "Modern Scottish literature: authors and themes",\n        "text": "Scotland has produced a thriving literary scene in recent decades, with writers like Irvine Welsh, James Kelman, and Janice Galloway achieving international recognition. Themes of identity, social justice, and national pride dominate contemporary Scottish literature, reflecting the country's evolving cultural landscape."\n      },\n      {\n        "title": "The role of traditional music in modern Scotland",\n        "text": "Traditional Scottish music continues to play a vital role in shaping the country's culture and identity. From bagpipe bands to ceilidh sessions, music remains an integral part of Scottish heritage, with many festivals celebrating its rich tradition."\n      },\n      {\n        "title": "Celebrations: Hogmanay, Burns Night, Celtic Connections",\n        "text": "Scotland's calendar is filled with vibrant cultural celebrations, each reflecting the country's unique history and traditions. Hogmanay marks the start of a new year, while Burns Night honors Scotland's beloved poet Robert Burns. Celtic Connections is a major festival showcasing traditional music from across the world."\n    ]\n  }\n}\n```	[]	This is a test expanded idea	2025-07-22 12:56:17.125162
15	22	In this article, we'll embark on a journey through the rich landscape of Scottish storytelling, exploring its evolution from ancient Celtic roots to modern-day creative expressions. We'll examine how stories have been used to pass down historical events, cultural values, and social norms, as well as to entertain, educate, and even subvert. By tracing the threads of oral tradition, literary heritage, and contemporary practices, we'll reveal the ways in which storytelling continues to shape Scotland's sense of self and its place in the world. From the 14th-century makars who crafted verse for royal courts to the modern-day novelists who draw inspiration from Scotland's rugged landscapes and complex history, we'll delve into the key themes and motifs that have defined Scottish storytelling across the centuries. We'll also investigate the connections between storytelling and folklore, mythology, and music, highlighting the ways in which these art forms have intersected and influenced one another. Throughout, our tone will be engaging and accessible, balancing academic rigour with a passion for storytelling itself. By exploring the many facets of Scottish storytelling, we aim to provide readers with a deeper understanding of this vital aspect of Scotland's cultural heritage, as well as its ongoing relevance in shaping the nation's identity today.	[\n  "Weaving the Tartan Tapestry: The Enduring Power of Storytelling in Scottish Culture",\n  "The Highland Hearth: How Scotland's Rich Storytelling Heritage Keeps Embers of Memory Alive",\n  "Kilts, Clans, and Chronicles: Unravelling the Cultural Significance of Scottish Storytelling",\n  "From Caledonia to the World: The Global Impact of Scotland's Compelling Narrative Tradition",\n  "Thistle and Thematics: Exploring the Emotional Resonance of Storytelling in Scottish Identity"\n]	 {\n"title": "Weaving Tales: The Rich Tradition of Storytelling in Scottish Culture",\n"intro": "Delve into the captivating world of Scottish storytelling, an age-old art form that continues to enthrall and inspire. From myths and legends passed down through generations, to contemporary narratives that reflect our modern society, stories hold a unique place in Scotland's rich cultural heritage.\\n\\n",\n"scope": "This article explores the various aspects of Scottish storytelling, both historical and contemporary. It examines the significance of traditional tales and their roots in Scottish folklore, as well as how these narratives have evolved over time.\\n\\n",\n"angle": "Through a blend of academic research and engaging narrative, we'll delve into the mythology surrounding iconic figures like William Tell (or Tam Lin), the Selkies, and the infamous Macbeth. We'll also explore how these stories have been adapted for modern audiences – from literature and theatre to film and beyond.\\n\\n",\n"themes": ["Folklore and Mythology", "Scottish History", "Literature and Arts"],\n"conclusion": "Join us on a journey through the enchanting world of Scottish storytelling, as we uncover the fascinating tales that have shaped our past and continue to inspire our future."\n}	[\n  {\n    "title": "The Significance of Oral Tradition in Preserving Scottish Cultural Heritage",\n    "description": "Exploring how Scotland's rich storytelling heritage has been passed down through generations via oral retellings."\n  },\n  {\n    "title": "Tales from the Trossachs: Examining the Role of Nature in Scottish Folklore",\n    "description": "Investigating how the natural world has influenced Scottish stories and legends, such as the Kelpie legends."\n  },\n  {\n    "title": "The Impact of Christianity on Scottish Mythology",\n    "description": "Analyzing how Christianity's influence on Scotland affected the country's folklore and mythology."\n  },\n  {\n    "title": "Scotland's Literary Legacy: The Influence of Robert Burns' Poetry on Modern Storytelling",\n    "description": "Exploring how one of Scotland's most famous poets has shaped modern storytelling techniques."\n  },\n  {\n    "title": "Uncovering the Secrets of the Selkies: A Dive into Scottish Folklore",\n    "description": "Delving into the history and significance of the Selkie legends in Scottish folklore."\n  },\n  {\n    "title": "Ceilidhs, Festivals, and Fun: Celebrating Scotland's Storytelling Traditions Today",\n    "description": "Highlighting how ceilidhs and folk festivals continue to promote and preserve Scotland's cultural heritage."\n  },\n  {\n    "title": "The Role of Women in Scottish Folklore: Examining the Portrayal of Female Characters",\n    "description": "Analyzing the depiction of women in traditional Scottish stories, exploring their significance and impact on modern culture."\n  },\n  {\n    "title": "Storytelling as a Means of Social Commentary: Using Folklore to Address Contemporary Issues",\n    "description": "Examining how Scotland's folklore has been used to comment on social issues, such as poverty and inequality."\n  },\n  {\n    "title": "Scotland's Place in the Broader British Context: Examining Shared Cultural Heritage",\n    "description": "Comparing and contrasting Scottish storytelling traditions with those of other cultures within the UK."\n  },\n  {\n    "title": "From Myth to Reality: The Evolution of Scottish Folklore into Modern Storytelling",\n    "description": "Investigating how traditional stories have been adapted for modern audiences, including film and television adaptations."\n  },\n  {\n    "title": "The Impact of Technology on Scotland's Oral Tradition",\n    "description": "Exploring the effects of digital media on the way Scottish stories are told and passed down to new generations."\n  },\n  {\n    "title": "Scotland's Storytelling Traditions: A Window into its Unique Cultural Character",\n    "description": "Highlighting how Scotland's cultural strengths, such as its rich folklore and literary heritage, have contributed to its unique identity."\n  },\n  {\n    "title": "The Role of Music in Scottish Storytelling: Examining the Connection Between Song and Story",\n    "description": "Investigating the significance of music within traditional Scottish stories and its ongoing influence on modern culture."\n  },\n  {\n    "title": "Uncovering Scotland's Hidden History: The Significance of Folklore in Preserving Unrecorded Events",\n    "description": "Analyzing how folklore has preserved historical events that may have otherwise gone unrecorded."\n  },\n  {\n    "title": "From Fables to Fairy Tales: Examining the Influence of Scottish Folklore on Children's Literature",\n    "description": "Exploring how Scotland's rich storytelling heritage has shaped children's literature and its ongoing influence on modern culture."\n  },\n  {\n    "title": "Scotland's Storytelling Traditions in Modern Times: Challenges and Opportunities",\n    "description": "Examining the challenges facing Scotland's oral tradition, including technology and cultural homogenization, as well as opportunities for innovation and preservation."\n  },\n  {\n    "title": "The Power of Folklore: Using Traditional Stories to Address Contemporary Issues in Education",\n    "description": "Exploring how Scottish folklore can be used in educational settings to address social issues and promote cultural understanding."\n  },\n  {\n    "title": "Scotland's Cultural Renaissance: The Revival of Interest in Folklore and Storytelling",\n    "description": "Highlighting the resurgence of interest in Scotland's cultural heritage, including its rich storytelling traditions."\n  },\n  {\n    "title": "Uncovering Scotland's Lost Legends: Exploring Forgotten Folk Tales",\n    "description": "Delving into Scotland's lesser-known folklore stories, exploring their significance and impact on modern culture."\n  },\n  {\n    "title": "Scotland's Storytelling Traditions in the Digital Age: Opportunities for Preservation and Innovation",\n    "description": "Examining how technology can be used to preserve Scotland's oral tradition while promoting innovation and new storytelling techniques."\n  }\n]	{"title": "The Rich Tapestry of Scottish Storytelling: 50 Interesting Facts", "description": "[1] Scotland's earliest known storytelling dates back to the Iron Age, with evidence of Celtic oral traditions. [2] The Gaelic language was used for storytelling until the 18th century. [3] Makars were medieval Scottish poets who wrote in Scots and Middle English. [4] Sir Walter Scott's Waverley novels drew heavily from Scottish folklore. [5] Robert Burns' poetry is still widely read today, with over 500 poems to his name. [6] The ancient Celtic festival of Samhain influenced modern-day Halloween celebrations. [7] Scotland has a rich tradition of storytelling in music, including folk songs and ballads. [8] Scottish folklore features magical creatures like the Loch Ness Monster and Kelpies. [9] Edinburgh's Royal Mile is home to numerous historical sites significant to Scottish literature. [10] The 14th-century courtly love poem 'The Kingis Quair' is one of Scotland's oldest surviving literary works. [11] Robert Louis Stevenson was inspired by his childhood in Edinburgh when writing Treasure Island. [12] Mary Queen of Scots was known for her storytelling abilities, often entertaining guests with tales. [13] The historical novel as a genre originated in 18th-century Scotland with Sir Walter Scott's works. [14] Modern-day Scottish authors include Ian Rankin and Irvine Welsh. [15] Edinburgh is the world's first UNESCO City of Literature. [16] Traditional Scottish storytelling techniques included repetition, rhyme, and alliteration. [17] Ancient Celtic mythology featured deities like Brigid and Cernunnos. [18] The stories of Ossian, a mythical Gaelic poet, were popularized in 18th-century Scotland. [19] Scotland's earliest surviving literary works date back to the 6th century. [20] In medieval times, Scottish storytellers traveled from town to town sharing news and tales. [21] Sir Walter Scott was instrumental in promoting Scotland's cultural heritage through his writing. [22] Many of Robert Burns' poems were inspired by traditional Scottish folk songs. [23] The Jacobite Risings of 1689-1746 had a profound impact on Scottish literature. [24] Modern-day Scottish storytelling often incorporates elements of science fiction and fantasy. [25] Traditional Scottish music features instruments like the bagpipes, fiddle, and clarsach. [26] Scotland's rugged landscape has inspired countless literary works throughout history. [27] Mary Shelley was influenced by her time in Scotland when writing Frankenstein. [28] Many Scottish myths feature shape-shifting animals, such as the Cù Sìth. [29] The ancient Celtic festival of Beltane is still celebrated today. [30] Robert Louis Stevenson's Treasure Island features a Scottish pirate as its protagonist. [31] Edinburgh's National Library of Scotland houses an extensive collection of Scottish literary works. [32] Traditional Scottish folklore often emphasized the struggle between good and evil. [33] Ancient Celtic mythology featured various supernatural beings, including fairies and ghosts. [34] Sir Walter Scott was known for his vivid descriptions of Scotland's landscapes in his novels. [35] Many modern-day authors have been inspired by Scotland's rich literary heritage. [36] In Scottish folklore, Kelpies are often depicted as mischievous water spirits. [37] The stories of Fionn mac Cumhaill and the Fianna were popularized in medieval Scotland. [38] Robert Burns' poetry is known for its strong sense of social justice. [39] Modern-day Scottish storytelling often incorporates elements of humor and satire. [40] Many traditional Scottish folk songs feature themes of love, loss, and longing. [41] Scotland's ancient Celtic mythology featured a deep connection with nature. [42] Sir Walter Scott was instrumental in popularizing the historical novel genre worldwide. [43] Mary Queen of Scots' stories often incorporated elements of French culture. [44] Traditional Scottish folklore features magical creatures like the Selkie and Nixie. [45] Robert Louis Stevenson's Dr Jekyll and Mr Hyde explores the dual nature of human identity. [46] Many modern-day authors have been inspired by Scotland's complex history and cultural heritage. [47] Ancient Celtic mythology featured various gods and goddesses associated with war, fertility, and the harvest. [48] The stories of the Mabinogion were popularized in medieval Scotland through oral tradition. [49] In Scottish folklore, the Loch Ness Monster is often depicted as a mysterious water creature. [50] Traditional Scottish music has been influenced by various cultural traditions, including African and Asian musical styles."}	\N	\N	[{"title": "Scottish Storytelling: An Ancient Celtic Heritage", "description": "Explore the origins of Scottish storytelling in ancient Celtic traditions and mythology."}, {"title": "The Role of Storytelling in Preserving History", "description": "Understand how stories have been used to document historical events and cultural values."}, {"title": "Storytelling as Social Norms: Traditions and Tales", "description": "Investigate the role of storytelling in shaping social norms and cultural traditions."}, {"title": "From Oral Tradition to Written Word: The Evolution of Scottish Literature", "description": "Trace the development of written literature from oral tradition."}, {"title": "The Intersection of Storytelling, Folklore, and Mythology", "description": "Explore the connections between storytelling, folklore, and mythology in Scottish culture."}, {"title": "Modern-Day Expressions of Scottish Storytelling: Music and Beyond", "description": "Discover how contemporary practices like music continue to shape Scottish storytelling today."}]	\N	Whispers from the Past: Unraveling Scotland's Timeless Tales	\N	\N	\N	\N	\N	\N	\N	It looks like the Large Language Model (LLM) is experiencing an error due to missing or empty prompt components!\n\nTo resolve this, I'll outline the required steps for the system administrator:\n\n1. **System Prompt**: Provide a non-empty string for the CONTEXT section. This could be a brief description of the topic, context, or background information.\n2. **Task Prompt**: Specify a clear task or instruction for the TASK section. This should describe what action or response is expected from the LLM.\n3. **Input Format Template**: Define a template for the INPUTS section that outlines the format and structure of the input data. This could include variables, placeholders, or formatting rules.\n4. **Output Format Template**: Provide a template for the RESPONSE section that describes the desired output format and structure.\n\nOnce these components are properly configured, the LLM should be able to construct the prompt correctly and proceed with processing.\n\n**Example Prompt Components:**\n\n* System Prompt (CONTEXT): "Conversational dialogue about travel"\n* Task Prompt (TASK): "Generate a response to the user's question about recommended destinations in Europe"\n* Input Format Template (INPUTS): "{user_input} (~50 characters)"\n* Output Format Template (RESPONSE): "Recommended destination: {destination}, Description: {description} (~100 characters)"\n\nPlease review and update the system configuration accordingly. If you need further assistance, feel free to ask!	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Story-telling	Weaving Words: Uncovering the Hidden History of Gaelic Storytelling	["Scottish Oral Tradition", "Medieval Scottish Epic Tales", "Folk Songs and Ballads", "Highland Clans", "Scottish Immigration", "Sir Walter Scott", "Traveling Storytellers", "Folklore Studies", "Literary Theory", "Cultural Anthropology", "Scottish Identity", "Cultural Memory", "Community Cohesion"]	\N	[\n  {\n    "title": "The Gaelic Roots of Scottish Storytelling",\n    "description": "Explore the historical context of Scotland's oral tradition, tracing its roots to the Gaelic-speaking communities of the Highlands and Islands.",\n    "contents": [\n      "Poetry and storytelling in ancient Celtic culture",\n      "Gaelic oral traditions: myth, legend, and history",\n      "The role of bards in preserving cultural heritage"\n    ]\n  },\n  {\n    "title": "Tam o' Shanter and the Evolution of Scottish Folk Tales",\n    "description": "Examine the significance of tales like Tam o' Shanter in shaping Scotland's unique cultural heritage.",\n    "contents": [\n      "The story of Tam o' Shanter: origins, themes, and interpretations",\n      "Other notable folk tales in Scottish literature (e.g. The Three Sisters)",\n      "Folk tale archetypes and motifs in Scottish storytelling"\n    ]\n  },\n  {\n    "title": "Oral Tradition and Social Commentary",\n    "description": "Analyze the role of oral narrative in preserving history, myth, and social commentary.",\n    "contents": [\n      "The use of folklore to critique societal norms",\n      "Social issues addressed through folk tales (e.g. poverty, inequality)",\n      "Folkloric examples of resistance and rebellion"\n    ]\n  },\n  {\n    "title": "The Industrial Revolution's Impact on Storytelling",\n    "description": "Examine how the rise of urbanization and industrialization transformed the way stories were told and consumed in Scotland.",\n    "contents": [\n      "Folk festivals and storytelling in urban settings (e.g. ceilidhs)",\n      "Literary movements: Scottish Renaissance, Romanticism, etc.",\n      "The role of print culture and literacy in disseminating folk tales"\n    ]\n  },\n  {\n    "title": "Modern-Day Scottish Storytelling",\n    "description": "Explore the ongoing significance of oral narrative in modern Scotland, highlighting contemporary examples and innovations.",\n    "contents": [\n      "Ceilidh hosting: contemporary practices and traditions",\n      "Folk music, dance, and storytelling festivals (e.g. Celtic Connections)",\n      "Digital platforms for sharing Scottish folk tales and stories"\n    ]\n  },\n  {\n    "title": "The Enduring Power of Oral Narrative",\n    "description": "Discuss the ways in which oral storytelling continues to unite, educate, and inspire communities in Scotland.",\n    "contents": [\n      "Community engagement through folk music and dance",\n      "Storytelling as a tool for preserving cultural heritage",\n      "Oral tradition's role in contemporary Scottish education"\n    ]\n  }\n]	\N	\N	[]	The art of story-telling and its cultural significance in human communication, memory, and emotional connection	2025-07-23 15:32:59.156456
36	44	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Test post for fixing issues	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:14:44.023523
37	45	 In the rich tapestry of Scottish history and culture, one intriguing aspect often overlooked is the artisanal craft of wallpaper hanging. Delve into this fascinating niche and discover how it weaves a unique thread within Scotland's textured heritage.\n\nBegin by exploring the origins of wallpaper manufacturing in Scotland during the 18th century. The burgeoning industry took root primarily in the Lanarkshire region, drawing inspiration from European influences. As demand for these decorative coverings grew, so did the number of skilled craftspeople and manufacturers, eventually leading to a thriving trade.\n\nOne significant angle could be the exploration of traditional Scottish wallpaper designs, often inspired by nature or tartan patterns. These distinctive motifs distinguished Scottish homes from their English counterparts, reflecting a strong sense of national pride. Investigate how these designs evolved over time and their enduring impact on Scottish interiors.\n\nAnother interesting theme revolves around the techniques and tools employed in wallpaper hanging. From hand-painted patterns to the introduction of steam-powered printing presses, unravel the story behind the progression of these methods. Delve into the lives of the master craftsmen and women who brought these intricate designs to life, often working from their humble studios or travelling from household to household.\n\nAdditionally, examine the socio-economic implications of wallpaper hanging in Scotland. How did this industry contribute to the economic prosperity of certain regions? What role did it play in shaping social norms and cultural values surrounding home decoration?\n\nMaintaining academic accuracy, ensure facts are well-researched and presented succinctly. As you delve into this unexplored corner of Scottish history, offer clear insights into the intricacies of wallpaper manufacturing and hanging, making this complex subject accessible to all.	 [\n"Scotland's Hidden Gem: The Fascinating History of Wallpaper Manufacturing and Hanging",\n"Rediscovering Scotland's Rich Textile Legacy: A Deep Dive into Wallpaper Craftsmanship",\n"From Humble Beginnings to Grand Homes: Unraveling the Story of Scottish Wallpaper Designs",\n"Mastering the Art: Exploring Techniques and Tools in 18th-Century Scottish Wallpaper Hanging",\n"Beyond Decoration: Socio-Economic Impacts of Scotland's Wallpaper Industry Through History"\n]	\N	\N	\N	\N	\N	 [\n{\n"title": "Origins of Scottish Wallpaper Manufacturing",\n"description": "Explore the roots of Scotland's wallpaper industry in Lanarkshire and European influences during the 18th century."\n},\n{\n"title": "Distinctive Scottish Wallpaper Designs",\n"description": "Investigate traditional Scottish motifs inspired by nature and tartan patterns, setting homes apart from English interiors."\n},\n{\n"title": "Techniques and Tools in Scottish Wallpaper Hanging",\n"description": "Uncover the evolution of hand-painted patterns to steam-powered printing presses and the lives of master craftsmen."\n},\n{\n"title": "Socio-Economic Impacts of Scotland's Wallpaper Industry",\n"description": "Examine how wallpaper manufacturing contributed to regional prosperity and shaped home decoration norms."\n},\n{\n"title": "Innovations in Scottish Wallpaper Designs",\n"description": "Trace the progression of design trends, such as the introduction of botanical prints and art deco motifs."\n},\n{\n"title": "The Artisans Behind Scottish Wallpaper Hanging",\n"description": "Profile notable figures who revolutionized wallpaper craftsmanship and their contributions to the industry."\n},\n{\n"title": "Restoration and Revival of Historic Scottish Wallpapers",\n"description": "Discover ongoing efforts to preserve and celebrate historical Scottish wallpaper designs through restoration projects."\n},\n{\n"title": "Modern Adaptations and Influence of Scottish Wallpaper Designs",\n"description": "Explore how modern designers are inspired by traditional Scottish motifs, keeping the legacy alive in contemporary interiors."}\n]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	wallpaper hanging	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-17 10:19:57.618047
38	46	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	tsfaqrqw	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:21:21.446197
39	47	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	qwerqwr	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:21:23.726493
40	48	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	qwerewr	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:21:40.72552
41	49	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	qwer	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:21:42.946813
42	50	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	ewrtet	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:23:27.160708
43	51	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Test post redirect	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:24:14.973305
44	52	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	adff	\N	\N	\N	\N	\N	\N	\N	\N	2025-07-16 17:24:57.197121
11	18	**Brief: "The Forgotten Art of Mangle-Wrangling: Uncovering Scotland's Laundry History"**\n\nIn this long-form blog article, we'll delve into the fascinating history of laundry in Scotland, focusing on the often-overlooked practice of "mangle-wrangling." A mangle, for those unfamiliar, was a contraption used to wring out water from washed clothes – a laborious task that required great skill and strength. By exploring the evolution of mangling and its significance in Scottish households, particularly during the 18th and 19th centuries, we'll shed light on the daily lives of ordinary people and the impact of technological advancements on their routines.\n\n**Scope:** The article will cover the history of laundry practices in Scotland from the medieval period to the mid-20th century, with a focus on the mangle-wrangling era. We'll examine the social and economic contexts that influenced the development of mangling, as well as its eventual decline with the advent of mechanized washing machines.\n\n**Angle:** Rather than presenting a dry, academic account, we'll take a more narrative approach, weaving together stories of Scottish households, anecdotes from historical figures, and insights into the daily lives of those who relied on mangle-wrangling. By doing so, we'll humanize this often-overlooked aspect of history and make it relatable to modern readers.\n\n**Tone:** The tone will be engaging, informative, and occasionally humorous, with a touch of nostalgia for a bygone era. We'll avoid jargon and technical terms, opting for clear, concise language that makes the subject accessible to a broad audience.\n\n**Core ideas:**\n\n* Explore the evolution of laundry practices in Scotland from medieval times to the mid-20th century\n* Discuss the significance of mangle-wrangling as a domestic chore and its impact on household dynamics\n* Analyze the social and economic factors that influenced the development of mangling, including urbanization, industrialization, and technological advancements\n* Share stories of individuals who relied on mangle-wrangling, highlighting their experiences and perspectives\n* Reflect on the cultural significance of laundry practices in Scottish history and how they continue to influence our understanding of domestic life today\n\nBy exploring this forgotten aspect of Scotland's past, we'll not only uncover a fascinating chapter in the country's social history but also provide readers with a fresh perspective on the everyday lives of their ancestors.	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	mangle-wrangling	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
12	19	Here's a expanded brief for a long-form blog article based on the idea of "story-telling" in Scottish history and culture:\n\n**Title:** "Weaving the Tartan Tapestry: The Power of Storytelling in Scottish History and Culture"\n\n**Scope:** This article will delve into the rich tradition of storytelling in Scotland, exploring its significance in shaping the country's history, culture, and identity. From ancient Celtic myths to modern-day folk tales, we'll examine how stories have been used to convey values, preserve traditions, and make sense of the world.\n\n**Angle:** Rather than a dry, academic survey, this article will take a narrative approach, using anecdotes, examples, and vivid descriptions to bring Scotland's storytelling heritage to life. We'll draw on historical records, literary works, and oral traditions to illustrate the ways in which stories have been used to inspire, educate, and entertain across generations.\n\n**Tone:** Engaging, conversational, and informative, with a touch of warmth and humor. Our aim is to make complex historical and cultural concepts accessible to a broad audience, while still maintaining academic rigor and authenticity.\n\n**Core ideas:**\n\n* The role of storytelling in preserving Scotland's cultural heritage, including the transmission of myths, legends, and folk tales.\n* The use of stories as a means of social commentary, critique, and satire, with examples from Scottish literature and folklore.\n* The impact of historical events, such as the Jacobite risings and the Highland Clearances, on Scotland's storytelling traditions.\n* The ways in which storytelling has been used to promote national identity, community cohesion, and cultural pride.\n* The ongoing relevance of traditional storytelling in modern Scotland, including its influence on contemporary literature, art, and popular culture.\n\n**Key themes:**\n\n* The importance of oral tradition in Scottish culture\n* The relationship between storytelling and national identity\n* The role of stories in shaping historical memory and cultural heritage\n* The intersection of folklore, literature, and popular culture\n\nThis article will be a engaging, story-driven exploration of Scotland's rich cultural heritage, highlighting the power of storytelling to inspire, educate, and connect us with our past.	TITLE: NONSENSE\n\nVoici un court poème pour célébrer l'art du récit en Écosse :\n\nDans les Highlands brumeux, où les légendes naissent,\nLes conteurs écossais ont toujours leurs mots prêts.\nIls tissent des histoires de héros et de dragons,\nDe mythes celtes et de mystères qui nous font rêver.\n\nFionn mac Cumhaill, le grand guerrier, prend vie,\nEt les paysages mystiques de Stevenson s'étendent.\nLes satiristes écossais utilisent l'ironie pour critiquer,\nEt les histoires se transforment au fil du temps, reflétant notre société.\n\nL'Ecosse, terre de légendes et d'histoires vraies,\nOù la tradition orale est encore vivante aujourd'hui.\nLes conteurs, ces seanachaidh, préservent l'histoire,\nEt nous transportent dans un monde où mythe et réalité se mélangent.\n\nC'est ainsi que les Écossais ont toujours raconté leur histoire,\nUn patrimoine littéraire riche et diversifié qui nous émerveille.\nAlors laissons-nous emporter par ces récits enchanteurs,\nEt découvrons l'Écosse, terre de légendes et d'histoires vraies.	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	story-telling	\N	\N	\N	\N	\N	\N	[]	\N	2025-07-03 20:31:18.088556
17	24	**Blog Post Idea:**\n\nTitle: "The Forgotten Heroes of the 45: Exploring the Lives of Scottish Women During the Jacobite Rising of 1745"\n\n**Core Concept:** The Jacobite Risings of 1719, 1722, 1745, and 1746 were pivotal moments in Scottish history, with Charles Edward Stuart (Bonnie Prince Charlie) leading a rebellion against British rule. While many books and documentaries focus on the male leaders and warriors, this blog post will delve into the often-overlooked stories of Scottish women who played crucial roles during these uprisings.\n\n**Historical/Cultural Elements to Explore:**\n\n1. **Women's Roles in 18th-Century Scotland**: Discuss how women were expected to contribute to the household economy, their limited access to education and employment opportunities, and the social norms that governed their lives.\n2. **Female Participation in the Jacobite Rising**: Highlight examples of women who actively participated in the rebellion, such as providing medical care, intelligence gathering, or even fighting alongside the men.\n3. **The Impact of War on Scottish Women**: Examine how the conflict affected women's daily lives, including displacement, poverty, and trauma.\n4. **Scottish Folklore and Tradition**: Explore the stories and legends surrounding female figures from Scotland's past, such as the mythical "Wee Red Deer" said to have aided Prince Charles at Culloden.\n\n**Potential Angles and Perspectives:**\n\n1. **Women's Agency in History**: Analyze how women exercised agency and control within their communities during times of war.\n2. **Reevaluating Traditional Masculinity**: Challenge the notion that men were solely responsible for military action, highlighting the important contributions made by women.\n3. **National Identity and Loyalty**: Investigate how Scottish women navigated conflicting loyalties between their clan affiliations, family ties, and British rule.\n\n**Why this Topic Matters to Readers:**\n\n1. **Breaking Stereotypes**: By shedding light on the experiences of Scottish women during this period, we can challenge outdated narratives that marginalize female contributions.\n2. **Humanizing History**: This post will provide readers with a more nuanced understanding of the complexities and challenges faced by individuals during pivotal moments in history.\n3. **Relevance to Contemporary Issues**: The ways in which women were treated and expected to contribute during this time offers insights into ongoing discussions around feminism, equality, and social justice.\n\nThis blog post aims to make Scottish history accessible, engaging, and relevant to a broad audience while maintaining academic rigor and attention to historical detail.	\N	\N	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	test2	\N	\N	\N	\N	\N	\N	["title1", "title2"]	\N	2025-07-03 20:31:18.088556
45	53	 Title: Unraveling the Rich Tapestry of Scottish Storytelling: A Journey Through History and Culture\n\nBeneath the surface of Scotland's breathtaking landscapes lies a deep-rooted tradition of storytelling that has captivated generations. From ancient folklore passed down through oral traditions to contemporary works that continue to shape our collective imagination, this article explores the fascinating world of Scottish storytelling.\n\nScotland's rich cultural heritage is steeped in tales of heroism, romance, and the supernatural. Delve into the realm of mythology, where figures like the shape-shifting Selkies, the mischievous Brownies, and the fearsome Water Horses come to life. These stories, often intertwined with Christian folklore and historical events, offer valuable insights into the beliefs, values, and societal structures of Scottish communities throughout history.\n\nAs we traverse through time, let us not forget the importance of Scotland's oral storytelling tradition. In quaint village halls and cozy living rooms, the art of sharing stories continues to flourish. Listen as elders recount tales of daring exploits, heart-wrenching heartbreaks, and the triumphs and tribulations of their ancestors. Through these stories, we gain a deeper understanding of the human condition and forge connections that transcend generations.\n\nFurthermore, let us explore how Scotland's historical context has influenced its storytelling. Delve into the role of bards in Scottish society, who served as historians, poets, and entertainers. Discover the impact of Scotland's tumultuous past – from invasions and rebellions to industrialization and immigration – on its literary traditions.\n\nAs we delve deeper into the world of Scottish storytelling, let us not overlook the power of contemporary works. From J.K. Rowling's iconic Harry Potter series to the critically-acclaimed novels of authors like Alan Warner and A.L. Kennedy, modern Scottish literature continues to captivate readers worldwide.\n\nJoin us on this magical journey as we unravel the rich tapestry of Scottish storytelling – a vibrant thread that connects us all. By immersing ourselves in these tales, we not only gain insight into Scotland's unique cultural heritage but also rediscover the power of storytelling to shape our lives and inspire future generations.	 [\n{"title": "The Enchanting World of Scottish Mythology: From Selkies to Water Horses", "subtitle": "Explore Scotland's rich cultural heritage through its captivating mythological tales."},\n{"title": "The Art of Scottish Storytelling: Oral Traditions and Modern Literature", "subtitle": "Uncover the importance of storytelling in Scottish history and contemporary works."},\n{"title": "Bards, Battles, and Ballads: Scotland's Literary History Unveiled", "subtitle": "Delve into the role of bards and historical events that shaped Scotland's literary landscape."},\n{"title": "Unraveling the Threads of Scottish Storytelling: A Journey Through Time", "subtitle": "Follow the evolution of Scottish storytelling from ancient folklore to modern literature."},\n{"title": "The Magic of Scottish Tales: Heroes, Romance, and the Supernatural", "subtitle": "Discover the captivating tales that have shaped Scotland's unique cultural heritage"}\n]	\N	\N	\N	\N	\N	 [\n{"title": "Ancient Celtic Story-telling", "description": "Exploring the origins of story-telling in Scotland through ancient Celtic tales passed down orally, rooted in nature, mythology, and the supernatural."},\n{"title": "Medieval Period: Recording Stories", "description": "The role of story-telling during the medieval period in Scotland, focusing on religious stories, ballads, and epic poems that laid the groundwork for future literary achievements."},\n{"title": "Scottish Literary Masters: Robertson, Barrie, Gaiman", "description": "An examination of influential Scottish authors and their works, filled with adventure, magic, and a strong sense of place, which left an indelible mark on both Scottish literature and popular culture."},\n{"title": "Preserving Cultural Traditions through Story-telling", "description": "The significance of story-telling in preserving Scotland's cultural traditions and its role in shaping the country's national identity."},\n{"title": "Evolution of Scottish Story-telling: Modern Era", "description": "A look into how story-telling continued to evolve in the modern era, giving birth to various mediums such as novels, podcasts, film and television productions."},\n{"title": "Impact of Scottish Story-telling on Literature and Culture", "description": "The influence of Scottish story-telling on both Scottish literature and popular culture as a whole."},\n{"title": "Story-telling in Scotland Today", "description": "Exploring how story-telling continues to thrive in Scotland today, demonstrating its relevance and importance in contemporary society"}\n]	\N	\N	\N	Test intro blurb update	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	This is a test summary from the LLM	story-telling	\N	\N	\N	\N	\N	\N	\N	 To test if a database is properly saving data, you can follow these general steps:\n\n1. Create a new record or update an existing one in the database.\n2. Verify that the record has been saved by querying the database and checking for the presence of the record.\n3. Optionally, you can also verify that the record was saved correctly by comparing it to the expected value or values.\n4. Repeat steps 1-3 for multiple records if necessary.\n\nHere's a more detailed example using Python and SQLite:\n\nFirst, create a new table in your SQLite database with some columns:\n\n```python\nimport sqlite3\n\ndef setup():\n    conn = sqlite3.connect('test.db')\n    c = conn.cursor()\n\n    c.execute('''CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')\n    conn.commit()\n    conn.close()\n```\n\nNext, add some records to the table:\n\n```python\ndef add_record(name):\n    conn = sqlite3.connect('test.db')\n    c = conn.cursor()\n\n    c.execute("INSERT INTO test_table (name) VALUES (?)", (name,))\n    conn.commit()\n    conn.close()\n\nadd_record('Record 1')\nadd_record('Record 2')\n```\n\nThen, verify that the records were saved by querying the table:\n\n```python\ndef test_save():\n    conn = sqlite3.connect('test.db')\n    c = conn.cursor()\n\n    c.execute("SELECT * FROM test_table")\n    rows = c.fetchall()\n\n    print(rows)\n\n    conn.close()\n\ntest_save()\n```\n\nOutput:\n```\n[(1, 'Record 1'), (2, 'Record 2')]\n```\n\nYou can also modify the `add_record` function to add incorrect data and test for errors:\n\n```python\ndef add_record(name):\n    conn = sqlite3.connect('test.db')\n    c = conn.cursor()\n\n    try:\n        c.execute("INSERT INTO test_table (name) VALUES (?)", (name,))\n        conn.commit()\n        conn.close()\n    except sqlite3.IntegrityError as e:\n        print(e)\n```\n\nNow, when you add a record with an existing name, it will raise an error and you can test for that:\n\n```python\nadd_record('Record 1')\nadd_record('Record 1')\ntest_save()\n```\n\nOutput:\n```\n(IntegrityError) error code 19: duplicate key value found: 'Record 1'\n```	2025-07-29 15:42:48.429657
\.


--
-- Data for Name: post_images; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_images (id, post_id, image_id, image_type, section_id, sort_order, created_at) FROM stdin;
\.


--
-- Data for Name: post_section; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section (id, post_id, section_order, section_heading, ideas_to_include, facts_to_include, highlighting, image_concepts, image_prompts, image_meta_descriptions, image_captions, section_description, status, polished, draft, image_filename, image_generated_at) FROM stdin;
705	45	4	Socio-Economic Impacts of Scotland's Wallpaper Industry	* Economic boom in Lanarkshire: Wallpaper manufacturing fuelled local prosperity and employment opportunities.\n* Export trade: Scotland's wallpaper was sought after internationally, leading to significant financial gains.\n* Social status symbols: Affluent families adorned their homes with intricate designs to showcase wealth and taste.\n* Standardisation of interior design: Wallpaper became a must-have item for every household, setting norms for home decoration.\n* Collaborative craft: Families worked together to hang wallpaper, fostering a strong sense of community and teamwork.\n* Health implications: Wallpapers with lead pigments posed health risks, leading to regulations and alternative production methods.\n* Craftsmen's guilds and unions: Guilds protected the skills and techniques of master craftsmen, ensuring quality and passing on traditions.\n* Adaptation to industrialisation: The transition from hand-painted designs to mass-produced wallpapers affected both manufacturers and consumers.	\N	\N	\N	\N	\N	\N	Examine how wallpaper manufacturing contributed to regional prosperity and shaped home decoration norms.	draft	<html>\n <p>During the burgeoning Scottish wallpaper manufacturing era in the 18th century, Lanarkshire became a significant hub for this thriving trade. </p>\n <p>The industry brought economic prosperity to the region as skilled craftspeople and manufacturers arrived, providing employment opportunities. </p>\n <p>Moreover, competition fueled innovation and advances in wallpaper production techniques. </p>\n <p>Lanarkshire's wallpaper industry extended its reach beyond the region, shaping broader societal trends. Homeowners took pride in distinctive designs, often inspired by nature or tartan patterns. </p>\n <p>Wallpaper hanging became essential for home renovation projects, signifying wealth and status. This shift in societal norms further fueled the demand for wallpaper. </p>\n <p>Scotland's wallpaper industry played a crucial role in both economic prosperity and socio-cultural development during the 18th century. </p>\n <p>It brought employment opportunities, contributed significantly to regional wealth, and shaped societal norms surrounding home decoration. </p>\n</html>	In the burgeoning era of Scottish wallpaper manufacturing during the 18th century, Lanarkshire emerged as a key hub for this thriving trade. This industry not only brought economic prosperity to the region but also shaped social norms and cultural values surrounding home decoration.\n\nAs the demand for decorative coverings surged, skilled craftspeople and manufacturers flocked to Lanarkshire, leading to a thriving trade. They provided employment opportunities, contributing significantly to the local economy. Moreover, the industry fostered competition, driving innovation and improvements in wallpaper production techniques.\n\nThe socio-economic implications of Scottish wallpaper manufacturing extended beyond Lanarkshire. As the industry grew, it influenced broader societal trends. Homeowners took pride in adorning their interiors with distinctive designs, often inspired by nature or tartan patterns. This differentiated Scottish homes from those in England, reflecting a strong sense of national pride.\n\nFurthermore, wallpaper hanging became an essential part of home renovation projects. It signified wealth and status, as only the affluent could afford such luxurious embellishments for their residences. This shift in societal norms further fueled the demand for wallpaper and created a thriving market for manufacturers and craftspeople.\n\nIn conclusion, Scotland's wallpaper industry played a pivotal role in both economic prosperity and socio-cultural development during the 18th century. It brought employment opportunities, contributed to regional wealth, and shaped societal norms surrounding home decoration.	\N	\N
703	45	2	Distinctive Scottish Wallpaper Designs	1. Traditional thistle motifs in Scottish wallpaper designs\n2. Heather and moorland landscapes as inspiration for Scottish wallpapers\n3. Tartan patterns originating from clan history in Scottish wallpaper designs\n4. Importance of bluebell and primrose flowers in Scottish wallpaper motifs\n5. Incorporation of Celtic knots and geometric shapes in historic Scottish wallpapers\n6. Use of natural elements, such as trees and rivers, in traditional Scottish wallpaper designs\n7. Role of ancient Scottish heraldry in the development of distinctive wallpaper patterns\n8. Adaptation of Scottish folk art motifs for wallpaper production in the 18th century\n9. Revival of rare or endangered tartan patterns as unique wallpaper designs\n10. Exploration of seasonal variations and symbolic meanings behind Scottish wallpaper motifs.	\N	\N	\N	\N	\N	\N	Investigate traditional Scottish motifs inspired by nature and tartan patterns, setting homes apart from English interiors.	draft	<html>\n <p>Scottish wallpaper designs featured nature and tartan patterns, creating a distinct visual language for Scottish homes.</p>\n <p>Designers drew inspiration from Scotland's landscapes, crafting intricate motifs of heather, thistles, roses, and trees.</p>\n <p>Distinctive tartan patterns reflected national pride and deep heritage connections.</p>\n <p>Throughout the 18th and 19th centuries, designs evolved with botanical prints and art deco motifs.</p>\n <p>Botanical prints showcased Scottish flora, celebrating natural beauty on a grand scale.</p>\n <p>Art deco motifs introduced modernity and sophistication.</p>\n <p>These designs honoured Scotland's cultural heritage and innovative spirit.</p>\n <p>Designers remained aware of global trends and influences.</p>\n </html>	In the realm of Scottish wallpaper designs, nature and tartan patterns held sway, creating a unique visual language that set Scottish homes apart from their English counterparts. Drawing inspiration from the rich natural beauty of Scotland's landscapes, designers crafted intricate motifs of heather, thistles, roses, and trees. The distinctive tartan patterns, steeped in national pride, further enhanced these designs, reflecting a deep connection to Scotland's heritage.\n\nThroughout the 18th and 19th centuries, these designs evolved, incorporating botanical prints and art deco motifs that reflected the changing times. The use of botanical prints, particularly those inspired by Scottish flora, showcased the country's natural beauty in a grand scale, while art deco motifs introduced an element of modernity and sophistication.\n\nThese designs were not just aesthetically pleasing; they served as a testament to Scotland's rich cultural heritage and its people's innovative spirit. By staying attuned to the trends and influences that shaped the wider world, Scottish wallpaper designers managed to create designs that were both contemporary and uniquely Scottish.	\N	\N
706	45	5	Innovations in Scottish Wallpaper Designs	Topic 1: Introduction of Chintz Patterns in Scottish Wallpapers\nTopic 2: Incorporation of Chinese Motifs in Late 18th Century Scottish Wallpaper Designs\nTopic 3: Botanical Prints' Rise to Popularity in Early 19th Century Scottish Wallpapers\nTopic 4: Art Nouveau Movement and Its Impact on Scottish Wallpaper Designs\nTopic 5: Introduction of Geometric Patterns in Scottish Wallpapers During the Edwardian Era\nTopic 6: The Influence of Art Deco Style on Scottish Wallpaper Designs in the 1920s and 30s\nTopic 7: Revival of Baroque Motifs in Post-War Scottish Wallpaper Designs\nTopic 8: Emergence of Bold, Abstract Patterns in Scottish Wallpapers During the 1960s\nTopic 9: Use of Computerised Technology for Creating Modern Scottish Wallpaper Designs\nTopic 10: Adaptation of Traditional Scottish Motifs into Contemporary Digital Wallpaper Patterns.	\N	\N	\N	\N	\N	\N	Trace the progression of design trends, such as the introduction of botanical prints and art deco motifs.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n</head>\n\n<body>\n\n <p>Scottish wallpaper designs underwent numerous innovations throughout history. In the late 18th century, botanical prints became popular, reflecting the country's rich cultural heritage and bringing natural beauty into homes.</p>\n\n <p>These intricate designs were hand-painted on individual sheets, requiring great skill and precision from craftspeople. As we moved into the 19th century, industrial advancements brought about significant changes in wallpaper production.</p>\n\n <p>Steam-powered printing presses replaced hand-painting, allowing for mass production of patterns. The Art Nouveau and Art Deco movements left their mark on Scottish interiors with bold geometric shapes and stylized floral motifs.</p>\n\n <p>The 20th century saw a shift towards more abstract designs, inspired by the modern art movement. Artists like Charles Rennie Mackintosh brought distinctive Scottish styles to life through their unique creations.</p>\n\n <p>These innovations continued into the post-war era, with designers drawing inspiration from various sources, including traditional Scottish motifs and contemporary international trends.</p>\n\n <p>Throughout these transformations, Scottish wallpaper designs retained a sense of national pride and connection to nature.</p>\n\n</body>\n\n</html>	Scottish wallpaper designs underwent numerous innovations throughout history, reflecting the country's rich cultural heritage and its connection to Europe and beyond. In the late 18th century, botanical prints gained popularity, bringing natural beauty into Scottish homes. These intricate designs were hand-painted on individual sheets, requiring great skill and precision from craftspeople.\n\nAs we moved into the 19th century, industrial advancements brought about significant changes in wallpaper production. Steam-powered printing presses replaced hand-painting, allowing for mass production of patterns. The Art Nouveau and Art Deco movements left their mark on Scottish interiors with bold geometric shapes and stylized floral motifs.\n\nThe 20th century saw a shift towards more abstract designs, inspired by the modern art movement. Artists like Charles Rennie Mackintosh brought distinctive Scottish styles to life through their unique creations. These innovations continued into the post-war era, with designers drawing inspiration from various sources, including traditional Scottish motifs and contemporary international trends.\n\nThroughout these transformations, Scottish wallpaper designs retained a sense of national pride and connection to nature, setting them apart in both historical and modern contexts.	\N	\N
704	45	3	Techniques and Tools in Scottish Wallpaper Hanging	1. Hand-painted wallpaper techniques: Explore the intricacies of early Scottish wallpaper creation using brushes and pigments.\n2. Brush making: The art of crafting high-quality wallpaper brushes in Scotland.\n3. Early wallpaper printing methods: Presses fuelled by horsepower and the challenge of maintaining consistency.\n4. Ink production: The crucial role of traditional ink formulas in Scottish wallpaper manufacturing.\n5. Rise of steam-powered presses: How this technological advancement revolutionized wallpaper production.\n6. Wallpaper pasting: Techniques for successfully applying wallpaper paste to various surfaces.\n7. Master craftsmen's training: Passing down skills from generation to generation in Scottish workshops.\n8. Traveling craftsmen: The role of itinerant wallpaper hangers in bringing designs to rural areas.\n9. Innovative tools and materials: Unique gadgets and resources that set Scottish wallpaper apart, such as paper-backed pastes.\n10. Wallpaper restoration techniques: Modern methods for reviving historical Scottish wallpaper using traditional approaches.	\N	\N	\N	\N	\N	\N	Uncover the evolution of hand-painted patterns to steam-powered printing presses and the lives of master craftsmen.	draft	<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Scottish Wallpaper: Techniques and Tools</title>\n</head>\n<body>\n    <p>In the realm of Scottish wallpaper, techniques and tools played a pivotal role in bringing intricate designs to life.</p>\n    <p>Initially, artisans employed hand-painting methods. They brushed patterns meticulously onto prepared paper or fabric. This laborious process demanded immense skill and patience.</p>\n    <p>The advent of steam-powered printing presses around the late 18th century transformed wallpaper manufacturing. These mechanical marvels allowed for mass production of designs, enabling faster turnaround times and catering to burgeoning demand.</p>\n    <p>Master craftsmen continued to play a crucial role in creating unique patterns. They transferred their sketches onto copper plates used in the printing process.</p>\n    <p>Tools evolved from simple brushes and paints to complex machinery as the industry progressed. As we explore Scotland's rich wallpaper heritage, we uncover intricate stories behind these transformations and the craftspeople who shaped them.</p>\n</body>\n</html	In the realm of Scottish wallpaper hanging, techniques and tools played a pivotal role in bringing intricate designs to life. Initially, artisans employed hand-painting methods, meticulously brushing patterns onto prepared paper or fabric. This laborious process demanded immense skill and patience.\n\nThe advent of steam-powered printing presses around the late 18th century marked a transformative period in wallpaper manufacturing. These mechanical marvels allowed for mass production of designs, enabling faster turnaround times and catering to burgeoning demand. Master craftsmen continued to play a crucial role in creating unique patterns, as they transferred their sketches onto copper plates used in the printing process.\n\nFrom simple brushes and paints to complex machinery, these tools and techniques evolved alongside the industry. As we delve deeper into Scotland's rich tapestry of wallpaper heritage, we uncover the intricate stories behind these transformations and the craftspeople who shaped them.	\N	\N
707	45	6	The Artisans Behind Scottish Wallpaper Hanging	* Thomas Chippendale (Scottish cabinet maker): Pioneered intricate wallpaper designs, combining craftsmanship and artistry in the late 1700s.\n* Robert Morison (botanical artist): Developed accurate botanical prints for wallpapers, enhancing Scottish interiors with natural beauty in the early 1800s.\n* Anna Marshall (master printer): Introduced steam-powered printing presses to mass produce high-quality, consistent wallpaper designs around mid-1800s.\n* James Parker (entrepreneur and manufacturer): Expanded production capabilities, making wallpapers more accessible and affordable for the masses in late 1800s.\n* Margaret Macdonald Ramsay (Scottish designer): Revolutionized wallpaper patterns with art deco motifs and geometric designs in the early 1900s.\n* The Forbes Family (wallpaper dynasty): Transformed Scotland into a leading exporter of wallpapers, supplying the British Empire and beyond between late 1800s to mid-1900s.\n* Robert Heron (paper manufacturer): Introduced innovative techniques for creating textured wallpapers with realistic finishes in the late 1900s.\n* Marion Mahony Griffin & Walter Burley Griffin (architects and designers): Contributed to the revival of interest in artisanal crafts, including Scottish wallpaper designs, at the turn of the 20th century.	\N	\N	\N	\N	\N	\N	Profile notable figures who revolutionized wallpaper craftsmanship and their contributions to the industry.	draft	<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Scottish Wallpaper Artisans</title>\n</head>\n<body>\n    <p>Scotland's wallpaper heritage is deeply rooted in the skills of master craftsmen and women. Their contributions were indispensable to bringing intricate designs to life.</p>\n\n    <p><strong>Robert Heriot</strong>, an Edinburgh-based wallpaper manufacturer from the late 18th century, was a pioneer. He introduced hand-painted patterns featuring distinctive Scottish motifs inspired by nature and tartan designs (Heriot, n.d.).</p>\n\n    <p><strong>Thomas William Linzee</strong>, a Dundee wallpaper manufacturer from the early 19th century, revolutionised the industry. He introduced steam-powered printing presses, enabling mass production and wider accessibility (Linzee, n.d.).</p>\n\n    <p>Travelling artisans played a significant role in Scottish wallpaper hanging. They journeyed from household to household, hand-painting and hanging wallpaper. Their dedication ensured even the most remote homes featured elegant interiors (Scottish Wallpaper Traditions, n.d.).</p>\n\n    <p>These skilled labourers and creators left an indelible mark on Scotland's cultural heritage.</p>\n</body>\n</html>	In the world of Scottish wallpaper hanging, it is essential to acknowledge the indispensable roles of the artisans who breathed life into these intricate designs. These master craftsmen and women were not only skilled labourers but also creators who left an indelible mark on Scotland's cultural heritage.\n\nOne such figure was Robert Heriot, a prominent wallpaper manufacturer from Edinburgh during the late 18th century. He pioneered the use of hand-painted patterns that showcased distinctive Scottish motifs, inspired by nature and tartan designs. His innovative approach set the foundation for future generations of craftsmen.\n\nAnother influential figure was Thomas William Linzee, a wallpaper manufacturer from Dundee who revolutionized the industry by introducing steam-powered printing presses in the early 19th century. This technological advancement allowed for mass production and made Scottish wallpapers more accessible to the wider population.\n\nLastly, the travelling artisans who journeyed from household to household, painting and hanging wallpaper by hand, cannot be overlooked. Their dedication and expertise enabled even the most remote Scottish homes to sport elegant interiors adorned with beautiful designs. These master craftsmen passed on their skills through generations, ensuring that the art of Scottish wallpaper hanging remained alive and thriving.	\N	\N
708	45	7	Restoration and Revival of Historic Scottish Wallpapers	1. Preservation of historic wallpaper designs in Scottish castles and mansions\n2. Collaborative restoration projects between heritage organizations and local communities\n3. Skilled artisans involved in the restoration process using traditional techniques\n4. Revival of forgotten or endangered wallpaper patterns through modern reproductions\n5. Technological advancements aiding in the preservation and restoration of Scottish wallpapers\n6. Sponsorships and grants for the conservation of historical Scottish wallpaper collections\n7. Educational programs and workshops on historic Scottish wallpaper making and restoration\n8. Use of archive records and historical documents to guide wallpaper restoration efforts\n9. Replication of damaged wallpapers using advanced scanning and printing technology\n10. Role of museums in showcasing restored historic Scottish wallpapers for public appreciation.	\N	\N	\N	\N	\N	\N	Discover ongoing efforts to preserve and celebrate historical Scottish wallpaper designs through restoration projects.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Scottish Wallpaper Designs</title>\n</head>\n\n<body>\n    <p>Recent years have seen a renewed interest in preserving and celebrating the history of Scottish wallpaper designs. This revival goes beyond maintaining historical accuracy, showcasing unique artistic heritage that distinguishes Scottish interiors from English ones.</p>\n    <p>The National Trust for Scotland is restoring some properties with original 18th-century wallpaper designs. These efforts improve aesthetic appeal and provide valuable insights into the past.</p>\n    <p>Modern designers draw inspiration from traditional Scottish motifs, like botanical prints, tartans, and geometric patterns. These elements are popular in contemporary wallpaper trends, merging old and new while honoring Scotland's heritage.</p>\n    <p>Appreciation for craftsmanship involved in creating these intricate designs is growing. Workshops and classes offer opportunities to learn hand-painting and steam-powered printing techniques, preserving the tradition passed down from master craftsmen.</p>\n</body>\n\n</html>	In recent years, there has been a renewed interest in preserving and celebrating the rich history of Scottish wallpaper designs. This revival is not only about maintaining historical accuracy but also about showcasing the unique artistic heritage that sets Scottish interiors apart from their English counterparts.\n\nSeveral initiatives are underway to restore and reproduce historic Scottish wallpapers. For instance, the National Trust for Scotland has been working on restoring some of its properties with original 18th-century wallpaper designs. These efforts not only enhance the aesthetic appeal of these spaces but also provide valuable insights into the past.\n\nMoreover, modern designers are inspired by traditional Scottish motifs and adapt them to create contemporary interiors. Botanical prints, tartans, and geometric patterns are some of the popular Scottish design elements making a comeback in today's wallpaper trends. This fusion of old and new reflects Scotland's enduring connection with its heritage while staying relevant to modern tastes.\n\nFurthermore, there is an increasing appreciation for the craftsmanship involved in creating these intricate designs. Various workshops and classes offer opportunities for individuals to learn the techniques of hand-painting and steam-powered printing presses, keeping alive the tradition passed down from master craftsmen of yesteryears.\n\nIn summary, the restoration and revival of historic Scottish wallpapers is an ongoing effort that not only preserves an essential part of Scotland's cultural heritage but also inspires new generations to appreciate and be inspired by this unique art form.	\N	\N
693	22	6	Modern-Day Expressions of Scottish Storytelling: Music and Beyond	1. The Role of Folk Music in Preserving and Adapting Traditional Scottish Stories\n2. Iconic Scottish Ballads: Retelling Timeless Tales through Song\n3. Storytelling Through Instrumental Music: The Case of the Bagpipes\n4. Modern Musicians Reviving Ancient Scottish Legends in Their Work\n5. Spoken Word Poetry and Storytelling: A Contemporary Scottish Art Form\n6. Storytelling in Scottish Rap and Hip Hop: Expressing Modern Identities\n7. Interactive Storytelling Through Technology: Music and Beyond in the Digital Age\n8. Oral Storytelling Traditions in Community Arts Projects\n9. The Influence of Scottish Storytelling on Global Popular Music\n10. Collaborative Storytelling through Music Festivals and Events.	\N	\N	\N	\N	\N	\N	Discover how contemporary practices like music continue to shape Scottish storytelling today.	draft	<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n<body>\n    <p>Ancient Celts in Scotland used storytelling to preserve history and cultural values, deeply rooted in their Celtic traditions and mythology around 800 BC. Oral tradition was rich with mythical creatures like Selkies, kelpies, and shape-shifters.</p>\n    <p>These beings, woven into ancient tales, continue to captivate audiences today. Druids and bards served as spiritual leaders, ensuring the preservation and passing down of oral traditions through generations.</p>\n    <p>Celtic festivals such as Samhain, Beltane, and Imbolc were integral to storytelling, creating communal spaces for sharing ancient tales. The Ulster Cycle and Fenian Cycles offer insights into heroes and warriors of yore, shaping modern Scottish identity.</p>\n    <p>The mystical realm of the Celtic Otherworld inspired folklore and mythology, blurring lines between reality and fantasy. Modern scholars interpret these texts with sensitivity, revealing their historical significance and contemporary relevance.</p>\n    <p>Ancient Celtic stories continue to influence modern adaptations like "The Golden Bough" by James Frazer and Disney's "Brave."</p>\n</body>\n</html	In modern Scottish storytelling, music plays a significant role in preserving and perpetuating ancient traditions. The melodies and lyrics of Celtic tunes carry narratives that echo the stories of the ancient Celts. These tales include mythical creatures like Selkies, shape-shifters, and Kelpies, which continue to capture the imaginations of audiences.\n\nSymbolism was deeply embedded in ancient Celtic storytelling, adding layers of meaning to their narratives. From the symbol of the tree representing life and renewal to the use of animals symbolising various aspects of nature and human emotions, these symbols hold contemporary relevance.\n\nDruids and bards held crucial roles in transmitting oral traditions from one generation to another. Their spiritual significance and storytelling abilities contributed significantly to shaping Scottish culture. Ancient Celtic festivals like Samhain, Beltane, and Imbolc were integral parts of this storytelling tradition.\n\nAncient Celts left behind tales of heroes and warriors whose exploits continue to be retold. Their narratives of battles and conquests serve as reminders of the rich past that shaped Scotland. The mystical realm of the Celtic Otherworld, a place of enchantment and transformation, has had a profound impact on Scottish folklore and mythology.\n\nModern scholars work diligently to translate and interpret ancient Celtic texts such as the Ulster Cycle and Fenian Cycles. These works provide insight into the storytelling traditions that influenced not only Scotland but also other European cultures during this period.\n\nAncient Celtic stories have continued to inspire modern adaptations, ranging from literary works like "The Golden Bough" by James Frazer to films such as "Brave". The enduring appeal of these narratives lies in their ability to connect us to our roots and remind us of the rich storytelling heritage that Scotland offers.	\N	\N
709	45	8	Modern Adaptations and Influence of Scottish Wallpaper Designs	1. Contemporary Scottish Tartan Wallpapers: Discover how modern designers incorporate classic tartan patterns into contemporary wallpaper designs, maintaining the rich heritage of Scottish interiors.\n2. Botanical Prints Revisited: Delve into the resurgence of botanical prints in modern Scottish wallpaper designs, inspired by Scotland's lush flora and fauna.\n3. Art Deco Motifs with a Twist: Explore how designers adapt Art Deco motifs from traditional Scottish sources, such as intricate geometric patterns and natural elements.\n4. Urban Scotland Wallpapers: Uncover modern interpretations of urban landscapes in Scottish wallpaper designs, capturing the unique character of cities like Glasgow or Edinburgh.\n5. Transforming Traditional Patterns: Discover how designers modify traditional Scottish motifs, creating innovative and fresh wallpaper patterns for modern interiors.\n6. Scottish Coastal Themes: Delve into the world of coastal-inspired contemporary Scottish wallpapers, evoking the beauty of Scotland's sea and sandy shores.\n7. Incorporating Modern Technology: Explore how modern wallpaper printing techniques are used to recreate traditional Scottish designs with enhanced vibrancy and intricacy.\n8. Scottish Wallpapers in International Design: Trace the influence of Scottish wallpaper designs on international contemporary interiors, as designers draw inspiration from Scotland's rich heritage.\n9. Sustainability in Modern Scottish Wallpapers: Delve into how designers incorporate sustainability practices in their modern interpretations of traditional Scottish wallpaper motifs and patterns.\n10. Collaborative Design Projects: Uncover collaborative design projects where contemporary artists and architects work together to create unique, modern Scottish wallpapers that blend history with innovation.	\N	\N	\N	\N	\N	\N	Explore how modern designers are inspired by traditional Scottish motifs, keeping the legacy alive in contemporary interiors.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n\n<body>\n    <p>Scottish wallpaper designs hold a captivating allure in contemporary interior design. Traditional motifs, celebrated for their uniqueness in Scottish homes during the 18th and 19th centuries, inspire modern designers.</p>\n\n    <p>Botanical prints draw from Scotland's rich natural heritage. These patterns are adapted in fresh and innovative ways on walls.</p>\n\n    <p>Art deco motifs pay homage to Scottish artisanal craftsmanship with geometric lines and vibrant hues.</p>\n\n    <p>Modern designers experiment with tartan patterns, blending them with abstract designs and global influences.</p>\n\n    <p>Digital technology revolutionises wallpaper production, allowing near-limitless possibilities for intricate pattern creation.</p>\n</body>\n\n</html	In the contemporary realm of interior design, Scottish wallpaper designs continue to cast a captivating spell. Traditional motifs, once celebrated for their distinctiveness in Scottish homes during the 18th and 19th centuries, have inspired modern designers to breathe new life into these timeless patterns.\n\nBotanical prints, an enduring favorite drawn from Scotland's rich natural heritage, adorn walls in fresh and innovative ways. Art deco motifs, with their geometric lines and vibrant hues, pay homage to the grandeur of Scottish artisanal craftsmanship. These modern adaptations carry a sense of nostalgia while forging a connection with contemporary aesthetics.\n\nModern designers reimagine traditional tartan patterns by experimenting with color palettes or incorporating them into abstract designs, blurring the line between heritage and innovation. They skillfully blend these Scottish motifs with global influences, creating interiors that resonate with a diverse audience.\n\nFurthermore, digital technology has revolutionized wallpaper production, enabling near-limitless possibilities for designers to create and recreate intricate patterns inspired by Scotland's cultural tapestry. This technological advancement empowers artists to preserve the legacy of Scottish wallpaper designs while pushing the boundaries of design and craftsmanship.\n\nIn essence, modern adaptations of Scottish wallpaper designs serve as a testament to the enduring appeal and influence of this unique aspect of Scotland's rich cultural heritage.	\N	\N
691	22	4	From Oral Tradition to Written Word: The Evolution of Scottish Literature	* The Transition from Oral Poetry to Written Verse: Early Scottish Poets and their Manuscripts\n* Scribes and Illuminated Manuscripts: Preserving Scotland's Early Literary Heritage\n* The Influence of Latin Learning on Scottish Writers in the Middle Ages\n* The Renaissance: Scottish Humanists and the Classics\n* Printing Presses and Mass Production of Literature in Scotland\n* The Scottish Enlightenment: Writers, Ideas, and Impact\n* Romanticism: Scotland's Poets and their Landscapes\n* 19th-century Scottish Authors: A Literary Golden Age?\n* Modern Scottish Writers: From MacDiarmid to Rankin\n* The Future of Scottish Literature: New Voices and Innovative Forms	\N	\N	\N	\N	\N	\N	Trace the development of written literature from oral tradition.	draft	<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>Ancient Celtic Storytelling in Scotland</title>\n</head>\n<body>\n  <p>In ancient Scotland, storytelling held significant importance in preserving history and cultural values, deeply intertwined with the Celtic traditions and mythology.</p>\n  <p>The Celts, who inhabited Scotland around 800 BC, employed storytelling as a means to shape modern Scottish narratives. Their oral tradition, rich in mythical creatures like Selkies, kelpies, and shape-shifters, influenced modern Scottish stories.</p>\n  <p>Ancient Celts' tales were filled with symbolism, often representing natural elements or moral values, which remains relevant in contemporary literature.</p>\n  <p>Druids and bards served as spiritual leaders, ensuring the preservation and passing down of oral traditions through generations. Celtic festivals like Samhain, Beltane, and Imbolc were integral to storytelling, creating communal spaces for sharing ancient tales.</p>\n  <p>Ancient Celtic texts, such as the Ulster Cycle and Fenian Cycles, provide insights into heroes and warriors of yore. Their battles and conquests shaped modern Scottish identity.</p>\n  <p>The mystical realm of the Celtic Otherworld inspired folklore and mythology, blurring the lines between reality and fantasy.</p>\n  <p>Modern scholars interpret ancient Celtic texts with sensitivity, revealing their historical significance and contemporary relevance.</p>\n  <p>European cultures show both similarities and differences in storytelling traditions during this period. However, the unique aspects of Scottish folklore continue to captivate audiences today.</p>\n  <p>Ancient Celtic stories' enduring influence is evident in modern adaptations like "The Golden Bough" by James Frazer and Disney's animated film "Brave."</p>\n</body>\n</html	The evolution of Scottish literature is deeply rooted in the ancient Celtic oral tradition. Ancient Celts shaped modern Scottish narratives through their storytelling, passing down tales that included mythical creatures like Selkies, shape-shifters, and Kelpies (1). These beings continue to intrigue and inspire contemporary Scottish stories.\n\nSymbolism played a significant role in ancient Celtic storytelling, representing various aspects of nature, faith, and life (2). Druids and bards were the spiritual leaders who preserved these oral traditions through generations, with their oral recitations passed down from teacher to student.\n\nCeltic festivals like Samhain, Beltane, and Imbolc were integral to Scottish storytelling, serving as occasions for sharing tales of heroes and warriors, such as Fingal and Oisin (3). The Celtic Otherworld, a mystical realm inspired by the afterlife, heavily influenced Scottish folklore and mythology.\n\nModern scholars continue to interpret ancient Celtic texts like the Ulster Cycle and Fenian Cycles, providing insights into the rich storytelling heritage of Scotland (4). Comparing these stories with those of other European cultures reveals both similarities and differences in their evolution (5).\n\nAncient Celtic stories have continued to inspire modern adaptations, from James Frazer's "The Golden Bough" to Disney's animated film "Brave," demonstrating the lasting impact of this ancient tradition on contemporary storytelling.	\N	\N
702	45	1	Origins of Scottish Wallpaper Manufacturing	1. The emergence of wallpaper production in Lanarkshire: A brief overview of the region's geographical advantages and resources that facilitated the industry's birth.\n2. European influences on Scottish wallpaper design: Exploring the impact of Dutch, French, and English decorative arts on early Scottish wallpaper manufacturing.\n3. Notable figures in Lanarkshire's wallpaper trade: Profiling pioneering entrepreneurs who established Scotland's wallpaper industry during the 1700s.\n4. The humble beginnings of hand-painted wallpaper: An insight into the laborious process of creating intricate patterns using natural pigments and brushes.\n5. Watermarks and signatures on early Scottish wallpapers: Uncovering the significance of these elements in authenticating the provenance and origin of historic designs.\n6. The role of waterways in transporting raw materials and finished products: Delving into the importance of Scotland's extensive network of rivers and canals for trade during this period.\n7. Skilled artisans' workshops: Describing the traditional methods used by master craftspeople to create wallpaper patterns in their studios or homes.\n8. The rise of factories and mechanization: Examining how the introduction of steam-powered machinery revolutionized wallpaper manufacturing processes.\n9. Preserved wallpapers as historical records: Highlighting the importance of these fragments as material evidence of Scotland's rich decorative arts heritage.\n10. Revival of 18th-century Scottish wallpaper techniques: Describing modern workshops and studios where traditional skills are being passed down to future generations.	\N	\N	\N	\N	\N	\N	Explore the roots of Scotland's wallpaper industry in Lanarkshire and European influences during the 18th century.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n\n<body>\n    <p>In the 18th century heart of Lanarkshire, Scotland, emerged a unique industry: wallpaper manufacturing. Artisans drew inspiration from European techniques in small workshops and studios.</p>\n    <p>Hand-painting intricate patterns onto paper or linen were their methods. Natural Scottish landscapes influenced early designs, featuring motifs of heather, thistles, and forests.</p>\n    <p>As demand increased, skilled craftspeople and manufacturers arose. Rutherglen, a port town, became a hub due to its export capabilities across the UK and Europe.</p>\n    <p>Technological advances, like steam-powered printing presses, transformed production in the late 1800s, leading to increased efficiency and design variety.</p>\n</body>\n\n</html	In the heart of Lanarkshire during the 18th century, Scotland witnessed the birth of a distinctive industry – wallpaper manufacturing. This burgeoning trade took inspiration from European influences, with craftspeople and manufacturers drawing on techniques honed across the continent.\n\nThe origins of Scottish wallpaper can be traced back to small workshops and studios where artisans hand-painted intricate patterns onto lengths of paper or linen. The natural beauty of Scotland's landscapes influenced these early designs, with motifs of heather, thistles, and forests adorning the walls of homes.\n\nThe industry began to flourish as demand for these decorative coverings grew, giving rise to skilled craftspeople and manufacturers. Notably, the port town of Rutherglen became a significant hub for wallpaper production due to its strategic location for exporting goods across the UK and Europe. With each passing decade, advances in technology, such as steam-powered printing presses, revolutionised the production process, allowing for greater efficiency and variety in designs.\n\nThese early innovations set the stage for a thriving trade that would shape Scottish interiors, providing a unique thread in the rich tapestry of Scotland's cultural heritage.	\N	\N
692	22	5	The Intersection of Storytelling, Folklore, and Mythology	Topic 1: The Selkies and the Sea: Unraveling the Connection between Mythology and Folktales\nTopic 2: Transforming Tales: A Look into the Alchemical Process of Storytelling and Myth-Making\nTopic 3: Mythic Origins of Scottish Landmarks: The Role of Folklore in Shaping Cultural Narratives\nTopic 4: Deities, Dragons, and Damsels: Exploring the Interwoven Worlds of Scottish Mythology and Folk Tales\nTopic 5: Weaving the Threads of Storytelling, Folklore, and Mythology: An Analytical Approach\nTopic 6: The Power of Symbolism: Examining Common Motifs in Scottish Storytelling, Folklore, and Mythology\nTopic 7: The Evolution of Scottish Myths and Legends: A Journey from Oral Tradition to Written Texts\nTopic 8: The Bard's Ballad: How Folk Tales and Mythology Inspired Scotland's Literary Greats\nTopic 9: Mythic Music: The Influence of Scottish Folklore and Mythology on Traditional Musical Compositions\nTopic 10: Modern Interpretations of Scottish Mythology and Folktales: Preserving Cultural Narratives for Future Generations	\N	\N	\N	\N	\N	\N	Explore the connections between storytelling, folklore, and mythology in Scottish culture.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n</head>\n\n<body>\n\n <p>In ancient Scotland, storytelling was essential for preserving history and cultural values, grounded in Celtic traditions and mythology. The Celts, inhabitants around 800 BC, used storytelling to form modern Scottish narratives.</p>\n\n <p>Their oral tradition, filled with mythical creatures like Selkies, kelpies, and shape-shifters, shaped contemporary Scottish stories. These beings, woven into ancient tales, continue to enthrall audiences today. Symbolism in these stories, frequently representing natural elements or moral values, remains pertinent in modern literature.</p>\n\n <p>Druids and bards served as spiritual leaders, maintaining the preservation and transmission of oral traditions through generations.</p>\n\n <p>Celtic festivals such as Samhain, Beltane, and Imbolc were integral to storytelling, fostering shared spaces for ancient tale exchanges.</p>\n\n <p>Ancient Celtic texts, like the Ulster Cycle and Fenian Cycles, provide insights into heroes and warriors of the past. Their tales of battles and conquests have influenced modern Scottish identity.</p>\n\n <p>The mystical realm of the Celtic Otherworld inspired folklore and mythology, merging reality and fantasy.</p>\n\n <p>Modern scholars interpret ancient Celtic texts with care, revealing their historical significance and contemporary relevance. European cultures showcase both similarities and differences in storytelling traditions during this era, underscoring the unique aspects of Scottish folklore.</p>\n\n</body>\n\n</html	In Scottish culture, the interconnected threads of storytelling, folklore, and mythology are deeply rooted in ancient Celtic traditions. The Celts, who inhabited Scotland from around 900 BC, left an indelible mark on modern Scottish narratives.\n\nThe ancient Celts shaped modern Scottish stories through their oral tradition. Mythical creatures like Selkies, shape-shifters, and kelpies, which continue to fascinate contemporary audiences, originated from this rich storytelling heritage. These beings, imbued with magical powers, populate numerous Celtic tales.\n\nSymbolism played a significant role in ancient Celtic storytelling. For instance, the triple spiral design found in many Scottish stone carvings and the oak tree as a symbol of strength and rebirth carry contemporary relevance. These symbols have continued to inspire and shape modern Scottish narratives.\n\nDruids and bards held immense importance within Celtic society. As spiritual leaders, they were responsible for preserving and passing down oral traditions through generations. Their role in weaving stories became a vital part of Celtic culture.\n\nCeltic festivals like Samhain, Beltane, and Imbolc celebrated the changing seasons and marked significant moments in the agricultural calendar. Storytelling was an integral part of these celebrations, fostering community bonds and strengthening cultural ties.\n\nAncient Celtic tales of heroes and warriors, such as Fingal and Oisin or epic battles like the Battle of the Trees, have left a lasting impact on Scottish storytelling. The mystical realm of the Otherworld, where the supernatural and divine resided, served as an essential source of inspiration for countless folktales and myths.\n\nModern scholars study ancient Celtic texts like the Ulster Cycle and the Fenian Cycles to unravel their meanings and interpret them in contemporary contexts. The interconnections between ancient Celts and other European cultures, particularly in storytelling traditions, also provide valuable insights into our shared past.\n\nToday, we see modern adaptations of ancient Celtic stories in various forms – from literature like James Frazer's "The Golden Bough" to popular films like "Brave." These reinterpretations continue to enrich and expand the world of Scottish storytelling.	\N	\N
688	22	0	Scottish Storytelling: An Ancient Celtic Heritage	1. The Role of Ancient Celts in Scottish Oral Tradition: An exploration of how ancient Celts' storytelling shaped modern Scottish narratives.\n2. Mythical Creatures in Celtic Mythology: A deep dive into popular mythical creatures like the Selkies, kelpies, and shape-shifters.\n3. The Use of Symbolism in Ancient Celtic Storytelling: Uncovering the significance of symbols in ancient Scottish stories and their contemporary relevance.\n4. Druids and Bards: The importance of these spiritual leaders in preserving and passing down oral traditions through generations.\n5. Celtic Festivals and Storytelling: How storytelling was an integral part of traditional Scottish celebrations like Samhain, Beltane, and Imbolc.\n6. Ancient Celtic Tales of Heroes and Warriors: From legendary figures like Fingal and Oisin to the epic tales of battles and conquests.\n7. The Celtic Otherworld and its Influence on Scottish Storytelling: Investigating how this mystical realm inspired Scottish folklore and mythology.\n8. Interpreting Ancient Celtic Texts: A discussion on how modern scholars translate and interpret ancient Celtic texts, such as the Ulster Cycle and the Fenian Cycles.\n9. The Relationship Between Ancient Celts and Other European Cultures: Highlighting similarities and differences in storytelling traditions across Europe during this period.\n10. Modern Adaptations of Ancient Celtic Stories: From literature like "The Golden Bough" by James Frazer to popular films like "Brave," how ancient Celtic stories continue to influence modern storytellers.	\N	\N	\N	\N	\N	\N	Explore the origins of Scottish storytelling in ancient Celtic traditions and mythology.	draft	It seems like you have typed "test" without any specific context. If you meant to ask a question or provide some context, please do so and I'll be happy to help you out!\n\nIf you were asking for information about testing in general, testing is an important process of evaluating a product, system or software to determine if it meets the specified requirements or functions correctly. Testing can help identify defects, ensure compatibility with other systems or applications, and improve overall quality before releasing the product to the market.\n\nThere are various types of testing such as functional testing, regression testing, load testing, performance testing, security testing, and many others depending on the specific needs and goals of the project. It's important to design a comprehensive test strategy that covers all aspects of the system or application to ensure its reliability, usability, and maintainability.	 Title: "50 Fascinating Facts about Scotland's Rich History and Culture"\n\n1. Scotland is the northernmost country in the United Kingdom, with an area of around 30,414 square miles (78,772 square kilometers).\n2. The capital city of Scotland is Edinburgh, famous for its iconic castle and annual international festival.\n3. Scotland's national animal is the unicorn, although it's a mythical creature; the real national animals are the red deer and the golden eagle.\n4. Scotland has produced four Kings who ruled as monarchs of England: Malcolm III Canmore (1058–1093), David I (1124–1153), Robert II (1371–1390), and James VI (1567–1625).\n5. Scotland's national flag, the Saltire or St Andrew's Cross, features the white diagonal cross of St Andrew on a blue background.\n6. The first university in Scotland was the University of St Andrews, founded around 1413.\n7. Scotland is home to over 800 castles and fortresses, including the iconic Edinburgh Castle and Stirling Castle.\n8. Scotch whisky, a protected product worldwide, has been produced for over 500 years.\n9. The Scottish national dress includes the kilt, which comes in various tartans representing different clans.\n10. Scotland's landscape varies greatly, from mountains and lochs to rolling hills and sandy beaches.\n11. The Loch Ness Monster is a legendary creature said to inhabit Loch Ness in the Highlands.\n12. Scotland gave the world golf – the oldest known rules for playing golf were published in Scotland in 1457.\n13. Stonehenge, though primarily associated with England, may have been built by Scottish architects, as evidenced by a stone with a depiction of the Aberdeen Angus bull carved on it found at the site.\n14. Scotland's national poet Robert Burns (1759–1796) wrote "Auld Lang Syne," a poem that has become a popular New Year song around the world.\n15. Scotland was one of the first countries in Europe to adopt Christianity, as St Columba brought it to the region in 563 AD.\n16. Scotland is home to several UNESCO World Heritage Sites, including the Heart of Neolithic Orkney and New Lanark.\n17. The Stone of Destiny (also called the Stone of Scone) has been used for the coronation of Scottish monarchs since ancient times and was taken to England in 1296 before being returned in 1996.\n18. Scotland's national dish is haggis, a savory pudding containing sheep's heart, liver, and lungs mixed with onions, oatmeal, and spices.\n19. The Great Seal of Scotland, created in the late 13th century, is one of Europe's oldest national seals.\n20. Scotland's currency is the pound sterling (GBP), shared with England, Wales, and Northern Ireland.\n21. Robert the Bruce, who became King of Scots in 1306, led a successful resistance against Edward I of England, earning him the nickname "The Braveheart."\n22. Scotland's national tree is the Scot's pine (Pinus sylvestris), but the country is home to many other tree species.\n23. The famous Scottish poet and philosopher Thomas A. Clark once wrote, "There is a land of the living, and a land of the dead." Modern Scotland is the former.\n24. Scotland was the first European nation to grant women the right to vote in all parliamentary elections.\n25. Scotland has eight universities, including the University of Glasgow and University of Aberdeen.\n26. Scotland's longest river is the River Tay, which measures about 117 miles (188 kilometers).\n27. Mary, Queen of Scots (1542–1587) was a historical queen of Scotland and later of France. She ruled Scotland from 1542 to 1603.\n28. The Scottish Clans System is based on ancient family ties that can be traced back for centuries, often with their own distinctive tartans and symbols.\n29. Scotland's national bird is the osprey (Pandion haliaetus), which was reintroduced to Scotland in the late 1950s after being extinct for around 170 years.\n30. The Scottish Highlands are home to many ancient monuments, including standing stones and brochs, that predate recorded history.\n31. The famous Scottish poet William Shakespeare (1564–1616) has a connection to Scotland: his mother was from the kingdom.\n32. The first modern oil discovery in Europe occurred in 1897 at Lochaber in Scotland.\n33. Scotland's national sport is shinty (also known as camanachd), which combines elements of soccer, hockey, and rugby.\n34. Scotland is the birthplace of many famous writers, including J.K. Rowling (author of Harry Potter) and Robert Louis Stevenson (author of Treasure Island).\n35. The Scottish Borders are home to several iconic castles, including Jedburgh Castle and Melrose Abbey.\n36. Scotland's national flower is the thistle, which has prickly leaves and purple flowers.\n37. Scotland has over 790 islands, with some of the most famous being Skye, Arran, Mull, and Lewis.\n38. The Scottish Gaelic language still plays an important role in Scottish culture, with around 1% of the population speaking it fluently.\n39. Scotland's national instrument is the bagpipes, which have a distinctive sound and are often associated with military and ceremonial occasions.\n40. Scotland's geology is diverse, with numerous rock formations, volcanic outcrops, and unique landscapes such as the Isle of Skye.\n41. Scotland has a rich literary tradition, with many famous authors from Robert Louis Stevenson to J.K. Rowling.\n42. Scotland's national drink is whisky, which is produced in various regions across the country using traditional methods.\n43. The Scottish National Portrait Gallery in Edinburgh houses an extensive collection of portraits and sculptures of notable Scots throughout history.\n44. Scotland is home to several important historical figures, such as Mary Queen of Scots, William Wallace, and Robert the Bruce.\n45. Scotland's national emblem includes a unicorn, a lion rampant, and a harp.\n46. The Scottish National Museum in Edinburgh explores the history and culture of Scotland through various exhibits and collections.\n47. Scotland's rich folklore includes tales of magical creatures such as elves, fairies, and kelpies.\n48. Scotland is home to several important prehistoric sites, including Skara Brae in Orkney and the Standing Stones of Stenness.\n49. Scotland's climate varies from region to region, with some areas experiencing temperate rainforest conditions while others have a more arid climate.\n50. Scotland's natural wonders include the Northern Lights, which can be seen in the far north during certain seasons.	\N	\N
714	53	4	Evolution of Scottish Story-telling: Modern Era	Topic 1: The Radio Revolution - Origins of Scottish Radio Broadcasting and its impact on story-telling\nTopic 2: The Birth of the Scottish Comics Industry - From "The Broons" to "Watchmen"\nTopic 3: The Role of Scottish Story-telling in Video Games - From "Grand Theft Auto" to "Deus Ex"\nTopic 4: The Rise of Scottish Podcasts - A new era for oral story-telling and folklore\nTopic 5: Transatlantic Connections: Scottish writers' influence on American literature and pop culture\nTopic 6: Adaptations and Remakes: Modern takes on ancient Celtic tales, from "Braveheart" to "Outlander"\nTopic 7: The Impact of Social Media on Scottish Story-telling - From fan fiction to viral sensations\nTopic 8: Scottish Story-telling in the Digital Age: E-books, audiobooks, and beyond\nTopic 9: Multimedia Story-telling: Merging art, literature, and technology in contemporary Scotland\nTopic 10: Ongoing Traditions - How modern story-tellers continue to preserve Scotland's rich heritage through their craft	\N	\N	 Based on the input, I suggest an image that illustrates the evolution of Scottish storytelling from the modern era to the present day. The image should focus on a bookshelf as its main feature, symbolizing the wealth of Scottish literature throughout history.\n\nLayout: The image consists of a well-lit, wooden bookshelf filled with books, arranged in an orderly manner to depict the passage of time. The bookshelf spans from left to right, with the older books at the back and the newer ones at the front.\n\nKey Features: The older books have leather covers with intricate designs, signifying ancient Celtic tales and medieval ballads. As we move towards the newer books, the covers become more modern, with dust jackets featuring famous Scottish authors like Robert Louis Stevenson and J.M. Barrie. A few books near the front are replaced by tablets or e-readers, symbolizing digital media and podcasts.\n\nBackground: The background of the image is a simple, neutral tone that does not distract from the bookshelf. To maintain the focus on Scottish storytelling, there are subtle elements in the background, such as thistles (the national flower of Scotland) or a tartan pattern, adding to the overall Scottish theme without being overbearing.\n\nAccessories: A few accessories can be added to further emphasize the evolution of storytelling. For instance, an old radio or a vinyl record on a small table next to the bookshelf represent early forms of technology that brought stories to a wider audience. Additionally, a laptop or tablet with headphones symbolizes contemporary digital media. A television in the background can also be included to represent film and television productions.\n\nOverall, this image effectively illustrates the evolution of Scottish storytelling while avoiding clichés, romance, and multiculturalism as per the requirements. It maintains a clear focus on the topic and creates an engaging visual that is suitable for a blog article.	 Image description: A well-lit, wooden bookshelf stretches from left to right, filled with a chronological arrangement of books. Older books at the back boast leather covers adorned with intricate Celtic designs, representing ancient Scottish tales and medieval ballads. As the focus shifts towards the front, covers transform into modern dust jackets, showcasing works by renowned authors like Robert Louis Stevenson and J.M. Barrie. A few books are replaced with tablets or e-readers, symbolizing digital media and podcasts. In the background, subtle Scottish elements - thistles and tartan - subtly complement the scene without overpowering it. Accessories include an old radio, a vinyl record, a laptop, and a television, representing various forms of technology that carried stories through time. The bookshelf's evolution is a testament to the rich heritage of Scottish storytelling.	\N	 Image Idea:\n\nTitle: "Modern Scottish Storytelling Mosaic"\n\nDescription:\nThis image is a vibrant, colorful mosaic that showcases the various forms of modern Scottish storytelling. At the center of the mosaic is an open book with the title "Evolution of Scottish Storytelling: Modern Era," symbolizing the evolution and transformation of storytelling in Scotland throughout history.\n\nSurrounding the central book are intricate, multicolored tiles representing different aspects of modern Scottish storytelling. These tiles depict various scenes from novels like "Treasure Island" and "Peter Pan," radio microphones symbolizing the radio revolution, comic strips featuring characters from "The Broons" and "Watchmen," a television set displaying scenes from film and television productions, podcast logos, and digital devices such as tablets and laptops.\n\nAt the edges of the mosaic, there are depictions of transatlantic connections between Scottish writers and American literature, adaptations and remakes of ancient Celtic tales, social media icons like Facebook and Twitter, and a digital clock representing the impact of storytelling in the digital age.\n\nThe overall layout of the image is visually engaging, with each tile offering a unique glimpse into various aspects of modern Scottish storytelling while still blending seamlessly within the larger mosaic design. The intricate, colorful details capture the viewer's attention and highlight the richness and diversity of this cultural tradition in Scotland.	A look into how story-telling continued to evolve in the modern era, giving birth to various mediums such as novels, podcasts, film and television productions.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n\n<body>\n    <p>In the modern era, Scottish story-telling evolved. Novels like those by Robert Louis Stevenson and J.M. Barrie shaped Scottish literature and left a global impact. Their works were filled with adventure, magic, and strong place elements.</p>\n    <p>Radio broadcasts in the early 20th century made oral story-telling more accessible. Later, podcasts and digital media continued this tradition.</p>\n    <p>Visual story-telling flourished. Films and television brought ancient Celtic tales and medieval ballads to life on the big screen.</p>\n    <p>These adaptations entertained audiences and introduced new generations to Scotland's rich story-telling heritage.</p>\n    <p>Today, story-telling remains a vital part of Scottish culture. It shapes our national identity and inspires creativity for future generations.</p>\n</body>\n\n</html	In the modern era, Scottish story-telling continued to evolve, adapting to new mediums and reaching wider audiences. Novels became a popular form of expression, with authors like Robert Louis Stevenson and J.M. Barrie leaving an indelible mark on both Scottish literature and the world at large. Their works, filled with adventure, magic, and a strong sense of place, captivated readers with their intriguing narratives.\n\nAs technology advanced, story-telling began to take new forms. In the early 20th century, radio broadcasts introduced listeners to the art of oral story-telling in a more accessible way than ever before. Later, podcasts and digital media continued this tradition, offering listeners a diverse range of stories that could be accessed anywhere, anytime.\n\nVisual story-telling also flourished during the modern era, with film and television productions bringing ancient Celtic tales and medieval ballads to life on the big screen. These adaptations not only entertained audiences but also introduced new generations to Scotland's rich story-telling heritage. Today, story-telling remains a vibrant part of Scottish culture, continuing to shape our national identity and inspire creativity for generations to come.	scottish_section_714,_realisti_20250726_134937_1bda4e.png	2025-07-26 13:49:39.768706
690	22	3	Storytelling as Social Norms: Traditions and Tales	1. The Significance of Tales in Early Scottish Societies: Explore how stories served as a means of communication and social cohesion among early Celtic communities.\n2. Healing Stories: Delve into the role of storytelling in Scottish folk medicine, including tales that explained the cause and cure of various ailments.\n3. Funeral Rituals and Storytelling: Investigate how stories were incorporated into funerals and memorial services to pass on traditions and values.\n4. Agricultural Tales: Discover the connection between farming practices and storytelling, including tales that explained the importance of seasons and weather patterns.\n5. The Art of Storytelling in Daily Life: Examine how stories were a integral part of daily life in Scottish communities, from telling bedtime stories to passing on traditions during mealtimes.\n6. Storytelling and Marriage Customs: Explore the role of storytelling in Scottish marriage traditions, including tales that explained the importance of matchmaking and courtship rituals.\n7. Tales of Heroes and Villains: Delve into stories about legendary figures who embodied societal values or challenged social norms, such as heroic warriors or cunning tricksters.\n8. Storytelling in Education: Investigate how storytelling was used to teach children important skills and knowledge, from learning the alphabet to understanding moral values.\n9. Storytelling and Community Building: Delve into the role of storytelling in creating a sense of community and identity within Scottish societies, both historically and in contemporary times.\n10. The Impact of Religion on Storytelling: Explore how religious beliefs influenced the content and form of stories told within Scottish communities, from religious parables to saints' legends.	\N	\N	\N	\N	\N	\N	Investigate the role of storytelling in shaping social norms and cultural traditions.	draft	<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n    <title>Ancient Celtic Storytelling in Scotland</title>\n  </head>\n  <body>\n    <p>\n      In ancient Scotland, storytelling played a crucial role in preserving history and cultural values rooted in the Celtic traditions and mythology. The Celts inhabited Scotland around 800 BC and employed storytelling to shape modern Scottish narratives.\n    </p>\n\n    <p>\n      The ancient Celts' oral tradition, rich in mythical creatures like Selkies, kelpies, and shape-shifters, significantly influenced modern Scottish stories. These beings, woven into ancient tales, continue to captivate audiences today. Symbolism in these stories, often representing natural elements or moral values, remains relevant in contemporary literature.\n    </p>\n\n    <p>\n      Druids and bards served as spiritual leaders, ensuring the preservation and passing down of oral traditions through generations. Celtic festivals like Samhain, Beltane, and Imbolc were integral to storytelling, creating communal spaces for sharing ancient tales.\n    </p>\n\n    <p>\n      Ancient Celtic texts, such as the Ulster Cycle and Fenian Cycles, offer insights into heroes and warriors of yore. Their tales of battles and conquests have shaped modern Scottish identity. The mystical realm of the Celtic Otherworld inspired folklore and mythology, blurring the lines between reality and fantasy.\n    </p>\n\n    <p>\n      Modern scholars interpret ancient Celtic texts with sensitivity, uncovering their historical significance and contemporary relevance. European cultures show both similarities and differences in storytelling traditions during this period, highlighting unique aspects of Scottish folklore.\n    </p>\n  </body>\n</html	In ancient Scotland, storytelling played a significant role in shaping social norms and cultural traditions, with roots deeply embedded in the Celtic heritage. The Celts, an early people inhabiting the land, wove intricate narratives that continue to influence modern Scottish stories.\n\nMythical creatures like Selkies, transforming from seals into humans, Kelpies, water horses, and shape-shifters populated their tales. These beings reflect the Celts' connection to nature and the supernatural. Ancient Celtic storytelling employed symbolism profoundly, as seen in the use of the triquetra knot representing the interconnectedness of life, love, and faith.\n\nDruids and bards served as spiritual leaders who preserved and passed down these oral traditions through generations. Their role extended beyond religious functions to include storytelling during Celtic festivals such as Samhain, Beltane, and Imbolc. These celebrations were integral to life, marking the changing seasons and reinforcing social norms.\n\nAncient Celtic tales of heroes and warriors, like Fingal and Oisin, and epic battles and conquests, showcased courage, loyalty, and honor – virtues still cherished in Scottish society today. The mystical realm of the Otherworld, a place of enchantment and magic, further fueled the imagination and inspired much of Scottish folklore and mythology.\n\nModern scholars interpret ancient Celtic texts, like the Ulster Cycle and Fenian Cycles, to gain insights into this rich storytelling tradition. Comparing these tales with those from other European cultures reveals similarities and differences that contribute to our understanding of early European societies.\n\nThe influence of ancient Celtic stories extends beyond academia; they continue to inspire modern adaptations in literature, like "The Golden Bough" by James Frazer, and popular films such as "Brave." In essence, storytelling is an enduring thread that binds the past and present of Scottish culture.	\N	\N
689	22	1	The Role of Storytelling in Preserving History	Topic 1: The Significance of Oral Storytelling in Recording Historical Events\nTopic 2: The Ballads of William Wallace and Robert the Bruce: Historical Narratives in Scottish Music\nTopic 3: The Role of Storytelling in Chronicling Scotland's Ancient Battles\nTopic 4: The Tale of Mary, Queen of Scots: Documenting Historical Women in Scottish Stories\nTopic 5: The Importance of Bardic Poets and their Historiographical Roles\nTopic 6: How Storytelling Preserved the Legacy of Scotland's Saints and Martyrs\nTopic 7: Folk Tales as Reflections of Historical Moments: The Potato Famine and Clearances\nTopic 8: Storytelling as a Tool for Cultural Memory: Keeping Scottish Jewish History Alive\nTopic 9: The Impact of the Printing Press on Scottish Historiography and Storytelling\nTopic 10: The Role of Storytelling in Preserving Scotland's Architectural Heritage.	\N	\N	\N	\N	\N	\N	Understand how stories have been used to document historical events and cultural values.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n</head>\n\n<body>\n\n <p>In ancient Scotland, storytelling held significant importance in preserving history and cultural values, deeply rooted in the Celtic traditions and mythology. The Celts, inhabiting Scotland around 800 BC, utilized storytelling as a means to shape modern Scottish narratives.</p>\n\n <p>The Celts' oral tradition, rich in mythical creatures like Selkies, kelpies, and shape-shifters, influenced modern Scottish stories. These beings, woven into ancient tales, continue to captivate audiences today. The use of symbolism in these stories, representing natural elements or moral values, remains relevant in contemporary literature.</p>\n\n <p>Druids and bards served as spiritual leaders, ensuring the preservation and passing down of oral traditions through generations. Celtic festivals like Samhain, Beltane, and Imbolc were essential to storytelling, creating communal spaces for sharing ancient tales.</p>\n\n <p>Ancient Celtic texts, such as the Ulster Cycle and Fenian Cycles, provide insights into heroes and warriors of yore. Their tales of battles and conquests have shaped modern Scottish identity. The mystical realm of the Celtic Otherworld inspired folklore and mythology, blurring the lines between reality and fantasy.</p>\n\n <p>Modern scholars interpret ancient Celtic texts with sensitivity, uncovering their historical significance and contemporary relevance. Comparatively, European cultures exhibited both similarities and differences in storytelling traditions during this period, emphasizing the unique aspects of Scottish folklore.</p>\n\n <p>The enduring influence of ancient Celtic stories is evident in modern adaptations like "The Golden Bough" by James Frazer and Disney's animated film "Brave". These interpretations continue to shape contemporary Scottish storytelling.</p>\n\n</body>\n\n</html	 Title: "50 Fascinating Facts About Scotland's Rich History and Culture"\n\n1. Scotland is home to the oldest continually inhabited city in Europe, Perth, founded around 3,000 years ago.\n2. The Scottish flag, or Saltire, features two diagonal white stripes on a blue background, representing the victory of St Andrew over the Saxons in AD 832.\n3. Scotland was the first European country to recognize the United States as an independent nation.\n4. Bagpipes, a symbol of Scottish culture, were originally used for communication between clans and soldiers.\n5. Scotland has more castles than any other country in Europe - over 3,000!\n6. The world's oldest working lighthouse is located on the Isle of May, off the Fife coast.\n7. The Scottish Highlands are home to one-third of Britain's rare and endangered species.\n8. Scotland has a long tradition of whisky production, dating back over 500 years.\n9. Inverness is the northernmost city in the UK and is said to be where Columba, the first Scottish saint, converted Pictish tribes to Christianity.\n10. The Stone of Destiny, or Lia Fail, was believed to have been used for centuries as the coronation stone of Scottish monarchs.\n11. Scotland has a deep connection to the Vikings, with over 800 Norse place names found throughout the country.\n12. Mary, Queen of Scots, was a significant queen regnant in Scotland from 1542 to 1567 and later a claimant to the English throne.\n13. The Scottish language, Gaelic, has fewer than 60,000 speakers, making it one of Europe's most endangered languages.\n14. The famous Loch Ness Monster is a mythical creature said to inhabit the waters around Inverness-shire, Scotland.\n15. Scotland was once part of a larger kingdom called Alba, whose name later became Scotland.\n16. The first known written records in Scottish Gaelic date from 1116.\n17. Scotland's highest mountain, Ben Nevis, reaches a height of 1,345 meters (4,409 feet).\n18. The Scottish National Portrait Gallery in Edinburgh is home to over 17,000 portraits.\n19. The famous poem "Tam O' Shanter" by Robert Burns features a supernatural event at the Ayrshire village of Alloway.\n20. The world record for longest-running military tattoo is held by the Edinburgh Military Tattoo, which began in 1950.\n21. Scotland was home to the first known human footprints in Europe, discovered on the island of South Uist.\n22. Scotland's national animal is the unicorn. While unicorns are mythical creatures, they symbolize strength, purity, and wisdom.\n23. Scotland has a diverse literary heritage, with authors such as Robert Louis Stevenson, J.K. Rowling, and Sir Walter Scott.\n24. The Scottish Borders were once part of the Roman Empire's frontier territory, known as Hadrian's Wall.\n25. Scotland is home to one-third of Europe's fresh water resources.\n26. The Scottish Enlightenment, a period of intellectual and scientific advances in the late 17th and 18th centuries, gave the world influential thinkers such as David Hume and Adam Smith.\n27. Scotland was home to the first university in Europe, founded in St Andrews around AD 1413.\n28. The Scottish National Gallery in Edinburgh is home to over 50,000 works of art.\n29. The famous poet Robert Burns wrote "Auld Lang Syne," a song traditionally sung at the stroke of midnight on New Year's Eve.\n30. The world-famous Glenfiddich whisky distillery is located in Dufftown, Banffshire.\n31. Scotland has over 790 islands, with only around 130 inhabited.\n32. Scottish clans were once led by chieftains who made decisions for their people based on ancestral traditions and knowledge.\n33. The world's first recorded game of golf was played at the Old Course in St Andrews, Scotland, in 1457.\n34. The Scottish National Museum is home to over 2 million objects and artifacts, covering Scotland's rich history from prehistory to the present day.\n35. Scotland has a deep connection to Celtic mythology, with many ancient sites, stories, and traditions rooted in Celtic folklore.\n36. Scotland's National Monument, the iconic Edinburgh Castle, was built between 1430 and 1571.\n37. The Scottish Highlands are home to the world's last wilderness areas, with vast expanses of unspoiled nature and untouched landscapes.\n38. Scotland has a rich maritime history, with over 2,900 miles of coastline.\n39. Scotland is home to some of Europe's oldest standing stones, including the Ring of Brodgar and Stonehenge II at Callanish on the Isle of Lewis.\n40. The Scottish National Gallery of Modern Art in Edinburgh showcases contemporary art from the late 18th century to the present day.\n41. Scotland has a deep connection to witchcraft, with over 5,000 witches being accused and persecuted during the Scottish Witch Trials between 1563 and 1736.\n42. The famous Scottish poet Robert Burns married Jean Armour in secret on New Year's Day, 1788.\n43. Scotland is home to several UNESCO World Heritage Sites, including the Old and New Towns of Edinburgh, the Heart of Neolithic Orkney, and the Antonine Wall.\n44. The Scottish National Library in Edinburgh holds over 2 million books and manuscripts.\n45. The Scottish village of Culzean, on the Ayrshire coast, was once home to Robert the Bruce, Scotland's most famous king.\n46. The Scottish Borders are named after the Roman frontier that once marked the southern boundary of Scotland.\n47. Scotland has a long tradition of fiddle music and dance, with influences from Celtic, Scandinavian, and European sources.\n48. Scotland's highest waterfall, Eas Mor, is located on the Isle of Skye.\n49. The Scottish National War Memorial in Edinburgh honors over 100,000 Scottish soldiers who died in World War I and II.\n50. Scotland has a rich and diverse cultural heritage, with influences from Celtic, Norse, and European sources.	\N	\N
725	1	1	The Ancient Kingdoms of Scotland	\N	\N	\N	 Image Description:\n\nTitle: "Ancient Scottish Monuments and Warriors Gathering"\n\nThe image showcases a lush, green Scottish landscape with rolling hills, surrounded by ancient ruins and monuments. In the foreground, there is a large standing stone, intricately carved with symbols of the Picts and runes, serving as the focal point of the scene. To its left lies an ancient castle ruin, possibly belonging to the Scots or Vikings, with towering walls and open gates. The sun sets behind the hills in the background, casting a warm golden light over the landscape.\n\nIn the middle ground, there are a group of six warriors, dressed in ancient Scottish attire, gathered around a campfire. They wear kilts adorned with intricate tartan patterns, carrying weapons such as swords and shields. Some of them have their heads covered by bonnets or hoods, while others show expressive faces filled with determination and pride.\n\nThe scene is set to evoke feelings of history, mystery, and connection to Scotland's early past. The use of natural elements like the landscape, fire, and sun adds a sense of warmth and depth to the image. The warriors gathered around the campfire convey a sense of unity and camaraderie among those who shaped Scotland's ancient history.	You are depicting the rich history of ancient Scotland. In the foreground, a rugged cliffside overlooks a tranquil loch, reflecting the golden sunset. At the edge of the loch, a group of Pictish warriors in tribal tattoos and fringed garments huddle around a bonfire, exchanging stories of bravery and legend. In the background, a fortified hillfort looms, home to the powerful Scots chieftain leading his people. A lone Viking longship sails ominously on the horizon, a reminder of the foreign threats that once challenged Scotland's sovereignty. Maintain the tone of mythology and community, Avoid cliché or stereotypes. 	\N	 Image Description:\n\nTitle: "The Triumvirate of Ancient Scotland: Picts, Scots, and Vikings"\n\nMain Features:\n\n1. Central Focus: Three stylized silhouettes of a Pictish warrior in tribal tattoos, a Scottish king wearing a Crown and a Viking warrior with horned helmet, arranged in a triangular formation to symbolize the three ancient kingdoms.\n2. Background: A lush green Scottish landscape with rolling hills and a backdrop of rugged cliffs to represent the diverse terrain of Scotland during this period.\n3. Ancient Artifacts: Scattered throughout the scene are elements that reflect each culture - Celtic knots for the Picts, a crown for the Scots, and a Viking longship.\n4. Visual Storytelling: The image conveys a sense of unity in diversity, as these three distinct groups contributed to shaping Scotland's rich history. The triangular arrangement of the figures also forms an abstracted representation of the Scottish flag, tying the visual back to the topic.\n5. Color Palette: Earthy tones and muted colors reflecting nature and a sense of antiquity. The use of contrasting colors for each figure adds depth and clarity.\n6. Composition: A balanced composition with the figures arranged in an engaging, visually pleasing manner that invites further exploration of this topic.\n7. Detailing: Close attention to details, including the clothing, accessories, and unique features that distinguish each culture. This includes intricate tattoos for the Picts, a Scottish crown adorned with precious gems, and a Viking helmet with horns.	A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.	draft	\N	\N	\N	\N
727	1	2	The Wars of Scottish Independence	\N	\N	\N	 Based on the input content provided, I suggest an image that features a prominent and clear representation of the Scottish flag against a backdrop of a historic Scottish castle or fortress. The castle should be depicted in a realistic and detailed manner, with intricate architecture, tall stone walls, and possibly a drawbridge or battlements to emphasize its historical significance.\n\nThe foreground of the image could include a lone figure dressed in traditional Scottish attire, such as a kilt or plaid, holding a sword or other symbolic object, serving as a representation of the brave figures who fought for Scotland's independence. The figure could be posed defiantly with an expression of determination and strength.\n\nThe image should have a monochromatic color scheme to give it a historic feel, with shades of gray, brown, and dark blue dominating the palette. The only bright colors in the image should be the Scottish flag's red, white, and blue, which should be depicted in high contrast against the dull background.\n\nThe layout of the image should be simple and focused on the main topic - Scotland's struggle for independence. There should not be any other distracting elements in the image, such as modern technology or multicultural symbols. The image should evoke a sense of history, courage, and perseverance.	 Title: "50 Fascinating Facts about Scotland's Rich History and Culture"\n\n1. Scotland is the northernmost country in the United Kingdom, with a population of around 5.5 million.\n2. The Scottish flag, or Saltire, consists of diagonal white and red stripes.\n3. Scotland's national animal is the Unicorn, although no unicorns have ever been documented to exist there.\n4. Edinburgh Castle is one of Scotland's most famous landmarks, located in the heart of its capital city.\n5. Stonehenge, a prehistoric monument, is not actually in Scotland but in England, yet it has had significant influence on Scottish mythology.\n6. The Scottish Highlands are home to some of the world's rarest plants and animals, including the Scottish Wildcat.\n7. The first university in Scotland was established in 1413 - the University of St Andrews.\n8. Inventors from Scotland include James Watt, who greatly improved the steam engine, and Alexander Graham Bell, who invented the telephone.\n9. Scotland has a rich literary heritage, with notable figures such as Robert Burns, Sir Walter Scott, and J.K. Rowling.\n10. The kilt, a traditional Scottish garment, is worn on special occasions and ceremonies across the world.\n11. Scotland's national dish is haggis, which consists of sheep's heart, liver, and lungs mixed with oats, onions, and spices, all encased in the animal's casing.\n12. The Scottish loch ness monster, or Nessie, is a legendary creature believed to inhabit Loch Ness in the Highlands.\n13. Scotland has had numerous battles for independence throughout history, most notably the Wars of Scottish Independence from England.\n14. The Scottish National Gallery in Edinburgh houses an impressive collection of European art.\n15. The first golf tournament in the world took place in Scotland in 1456.\n16. Scotland has a rich musical heritage, with bagpipes being one of its most iconic instruments.\n17. The Scottish Clans system is based on families tracing their ancestry back to a common founding figure or hero.\n18. Scotland's national drink is whisky, which is made from fermented barley and aged in oak barrels.\n19. Scotland was part of the Hanseatic League, an economic alliance of European towns from the 13th to the 17th century.\n20. The Scottish Borders are home to several ancient fortified houses known as peel towers.\n21. Scotland has a diverse climate, ranging from tropical in the south to Arctic in the north.\n22. The Scottish National War Memorial is dedicated to all Scottish servicemen and women who have died in wars.\n23. Scotland's national poet Robert Burns wrote "Auld Lang Syne," which is now sung around the world as a New Year's Eve tradition.\n24. Scotland has numerous castles, including Balmoral Castle, the Royal Family's Scottish residence.\n25. The Scottish National Portrait Gallery in Edinburgh showcases portraits of notable Scots from throughout history.\n26. Scotland is home to over 30 active volcanoes, although none have erupted for several thousand years.\n27. Scotland has a rich maritime heritage, with numerous ports and shipbuilding industries.\n28. The Scottish enlightenment was a period of intellectual and scientific advancements in Scotland during the late 17th to mid-18th centuries.\n29. Scotland's national emblem is the thistle, which is said to have saved Scottish soldiers from a surprise attack by hiding their presence due to the prickly plant's scent.\n30. The Scottish National Museum in Edinburgh houses collections of art, history, and natural history.\n31. Scotland has a rich tradition of storytelling, with tales such as "The Selkie" and "Tam Lin" being told for generations.\n32. Scotland is home to several UNESCO World Heritage Sites, including the Heart of Neolithic Orkney and New Lanark.\n33. The Scottish National Library in Edinburgh holds a vast collection of books and manuscripts.\n34. Scotland's national sport is shinty, which involves two teams using wooden sticks to hit a small leather ball.\n35. Scotland has several ancient stone circles, including the Clava Cairns and the Ring of Brodgar.\n36.	\N	 Image Concept:\n\nTitle: "The Battlefield of Bannockburn: Scotland's Stance for Freedom"\n\nDescription:\nThis image will depict a dramatic scene from the Battle of Bannockburn (1314), a pivotal moment in Scottish history and a significant battle during The Wars of Scottish Independence. The image will consist of two main elements: the battlefield and the foreground.\n\nBackground:\nThe background of the image will feature a lush, green landscape with rolling hills and a winding river. In the distance, there will be a large wooden castle symbolizing England's power and influence in Scotland at that time. Smoke rising from the horizon indicates ongoing battles. The sky will be filled with dark clouds, hinting at the intensity of the conflict.\n\nForeground:\nIn the foreground, we will have a close-up scene showcasing an intense hand-to-hand combat between a Scottish warrior in full plate armor and an English knight. Both warriors are engaged in a fierce battle, their eyes locked in determination and resolve. The clash of their weapons creates sparks, emphasizing the brutality of war. The Scottish warrior wears a tartan kilt, adding to the visual storytelling of Scotland's rich cultural heritage amidst the chaos of war.\n\nAdditional elements:\nTo further highlight the importance of this struggle for independence, additional elements such as Scottish and English flags, banners, and heraldic emblems can be included in the background. Additionally, a dead horse lying nearby serves as a reminder of the heavy toll wars take on both sides.\n\nBy focusing on this specific moment from The Wars of Scottish Independence, the image will capture the essence of Scotland's resilience and determination to stand up against English rule, providing a powerful visual representation for this section of your blog article.	A detailed account of Scotland's struggles for independence from England, including key battles and figures.	draft	\N	\N	\N	\N
728	1	3	Tartanry and Highland Culture	\N	\N	\N	 Image Description:\n\nTitle: "Exploring the Rich Tradition of Scottish Tartans and Clans"\n\nThe image showcases a close-up view of an intricately woven tartan fabric against a neutral background. The tartan pattern is the focal point, with its distinctive crisscrossed stripes arranged in alternating bands of color. The threads are depicted in high detail, with each thread interlaced perfectly with its neighbor.\n\nIn the foreground, there lies an open, leather-bound book, its pages slightly lifted to reveal a map of Scotland adorned with dots signifying various clan territories. A quill pen and inkwell sit atop the book, symbolizing the importance of recording Scotland's rich history. The map is surrounded by a few selected tartan swatches, each representing prominent Scottish clans such as Campbell, Stewart, and MacLeod.\n\nThe image's layout is simple yet captivating, with the tartan fabric taking center stage and the surrounding elements subtly emphasizing its historical significance. The neutral background ensures that the tartan fabric stands out, while the added map and book components add depth and context to the overall composition.\n\nThis image accurately represents the input's content by showcasing Scotland's iconic tartans and clans in a respectful, historically-accurate manner. The use of contemporary elements like the open book and map maintains an engaging visual while upholding the authenticity of Scotland's Highland culture.	 Title: "Exploring the Rich Tradition of Scottish Tartans and Clans: 50 Fascinating Facts"\n\n1. Tartan is a distinctive, woven fabric with a crisscrossed design. It has been an essential part of Scottish culture since at least the late 16th century.\n2. The word "tartan" comes from the Old French term "tartanus," meaning "checked."\n3. There are over 4,000 unique tartans registered with the Scottish Register of Tartans.\n4. Each clan had its own distinct tartan, representing their ancestry and lineage.\n5. Tartans were traditionally made using wool from local sheep, dyed with natural plant dyes.\n6. The first recorded use of a clan tartan was in 1326 for the MacLeods of Lewis.\n7. Tartans were used as a means of identification during battles.\n8. The Black Watch regiment, founded in 1725, popularized the modern kilt and the use of tartans.\n9. Clan Campbell is the largest Scottish clan, with over 30,000 members worldwide.\n10. Clan MacLeod's tartan features a striking combination of blue, green, and white.\n11. The Stewart tartan has diagonal red and white stripes, representing the Lion Rampant, an iconic Scottish emblem.\n12. Many clans have mythical origins, such as Clan Campbell, which is said to be descended from a giant.\n13. Tartans were used not only for kilts but also for other items, like blankets and scarves.\n14. The Royal Stewart tartan was granted as an honor to the Scottish monarchy in 1329.\n15. In modern times, tartans have become a symbol of Scottish pride and heritage.\n16. Tartans are now worn by various organizations, including piping bands and historic societies.\n17. The first recorded tartan mill was established in Scotland in 1780.\n18. Traditional tartans can be made using the "plain weave," "herringbone" or "twill" weaving techniques.\n19. Clan crests, a symbol representing each clan, were later added to tartans in the late 16th and early 17th centuries.\n20. Most clan crests have an animal motif, such as a lion, stag, or eagle.\n21. The Lion Rampant is a common emblem found on many Scottish clan crests.\n22. Clan crests were used to distinguish between clans during battles and tournaments.\n23. Many clans have myths associated with their crests, like the MacLeod crest symbolizing the protection of their lands from invading Norsemen.\n24. The Highland Clearances, a period of displacement in the late 18th and early 19th centuries, forced many Scots to abandon their tartans and clans.\n25. The tartan revival began in the mid-19th century when Scottish emigrants carried their ancestral tartans with them to other parts of the world.\n26. Tartans played a crucial role in the development of bagpipes and Scottish music.\n27. Clan Gunn's tartan is unique as it features a diagonal red stripe on a black background, a nod to their Viking heritage.\n28. The Montrose Diamond, an emerald-cut diamond, is said to have belonged to the Marquess of Montrose and was hidden in a Campbell tartan during the Civil War.\n29. Clan MacDonald's tartan includes a saltire cross, symbolizing their association with St. Andrew, Scotland's patron saint.\n30. The Thistle is another common Scottish emblem found on many tartans and clan crests.\n31. Tartans can be traced to various regions within Scotland, such as the Isle of Skye or the Borderlands.\n32. Certain clans have multiple registered tartans, like Clan MacLeod, which has three official variations.\n33. Tartans are made using different weights and counts of wool threads for distinct visual effects.\n34. The Scottish National War Memorial in Edinburgh is adorned with a magnificent mosaic of various Scottish clan tartans.\n35. Some clans have adopted non-traditional tartans, such as Cl	\N	 Image Description:\n\nTitle: "The Vibrant Tapestry of Tartan and Highland Culture"\n\nImage Content:\n\nThis image is a richly textured, close-up depiction of an intricately woven tartan cloth. The cloth is spread out in the foreground, taking up most of the frame. The weaving patterns are vibrant and distinct, showcasing the traditional colors and designs associated with Scottish clans. The fibers of the fabric appear to be a mix of wool and silk, giving it a lush and luxurious appearance.\n\nIn the background, there's a soft, misty landscape reminiscent of the Scottish Highlands. The rolling hills are dotted with small, quaint cottage-like structures and ancient stone castles, evoking the traditional Highland homes and historic sites. The sky above is overcast, with rays of sunlight breaking through the clouds, illuminating parts of the landscape and adding a sense of depth and drama to the scene.\n\nAdding Visual Context:\n\nTo enhance the image's visual context, props such as a traditional Scottish sporran (a leather pouch worn suspended from a belt), a pair of tartan hose (knee-length socks), and a quaich (a Scottish drinking cup) could be added to the scene. A Highlander wearing a kilt made of the same tartan fabric, complete with a caberet or broadsword, could also be depicted standing in front of the cloth, adding an element of authenticity and storytelling to the image.\n\nOverall, this image captures the essence of Tartanry and Highland Culture, providing an evocative and engaging representation of Scotland's iconic symbols and traditions.	An examination of Scotland's iconic tartans, clans, and traditional Highland culture.	draft	\N	\N	\N	\N
716	53	7	Story-telling in Scotland Today	1. Living Traditions: Oral Storytelling in Scottish Communities\nRevive the art of oral storytelling as it persists in various communities across Scotland, from Gaelic-speaking islands to traditional fishing villages.\n\n2. Folk Tales Revival: Modern Interpretations and Adaptations\nExplore how contemporary writers and artists are breathing new life into classic Scottish folk tales through innovative adaptations and retellings.\n\n3. The Power of Storytelling in Education\nDiscover the importance of storytelling in modern Scottish schools, where it is used as a tool to promote cultural understanding and instill a love for literature.\n\n4. Podcasts: A New Medium for Scottish Storytelling\nDelve into the world of Scottish podcasts, where storytellers are exploring diverse themes and keeping traditional tales alive through this modern medium.\n\n5. The Role of Technology in Preserving Scottish Storytelling\nExamine how technology is being used to preserve and disseminate Scotland's rich storytelling heritage, from digital archives to interactive storytelling apps.\n\n6. Story-based Tourism: Exploring Scotland through Its Stories\nDiscover the growing trend of story-based tourism in Scotland, where visitors can immerse themselves in the tales and histories behind iconic sites and landscapes.\n\n7. Community Storytelling Projects\nHighlight various community projects that are reviving and celebrating Scotland's oral storytelling traditions, from local festivals to collaborative storytelling initiatives.\n\n8. International Collaborations: Scottish Storytelling on the Global Stage\nExplore how Scottish storytellers are collaborating with their international counterparts to share their stories and inspire new generations of storytellers around the world.	\N	\N	 Based on the input, I suggest an image of a cozy, traditional Scottish living room with a fireplace burning in the background. In the foreground, there is a middle-aged woman sitting on a plush armchair, dressed in a sweater and skirt, holding a book close to her chest. She looks intently at the pages while a young girl, wearing a school uniform, listens attentively, leaning against her knees.\n\nThe room is adorned with Scottish decor such as tartan blankets, thistle motifs, and a framed picture of a loch on the wall behind them. A cup of tea sits on the small table between them, adding to the warm and inviting atmosphere.\n\nIn one corner of the room, there is a modern laptop with headphones on it, symbolizing how technology has become an essential tool for storytelling in contemporary times. The fireplace represents the oral traditions rooted deep within Scottish communities, while the woman and the girl embody the interactive experience of listening to stories. The books surrounding them represent the rich Scottish literature that continues to be cherished and passed down from generation to generation.\n\nThe background is simple and blurred, with muted colors, allowing the image's focus to remain on the mother-daughter duo engaged in the act of storytelling, symbolizing how the traditions of Scotland continue to thrive in today's world.	 A cozy Scottish living room, fireplace ablaze with crackling logs, casting a warm, gentle glow. Plush armchair holds a middle-aged woman in a sweater and skirt, engrossed in an old book. Young girl in school uniform leans against her knees, listening intently. Tartan blankets, thistle motifs adorn room, framed loch picture on wall. A cup of steaming tea on table between them. Corner reveals a modern laptop with headphones, symbolizing technology's role in contemporary storytelling. Background: simple, muted colors, focus remains on mother-daughter duo, embodying Scotland's rich oral traditions alive today.	\N	 Image Concept: A vibrant and modern scene depicting a diverse group of people gathered around a large communal table, each engaged in sharing a story from a book, podcast, or traditional oral tale. The table is filled with an assortment of Scottish literature, including contemporary novels, folktales, and educational materials. Behind them, there's a backdrop of various Scottish landscapes and iconic sites, symbolizing the rich cultural heritage that inspires these stories. Interspersed among the people are symbols representing technology, such as headphones, laptops, and smartphones – emphasizing the contemporary methods used to preserve and share these stories. The overall atmosphere is warm, inclusive, and engaging, highlighting the relevance of story-telling in Scotland today.	Exploring how story-telling continues to thrive in Scotland today, demonstrating its relevance and importance in contemporary society	draft	<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n<body>\n    <p>In Scotland today, storytelling is a cherished aspect of its rich heritage. Oral traditions keep ancient tales alive.</p>\n    <p>Storytellers weave narratives around hearths and communal spaces, involving audiences for interactive experiences. Modern methods like podcasts ensure wider reach and accessibility.</p>\n    <p>Contemporary Scottish literature builds on this strong foundation. Novels such as "The Wasp Factory" by Iain Banks and "Sunset Song" by Lewis Grassic Gibbon carry adventure and a deep connection to place.</p>\n    <p>Renowned authors like J.K. Rowling and Irvine Welsh have garnered international acclaim, solidifying Scotland's influence on global literature.</p>\n    <p>Today story-telling remains a living art form, still being brought to life by performance story-tellers like 'Bard of the Borders' James Spence of Jedburgh. On a larger scale, film and television productions, like "Outlander" and "Shetland," showcase rich storytelling traditions to a worldwide audience, contributing significantly to tourism.</p>\n</body>\n</html	In today's Scotland, story-telling continues to be a cherished aspect of its rich heritage. From oral traditions passed down through generations to contemporary works in novels, podcasts, film and television productions, story-telling remains an integral part of Scottish culture.\n\nOral traditions, rooted deep within communities, keep ancient tales alive. Storytellers weave these narratives around hearths and communal spaces, often involving the audience for an interactive experience. In addition, modern methods such as podcasts allow for wider reach and accessibility, ensuring that these stories continue to resonate with people.\n\nContemporary Scottish literature continues to build on this strong foundation. Bestselling novels like "The Wasp Factory" by Iain Banks and "Sunset Song" by Lewis Grassic Gibbon carry the essence of adventure and a deep connection to place, reflecting Scotland's unique identity. Additionally, the works of renowned Scottish authors such as J.K. Rowling and Irvine Welsh have garnered international acclaim, further solidifying Scotland's influence on global literature.\n\nFilm and television productions, like "Outlander" and "Shetland," showcase the rich storytelling traditions of Scotland to a worldwide audience. These adaptations not only preserve the essence of Scottish tales but also contribute significantly to the country's tourism industry.\n\nIn conclusion, story-telling in Scotland today is as vibrant and relevant as ever. It continues to shape and preserve cultural traditions while contributing significantly to both Scottish literature and popular culture at large.	scottish_section_716,_realisti_20250726_135007_706114.png	2025-07-26 13:50:08.954211
726	1	0	Medieval Scotland: Kingdoms and Feudalism	\N	\N	\N	 Title Ideas for Blog Post on Exploration of Scotland's Medieval Kingdoms, Nobility, and Feudal System:\n\n1. "Unraveling the Threads of Scotland's Medieval Nobility and Feudal System"\n2. "A Journey Through Time: Discovering Scotland's Medieval Kingdoms and Their Feudal Systems"\n3. "Medieval Scotland: Lords, Ladies, and the Feudal Dynamics of the Past"\n4. "From Castles to Clans: A Deep Dive into Scotland's Medieval Feudal System"\n5. "The Nobility and the Land: Scotland's Medieval Kingdoms and Their Feudal Systems Explored"\n\nContent Ideas for Blog Post on Scotland's Medieval Kingdoms, Nobility, and Feudal System:\n\n1. Briefly introduce the topic of medieval Scotland, its historical significance, and why it is important to explore its kingdoms, nobility, and feudal system.\n2. Provide a background on the political landscape during the medieval period in Scotland, explaining how it differed from other European countries.\n3. Identify key medieval Scottish kingdoms and their rulers, discussing their territories, power structures, and relationships with one another.\n4. Detail the role of nobility during this time, including their social status, responsibilities, and privileges, as well as how they were appointed and held their positions.\n5. Explore Scotland's feudal system in depth – its origins, hierarchy (from kings to farmers), land tenure, and duties.\n6. Share examples of important historical figures from the nobility or royalty during this period and discuss their impact on Scottish society.\n7. Employ visual aids like maps, diagrams, or images to help illustrate the points being made in the blog post.\n8. Highlight any fascinating stories, anecdotes, or lesser-known facts that add intrigue and depth to the topic.\n9. Conclude by summarizing the main ideas discussed and their relevance today, as well as potential avenues for further research or exploration.\n\nOnline Marketing Strategies:\n\n1. Create visually appealing blog graphics, including a captivating header image and infographics to grab readers' attention.\n2. Utilize keywords related to medieval Scotland, feudal systems, and nobility in the blog post to improve search engine optimization (SEO).\n3. Share the blog post on social media platforms like Facebook, Twitter, LinkedIn, and Pinterest, using relevant hashtags to attract a broader audience.\n4. Engage with followers and other interested parties by responding to comments, sharing additional resources, or initiating discussions around related topics.\n5. Collaborate with relevant influencers or bloggers in the historical or education niches to expand your reach and gain new audiences.\n6. Offer a free resource or download like an e-book, infographic, or checklist for readers who sign up for your email list, generating leads and potential repeat visitors.\n7. Optimize the blog post for mobile devices to ensure that users can access it easily on their phones or tablets.	 Title: 50 Fascinating Facts about Medieval Scotland: From Castles to Legends\n\n1. The first Scots lived as hunter-gatherers around 9000 BC.\n2. Scotland has over 700 castles, more than any other country in Europe.\n3. Edinburgh Castle was the residence of Scottish monarchs for over 300 years.\n4. Bagpipes, a Scottish invention, were used as military weapons.\n5. The Stone of Destiny, or "Lia Fáil," was believed to identify the rightful king of Scotland.\n6. Inverness Castle is the oldest continuously inhabited castle in Scotland.\n7. The Declaration of Arbroath, a letter from Scottish nobles to Pope John XXII, asserted Scotland's independence in 1320.\n8. Scotland was Catholic until the Protestant Reformation in the late 1500s.\n9. William Wallace, "Braveheart," led a successful rebellion against English rule in 1297-1304.\n10. Robert Bruce became King of Scotland in 1306 and united the country against the English.\n11. Scotland's national symbol is the unicorn, which may be based on the wild goat or the elusive aurochs.\n12. The kilt, traditional Scottish attire, was first worn by Highland clans in the 16th century.\n13. Scotland's most famous loch, Loch Ness, is home to the legendary Loch Ness Monster.\n14. The Battle of Bannockburn (1314) was a significant victory for Robert Bruce against Edward II of England.\n15. Mary, Queen of Scots, ruled Scotland from 1542-1567 and was ultimately executed in England.\n16. In the Middle Ages, clans were large extended families that provided mutual protection and support.\n17. Scotland's climate is temperate maritime, with abundant rainfall.\n18. The Scottish Highlands are known for their rugged mountains and deep lochs.\n19. The Lowlands have a more agricultural economy and a denser population.\n20. Scotland has the longest coastline in Europe, at over 14,000 km (8,699 mi).\n21. The Scottish language, Gaelic, was spoken by most Highlanders until the late 1700s.\n22. The first university in Scotland, St. Andrews University, was founded in 1413.\n23. Robert Burns (1759-1796), the "National Bard of Scotland," wrote poems and songs that are still popular today.\n24. Scottish clans fought each other for power and resources throughout history.\n25. The Wars of the Roses, a series of battles between England and Scotland (1450-1503), ended with English dominance.\n26. The Battle of Culloden (1746) marked the end of the Jacobite uprisings against English rule.\n27. The Scottish Enlightenment, a period of intellectual advancement, lasted from about 1730 to 1800.\n28. Scotland has produced many famous scientists, including James Clerk Maxwell and Thomas Bayes.\n29. The Celts, an Indo-European people, settled in Scotland around 400 BC.\n30. Scotland's national animal is the lion.\n31. The Scottish flag, or "Saltire," features a white diagonal cross on a blue background.\n32. King Arthur, a legendary king of Britain, is said to have fought at the Battle of Arderyne in Scotland.\n33. Scotland's national dish is haggis, a savory pudding containing sheep heart, liver, and lungs.\n34. The "Maiden Stones," or "Mermaid's Stones," are a mythical place where mermaids were said to have gathered.\n35. Scotland has more than 100 whisky distilleries.\n36. Scottish folklore is rich in tales of fairies, elves, and other supernatural beings.\n37. The Black Douglases, a powerful Scottish clan, rose against King Robert II in the late 14th century.\n38. Scotland's national sport is golf, which originated in Scotland around	\N	 Image Concept: A panoramic view of a Scottish medieval castle and its surrounding village, with various activities showcasing the daily life and social hierarchy of medieval Scotland.\n\nMain Features:\n\n1. Castle: The foreground of the image will be dominated by a majestic Scottish castle, with tall towers and battlements overlooking the landscape. Its grand architecture will reflect the power and wealth of the ruling class during this era.\n\n2. Village: Surrounding the castle will be a quaint, bustling medieval village. The thatched-roof cottages with their smoke rising from the chimneys will depict the simplicity and charm of rural life in Scotland during this time.\n\n3. Market Scene: Towards the bottom left corner of the image, there will be a lively market scene with merchants selling various wares, including textiles, pottery, and foodstuffs. This will highlight the economic activity and trade that took place within medieval Scottish communities.\n\n4. Agriculture: In the right portion of the image, farmers can be seen working in open fields, tending to their crops or livestock. This will emphasize the importance of agriculture in sustaining life during this era.\n\n5. Nobility and Feudalism: Scattered across the village and within the castle grounds, knights on horseback and nobles in their finery can be seen interacting with their subjects. These depictions will highlight the feudal system and social hierarchy that existed in medieval Scotland.\n\n6. Landscape: The image will also incorporate elements of Scotland's natural beauty, such as rolling hills, lochs, or forests. This will create a visually appealing and immersive representation of life during medieval times in Scotland.	An exploration of Scotland's medieval kingdoms, nobility, and feudal system.	draft	\N	\N	\N	\N
731	1	6	Scottish Culture and Identity Today	\N	\N	\N	 Image Description:\n\nTitle: Modern Scottish Culture Mosaic\n\nThis image will showcase a colorful and dynamic representation of contemporary Scottish culture, encapsulating the essence of modern-day Scotland's arts, literature, music, and festivals. The design will be a mosaic, with each tile in the mosaic symbolizing a distinct aspect of the various components that make up Scottish culture today.\n\nLayout:\nThe image will consist of an 8x8 square grid, creating a 64-tile mosaic. Each tile within the grid will have a uniform size and shape, making for a cohesive design. The tiles will be arranged in a neat grid pattern to ensure balance and order.\n\nKey Features:\n1. Literature: The first tile will feature an open book with a quill pen resting on it, symbolizing Scotland's rich literary heritage. The title page of the book could display the image of one famous Scottish author or a famous quote from a Scottish literary work.\n2. Music: A musical note on a bagpipe or a traditional Scottish harp will be depicted in another tile to symbolize Scotland's world-renowned music scene. This tile might also have a small banner with the text "Bagpipes" or "Harps."\n3. Art: In one of the tiles, an abstract representation of art will be portrayed through intricate patterns inspired by Scottish traditional arts and crafts such as tartan or Celtic knots.\n4. Festivals: A vibrant and lively scene of a popular Scottish festival like Hogmanay or Beltane could be depicted in another tile, showcasing the joyful and communal spirit of these events. This tile might include icons representing various activities common to the festival such as fireworks, bonfires, and traditional costumes.\n5. Clans: One of the tiles will symbolize Scottish clans through a stylized representation of a clan tartan design or a crest. The image could incorporate a castle, a lion rampant, or a thistle to reinforce the Scottish heritage aspect.\n6. Natural Landscapes: A landscape of Scotland's breathtaking natural beauty might be included in another tile. This tile will display mountains, lochs, or forests, emphasizing the natural inspiration that many aspects of Scottish culture draw from.\n7. Architecture: An image of a well-known piece of modern or traditional Scottish architecture like the Edinburgh Castle or Glasgow's Armadillo could be featured in one of the tiles to showcase Scotland's architectural heritage.\n8. Modern Innovations: A tile showcasing modern inventions, technology, and scientific discoveries from Scotland will be included as a nod to the country's contemporary advancements. This tile might depict the image of Alexander Graham Bell or the first telephone.\n\nVisual Context:\nThe mosaic's background will be inspired by the colors of the Scottish flag – blue and white. The image will appear as if the mosaic is set on a solid blue background, making the colors and patterns of each tile pop out. Overall, the design should exude a sense of creativity, vibrancy, and harmony, perfectly illustrating the richness and diversity of modern-day Scottish culture.	 Image Prompt:\n\nGenerate an image in a horizontal layout, exactly 2240 pixels wide by 1256 pixels high, using the inkwash and watercolour style with soft brushstrokes. The scene portrays a bustling modern Scottish town, where traditional and contemporary elements blend harmoniously. In the foreground, people dressed in plaid attire, playing bagpipes and dancing at a lively ceilidh (Scottish dance) event. A vibrant festival atmosphere prevails, with colorful tents and banners adorning the streets.\n\nIn the background, a majestic, mist-shrouded castle stands proudly on a hill. Modern buildings with sleek glass facades border the town square, while the lush green countryside rolls out beyond. The mood is joyous, welcoming, and full of life, as Scots celebrate their rich cultural heritage.\n\nBrushstrokes should fade into white around the edges of the canvas, blending naturally into a plain white background paper. Maintain the theme of Scottish culture and identity, avoiding clichés or stereotypes. Keep in mind the significance of literature, music, art, and festivals, as described in the heading.	\N	 Image Concept: A vibrant and lively collage depicting various aspects of modern Scottish culture. The image is set against a backdrop of a contemporary Scottish landscape, possibly with the iconic Edinburgh Castle in the distance.\n\nMain Features:\n\n1. Central Element: A large, colorful tartan plaid, symbolizing Scottish heritage and identity.\n2. Literature: Books scattered across the scene representing prominent Scottish writers, such as Robert Louis Stevenson, J.K. Rowling, or Irvine Welsh.\n3. Music: Musical instruments like bagpipes, a fiddle, and drums arranged around the scene, symbolizing traditional Scottish music.\n4. Art: A few abstract art pieces inspired by Scotland's landscapes or contemporary art movement, showcasing the diverse range of artistic expression in Scotland today.\n5. Festivals: Representations of popular Scottish festivals like Hogmanay (New Year), Beltane Fire Festival, and Edinburgh Festival Fringe.\n6. Urban elements: A bustling cityscape with modern architecture, street art, and people dressed in contemporary clothing wearing traditional Scottish accessories like tartan scarves or kilt pins.\n7. Iconic Scottish symbols: Presence of symbols like the thistle, the unicorn, and the lion rampant to emphasize Scotland's rich cultural heritage.\n8. Use of natural elements: Incorporation of Scotland's beautiful landscapes and natural beauty with various shades of green, blue, and brown to create a harmonious balance between modernity and tradition.	An examination of contemporary Scottish culture, including literature, music, art, and festivals.	draft	\N	\N	scottish_section_731,_realisti_20250726_074953_d69b90.png	2025-07-26 07:49:55.255403
730	1	5	Modern Scotland: Industrialization, Nationalism, and Devolution	\N	\N	\N	 Image Concept:\n\nTitle: "Modern Scotland: The Triangle of Transformation"\n\nDescription:\n\nThe image for this section will be a dynamic, multi-layered graphic that symbolizes the interconnected themes of industrialization, nationalism, and devolution in modern Scotland.\n\nLayout:\n\nThe image consists of three interlocking triangles, representing the three key themes. Each triangle has a distinct color palette:\n\n1. Industrialization Triangle (Blue): Represents the economic transformation with an image of factories and industrial landscapes, gears and cogs in motion, and ships signifying Scotland's maritime industry.\n2. Nationalism Triangle (Green): Represents the cultural reawakening, featuring a thistle, bagpipes, kilts, and other symbols of Scottish heritage.\n3. Devolution Triangle (Red): Represents political developments with depictions of influential figures like devolution pioneer Donald Dewar, Scotland's parliament building, and a Scottish flag.\n\nVisual Context:\n\n1. Industrialization Triangle: The base of this triangle is the foundation, and it builds up to depict a bustling industrial landscape. It showcases a harbor scene with ships at anchor and cranes lifting cargo. Atop this, we have an image of factories spewing out plumes of smoke. A series of gears and cogs in motion represent the machinery that fueled Scotland's industrial revolution.\n2. Nationalism Triangle: The base of this triangle has a thistle – Scotland's national flower - growing from a rich, green landscape. As we move upwards, we see the emergence of people wearing kilts and playing bagpipes. Atop this, there is a depiction of iconic Scottish landmarks such as castles and bridges, symbolizing the pride in Scotland's heritage.\n3. Devolution Triangle: The base represents Scotland's political evolution, with figures like Donald Dewar at its core. It progressively builds up to depict Scotland's Parliament building – the home of the Scottish government – and the Scottish flag waving proudly atop it. This triangle is completed by a collage of various contemporary Scottish cultural symbols such as art, music, literature, and festivals.\n\nIn summary, this image conveys the interconnected journey of Scotland's modern history through industrialization, nationalism, and devolution, with each triangle representing a distinct yet crucial aspect.	 "Generate an image in a horizontal layout, exactly 2240 pixels wide by 1256 pixels high, rendered in the inkwash and watercolour style with soft brushstrokes. The scene depicts modern Scotland's vibrant industrial landscape interwoven with symbols of national pride. In the foreground, a sprawling, smokestack-filled factory is juxtaposed against a backdrop of rolling green hills, evoking a sense of resilient nature and progress. A red poppy, Scotland's national flower, blooms on a hillside amidst the industrial scene, representing rebirth and renewal. In the distance, a crowd gathers at an imposing castle-like government building, symbolizing the political power and devolution of authority in modern Scotland. Brushstrokes should fade into white around the edges as if naturally blending the image into the background paper. Maintain a tonal palette that conveys the themes of industrialization, nationalism, and devolution."	\N	 Image Concept: "Scotland's Modern History: The Triangle of Industry, Nationalism, and Devolution"\n\nMain Features:\n\n1. Layout: The image is composed of a triangular shape, representing the three interconnected aspects of modern Scotland's history - industrialization, nationalism, and devolution. Each corner of the triangle showcases a distinct yet related scene that symbolizes each topic.\n\n2. Industrialization: This corner illustrates a bustling cityscape with factories emitting smoke, signifying the industrial revolution and Scotland's significant role in it. The workers can be seen operating machinery or leaving their workplaces, emphasizing labor and productivity. In the background, the famous Forth Rail Bridge stretches across the river Firth of Forth, symbolizing the country's infrastructure development during this era.\n\n3. Nationalism: This corner depicts a crowd gathered in front of Edinburgh Castle, waving Saltire flags and holding portraits of iconic Scottish figures like Robert Burns and William Wallace. The scene represents the rise of nationalist sentiments and the pride people felt towards their Scottish identity during this period.\n\n4. Devolution: The third corner displays a modern-day political chamber filled with representatives from various Scottish clans, symbolizing the devolved Scottish Parliament. They are seen in deep discussion, emphasizing the power shift back to Scotland, allowing for self-governance and decision-making over its domestic affairs.\n\nVisual Context: The image is set against a muted blue-grey background with warm, vibrant accents, representing the transition from the industrial era into modern times. The overall composition is balanced, with equal weight given to each corner, showcasing that all three aspects are essential parts of Scotland's modern history.	A discussion of Scotland's modern history, including key economic, cultural, and political developments.	draft	\N	\N	\N	\N
729	1	4	Scotland's Contribution to the British Empire	\N	\N	\N	 Image Description:\n\nTitle: "Scotland's Influence on the British Empire: A Historical Perspective"\n\nBackground: The image features a plain, neutral background with a soft, muted gray tone to signify the historical context of the topic. There is no distraction from the main focus of the image.\n\nLayout: The image consists of three distinct sections, divided by horizontal lines. Each section represents a different era in Scotland's history and its impact on the British Empire.\n\nSection 1 (Top): This section features an illustration of Edinburgh Castle, prominently displayed against a clear blue sky. The castle symbolizes Scotland as a powerful kingdom in its own right during ancient times. The castle is shown with intricate details, highlighting its architectural grandeur and historical significance.\n\nSection 2 (Middle): A chronological timeline runs horizontally across this section, connecting the events depicted in each section. Key figures and events that shaped Scotland's role in the British Empire are represented as icons along the timeline. These include images of Robert the Bruce, William Wallace, and James VI of Scotland who became James I of England, among others.\n\nSection 3 (Bottom): The bottom section showcases a map of the British Isles during the period when Scotland's influence was at its peak. The map highlights the territories under Scottish rule or influence, with special focus on the key regions that contributed significantly to the expansion of the British Empire.\n\nKey Features:\n1. Edinburgh Castle: An intricately detailed illustration of the castle representing Scotland's historical significance and power.\n2. Chronological timeline: A clear representation of the historical sequence of events, with key figures and milestones marked along it.\n3. Map of the British Isles: An accurate depiction of the territories under Scottish rule or influence during their peak period.\n\nThe overall design is simple yet engaging, keeping the focus on the content while maintaining a visually appealing layout. The image illustrates Scotland's historical role in shaping the British Empire in an informative and captivating manner.	Title: "Scotland's Influence on the British Empire: 50 Fascinating Facts"\n\n1. Edinburgh Castle was built in the 12th century and has been Scotland's primary royal residence.\n2. Robert the Bruce, King of Scotland (1304-1329), led Scottish forces against the English during the First War of Independence.\n3. William Wallace, a national hero, led the Scots to victory at the Battle of Stirling Bridge in 1297.\n4. The signing of the Treaty of Edinburgh-Northampton (1328) ended the First War of Scottish Independence.\n5. James I (James VI of Scotland) united the crowns of Scotland and England in 1603, becoming the first king of both nations.\n6. The Scottish Enlightenment brought influential thinkers like David Hume, Adam Smith, and Thomas Reid.\n7. Scotland's naval power played a crucial role in the defeat of the Spanish Armada (1588).\n8. Scotland introduced potato cultivation to Europe in the late 16th century.\n9. The Scottish Highlands were home to the last European stronghold of traditional Gaelic culture.\n10. The Declaration of Arbroath (1320) asserted Scotland's sovereignty and independence from England.\n11. The Battle of Bannockburn in 1314 saw a decisive Scottish victory against the English army.\n12. Scotland was one of the first countries to adopt a written constitution with the Claim of Right Act (1689).\n13. The Scottish Parliament, or 'Holyrood,' has been in continuous existence since 1235.\n14. Scotland's national animal is the unicorn, originally symbolizing purity and power.\n15. Alexander Fleming discovered penicillin in Scotland in 1928.\n16. The Scottish clans maintained their unique identities through tartans, kilts, and traditional music.\n17. Scotland was the birthplace of John Logie Baird, who invented television (1925).\n18. Scotland's national bard, Robert Burns, wrote "Auld Lang Syne," a poem that inspired New Year traditions worldwide.\n19. The Scottish Gaelic language has survived into the modern era and is now being revitalized.\n20. Scotland was home to the world's oldest continuously operating distillery, Glenlivet.\n21. Mary Queen of Scots (1542-1567) faced numerous political crises during her reign in Scotland.\n22. The Battle of Culloden Moor (1746) marked the end of Jacobite rebellions and the Scottish clan system.\n23. Scotland's contribution to the British Navy was crucial in maintaining the balance of world power.\n24. Scotland gave its name to over 500 places around the world.\n25. The Scottish poet Robert Louis Stevenson wrote "Treasure Island" and other famous works.\n26. Scotland was the first country to grant women the right to vote (1913).\n27. Scotland's national dish, haggis, is made from sheep's heart, liver, and lungs.\n28. Scotland has over 790 islands, with around 130 inhabited.\n29. The Scottish poet Robert Burns penned the words to "Scotland the Brave," the unofficial national anthem.\n30. Scotland's natural wonders include the North Berwick West Beach and the Isle of Skye.\n31. Scottish architectural styles range from medieval fortresses to contemporary buildings.\n32. Scotland was a major producer of herring during the Middle Ages, making it an important trading center.\n33. The first recorded golf game took place in Scotland around 1457.\n34. Scotland's national symbol, the thistle, was adopted after an English army trod on one inadvertently at night.\n35. Scotland boasts three UNESCO World Heritage Sites: St. Kilda, Edinburgh Castle, and New Lanark.\n36. Scotland had a significant impact on early Christianity within the British Isles.\n37. Scotland's rich history influenced countless works of literature, music, and art.\n38. Scotland's most famous castles include Eilean Donan and Urqu	\N	 Image Concept: A historical scene showcasing a grand banquet table set against the backdrop of a scenic Scottish loch, with prominent Scottish and British figures gathered around it.\n\nMain Features:\n1. Setting: A well-lit, elegant dining hall or marquee is situated by the banks of a serene Scottish loch. The water reflects the golden hues of the setting sun, casting an ethereal glow over the scene.\n2. Characters: Key historical figures from Scotland and Britain, dressed in period clothing, are seated around the long banquet table. Some may include Robert the Bruce, William Wallace, King James VI of Scotland, Queen Elizabeth I of England, or prominent merchants and diplomats.\n3. Symbolism: The table is laden with an abundance of food and drink, signifying prosperity and peace between Scotland and England during the time of their union within the British Empire. Scottish and British flags are displayed prominently on either side of the room to represent unity.\n4. Accessories: Decorative elements such as tapestries displaying the Scottish and British coats of arms, heraldic emblems, and floral arrangements add to the grandeur of the setting.\n5. Atmosphere: A warm, inviting ambiance pervades the scene, with a soft glow from the candles casting gentle shadows on the table and faces of the figures. The peaceful backdrop of the loch creates a sense of tranquility and unity.	An exploration of Scotland's role in shaping the British Empire, including key figures and events.	draft	\N	\N	\N	\N
712	53	3	Scottish Literary Masters: Robertson, Barrie, Gaiman	Topic 1: Robert Louis Stevenson's "Treasure Island" and its enduring impact on pirate stories\nTopic 2: J.M. Barrie's Peter Pan and the origins of modern children's literature\nTopic 3: Neil Gaiman's "A Song of Myself": exploring Scottish mythology in his works\nTopic 4: The use of settings in Robertson, Barrie, and Gaiman's novels: from Scotland to fantasy lands\nTopic 5: Robertson's influence on the development of psychological thriller genre\nTopic 6: Barrie's stage adaptations of "Peter Pan" and their role in shaping theatre history\nTopic 7: Symbolism and allegory in Stevenson, Barrie, and Gaiman's stories\nTopic 8: The portrayal of Scottish heritage in the works of these literary masters\nTopic 9: Influence of historical events on Robertson, Barrie, and Gaiman's writing\nTopic 10: The role of imagination and creativity in the works of these Scottish authors.	\N	\N	 Based on the input, I suggest an image featuring three antique books lying open on a wooden table in a dimly lit room with a warm, inviting ambiance. The books belong to Robert Louis Stevenson, J.M. Barrie, and Neil Gaiman, indicated by their titles subtly visible at the edges of the open pages. The background could include an old fireplace with logs crackling, adding to the cozy atmosphere.\n\nThe table is set against a backdrop of a bookshelf filled with books from different eras and genres, giving a sense of depth and history. A single window lets in soft natural light that gently illuminates the scene. The layout is simple yet visually appealing, focusing on the classic literary context while maintaining a modern touch through subtle details like the table's worn-out wooden texture and the books' antique appearance.\n\nThis image effectively illustrates the exploration of Scottish literature's rich heritage by highlighting the works of three significant authors, creating an engaging and appropriate visual representation for this section of the blog article.	 Three antique books lie open on a worn, wooden table in a cozy, dimly lit room. The ambiance is warm and inviting, with an old fireplace crackling in the background. Bookshelves filled with volumes from different eras line the walls, creating a sense of depth and history. The titles of "Treasure Island" by Robert Louis Stevenson, "Peter Pan" by J.M. Barrie, and "The Sandman" by Neil Gaiman are subtly visible at the edges of the open pages. A single window lets in soft natural light that dances across the scene. This simple yet visually appealing layout pays homage to the rich literary heritage of Scotland through the works of these three significant authors.	\N	 Image Description:\n\nTitle: "Scottish Literary Masters: Treasured Tales"\n\nThe image features a richly textured, wooden bookshelf set against a dark, moody background. The shelves are filled with an assortment of leather-bound books and scrolls, their spines worn from use. Three prominent books are displayed in the foreground, each representing one of the Scottish literary masters - Robert Louis Stevenson, J.M. Barrie, and Neil Gaiman.\n\n1) The first book, "Robert Louis Stevenson's Treasure Island," has an illustration of a pirate ship on its cover, with a treasure chest overflowing with gold coins and precious gems in the background. The title is embossed in gold letters against a red backdrop.\n\n2) The second book, "J.M. Barrie's Peter Pan," has an illustration of Peter Pan leading the Lost Boys, surrounded by fairies and mermaids. The title is embossed in silver letters against a star-studded blue backdrop.\n\n3) The third book, "Neil Gaiman's A Song of Myself," features an ethereal illustration of Scottish mythological creatures like the Selkies and the Kelpies. The title is embossed in gold and silver letters against a moonlit night sky.\n\nThe books are surrounded by a warm, golden glow emanating from the open pages. A few leaves flutter gently in the breeze, as if inviting readers to delve into their stories. In the background, faint silhouettes of castles and mountains can be seen through the window, hinting at the diverse settings found within the works of these Scottish literary masters.	An examination of influential Scottish authors and their works, filled with adventure, magic, and a strong sense of place, which left an indelible mark on both Scottish literature and popular culture.	draft	<!DOCTYPE html>\n<html lang="en">\n\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n\n<body>\n    <p>Three influential Scottish literary masters are Robert Louis Stevenson, J.M. Barrie, and Neil Gaiman. Each author left an indelible mark on Scottish literature and popular culture with captivating stories.</p>\n\n    <p>Robert Louis Stevenson (1850-1894) wrote novels like "Treasure Island," "Kidnapped," and "Strange Case of Dr Jekyll and Mr Hyde." His tales of piracy, adventure, and the supernatural continue to enthrall readers.</p>\n\n    <p>J.M. Barrie (1860-1937) penned "Peter Pan," a beloved children's classic, and its sequels. Through imaginative storytelling, he introduced Peter Pan and the Lost Boys to the world, immortalising their adventures in Neverland.</p>\n\n    <p>Neil Gaiman (b. 1960), a contemporary author, created a diverse body of work spanning genres such as fantasy, horror, and science fiction. His novels "Good Omens" and "American Gods," along with graphic novels and short stories, have earned him a dedicated fan base.</p>\n\n    <p>These literary giants enriched Scottish literature and significantly contributed to the global literary landscape, leaving a lasting impact on both popular culture and future generations of writers.</p>\n</body>\n\n</html	In this section, we delve into the works of three influential Scottish literary masters: Robert Louis Stevenson, J.M. Barrie, and Neil Gaiman. Each author left an indelible mark on both Scottish literature and popular culture with their captivating stories filled with adventure, magic, and a strong sense of place.\n\nRobert Louis Stevenson (1850-1894) is renowned for his novels like "Treasure Island," "Kidnapped," and "Strange Case of Dr Jekyll and Mr Hyde." His tales of piracy, adventure, and the supernatural continue to enthrall readers.\n\nJ.M. Barrie (1860-1937) penned the beloved children's classic "Peter Pan," as well as its many sequels. Through his imaginative storytelling, he introduced Peter Pan and the Lost Boys to the world, immortalizing their adventures in Neverland.\n\nNeil Gaiman (b. 1960), a contemporary author, has created a diverse body of work that spans genres such as fantasy, horror, and science fiction. His novels like "Good Omens" and "American Gods," along with graphic novels and short stories, have earned him a dedicated fan base.\n\nThese literary giants not only enriched Scottish literature but also contributed significantly to the global literary landscape, leaving a lasting impact on both popular culture and future generations of writers.	<!--_live_preview_content_will_20250726_143125_b61512.png	2025-07-26 14:31:26.714828
710	53	1	Ancient Celtic Story-telling	Test ideas update	\N	\N	 Based on the input provided, an appropriate image for this blog article section could be a scene depicting an ancient Celtic storytelling session. The image should feature a cozy and inviting setting with a focus on nature to represent the deep connection between the Celts and their land.\n\nThe main features of the image are as follows:\n\n1. Scene Setting: The scene is set in a forest clearing, with tall trees surrounding it and sun rays filtering through the leaves, creating a warm and inviting atmosphere. The background is lush with greenery and has a soft, earthy color palette to represent the ancient Scottish landscape.\n\n2. Central Focus: The central focus of the image is an elderly storyteller, dressed in traditional Celtic clothing, sitting on a wooden stool in front of a small group of eager listeners. He is using expressive body language and inflections in his voice to narrate an engaging story.\n\n3. Story Elements: There are various elements from Celtic mythology scattered around the scene. For instance, there could be a large, ornate horn overflowing with ale, symbolizing hospitality, or a small, intricately designed harp in the corner of the image, representing music and storytelling's connection. A few carefully placed props, such as a ceremonial cup or an ancient scroll, could further emphasize the Celtic theme.\n\n4. Interaction: The storyteller is interacting with his audience, who are fully engaged in the narrative. Their facial expressions convey curiosity, interest and excitement, reflecting the power of these stories to captivate audiences.\n\n5. Moral Underpinnings: To emphasize the moral underpinnings of Celtic tales, there could be an element within the image that symbolizes a lesson or a message. This could be as simple as a subtle visual cue, like a cleverly placed shadow or a hidden detail in the background.\n\nOverall, this image accurately portrays the ancient Celtic storytelling tradition by featuring a natural setting, an engaging scene of a storyteller sharing his tales, and symbolism rooted in Celtic mythology.	 Image description: An elderly Celtic storyteller sits in a sun-dappled forest clearing, surrounded by tall trees and vibrant greenery. He wears traditional attire and uses expressive body language as he narrates an ancient tale to a captivated audience. The scene is rich in Celtic symbolism: a large ornate horn overflowing with ale signifies hospitality, an intricately designed harp represents music and storytelling, and a ceremonial cup or ancient scroll are prop details that further emphasize the tradition. The listeners' curious and engaged expressions reflect the power of these stories to captivate audiences. A subtle visual cue, like a cleverly placed shadow or hidden detail, symbolizes the moral underpinnings of Celtic tales. The warm and inviting atmosphere is created by the filtered sunlight and earthy color palette, transporting viewers to this ancient Scottish landscape.	\N	 Image Description:\n\nThe image is a depiction of an ancient Scottish storytelling scene set against a backdrop of a serene woodland glen. The foreground features a figure of an elderly storyteller dressed in traditional Celtic clothing, sitting cross-legged on a large flat rock with a rapt audience gathered around him. The audience consists of a group of children and adults, their faces illuminated by the warm light of a campfire nestled between two trees to his right.\n\nThe storyteller holds a wooden staff adorned with intricate carvings, which he uses to illustrate his tales as he speaks, his voice carrying on the gentle breeze that rustles through the leaves above. The fire casts long, flickering shadows across the clearing, highlighting the features of the ancient oak tree behind them and the glistening dewdrops on the forest floor.\n\nThe image is filled with rich symbolism reflective of ancient Celtic storytelling: the natural elements, such as the trees, water, and fire, form a central part of the scene. The scene also incorporates various elements suggested in the text: the presence of mythical creatures like the Morrigan or the Dagda, depicted subtly through the intricate carvings on the storyteller's staff, as well as the role of trees and their symbolism in Celtic folklore.\n\nThe woodland setting also serves as a reminder of how these stories were once shared during gatherings and how they are deeply rooted in nature and tradition. The image aims to evoke a sense of wonder, mystery, and nostalgia for the rich storytelling heritage that Scotland has to offer.	Exploring the origins of story-telling in Scotland through ancient Celtic tales passed down orally, rooted in nature, mythology, and the supernatural.	draft	<p>In ancient Scotland, story-telling was deeply rooted in Celtic tradition. The Picts and Scotts, inhabiting Scotland from around 400 BC to AD, orally passed down tales grounded in nature, mythology, and the supernatural.</p>\n<p>Storytelling techniques varied. Tales were embedded in seasonal cycles or daily life rituals. Genres ranged from creation myths to heroic epics. Characters included gods and goddesses like the Morrigan and Dagda, as well as animals or natural phenomena.</p>\n<p>Stories were shared during gatherings, often accompanied by music or dance. Storytellers used inflections and voice modulations to bring characters to life, captivating audiences with vivid descriptions and moral underpinnings.</p>\n<p>These stories have survived, inspiring awe, wonder, and respect for Scotland's rich storytelling heritage.</p>	In ancient Scotland, story-telling was deeply rooted in Celtic tradition. Orally passed down through generations, these tales were often grounded in nature, mythology, and the supernatural. Celtic tribes, such as the Picts and Scotts, inhabited Scotland from around 400 BC to AD 900. They believed that stories held great power, reflecting their deep connection with the land and its spirits.\n\nAncient Celtic story-telling employed various techniques. Stories were often embedded in seasonal cycles or daily life rituals, creating a sense of continuity and belonging. The tales themselves varied widely in genre, from creation myths to heroic epics. Many featured gods and goddesses like the Morrigan, the triple goddess of war and fate; and the Dagda, the father-god. Others revolved around animals or natural phenomena, such as the transformative power of water or the sun's daily journey across the sky.\n\nThese tales were shared during gatherings, often accompanied by music or dance. Storytellers, revered for their abilities, would use inflections and voice modulations to bring characters to life. Their narratives captivated audiences with their vivid descriptions and moral underpinnings, providing insight into the worldviews of ancient Celts. These stories have survived the test of time, continuing to inspire awe, wonder, and respect for Scotland's rich storytelling heritage.	<!--_live_preview_content_will_20250726_143054_b61512.png	2025-07-26 14:30:56.157145
713	53	5	Preserving Cultural Traditions through Story-telling	Topic 1: The role of story-telling in preserving oral traditions and folklore in Scotland\nTopic 2: Specific examples of folk stories that have been passed down through generations, such as "The Selkies" or "The Brownie"\nTopic 3: Story-telling in education: how Scottish schools are teaching children traditional stories to preserve cultural heritage\nTopic 4: Festivals and events dedicated to Scottish story-telling and preserving cultural traditions, like the "Edinburgh International Festival of Storytelling"\nTopic 5: The use of story-telling in modern advertising campaigns that honour Scotland's rich history and folklore\nTopic 6: Story-quilts: the art of telling stories through textiles and their significance in preserving cultural traditions\nTopic 7: Collaborative story-making within Scottish communities, such as "The Scotsman's Hame" project\nTopic 8: The role of museums and galleries in preserving and showcasing Scotland's rich story-telling heritage, like the "National Museum of Scotland"\nTopic 9: Story-telling in music: Scottish artists and bands that weave traditional tales into their songs and performances\nTopic 10: The impact of social media on the revival and dissemination of traditional stories, allowing for a wider audience and reach.	\N	\N	 Image Description:\n\nThe image is a digital collage depicting the fusion of Scotland's ancient storytelling traditions with modern elements. The background is an authentic, textured image of a Scottish landscape featuring rolling hills, lush greenery, and a clear blue sky. In the foreground, there is a wooden table with aged parchment papers and quills, symbolizing the historic oral and written storytelling methods.\n\nIn the bottom left corner, there's an image of a monk sitting at a similar table, copying texts from an ancient manuscript. This represents the role of religious stories in preserving traditions during medieval times. In the top right corner, there is a modern-day scene showing a woman wearing a traditional Scottish kilt and holding a tablet with a digital storybook on it. This illustrates how contemporary storytellers are embracing technology to preserve and share Scotland's rich cultural heritage.\n\nAt the center of the image, there's an open book, its pages filled with various scenes inspired by different stories – an ancient Celtic mythological creature appearing among the woods, a monk in a cloister copying texts, and a modern-day urban setting with characters from Robert Louis Stevenson's Treasure Island or J.M. Barrie's Peter Pan. This illustrates how storytelling has evolved over time while remaining deeply connected to Scotland's unique cultural traditions.\n\nThe image is designed in monochrome tones for a classic, timeless feel that emphasizes the historical significance of storytelling in Scotland while also highlighting its relevance and vibrancy in modern times.	 Image Description:\n\nA digital collage unfolds, blending Scotland's ancient storytelling heritage with contemporary elements. The backdrop is an authentic Scottish landscape: hills roll with lush greenery, a clear blue sky blankets above, and textured terrain weaves beneath. In the foreground, an antiquated wooden table emerges, bearing aged parchment and quills – vestiges of historic oral and written storytelling techniques.\n\nBottom left: A monk sits at a similar table, engrossed in copying from ancient texts. This symbolizes religion's role as tradition preserver during medieval periods.\n\nTop right: A woman donning a kilt stands, clutching a tablet showcasing a digital storybook. Modern storytellers embrace technology to preserve and share Scotland's heritage.\n\nCentral focus: An open book reveals various scenes - an ancient Celtic creature wandering among woodlands, monks cloistered in copying texts, and urban settings with characters from Stevenson's Treasure Island or Barrie's Peter Pan. Storytelling evolves while staying rooted in Scotland's rich cultural traditions.\n\nMonochrome tones dominate, emphasizing historical significance while accentuating modern relevance. Classic timelessness is intertwined with vibrant contemporary resonance.	\N	 Image Ideas:\n\nImage Concept: A vibrant tapestry being woven in the heart of an ancient Scottish village, filled with intricate threads that tell the story of Scotland's rich cultural traditions. The tapestry is adorned with various motifs representing oral tales, mythology, folklore, nature, and religious stories from different periods.\n\nLayout: The image features a wide, horizontal composition to accommodate the intricacies of the woven tapestry. It captures a close-up view of the weaving process, giving viewers an intimate look at the interconnected threads and designs. The scene is set in a dimly lit room with a fireplace in the background, casting a warm, inviting glow over the villagers who gather around to contribute their stories and ideas for the tapestry.\n\nKey Features: \n1. Vibrant colors and intricate patterns representing various Scottish folktales, mythology, nature, and religious stories.\n2. Villagers huddled around the weaving process, each contributing ideas or sharing stories that will be woven into the tapestry.\n3. A fireplace in the background providing a warm, inviting atmosphere.\n4. Detailed close-ups of individual threads and knots, symbolizing the interconnectedness of various stories within Scotland's rich cultural heritage.\n5. Subtle elements representing contemporary storytelling methods like podcasts, film, and television productions, signifying the continuation and evolution of traditional Scottish storytelling techniques.\n\nVisual Context: The image captures a moment of unity and creativity within the Scottish community as they work together to preserve their cultural traditions through story-telling. The tapestry acts as a visual representation of Scotland's rich history, showcasing various motifs and themes from different periods while also highlighting the importance of oral traditions and contemporary storytelling methods in shaping Scotland's national identity.	The significance of story-telling in preserving Scotland's cultural traditions and its role in shaping the country's national identity.	draft	<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n    <title document></title>\n  </head>\n  <body>\n    <p>\n      In ancient Scotland, story-telling held significance in Celtic culture. Narratives were orally passed down with themes rooted in nature, mythology, and the supernatural.\n    </p>\n    <p>\n      The Celts had a strong connection to the land, reflected in their stories. Many featured gods and goddesses symbolizing aspects of nature, such as Eostre, representing springtime and rebirth.\n    </p>\n    <p>\n      The supernatural also fascinated the Celts, with numerous myths featuring spirits, fairies, and magical creatures.\n    </p>\n    <p>\n      These stories offered insights into early Scottish societies' beliefs and values, preserving cultural traditions through generations.\n    </p>\n    <p>\n      Themes from these tales continue resonating with modern Scots, linking us to our past.\n    </p>\n  </body>\n</html	In Scotland, story-telling has long been a powerful means of preserving cultural traditions. Oral tales passed down through generations kept the ancient Celtic mythology and folklore alive. These stories often revolved around nature, supernatural beings, and local legends, which helped foster a deep connection with the land and its people.\n\nAs Christianity spread throughout Scotland during the medieval period, religious stories became integral to preserving cultural traditions. Monks copied sacred texts into illuminated manuscripts that survive today, offering invaluable insights into Scotland's early history. Ballads and epic poems served similar purposes, recording heroic deeds and historical events that might have otherwise been lost to time.\n\nIn modern times, story-telling has continued to play a crucial role in preserving Scottish traditions. The works of influential authors like Robert Louis Stevenson, J.M. Barrie, and Neil Gaiman have captured the world's imagination while highlighting the unique aspects of Scotland's culture. From the adventure tales of Treasure Island and Peter Pan to the supernatural elements in Sandman, these stories left an indelible mark on Scottish literature and popular culture.\n\nMoreover, story-telling continues to thrive in contemporary Scotland. Oral traditions persist through community events, while innovative storytellers explore new mediums like podcasts, film, and television productions. These creations help preserve Scotland's rich cultural heritage while engaging modern audiences, ensuring that the stories continue to captivate and inspire future generations.	scottish_section_713,_realisti_20250726_134921_9402e9.png	2025-07-26 13:49:23.160768
711	53	2	Medieval Period: Recording Stories	In the medieval period in Scotland, stories were primarily transmitted orally through bards and wandering storytellers. The following topics delve into various aspects of recording these tales during this era:\n\n1. Monasteries as Storykeepers: The significant role monasteries played in copying and preserving religious stories and ballads using parchment, quills, and ink.\n2. Illuminated Manuscripts: The artistic illustrations accompanying medieval Scots' tales, adding to their beauty and importance.\n3. Bards and Their Ballads: An exploration of the profession of bards who memorized long narrative poems, carrying on the oral tradition.\n4. Storytelling Tales of Heroes: A focus on heroic stories that were sung or recited in Scotland during the medieval period, showcasing tales of valor and chivalry.\n5. The Oral Poetry Tradition: An analysis of the structure and rhyme schemes used in the oral poetry tradition prevalent during this era.\n6. Storytelling Festivals: Discovering how storytelling festivals played a crucial role in preserving these ancient tales and connecting communities throughout Scotland.\n7. Sagas and Folktales: The significance of sagas and folktales, which often contained lessons or morals, in spreading stories among the Scottish populace.\n8. Interpreting Symbolism in Medieval Stories: Unraveling the symbolic meanings behind some popular medieval tales that continue to intrigue us today.\n9. Storytelling Instruments and Accessories: The importance of various musical instruments and storytelling tools used during the medieval period to enhance performances.\n10. Transmitting Tales Across Borders: Exploring how stories from neighboring lands influenced Scottish tales, as well as instances where Scottish stories traveled abroad.	\N	\N	 Image Description:\n\nThe image features a monk sitting at a wooden table in a dimly lit, stone-walled cell in a medieval Scottish monastery. The room is filled with stacks of parchment scrolls and ink pots on the table, indicating the monk's dedication to preserving the oral traditions of his time. A quill pen is in his hand, poised above an open scroll, ready for writing.\n\nIn the background, a fire crackles in the hearth, casting flickering shadows across the room. Above the fireplace hangs a large, ornate cross made of oak wood, symbolizing the strong influence of Christianity during this era. Through the small, arched window above the monk's shoulder, the moonlit landscape outside can be seen – rolling hills, a nearby loch reflecting the night sky, and the faint outline of a castle on the horizon.\n\nThis image illustrates the theme of storytelling during the medieval period in Scotland, with the monk representing the key figures who played an essential role in laying the foundation for future literary achievements by recording religious tales, ballads, and epic poems. The focus is on the monk's dedication to his craft and the importance of preserving oral traditions through manuscripts. The image has a single clear topic – the act of recording stories during the medieval period in Scotland – and avoids romanticism, clichés, or stereotypes.	 Monk, seated at a weathered wooden table in a dimly lit, stone-walled cell, surrounded by towering stacks of parchment scrolls and ink pots. Quill pen poised above an open scroll, fire crackling in hearth, casting dancing shadows. Ornate oak cross hangs above hearth. Moonlit landscape - rolling hills, loch reflecting night sky, castle outline, through small arched window on monk's shoulder. Medieval Scotland: storytelling, dedication, preservation of oral traditions.	\N	 Image Concept:\n\nThe image should depict a monk sitting at a long table in a dimly lit monastery room. In front of him are open manuscripts and scrolls, quills and ink pots nearby. He is engrossed in copying an intricate illustration from one of the parchments onto another. The scene should have an air of reverence and importance, emphasizing the significance of recording these stories for future generations.\n\nThe illustration being copied should be a section from a religious story, possibly featuring a saint or an event from their life. The artwork around it should showcase intricate details and vivid colors, symbolizing the beauty and importance of these ancient tales. A small window on one side of the room lets in soft natural light, creating an inviting atmosphere and highlighting the monk's dedication to his craft.\n\nKey Features:\n1. Monastery setting: A monastery background with its typical architectural elements such as stone walls, wooden tables, and stained glass windows.\n2. Monk at work: The monk should be portrayed in detail, with accurate attire and posture, to evoke a sense of authenticity and devotion.\n3. Illuminated manuscripts: Detailed and colorful illustrations on the manuscripts and scrolls, representing the rich visual storytelling traditions during this era.\n4. Tools of the trade: Ink pots, quills, parchment, and other essential tools should be included in the scene to reinforce the act of recording stories.\n5. Soft natural light: A small window with soft natural light entering the room, symbolizing knowledge and enlightenment.\n6. Symbolic religious imagery: The illustration being copied or nearby elements should include symbols representative of Christianity or other dominant faiths during this era.\n7. Ambiance of reverence: A serene, quiet, and contemplative atmosphere to emphasize the importance of preserving these ancient stories.	The role of story-telling during the medieval period in Scotland, focusing on religious stories, ballads, and epic poems that laid the groundwork for future literary achievements.	draft	<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  </head>\n  <body>\n    <p>\n      During the medieval period in Scotland, stories began to be recorded for the first time. Monks in monasteries were key figures in this process, preserving oral traditions through manuscripts.\n    </p>\n    <p>\n      Religious stories played a significant role during this era, with Christianity becoming the dominant faith. These narratives often revolved around saints' lives and moral teachings, providing guidance to the populace.\n    </p>\n    <p>\n      Ballads dealt with various themes like love, heroism, and historical events. They were passed down orally before being committed to parchment.\n    </p>\n    <p>\n      Monks also penned down epic poems, such as "The Song of Roland" and "Beowulf." These lengthy narratives featured heroes embarking on quests and overcoming adversity, inspiring a sense of pride and unity among their respective communities.\n    </p>\n    <p>\n      Overall, the act of recording stories marked an essential milestone in Scotland's rich literary history.\n    </p>\n  </body>\n</html	During the medieval period in Scotland, stories began to be recorded for the first time. Religious tales, ballads, and epic poems were penned down, laying the foundation for future literary achievements. Monks in monasteries were key figures in this process, preserving oral traditions through manuscripts.\n\nReligious stories played a significant role during this era, with Christianity becoming the dominant faith. These narratives often revolved around saints' lives and moral teachings, providing guidance to the populace. Ballads, on the other hand, dealt with various themes like love, heroism, and historical events. They were passed down orally before being committed to parchment.\n\nEpic poems, such as "The Song of Roland" and "Beowulf," also originated during this period. These lengthy narratives featured heroes embarking on quests and overcoming adversity, inspiring a sense of pride and unity among their respective communities. Overall, the act of recording stories marked an essential milestone in Scotland's rich literary history.	<!--_live_preview_content_will_20250726_143110_b61512.png	2025-07-26 14:31:12.038027
715	53	6	Impact of Scottish Story-telling on Literature and Culture	Topic 1: Influence on Children's Literature: From "Alice in Wonderland" to Harry Potter, explore how Scottish story-telling has shaped the realm of children's literature.\nTopic 2: Adaptations and Transformations: Delve into examples of classic Scottish stories that have been adapted for stage, screen, and radio.\nTopic 3: Story-telling in Scottish Poetry: Examine how Scottish poets like Robert Burns, Violet Jacob, and Edwin Morgan have drawn inspiration from Scotland's rich story-telling tradition.\nTopic 4: Fairy Tales and Folklore: Explore the enduring popularity of Scottish fairy tales and folktales, such as "The Selkie" and "Thistle the Whanging Cat."\nTopic 5: Story-telling in Contemporary Fiction: Highlight modern Scottish authors like Alan Warner, Janice Galloway, and A.L. Kennedy who continue to weave magical tales set in Scotland.\nTopic 6: International Influence: Discuss how Scottish story-telling has influenced the works of non-Scottish authors, such as J.K. Rowling, Robert Louis Stevenson, and Washington Irving.\nTopic 7: Story-telling in Art and Music: Explore how visual artists and musicians have drawn inspiration from Scotland's story-telling tradition, from paintings to opera.\nTopic 8: Tourism and Story-telling: Discuss how story-telling plays a role in attracting tourists to Scotland, with examples like the "Scottish Fairy Trail," the "Robert Burns Birthplace Museum," and the "Harry Potter" tours.\nTopic 9: Oral Tradition Revival: Talk about initiatives that aim to preserve oral story-telling traditions through events, workshops, and educational programs.\nTopic 10: Story-telling in Modern Media: Discuss how podcasts, film, television productions, and other modern media continue to reflect and contribute to Scotland's rich story-telling heritage.	\N	\N	 Image Description:\n\nThe image is a digitally painted illustration set against an overcast Scottish landscape. In the foreground, there's a figure of an elderly man sitting cross-legged on a large boulder, facing a young boy who sits in front of him. The old man wears a tartan kilt and a woolen sweater, while the boy dons a modern school uniform. They are both engrossed in a storybook, its pages flipping open to reveal intricate scenes from Scottish folklore.\n\nThe background shows rolling green hills, a misty loch reflecting the sky, and a faint silhouette of a castle on a distant hilltop. A gentle rain falls over them, adding to the peaceful atmosphere. The color palette is warm and inviting, with pops of red from the tartan fabric and autumnal hues from the landscape.\n\nKey Features:\n1. The focal point is the old man storytelling to the young boy, symbolizing the passing down of Scottish stories through generations.\n2. The modern and traditional elements represent how these stories continue to evolve while respecting their historic roots.\n3. The landscape serves as a reminder of the rich Scottish heritage and history associated with these tales.\n4. The image conveys a sense of warmth, connection, and continuity, emphasizing the importance of storytelling in preserving culture and identity.	 Image Description: An elderly man in a tartan kilt and woolen sweater sits cross-legged on a large boulder, engrossed in an open storybook. Before him, a young boy in modern school uniform listens intently. Rolling green hills and a misty loch form the backdrop, with a castle silhouette peeking from a distant hilltop. They are both nestled under a warm-toned overcast sky, surrounded by autumnal hues and pops of red from the tartan fabric. Gentle rain adds tranquility as they immerse themselves in Scottish folklore, symbolizing tradition's preservation through generations.	\N	 Image Idea:\n\nTitle: "The Influence Tree"\n\nDescription:\nThe image features a large, ancient tree in the center, its trunk covered in intricately carved symbols, illustrations, and stories from Scottish folklore. The tree's branches extend outwards, reaching towards the sky and forming a sprawling canopy. Each leaf on the branches represents a different aspect of Scottish story-telling - children's literature, adaptations and transformations, fairy tales and folklore, contemporary fiction, art and music, oral traditions, tourism, and modern media.\n\nThe leaves are adorned with vibrant illustrations, showcasing various scenes from these topics - a young girl reading an enchanted book under a tree, a traditional Scottish ballad being sung by a bard, children playing near a fairy trail, a painter inspired by the beauty of Scotland's landscapes and mythology, and tourists exploring story-rich sites like the Robert Burns Birthplace Museum.\n\nThe tree's roots reach deep into the earth, symbolizing the strong connection between Scottish stories and their origins, while its abundant foliage and the interconnectedness of the branches represent the far-reaching influence of these tales on literature and culture both within Scotland and beyond its borders. The background is filled with soft, muted colors inspired by Scotland's natural beauty, creating a serene and captivating environment.\n\nMain Features:\n1. Ancient tree as a central motif representing the rich history of Scottish story-telling.\n2. Carved symbols and illustrations on the trunk depicting various stories from Scottish folklore.\n3. Branches with leaves representing different aspects of Scottish story-telling, each adorned with vibrant illustrations showcasing scenes from these topics.\n4. Soft, muted background colors inspired by Scotland's natural beauty.\n5. Detailed and intricate visual elements that capture the imagination and evoke a sense of wonder and curiosity.	The influence of Scottish story-telling on both Scottish literature and popular culture as a whole.	draft	<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n<body>\n    <p>Scottish story-telling has significantly influenced literature and culture, both in Scotland and globally. From ancient Celtic tales to works by notable Scottish authors, these stories have left an indelible mark.</p>\n    <p>Notable works include "Treasure Island" by Robert Louis Stevenson and "Peter Pan" by J.M. Barrie. Their iconic characters and themes continue to resonate worldwide.</p>\n    <p>Authors like Neil Gaiman expanded the literary landscape, combining elements of fantasy and reality in captivating ways.</p>\n    <p>Beyond literature, story-telling has influenced art forms such as film, music, and visual arts. For instance, "Braveheart" and "Trainspotting" brought raw Scottish life to the big screen.</p>\n    <p>Traditional folktales inspire contemporary musicians with songs carrying tales of mythical creatures, heroes, and heartbreak.</p>\n    <p>In modern society, story-telling preserves cultural traditions and shapes Scotland's national identity. This occurs through oral narratives, literature, films, podcasts, and other mediums.</p>\n</body>\n</html>	Scottish story-telling has had a profound impact on literature and culture both within Scotland and beyond its borders. From ancient Celtic tales that captured the imagination of generations to the masterpieces penned by notable Scottish authors, these stories have left an indelible mark on various art forms.\n\nInfluential works like "Treasure Island" by Robert Louis Stevenson and "Peter Pan" by J.M. Barrie have contributed significantly to popular culture, introducing iconic characters and themes that continue to resonate with audiences worldwide. Neil Gaiman's dark yet magical tales further expanded the literary landscape, combining elements of fantasy and reality in a way that captivated readers.\n\nBeyond literature, Scottish story-telling has influenced various artistic expressions such as film, music, and visual arts. For instance, movies like "Braveheart" and "Trainspotting" have brought the raw energy and complexity of Scottish life to the big screen. Moreover, traditional Scottish folktales continue to inspire musicians, with songs carrying tales of mythical creatures, heroes, and heartbreak.\n\nIn contemporary society, story-telling remains a powerful tool for preserving cultural traditions and shaping Scotland's national identity. Through oral narratives, literature, films, podcasts, and other mediums, Scottish stories continue to evolve, showcasing the resilience, creativity, and deep connection with our rich history and heritage.	scottish_section_715,_realisti_20250726_134953_3bcff9.png	2025-07-26 13:49:55.130387
\.


--
-- Data for Name: post_section_backup_20250109; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section_backup_20250109 (id, post_id, section_order, section_heading, ideas_to_include, facts_to_include, first_draft, uk_british, highlighting, image_concepts, image_prompts, generation, optimization, watermarking, image_meta_descriptions, image_captions, image_prompt_example_id, generated_image_url, image_generation_metadata, image_id, section_description, status) FROM stdin;
675	1	1	The Ancient Kingdoms of Scotland	Include information about Pictish stone carvings and their significance in Scottish history	\N	 In the early chapters of Scotland's storied history, three distinct groups left indelible marks on the land and its people: the Picts, Scots, and Vikings. The Ancient Kingdoms of Scotland, as we delve into this period, offer a rich tapestry of intrigue and discovery.\n\nThe enigmatic Picts, inhabiting the northeastern parts of Scotland from around 300 AD, are celebrated for their unique cultural contributions. Known for their intricate stone carvings, these enigmatic people left behind an enduring legacy in Scottish history. These Pictish symbols, often found on standing stones and carved stones, continue to puzzle scholars with their meanings and origins. Their artistic creations speak volumes about the society and beliefs that once thrived in these shores.\n\nAs we journey further back in time, the Scots emerged as another powerful force in Scotland's ancient landscape. Originating from Ireland around 500 AD, they brought with them a new wave of influences that moulded Scotland into the land it is today. The Scots are renowned for their martial prowess and strategic acumen, laying the groundwork for the complex Scottish social structure that would unfold in later centuries.\n\nLastly, we cannot overlook the profound impact of the Vikings on Scotland's ancient story. Hailing from Scandinavia between the 8th and 11th centuries, these seafaring raiders established settlements along Scotland's eastern coastline. They left behind a lasting imprint through their cultural practices and interactions with the native Picts and Scots, shaping the very fabric of Scottish society.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.	draft
669	22	2	The Evolution of Scottish Storytelling: From Royal Courts to Modern-Day Novelists	 In the rich tapestry of Scottish storytelling, the evolution from medieval makars to contemporary novelists is an intriguing chapter. This period saw the emergence of distinct voices that shaped Scotland's literary heritage.\n\nDuring the 14th-century, makars or poets, were vital figures in royal courts, crafting verse for noble patrons and recording historical events in poetic form. Their work not only showcased their poetic prowess but also preserved stories and values of the time. This tradition continued well into the 16th-century with poets like William Dunbar and Robert Henryson contributing to Scotland's rich literary heritage.\n\nAs the world turned towards print, Scottish storytelling adapted. From the 17th-century onwards, writers began to explore the potential of prose narratives. Authors such as Allan Ramsay and Walter Scott drew inspiration from Scotland's rugged landscapes and complex history, penning works that captivated audiences both at home and abroad. Their tales brought Scottish storytelling into a new era, setting the stage for modern-day novelists like Irvine Welsh and J.K. Rowling.\n\nThrough this transformation, key themes and motifs continued to resonate within Scottish storytelling. The connection between personal identity and the natural world, exploration of societal norms, and a deep appreciation for Scotland's rich history remain integral elements of contemporary Scottish literature.	\N	 In the 14th-century, Scottish storytelling was shaped by the makars, or poets, who held significant influence in royal courts. These creative individuals crafted verse for noble patrons and documented historical events poetically. The work of these makars not only showcased their poetic skills but also preserved stories and values of the time. This tradition extended well into the 16th-century with poets like William Dunbar and Robert Henryson contributing to Scotland's literary heritage.\n\nAs the world turned towards print, Scottish storytelling adapted. From the 17th-century onwards, writers began to explore prose narratives. Authors such as Allan Ramsay and Walter Scott drew inspiration from Scotland's rugged landscapes and complex history, penning works that captivated audiences at home and abroad. Their tales set the stage for modern-day novelists like Irvine Welsh and J.K. Rowling.\n\nThrough this transformation, key themes and motifs continued to resonate within Scottish storytelling. The connection between personal identity and the natural world, exploration of societal norms, and a deep appreciation for Scotland's rich history remain integral elements of contemporary Scottish literature.	\N	\N	 Image Description:\n\nTitle: "The Timeless Tale: A Journey Through Scottish Storytelling"\n\nDescription:\n\nThis captivating illustration portrays a winding, scroll-like path extending from the royal castle at its centre to a contemporary novelist's writing desk. The castle represents the early origins of Scottish storytelling in the 14th century and is adorned with intricate carvings depicting scenes from medieval tales like those of William Tell (or Tam Lin) or Macbeth.\n\nAs we follow this path, it passes through various periods in Scottish history – a bustling marketplace teeming with traders sharing stories, an open-air gathering of villagers listening intently to a storyteller weaving an ancient yarn, and finally arriving at a modern-day library filled with books that continue these age-old narratives.\n\nThe characters and motifs from traditional tales subtly weave their way along the path, providing visual connections between the past and present. This stunning depiction highlights how Scottish storytelling has evolved over the centuries while retaining its essential essence – a powerful means of sharing history, culture, and values.	 Title: The Evolution of Scottish Storytelling: A Journey Through Time\n\nSection Heading: The Evolution of Scottish Storytelling: From Royal Courts to Modern-Day Novelists\n\nInstruction for Image Generation:\n\nCreate an image in a loose and airy pen & ink wash style, 2240 x 1256 pixels in landscape orientation. The colouring schema should be consistent with the tone of the article, which is realistic rather than romantic. depict a scene that illustrates the evolution of Scottish storytelling from medieval times to contemporary novelists.\n\nIn the foreground, include an image of a 14th-century bard (makar) reciting stories for a noble audience at the royal court. The bard should be dressed in appropriate clothing from this historical period – a long tunic with a belted plaid and a woolen cloak. He should carry a harp or other musical instrument, symbolizing the oral tradition of storytelling.\n\nIn the middle ground, depict a scene of children huddled around a fire in a traditional Scottish cottage, listening to an older woman telling tales of folklore and mythology. The older woman can be dressed in traditional Scottish attire – a long skirt, blouse, and shawl. She may carry a wooden spoon or other implement, used to add emphasis to her stories.\n\nIn the background, represent modern-day authors writing at their desks, surrounded by books and other literary paraphernalia. They can be depicted in more contemporary clothing. One author may be seen typing on a computer, symbolizing the digital evolution of storytelling.\n\nThe image should have a soft, faded effect around the edges to mimic the pen & ink wash style and create a sense of depth. The colouring schema should remain consistent throughout, with darker tones for the foreground scenes and lighter tones in the background as the focus shifts to contemporary times. No hard edges should be present on any side of the image.	\N	\N	\N	\N	\N	\N	\N	\N	\N	Tracing the development of Scottish storytelling from the 14th-century makars to contemporary authors, highlighting key themes and motifs	draft
670	22	3	Oral Tradition and Literary Heritage: The Threads that Bind Scotland's Storytelling	 In the heart of Scotland's storytelling tradition lie the threads of oral tradition and literary heritage, which have bound the nation's cultural identity for generations. Oral tradition refers to the passing down of stories, poems, ballads, and folklore through spoken word from one generation to the next. This ancient practice allowed Scottish communities to preserve their history, values, and social norms long before the advent of written records.\n\nLiterary heritage, on the other hand, encompasses the written works that have emerged from Scotland's rich storytelling tradition. From the 14th-century makars who crafted verse for royal courts to the modern-day novelists who draw inspiration from Scotland's rugged landscapes and complex history, these literary expressions reflect the nation's unique voice and contribute significantly to its cultural fabric.\n\nOral tradition and literary heritage are inextricably linked, with each influencing the other throughout history. Oral tales often served as the inspiration for written works, while the act of committing stories to writing helped preserve their essence for future generations. Today, these threads continue to shape Scotland's storytelling landscape, providing a rich tapestry of narrative that both reflects and enriches its past and present.	\N	 In the heart of Scotland's storytelling tradition lies a deep-rooted connection between oral tradition and literary heritage. Oral tradition refers to the age-old practice of passing down stories, poems, ballads, and folklore through spoken word from one generation to the next. This ancient method allowed Scottish communities to preserve their history, values, and social norms long before the advent of written records.\n\nLiterary heritage, on the other hand, encompasses the vast body of written works that have emerged from Scotland's rich storytelling tradition. From 14th-century makars who composed verse for royal courts to modern-day novelists drawing inspiration from Scotland's rugged landscapes and complex history, these literary expressions reflect the nation's unique voice and significantly contribute to its cultural fabric.\n\nThese threads of oral tradition and literary heritage are intricately linked, each influencing the other throughout history. Oral tales often served as the inspiration for written works, while committing stories to writing helped preserve their essence for future generations. Today, these threads continue to shape Scotland's storytelling landscape, providing a rich tapestry of narrative that both reflects and enriches its past and present.	\N	\N	 Image Description:\n\nTitle: "Weaving the Past into the Present: A Tapestry of Scottish Storytelling"\n\nDescription:\n\nThis captivating image showcases a beautifully intricate tapestry, woven with threads of various colours and textures that represent Scotland's rich storytelling heritage. The tapestry is set against a backdrop of an open hearth, reminiscent of a Scottish cottage or clan gathering place.\n\nAt the bottom left corner of the image, there's a representation of an ancient bard reciting a tale aloud to a rapt audience, symbolising the importance of oral tradition in Scottish storytelling. The threads in this part of the tapestry are depicted as thick and rough, representing the raw, unrefined nature of early storytelling.\n\nMoving towards the centre of the tapestry, there's a scene featuring a monk diligently copying an ancient manuscript under soft candlelight – symbolising the importance of literary heritage in preserving and passing down these stories through generations. The threads in this section are finer and more delicate compared to those at the bottom.\n\nThe upper right corner of the tapestry is filled with modern illustrations of Scottish tales, such as a Selkie transforming into her seal form, Tam Lin's enchanted forest, or Macbeth's castle – representing the evolution and adaptations of these stories in contemporary times. The threads in this part of the tapestry are bright and vibrant, reflecting the creativity and innovation present in modern storytelling.\n\nThe final thread that binds all sections of the tapestry together is a golden one, symbolising the lasting impact and influence of Scottish storytelling on Scotland's cultural identity. This golden thread intertwines with the other threads at various points, demonstrating the intricate connections between past and present, oral tradition, and literary heritage.\n\nThe overall composition of the image conveys a sense of history, continuity, and the timelessness of Scottish storytelling.	 Create an image of two figures engaging in an old Scottish storytelling tradition. The scene should take place outdoors, with rolling green hills and a clear blue sky in the background. One figure, dressed in traditional Scottish attire from centuries ago, sits cross-legged on the ground with a quill pen and inkwell in hand. He is recounting a tale to another figure standing beside him, who listens intently. The standing figure wears modern clothing, indicating a contemporary audience.\n\nBoth figures should have expressive faces, capturing the emotions of the moment – fascination, curiosity, or wonder. The older figure's clothing includes a plaid kilt, a woollen jumper with intricate patterns, and a tam o'shanter cap. His hands should be animated as he tells the story.\n\nThe younger figure wears casual clothing appropriate for the present day – jeans, a t-shirt, and a light jacket. He leans forward, fully absorbed in the narrative. The older figure's parchment lies open on his lap, with ink lines visible from the quill as he speaks.\n\nThe image should be executed in a loose, airy pen & ink wash style reminiscent of traditional Scottish calligraphy and illuminated manuscripts. The colouring schema should consist primarily of earthy tones – browns, greens, and blues – to emphasise the connection between storytelling and Scotland's natural beauty.\n\nEnsure that all details are anatomically correct for their historical periods and geographical location. The image should be in 2240 x 1256 landscape orientation and fade (as irregular brushstrokes) to pure white on all sides with no hard edges.	\N	\N	\N	\N	\N	\N	\N	\N	\N	Examining the role of oral tradition and literary heritage in shaping Scotland's cultural identity and storytelling practices	draft
672	22	5	Subversion and Social Commentary: The Power of Scottish Storytelling to Challenge and Educate	 Scottish storytelling has long held a powerful role in challenging social norms and educating its audience, both in medieval times and the present day. Throughout history, tales have been used as vehicles for social commentary, allowing listeners to question societal expectations and explore new ideas.\n\nIn the Middle Ages, bards and skalds weaved intricate narratives that subtly criticised the ruling classes or promoted moral values. The Ballad of Sir Patrick Spens, for instance, disguises a prophecy about a disastrous sea voyage as an entertaining story, while carrying a deeper message about treachery and betrayal.\n\nFast forward to modern times, and Scottish storytelling continues to push boundaries. Writers like Alasdair Gray and Irvine Welsh have employed scathing satire and raw realism to critique society and challenge conventions. Their works often reflect the complexities of urban life in Scotland, offering a nuanced perspective on contemporary issues.\n\nThese stories not only entertain but also serve as powerful educational tools, shedding light on historical events and cultural values. By exploring themes of social justice, identity, and resistance, they foster a deeper understanding of Scotland's rich heritage and ongoing relevance in the world.	\N	 Scottish storytelling has held a significant role in challenging social norms and educating its audience throughout history. In medieval times, bards and skalds employed intricate narratives to subtly criticise the ruling classes or promote moral values. The Ballad of Sir Patrick Spens is an example, disguising a prophecy about a disastrous sea voyage as an entertaining story while carrying a deeper message about treachery and betrayal (Scott, 1961).\n\nFast-forward to modern times, and Scottish storytelling continues to push boundaries. Writers like Alasdair Gray and Irvine Welsh use scathing satire and raw realism to critique society and challenge conventions. Their works often reflect the complexities of urban life in Scotland, offering a nuanced perspective on contemporary issues (Gray, 1981; Welsh, 1993). These stories entertain while serving as powerful educational tools, shedding light on historical events and cultural values. They explore themes of social justice, identity, and resistance, fostering a deeper understanding of Scotland's rich heritage and ongoing relevance in the world.	\N	\N	 Image Description:\n\nTitle: "Subversion and Social Commentary in Scottish Storytelling: Challenging Norms Throughout History"\n\nMain Feature 1: A collage of scenes portraying various moments from Scottish stories, with each scene demonstrating subversion or social commentary. For instance, one scene could depict Tam Lin's story with Janet defying societal expectations to save her lover. Another may show Macbeth's witches prophesising against the established power structures of their time.\n\nMain Feature 2: In the foreground, a figure sits on a large, open book, surrounded by an array of traditional Scottish storytelling tools such as a quill pen, inkwell, and parchment. This figure represents the role of the storyteller, emphasising the importance of passing down these narratives to future generations.\n\nMain Feature 3: The background includes an abstract representation of a crowd, symbolising diverse audiences throughout history who have been captivated by the powerful messages within Scottish stories.\n\nMain Feature 4: Interspersed amongst the scenes are elements representing contemporary forms of storytelling, such as tablets and smartphones, emphasising how these traditional tales continue to influence modern narratives.\n\nOverall, this image conveys the rich history and ongoing relevance of Scottish storytelling in challenging societal norms and educating audiences, from ancient times to the present day.	 Create an image of a scene where storytelling is subverting social norms in Scottish culture. Visualize a gathering of people, both men and women, from different periods in Scottish history, seated in a circular arrangement around a central figure. The central figure is an animated storyteller, dressed in traditional Scottish attire from the medieval era, with a quill pen in hand and a captivated audience hanging onto his every word.\n\nIn the image, some characters are engaging in subtle but significant interactions that challenge social norms. For instance, a woman wearing modern clothing is listening intently to an older man's story, while another man, dressed in Scottish Highland garb from the 18th century, shares a secretive glance with a woman who wears a sari, symbolizing cultural exchange and acceptance beyond historical boundaries.\n\nUse loose pen & ink wash brushstrokes, creating irregular edges that give a sense of organic movement and flow in the image. The colours should be muted, evoking an authentic historic feel, but also possessing a hint of vibrancy to represent the power of the stories being told. Ensure all figures are proportionally correct for their historical periods, and pay attention to details such as clothing, accessories, and facial expressions.\n\nBlend the image so that it fades gently to white on all sides with no hard edges. The overall tone should be realistic, with the focus on the powerful impact of Scottish storytelling in challenging social norms and educating its audiences throughout history.	\N	\N	\N	\N	\N	\N	/static/uploads/images/section_672_20250709_105226_1d283457.png	{"file_size": 3167990, "uploaded_at": "2025-07-09T10:52:26.781480", "upload_method": "manual", "original_filename": "image.png"}	\N	Exploring how Scottish storytelling has been used to subvert social norms, educate, and entertain, from medieval times to the present day	draft
674	22	7	Contemporary Expressions: How Scottish Storytelling is Evolving in the Digital Age	 In today's digitally connected world, Scottish storytelling continues to evolve, adapting to new technologies, platforms, and mediums. This transformation is evident in various forms, from online literature to interactive multimedia experiences. One striking example is the emergence of digital storytelling platforms, which allow artists, writers, and performers to share their stories with a global audience.\n\nThese innovative spaces provide opportunities for experimentation, fostering a rich tapestry of contemporary Scottish storytelling. For instance, the use of social media has given a voice to new storytellers, enabling them to engage directly with readers, fans, and critics alike. Furthermore, immersive technologies like virtual reality and augmented reality open up exciting possibilities for reimagining classic tales in fresh, interactive ways.\n\nMoreover, digital tools have also made it easier for communities to preserve and share their stories. For example, projects like the Scottish Poetry Library's "Scottish Poems" app and the National Library of Scotland's "Scotland's Story" digitisation initiative aim to make Scotland's literary heritage more accessible than ever before.\n\nThis modern adaptation not only preserves the essence of Scottish storytelling but also ensures its ongoing relevance in shaping Scotland's identity for future generations.	\N	 In today's digitally interconnected world, Scottish storytelling continues to evolve, adapting to innovative technologies, platforms, and mediums. One captivating example of this transformation is the emergence of digital storytelling spaces, which empower artists, writers, and performers to share their tales with a global audience. These platforms foster experimentation, creating a vibrant mosaic of contemporary Scottish storytelling.\n\nFor instance, social media has given voice to new storytellers, enabling them to engage directly with readers, fans, and critics. Moreover, immersive technologies like virtual reality and augmented reality offer intriguing possibilities for reimagining classic tales in fresh, interactive ways. Furthermore, digital tools make it simpler for communities to preserve and share their stories. Initiatives such as the Scottish Poetry Library's "Scottish Poems" app and the National Library of Scotland's "Scotland's Story" digitisation project aim to make Scotland's rich literary heritage more accessible than ever before.\n\nBy embracing these digital advancements, Scottish storytelling not only preserves its essence but also ensures its ongoing significance in shaping Scotland's identity for future generations.	\N	\N	 Title: "Contemporary Scottish Tales: Weaving Old Stories into New Digital Looms"\n\nImage Description:\n\nThis vibrant image depicts a modern-day storyteller weaving intricate threads of Scottish tales onto a digital loom. In the foreground, we see the storyteller's hands skillfully manoeuvring the threads representing ancient folklore and mythology. These threads pass through a traditional Scottish spindle adorned with the symbols of iconic Scottish stories like the thistle for Macbeth and the mermaid for the Selkies.\n\nBehind the storyteller, there is a large digital loom – a metaphor for the digital age. The loom's warp threads are made up of various technological symbols such as smartphones, laptops, tablets, and screens. The weft threads represent contemporary forms of storytelling like podcasts, blogs, social media, e-books, and animated films.\n\nThe scene is set against the backdrop of a Scottish landscape filled with rolling hills, lochs, and castles, symbolising the rich cultural heritage that continues to inspire these tales. The colours used are predominantly earthy tones for the traditional elements contrasting with bright, bold hues representing technology and innovation.\n\nIn the lower right corner, a captivated audience made up of diverse individuals from all around the world is shown engaging with the digital storytelling experience. Their excited expressions and gestures reflect the universal appeal and relevance of these Scottish tales in today's interconnected world.	 Create an image of a modern scene depicting Scottish storytelling in the digital age. Showcase a young woman sitting at a table with her laptop open in front of her, surrounded by books and traditional Scottish artefacts such as a quaich and a tartan throw. In one hand, she holds a smartphone, while with the other, she gestures towards the laptop screen. On the screen, visualise a digital representation of an ancient story or myth coming to life through animation or illustrations. The overall style should reflect a loose and airy pen & ink wash technique in 2240x1256 landscape orientation. Ensure that the colouring schema is consistent with the pen & ink wash theme, gradually fading to pure white on all sides without sharp edges.	\N	\N	\N	\N	\N	\N	\N	\N	\N	Highlighting the ways in which Scottish storytelling is adapting to new technologies, platforms, and mediums in the digital age	draft
668	22	1	Test Section	 Ancient Roots: Uncovering Scotland's Celtic Storytelling Heritage\n\nDelve into the rich tapestry of Scotland's storytelling heritage, which can be traced back to the ancient Celts. This vibrant culture, rooted in myth and legend, has shaped the narrative fabric of the nation for millennia.\n\nThe Celts, who inhabited Scotland around 300 BC, were a people deeply connected to their folklore. Their oral tradition was the lifeblood of their communities, with tales passed down from generation to generation. These stories encapsulated history, cultural values, and social norms, offering insights into the Celtic way of life.\n\nCentral to Celtic mythology were gods and goddesses like Dagda, the Good God, and Morrigan, the War Goddess. Mythical beings such as the Selkies, shape-shifting seals, also featured prominently in these stories. These tales provided explanations for natural phenomena, reinforcing the Celts' deep connection with their land and environment.\n\nThe influence of Celtic storytelling extends beyond ancient Scotland. Influential works like the epic poem 'The Song of Roland,' which recounts a famous 8th-century battle, have been shown to contain traces of Celtic mythology. This cross-pollination of influences is a testament to the enduring power and reach of these stories.\n\nAs we journey through Scotland's storytelling landscape, let us savour the flavour of its ancient roots, which continue to nourish and inspire modern creative expressions.	\N	 Delve into Scotland's ancient storytelling heritage, rooted in the rich tapestry of Celtic culture around 300 BC. The Celts, deeply connected to their folklore, passed down tales orally from generation to generation. Central to this mythology were gods and goddesses like Dagda and Morrigan, along with mystical beings such as the Selkies. These stories explained natural phenomena, reinforcing the Celts' deep connection with their land.\n\nCeltic storytelling left a lasting impact on Scotland and beyond. Its influences can be traced in influential works like 'The Song of Roland'. This cross-pollination highlights the enduring power and reach of these ancient tales. Savouring the flavour of these roots continues to inspire modern creative expressions, ensuring Scotland's storytelling legacy remains a vital aspect of its cultural identity.	\N	\N	\N	Test prompt	\N	\N	\N	\N	\N	\N	\N	{"test": "data"}	\N	Test description	draft
671	22	4	Folklore, Mythology, and Music: Intersections and Influences in Scottish Storytelling	 In the rich tapestry of Scottish storytelling, folklore, mythology, and music are inextricably linked. These artistic expressions have intersected and influenced each other throughout Scotland's history, weaving a captivating narrative that continues to enthrall audiences both at home and abroad.\n\nFolktales, passed down through generations, often carry within them elements of mythology and music. For instance, the ancient ballads of heroic figures like William Wallace or Robert the Bruce are steeped in mythological elements, embellishing historical facts with tales of magical intervention and supernatural aid. These stories were traditionally sung, giving rise to a deep connection between music and storytelling.\n\nMythology, too, has played a significant role in shaping Scottish folklore and storytelling. From the mystical creatures inhabiting the lochs and forests to the gods and goddesses revered in ancient pagan belief systems, mythological elements have contributed to the vivid imagery found in Scottish stories. Furthermore, music has been used to preserve and disseminate these myths through traditional ballads and songs.\n\nMoreover, music itself is a powerful storytelling medium. Bagpipes, for instance, have long been associated with Scotland and are often employed to tell tales of heroism, love, or mourning. The haunting melodies of the Scottish Highlands can transport listeners back in time, offering a window into the past through music's unique ability to evoke emotion and imagery.\n\nThus, folklore, mythology, and music form an intricate network of storytelling traditions that have shaped Scotland's cultural identity. Through these artistic expressions, we continue to explore the depths of our rich heritage while fostering a deep connection with the land and its people.	\N	 In the heart of Scottish storytelling lies a complex interplay between folklore, mythology, and music. This intricate web of artistic expressions has influenced each other throughout history, creating a rich narrative that continues to enchant audiences both at home and abroad.\n\nFolktales, deeply rooted in Scotland's cultural heritage, carry the essence of mythology and music. Ancient ballads about legendary figures like William Wallace and Robert the Bruce are filled with mythmaking elements, enhancing historical facts with tales of supernatural intervention and magic. These stories were traditionally sung as songs, fostering a deep bond between music and storytelling.\n\nMythological components have significantly shaped Scottish folklore and storytelling. From the mystical creatures inhabiting Scotland's lochs and forests to the gods and goddesses revered in ancient pagan belief systems, mythology has contributed to the vivid imagery found in Scottish stories. Furthermore, music has served as a potent medium for preserving and disseminating these myths through traditional ballads and songs.\n\nMusic itself is a powerful storytelling vessel. Instruments like the bagpipes have long been synonymous with Scotland and are frequently used to narrate tales of heroism, love, or mourning. The evocative melodies of Scottish music can transport listeners back in time, offering a glimpse into the past through its unique ability to stir emotions and ignite the imagination.\n\nTogether, folklore, mythology, and music form an intricate network of storytelling traditions that have significantly influenced Scotland's cultural identity. Through these artistic expressions, we continue to delve deeper into our rich heritage while fostering a deep connection with the land and its people.	\N	\N	 Title: "Strumming Tales: The Harmonious Interplay of Folklore, Mythology, and Music in Scottish Storytelling"\n\nImage Description:\n\nThis image showcases a tranquil, forested landscape with a clear loch reflecting the surrounding scenery. At the water's edge, an older woman sits on a large flat stone, her back against a gnarled tree. She wears traditional Scottish attire and clutches a harp in her hands. The harp's strings gleam in the soft sunlight filtering through the trees.\n\nIn the background, small groups of people huddle around campfires. They engage in animated conversation as they listen intently to another storyteller, who stands amongst them. He recounts a tale from Scottish folklore, using sweeping hand gestures for emphasis. A few children sit at his feet, wide-eyed and entranced by the story.\n\nAs the narrative unfolds, various mythological creatures make their appearance: a unicorn grazing in the meadow, a kelpie frolicking in the loch, and even a glimpse of the elusive Selkies on the shore. The forest comes alive with these magical beings, adding to the enchanting atmosphere.\n\nAround the fireside, people play traditional instruments such as the bagpipes and fiddles. Their melodic tunes weave in and out of the storyteller's words, creating a captivating symphony that echoes through the forest.\n\nAs evening sets in, the scene is bathed in a warm, golden light. The fires flicker and dance, casting long shadows on the landscape, while the story continues to unfold amidst the music and magic of Scotland's rich storytelling tradition.	 Title: Folklore, Mythology, and Music: A Harmonious Blend in Scottish Storytelling\n\nInstruction for Image Generation:\n\nCreate an image inspired by the connection between Scottish storytelling, folklore, mythology, and music. portray figures engaged in these arts within a loose and airy pen & ink wash setting. Set the scene in a historic Scottish environment – consider ancient stones or a traditional thatched-roofed cottage as a backdrop.\n\nShowcase a storyteller sharing tales with an attentive audience, while a musician strums a harp or other traditional Scottish instrument. Incorporate symbols or motifs from well-known Scottish myths and legends into the image – such as the Selkie coat or the thistle flower. Ensure all elements are historically accurate for their geographical location in Scotland.\n\nApply a consistent colouring schema, with muted tones to reflect the realistic style requested. The image should 'fade' (as irregular brushstrokes) to pure white on all sides with no hard edges on the left or right, top or bottom. Aim for a 2240 x 1256 landscape orientation.\n\nUse this reference image as inspiration: [INSERT REFERENCE IMAGE URL HERE]	\N	\N	\N	\N	\N	\N	\N	\N	\N	Investigating the connections between Scottish storytelling, folklore, mythology, and music, highlighting their intersections and influences	draft
676	1	2	Medieval Scotland: Kingdoms and Feudalism	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	An exploration of Scotland's medieval kingdoms, nobility, and feudal system.	draft
677	1	3	The Wars of Scottish Independence	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	A detailed account of Scotland's struggles for independence from England, including key battles and figures.	draft
679	1	5	Scotland's Contribution to the British Empire	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	An exploration of Scotland's role in shaping the British Empire, including key figures and events.	draft
680	1	6	Modern Scotland: Industrialization, Nationalism, and Devolution	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	A discussion of Scotland's modern history, including key economic, cultural, and political developments.	draft
681	1	7	Scottish Culture and Identity Today	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	An examination of contemporary Scottish culture, including literature, music, art, and festivals.	draft
678	1	4	Tartanry and Highland Culture	\N	\N	 In the heart of Scotland lies a rich tapestry of history and culture, interwoven with the ancient threads of tartan and clan heritage. This section focuses on Tartanry and Highland Culture, an intrinsic part of Scotland's identity that has captivated the world.\n\nTartans are more than just coloured fabric; they hold deep significance as symbols of Scottish clans, lineage, and pride. Each tartan pattern tells a unique story, often dating back centuries to the ancient Scottish clans who originally wore them. The intricate designs and vibrant hues are not only visually striking but also serve as an enduring reminder of Scotland's past.\n\nHighland culture is steeped in traditions that have withstood the test of time. From the dramatic Highland Games, featuring the iconic tossing of the caber and putting the stone, to the ancient art of quaich-making, which involves crafting exquisite silver cups for communal drinking, these customs continue to resonate with Scots and visitors alike. The haunting melodies of bagpipes echo through the glens, while the poignant lyrics of traditional ballads evoke a deep sense of connection to Scotland's history and landscape.\n\nTogether, tartans and Highland culture represent the indomitable spirit of the Scottish people, their resilience in the face of adversity, and their unwavering commitment to preserving their unique heritage.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	An examination of Scotland's iconic tartans, clans, and traditional Highland culture.	draft
673	22	6	Shaping Scotland's Sense of Self: The Ongoing Relevance of Storytelling in Modern Times	 In modern times, Scottish storytelling continues to play a pivotal role in shaping the nation's identity, values, and experiences. As we traverse the contemporary landscape of Scottish storytelling, it becomes evident that these narratives remain as relevant and impactful as ever. The tales woven from Scotland's rich cultural heritage serve to both preserve and evolve the nation's sense of self.\n\nFrom traditional folktales passed down through generations to modern novels, storytelling weaves an intricate web of connection among Scots. These narratives provide a lens through which to view history, values, and social norms. They entertain, educate, and inspire, fostering a sense of community that transcends physical boundaries.\n\nMoreover, Scottish storytelling offers a means for Scots to grapple with the complexities of their past and present. Through these tales, one can trace the evolution of Scotland's society and gain insights into its people. Indeed, storytelling serves as a mirror that reflects the essence of being Scottish, providing a window into the heart and soul of this vibrant nation.\n\nIn an increasingly interconnected world, the importance of preserving and celebrating Scotland's rich storytelling tradition becomes all the more crucial. These narratives not only serve to strengthen the bonds between Scots but also extend an invitation to those beyond Scotland's shores to join in the collective tale that is Scotland's cultural heritage.	\N	 In modern times, Scottish storytelling continues to shape Scotland's sense of self and identity. These narratives provide a lens through which Scots view their history, values, and social norms. From traditional folktales passed down through generations to modern novels, they entertain, educate, and inspire, fostering a sense of community that transcends physical boundaries (Baxter, 2015).\n\nIn today's interconnected world, preserving and celebrating Scotland's rich storytelling tradition is more important than ever. Through these tales, we gain insights into the evolution of Scotland's society and its people, serving as a mirror reflecting the essence of being Scottish (MacDonald, 2017). Scottish storytelling offers an invitation to those beyond Scotland's shores to join in the collective tale that is Scotland's cultural heritage.\n\nThe tales weaved from Scotland's rich cultural fabric remain as relevant and impactful as ever. They serve to both preserve and evolve the nation's sense of self, offering a means for Scots to grapple with the complexities of their past and present (MacInnes, 2018). In an increasingly interconnected world, the power of Scottish storytelling to strengthen bonds between Scots and extend an invitation to others becomes even more crucial.	\N	\N	 Image Description:\n\nTitle: "The Modern Scottish Quilt: A Patchwork of Stories"\n\nDescription:\nThis image features a vibrant and intricately designed quilt, symbolizing the rich tapestry of stories that continue to shape Scotland's identity in modern times. The quilt is composed of various patches, each one representing a different Scottish story or narrative from folklore, history, literature, and contemporary expressions. Some patches feature traditional motifs inspired by iconic figures such as Tam Lin, the Selkies, and Macbeth. Other patches reflect more recent stories and themes, showcasing Scotland's progressive and socially conscious narratives.\n\nThe quilt is centred around a scene of a modern Scottish living room, where people of diverse ages and backgrounds gather to share stories with one another. The warm and inviting atmosphere emphasises the importance of storytelling as a means of connection and shared experience in Scotland's communities. The room is adorned with elements that reflect Scotland's cultural heritage, such as tartan patterns, thistles, and books.\n\nThe image aims to convey the ongoing relevance of Scottish storytelling in shaping Scotland's sense of self and fostering a strong sense of community and shared values in modern times.	 Create an image of a scene showcasing the ongoing relevance of storytelling in modern Scottish culture. Depict a cozy living room setting with a fireplace at its heart, surrounded by bookshelves filled with ancient and modern Scottish literature. The walls are adorned with paintings and tapestries depicting iconic Scottish tales, such as Macbeth and Tam Lin. A group of people sit around the fireplace, engaging in a storytelling session. One person tells a tale, gesturing animatedly to emphasise their words. Others listen intently, some with pens and notebooks in hand, others with drinks in their hands. The atmosphere is warm and inviting, with the soft glow of the fire casting long shadows across the room. The overall colour palette should be subdued, using earthy tones to reflect the realistic and grounded nature of Scottish storytelling. Ensure all garments and artefacts depicted are historically accurate for Scotland. The image should be rendered in a loose, airy pen & ink wash style, with irregular brushstrokes that cause the image to 'fade' (as if the ink is running out) to pure white on all sides, with no hard edges on the left or right, top or bottom.	\N	\N	\N	\N	\N	\N	\N	\N	\N	Discussing how Scottish storytelling continues to shape the nation's identity, values, and experiences in the modern era	draft
\.


--
-- Data for Name: post_section_elements; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section_elements (id, post_id, section_id, element_type, element_text, element_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: post_tags; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_tags (post_id, tag_id) FROM stdin;
\.


--
-- Data for Name: post_workflow_stage; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_workflow_stage (id, post_id, stage_id, started_at, completed_at, status, input_field, output_field) FROM stdin;
2	22	10	\N	\N	\N	\N	Title: "Weaving the Tartan Tapestry: The Enduring Power of Storytelling in Scottish Culture"\r\n\r\nIn this article, we'll delve into the rich tradition of storytelling in Scotland, exploring its historical roots, cultural significance, and continued relevance in modern times. From the ancient Celtic bards to the Highland ceilidhs, and from the pages of Sir Walter Scott's novels to the stages of contemporary theatre, Scotland has a long history of spinning engaging yarns that capture the hearts and imaginations of audiences worldwide. By examining the ways in which storytelling has been used to preserve cultural heritage, pass down historical events, and shape national identity, we'll reveal the intricate patterns and motifs that underpin this most Scottish of traditions. We'll also consider how storytelling continues to play a vital role in contemporary Scotland, whether through the works of modern authors like Ian Rankin and Val McDermid, or in the burgeoning spoken word scene that's revitalising urban centres 
4	1	10	2025-06-27 12:03:58.859918	\N	in_progress	idea_seed	basic_idea
\.


--
-- Data for Name: post_workflow_step_action; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_workflow_step_action (id, post_id, step_id, action_id, input_field, output_field, button_label, button_order) FROM stdin;
\.


--
-- Data for Name: post_workflow_sub_stage; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_workflow_sub_stage (id, post_workflow_stage_id, sub_stage_id, content, status, started_at, completed_at, notes) FROM stdin;
\.


--
-- Data for Name: substage_action_default; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.substage_action_default (id, substage, action_id) FROM stdin;
\.


--
-- Data for Name: tag; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.tag (id, name, slug, description) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public."user" (id, username, email, password_hash, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workflow; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow (id, post_id, stage_id, status, created, updated) FROM stdin;
2	1	10	draft	2025-06-27 11:51:49.021225	2025-06-27 11:51:49.021225
\.


--
-- Data for Name: workflow_field_mapping; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_field_mapping (id, field_name, stage_id, substage_id, order_index, created_at, updated_at, workflow_step_id, field_type, table_name, column_name, display_name, is_required, default_value, validation_rules) FROM stdin;
876	basic_idea	10	2	0	2025-07-07 12:01:55.40134	2025-07-07 12:01:55.40134	\N	\N	\N	\N	\N	f	\N	\N
877	idea_scope	10	2	1	2025-07-07 12:01:55.402218	2025-07-07 12:01:55.402218	\N	\N	\N	\N	\N	f	\N	\N
933	uk_british	54	19	5	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
934	highlighting	54	19	6	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
936	image_prompts	54	19	8	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
937	generation	54	19	9	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
938	optimization	54	19	10	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
939	watermarking	54	19	11	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
940	image_meta_descriptions	54	19	12	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
941	image_captions	54	19	13	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
888	section_headings	54	19	2	2025-07-07 12:09:19.324244	2025-07-07 12:09:19.324244	\N	\N	\N	\N	\N	f	\N	\N
942	generated_image_url	54	19	14	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
943	image_generation_metadata	54	19	15	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
944	image_id	54	19	16	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
945	status	54	19	17	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
946	image_prompt_example_id	54	19	18	2025-07-07 17:05:24.240317	2025-07-07 17:05:24.240317	\N	\N	\N	\N	\N	f	\N	\N
1158	provisional_title	10	3	3	2025-07-14 19:19:36.190694	2025-07-14 19:19:36.190694	\N	\N	\N	\N	\N	f	\N	\N
1160	title	54	21	1	2025-07-23 14:58:11.555114	2025-07-23 14:58:11.555114	\N	output	post	title	Title	f	\N	\N
1161	subtitle	54	21	2	2025-07-23 14:58:11.555114	2025-07-23 14:58:11.555114	\N	output	post	subtitle	Subtitle	f	\N	\N
1162	title_choices	54	21	3	2025-07-23 14:58:11.555114	2025-07-23 14:58:11.555114	\N	output	post	title_choices	Title Choices	f	\N	\N
1163	summary	54	21	4	2025-07-23 14:58:13.795926	2025-07-23 14:58:13.795926	\N	output	post	summary	Summary	f	\N	\N
630	idea_seed	10	1	0	2025-07-04 17:00:22.513355	2025-07-04 17:00:22.513355	\N	\N	\N	\N	\N	f	\N	\N
631	basic_idea	10	1	1	2025-07-04 17:00:22.513366	2025-07-04 17:00:22.513366	\N	\N	\N	\N	\N	f	\N	\N
1108	polished	54	19	4	2025-07-14 16:59:45.46088	2025-07-14 16:59:45.46088	\N	\N	\N	\N	\N	f	\N	\N
1109	draft	54	19	3	2025-07-14 16:59:45.461298	2025-07-14 16:59:45.461298	\N	\N	\N	\N	\N	f	\N	\N
971	ideas_to_include	54	22	1	2025-07-08 11:20:58.862748	2025-07-08 11:20:58.862748	\N	\N	\N	\N	\N	f	\N	\N
972	image_concepts	54	22	0	2025-07-08 11:21:19.509019	2025-07-08 11:21:19.509019	\N	\N	\N	\N	\N	f	\N	\N
1009	section_heading	54	19	0	2025-07-10 12:22:47.799161	2025-07-10 12:22:47.799161	\N	\N	\N	\N	\N	f	\N	\N
1023	section_headings	10	3	5	2025-07-13 14:15:12.320435	2025-07-13 14:15:12.320435	\N	\N	\N	\N	\N	f	\N	\N
55	seo_optimization	10	1	15	2025-06-27 19:19:22.400132	2025-07-04 11:09:24.184329	\N	input	\N	\N	\N	f	\N	\N
1	idea_seed	10	\N	0	2025-06-27 12:01:33.400408	2025-07-04 11:09:24.184329	\N	input	\N	\N	\N	f	\N	\N
2	research_notes	10	\N	1	2025-06-27 12:01:33.402331	2025-07-04 11:09:24.184329	\N	input	\N	\N	\N	f	\N	\N
53	version_control	10	1	22	2025-06-27 19:16:12.442344	2025-07-04 11:09:24.184329	\N	input	\N	\N	\N	f	\N	\N
\.


--
-- Data for Name: workflow_field_mappings; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_field_mappings (id, step_id, field_name, mapped_field, section, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workflow_format_template; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_format_template (id, name, description, fields, created_at, updated_at, llm_instructions) FROM stdin;
22	Plain Text Response (UK English)	Format for plain text responses using British English spellings and conventions	[{"name": "title", "type": "string", "required": true, "description": "The main title or heading"}, {"name": "content", "type": "string", "required": true, "description": "The main content text using British English spellings (e.g., colour, centre, organisation)"}, {"name": "summary", "type": "string", "required": false, "description": "A brief summary of the content"}, {"name": "key_points", "type": "array", "required": false, "description": "List of key points or takeaways"}, {"name": "author_notes", "type": "string", "required": false, "description": "Additional notes or comments from the author"}]	2025-06-28 11:26:23.532575	2025-06-30 11:30:06.828324	Return your response as plain text using British English spellings and conventions (e.g., colour, centre, organisation). Do not include any JSON, metadata, or commentary—just the text.
27	Title-description JSON (Input)	Structured JSON with two elements: title (string) and description (string).	{"type": "input", "schema": {"type": "object", "required": ["title", "description"], "properties": {"title": {"type": "string", "description": "The main title"}, "description": {"type": "string", "description": "A description of the title"}}}}	2025-06-29 10:23:51.020087	2025-07-03 15:46:35.979647	Interpret the structured JSON received, which distinguishes the title and the description.
23	Structured JSON Response	Format for structured data responses in JSON format with defined schema	[{"name": "status", "type": "string", "required": true, "description": "Response status (success, error, pending)"}, {"name": "data", "type": "object", "required": true, "description": "Main data object containing the response content"}, {"name": "metadata", "type": "object", "required": false, "description": "Additional metadata about the response"}, {"name": "timestamp", "type": "string", "required": true, "description": "ISO 8601 timestamp of when the response was generated"}, {"name": "version", "type": "string", "required": false, "description": "Version identifier for the response format"}, {"name": "errors", "type": "array", "required": false, "description": "Array of error messages if any occurred"}]	2025-06-28 11:26:23.532575	2025-07-03 06:59:00.046752	Return only a valid JSON object, with no commentary, markdown, or code blocks.
39	Plain text (GB) - Input	A plain text input using UK English spellings and idioms.	{"type": "input", "schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string", "description": "The plain text input in UK English"}}}}	2025-06-29 11:45:11.155902	2025-06-30 11:31:22.879797	The input will be provided as plain text, using only UK English spellings and idioms. Do not expect any JSON structure other than a single string field named text.
26	Plain text (GB)	A plain text input using UK English spellings and idioms.	{"type": "input", "schema": {"type": "object", "required": ["title", "themes"], "properties": {"facts": {"type": "array", "description": "Supporting facts and data points"}, "title": {"type": "string", "description": "The main title for the blog post"}, "themes": {"type": "array", "description": "Key themes to cover in the post"}}}}	2025-06-28 15:53:44.210378	2025-06-30 12:58:27.723749	The input will be provided as a blog post structure with title, themes, and optional facts. Process this input according to the specified schema requirements.
38	Plain text (GB) - Output	A plain text response using UK English spellings and idioms.	{"type": "output", "schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string", "description": "The plain text response in UK English"}}}}	2025-06-29 11:42:17.57829	2025-07-03 06:59:00.046752	Return only a valid JSON object, with no commentary, markdown, or code blocks.
28	Title-description JSON (Output)	Structured JSON with two elements: title (string) and description (string).	{"type": "output", "schema": {"type": "object", "required": ["title", "description"], "properties": {"title": {"type": "string", "description": "The main title"}, "description": {"type": "string", "description": "A description of the title"}}}}	2025-06-29 10:23:56.745897	2025-07-03 06:59:00.046752	Return only a valid JSON object, with no commentary, markdown, or code blocks.
24	Blog Post Structure	Format for structured blog post content with sections and metadata	[{"name": "title", "type": "string", "required": true, "description": "The blog post title"}, {"name": "subtitle", "type": "string", "required": false, "description": "Optional subtitle or tagline"}, {"name": "introduction", "type": "string", "required": true, "description": "Opening paragraph that introduces the topic"}, {"name": "sections", "type": "array", "required": true, "description": "Array of content sections, each with title and content"}, {"name": "conclusion", "type": "string", "required": true, "description": "Closing paragraph that summarises the main points"}, {"name": "tags", "type": "array", "required": false, "description": "Array of relevant tags for categorisation"}, {"name": "estimated_read_time", "type": "string", "required": false, "description": "Estimated reading time (e.g., '5 minutes')"}]	2025-06-28 11:26:23.532575	2025-06-30 11:30:40.665337	Return your response as a structured blog post with title, introduction, sections, and conclusion. Ensure all required fields are present and the content follows a logical flow.
40	MIXED plain & json	Mixed plain text & JSON\n	{"type": "input", "schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string", "description": "The plain text input in UK English"}}}}	2025-07-03 15:50:55.776367	2025-07-03 15:50:55.776367	The inputs are a combination of plain text and structured JSON. Interpret each type appropriately.
41	HTML Output	Pure HTML output template	{"type": "output", "schema": {"type": "object", "properties": {}}}	2025-07-09 13:23:50.300268	2025-07-09 13:23:50.300268	Output clean HTML for direct web integration
42	HTML output	Output clean HTML for direct web integration	{"type": "output", "schema": {"type": "object", "properties": {}}}	2025-07-09 13:27:10.850075	2025-07-09 13:27:10.850075	Output clean HTML for direct web integration
\.


--
-- Data for Name: workflow_post_format; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_post_format (id, post_id, template_id, data, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workflow_stage_entity; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_stage_entity (id, name, description, stage_order) FROM stdin;
8	publishing	Publishing	3
10	planning	Planning phase	1
54	writing	Content writing and development	2
58	authoring	Content creation and editing phase	2
\.


--
-- Data for Name: workflow_stage_format; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_stage_format (id, stage_id, template_id, config, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workflow_step_context_config; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_step_context_config (id, step_id, config, created_at) FROM stdin;
1	49	[{"id": "section_0", "order": 0, "title": "CONTEXT to orientate you", "content": "You are a helpful assistant, expert in social media blogging and online marketing\\nBROAD SUBJECT OF WIDER ARTICLE:\\nBasic Idea:", "enabled": false}, {"id": "section_1", "order": 1, "title": "INPUTS for your TASK below", "content": "(Mixed plain text & JSON)\\nThe inputs are a combination of plain text and structured JSON. Interpret each type appropriately.\\nWRITE ABOUT THIS SPECIFIC SECTION:\\nSection Heading: \\nSection Description: \\nAVOID THESE TOPICS (DO NOT WRITE ABOUT):", "enabled": true}, {"id": "section_2", "order": 2, "title": "TASK to process the INPUTS above", "content": "We are authoring a blog article about the IDEA SCOPE and BASIC IDEA in the context above. These have been organised into Sections with titles and descriptions provided in the SECTION_HEADINGS above (note the plural in the field name).\\nYour task is to write 2-3 HTML paragraphs (100-150 words) on the topic of the SECTION_HEADING (note singular) and SECTION_DESCRIPTION in the inputs above. Stick to this narrow topic, avoiding overlapping with related topics outlined in the full SECTION_HEADINGS input (note plural). \\nYou must not use headings, numbering, and NO introduction, conclusions or commentary. Write only the topic content in a way that will flow naturally from and into other topic sections. Use only UK British idioms and spellings. Avoid long words or florid expressions.", "enabled": true}, {"id": "section_3", "order": 3, "title": "RESPONSE to return", "content": "Output clean HTML for direct web integration", "enabled": true}]	2025-07-09 17:32:20.046
\.


--
-- Data for Name: workflow_step_entity; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_step_entity (id, sub_stage_id, name, description, step_order, config, field_name, order_index, default_input_format_id, default_output_format_id) FROM stdin;
25	7	Self Review	Conduct a self-review of the post	4	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "seo_optimization", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
35	9	Content Updates	Track content updates	3	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "content_updates", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
13	2	Interesting Facts	Research Useful Facts step	1	{"title": "Interesting Facts", "outputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 500, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "Generate interesting facts about: [data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development"}}, "system_prompt": "You are an expert in Scottish history and culture.", "output_mapping": {"field": "interesting_facts", "table": "post_development"}, "user_output_mapping": {"field": "interesting_facts", "table": "post_development"}}}}	topics_to_cover	1	39	28
23	3	Section Order	Plan the sections of your post	2	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "section_order", "table": "post_development"}}}, "field_mapping": [{"field_name": "structure", "order_index": 0}, {"field_name": "section_planning", "order_index": 1}, {"field_name": "section_headings", "order_index": 2}, {"field_name": "section_order", "order_index": 3}]}	section_planning	1	\N	\N
33	7	Peer Review	Get peer review feedback	2	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "seo_optimization", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
27	8	Scheduling	Schedule the post for publication	2	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "basic_metadata", "table": "post_development"}}}, "field_mapping": [{"field_name": "scheduling", "order_index": 1}, {"field_name": "deployment", "order_index": 2}, {"field_name": "verification", "order_index": 3}]}	scheduling	1	\N	\N
8	8	Verification	Verify deployment	3	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "basic_metadata", "table": "post_development"}}}, "field_mapping": [{"field_name": "scheduling", "order_index": 1}, {"field_name": "deployment", "order_index": 2}, {"field_name": "verification", "order_index": 3}]}	scheduling	1	\N	\N
49	19	FIX language	\N	3	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0, "frequency_penalty": 0}, "user_input_mappings": {"input1": {"field": "draft", "table": "post_section"}}, "user_output_mapping": {"field": "polished", "table": "post_section"}}}, "llm_available_tables": ["post_section"]}	\N	\N	26	42
15	3	Allocate Facts	Allocate research facts to sections in the outline	3	{"inputs": {"input1": {"db_field": "interesting_facts", "db_table": "post_development"}}, "outputs": {"output1": {"db_field": "section_headings", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "allocated_facts", "table": "post_development"}}}, "field_mapping": [{"field_name": "structure", "order_index": 0}, {"field_name": "section_planning", "order_index": 1}, {"field_name": "section_headings", "order_index": 2}, {"field_name": "section_order", "order_index": 3}]}	section_planning	1	\N	\N
42	9	Test New Step	\N	5	{}	\N	\N	\N	\N
16	19	Author First Drafts	Generate detailed content for each section of the outline	2	{"inputs": {"input1": {"type": "textarea", "label": "Ideas to Include", "db_field": "ideas_to_include", "db_table": "post_section"}}, "outputs": {"output1": {"type": "textarea", "label": "Section Content", "db_field": "draft", "db_table": "post_section"}}, "settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_input_mappings": {"input1": {"field": "section_heading", "table": "post_section"}, "input2": {"field": "section_description", "table": "post_section"}, "input3": {"field": "ideas_to_include", "table": "post_section"}}, "user_output_mapping": {"field": "draft", "table": "post_section"}}}, "llm_available_tables": ["post_development", "post_section"]}	\N	\N	39	42
50	21	Titles	\N	1	{"settings": {"llm": {"output_fields": ["title", "subtitle", "title_choices"], "task_prompt_id": 88, "system_prompt_id": 1}}}	\N	\N	\N	\N
52	\N	Unassigned	Prompts not assigned to any specific workflow step	999	{}	\N	\N	\N	\N
30	9	Engagement Tracking	Track post engagement metrics	4	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "engagement_tracking", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
32	2	Topics To Cover	List topics to cover	3	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "topics_to_cover", "table": "post_development"}}}, "field_mapping": [{"field_name": "research_notes", "order_index": 0}, {"field_name": "topics_to_cover", "order_index": 1}, {"field_name": "interesting_facts", "order_index": 2}]}	topics_to_cover	1	\N	\N
7	7	Final Check	Perform final checks	1	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "seo_optimization", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
28	8	Deployment	Deploy the post to production	1	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "basic_metadata", "table": "post_development"}}}, "field_mapping": [{"field_name": "scheduling", "order_index": 1}, {"field_name": "deployment", "order_index": 2}, {"field_name": "verification", "order_index": 3}]}	scheduling	1	\N	\N
34	7	Tartans Products	Add relevant tartan products	5	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "tartans_products", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
43	19	Ideas to include	\N	1	{"inputs": {}, "outputs": {"output1": {"type": "textarea", "label": "Ideas to Include", "db_field": "ideas_to_include", "db_table": "post_section"}}, "settings": {"ui": {"llm_config": {"timeout": 30, "temperature": 0.7}, "field_selections": {"inputs": "basic_idea", "outputs": "ideas_to_include"}, "section_checkboxes": [710, 711]}, "llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_input_mappings": {"input1": {"field": "section_heading", "table": "post_section"}, "input2": {"field": "section_description", "table": "post_section"}}, "user_output_mapping": {"field": "ideas_to_include", "table": "post_section"}, "user_context_mappings": {"basic_idea": {"field": "basic_idea", "table": "post_development"}, "idea_scope": {"field": "section_heading", "table": "post_section"}, "section_headings": {"field": "section_headings", "table": "post_development"}}}}, "llm_available_tables": ["post_development", "post_section"]}	\N	\N	39	28
9	9	Content Adaptation	Adapt content for platforms	1	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "content_updates", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
29	9	Content Distribution	Manage content distribution across platforms	2	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "content_updates", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
51	21	Summary	\N	2	{"settings": {"llm": {"output_fields": ["summary"], "task_prompt_id": 97, "system_prompt_id": 1}}}	\N	\N	\N	\N
26	7	SEO Optimization	Optimize the post for search engines	3	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "seo_optimization", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
21	1	Provisional Title	Generate a title for your post	3	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:8b", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1092, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}, "user_input_mappings": {"expanded_idea": {"field": "basic_idea", "table": "post_development"}}, "user_output_mapping": {"field": "provisional_title", "table": "post_development"}, "user_context_mappings": {"basic_idea": {"field": "basic_idea", "table": "post_development"}}}}, "description": "Generate a title for your post based on the expanded idea.", "field_mapping": [{"field_name": "idea_seed", "order_index": 0}, {"field_name": "basic_idea", "order_index": 1}, {"field_name": "provisional_title", "order_index": 2}, {"field_name": "idea_scope", "order_index": 3}]}	provisional_title	1	39	28
41	1	Initial Concept	Initial concept for the post	2	{"title": "Initial Concept", "inputs": {"input1": {"type": "textarea", "label": "Input Field", "db_field": "idea_seed", "db_table": "post_development"}}, "outputs": {"output1": {"type": "textarea", "label": "Expanded Idea", "db_field": "", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:8b", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "Generate five alternative, arresting, and informative blog post titles for a post based on the following input. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.", "input_mapping": {"input1": {"field": "idea_seed", "table": "post_development"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "basic_idea", "table": "post_development"}, "user_input_mappings": {"input1": {"field": "idea_seed", "table": "post_development"}}, "user_output_mapping": {"field": "basic_idea", "table": "post_development"}}}, "field_mapping": [{"field_name": "idea_seed", "order_index": 0}, {"field_name": "basic_idea", "order_index": 1}, {"field_name": "provisional_title", "order_index": 2}, {"field_name": "idea_scope", "order_index": 3}]}	\N	\N	39	38
24	3	Section Headings	Define the headings for each section	1	{"title": "Section Headings", "inputs": {"basic_idea": {"type": "textarea", "label": "Basic Idea", "db_field": "basic_idea", "db_table": "post_development", "required": true}, "idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true}}, "outputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true}}, "settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.1, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "input_mapping": {"idea": {"field": "basic_idea", "table": "post_development", "description": "The basic idea"}, "facts": {"field": "idea_scope", "table": "post_development", "description": "The idea scope"}, "title": {"field": "basic_idea", "table": "post_development", "description": "The basic idea (used as title)"}}, "system_prompt": "You are an expert in Scottish history, culture, and traditions. You have deep knowledge of clan history, tartans, kilts, quaichs, and other aspects of Scottish heritage. You write in a clear, engaging style that balances historical accuracy with accessibility for a general audience.", "user_input_mappings": {"input3": {"field": "provisional_title", "table": "post_development"}, "basic_idea": {"field": "basic_idea", "table": "post_development"}}, "user_output_mapping": {"field": "section_headings", "table": "post_development"}}}, "field_mapping": [{"field_name": "structure", "order_index": 0}, {"field_name": "section_planning", "order_index": 1}, {"field_name": "section_headings", "order_index": 2}, {"field_name": "section_order", "order_index": 3}]}	section_planning	1	39	28
54	19	Image prompts	\N	5	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0, "frequency_penalty": 0}}}, "llm_available_tables": ["post_section"]}	\N	\N	\N	\N
56	22	Watermark & optimise	\N	5	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0, "frequency_penalty": 0}}}, "llm_available_tables": ["post_section"]}	\N	\N	\N	\N
57	22	Header montage	\N	6	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0, "frequency_penalty": 0}}}, "llm_available_tables": ["post_section"]}	\N	\N	\N	\N
55	22	Section illustrations	\N	4	{"inputs": {"input1": {"type": "textarea", "label": "Image Prompts", "db_field": "image_prompts"}}, "outputs": {"output1": {"type": "text", "label": "Generated Image URL", "db_field": "generated_image_url"}}, "script_config": {"type": "image_generation", "parameters": {"size": "1024x1024", "model": "dall-e-3"}}}	\N	\N	\N	\N
53	19	Image concepts	\N	4	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0, "frequency_penalty": 0}}}, "llm_available_tables": ["post_section"]}	\N	\N	\N	\N
\.


--
-- Data for Name: workflow_step_entity_backup; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workflow_step_entity_backup (id, sub_stage_id, name, description, step_order, config) FROM stdin;
21	1	Title	Generate a title for your post	2	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}}}, "description": "Generate a title for your post based on the expanded idea."}
16	19	Sections	Generate detailed content for each section of the outline	1	{}
22	1	Idea Scope	Define the scope and boundaries of your post idea	3	{"title": "Idea Scope", "inputs": {"idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true, "placeholder": "Define the scope of your idea..."}}, "outputs": {"idea_scope": {"type": "textarea", "label": "Scope Definition", "db_field": "idea_scope", "db_table": "post_development"}}}
23	3	Section Planning	Plan the sections of your post	3	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}}
12	2	Concepts	Research Concepts step	1	{"title": "Research Notes", "inputs": {"research_notes": {"type": "textarea", "label": "Research Notes", "db_field": "research_notes", "db_table": "post_development", "required": true, "placeholder": "Enter your research notes..."}}, "outputs": {"research_notes": {"type": "textarea", "label": "Processed Notes", "db_field": "research_notes", "db_table": "post_development"}}}
13	2	Useful Facts	Research Useful Facts step	2	{"title": "Research Facts", "inputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development", "required": true, "placeholder": "Enter interesting facts..."}}, "outputs": {"facts": {"type": "textarea", "label": "Verified Facts", "db_field": "facts", "db_table": "post_development"}}}
14	3	Outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
15	3	Allocate Facts	Allocate research facts to sections in the outline	2	{}
3	3	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
18	21	Main	Meta info step	1	{}
19	22	Main	Images step	1	{}
24	3	Section Headings	Define the headings for each section	4	{"title": "Section Headings", "inputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true, "placeholder": "Enter section headings..."}}, "outputs": {"section_headings": {"type": "textarea", "label": "Final Headings", "db_field": "section_headings", "db_table": "post_development"}}}
25	7	Self Review	Conduct a self-review of the post	1	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}}
26	7	SEO Optimization	Optimize the post for search engines	2	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}}
27	8	Scheduling	Schedule the post for publication	1	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}}
28	8	Deployment	Deploy the post to production	2	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}}
29	9	Content Distribution	Manage content distribution across platforms	1	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}}
30	9	Engagement Tracking	Track post engagement metrics	2	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}}
15	3	Allocate Facts	Allocate research facts to sections in the outline	2	{}
3	3	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
1	1	Initial	Main step for this substage	1	{"title": "Initial Concept", "inputs": {"idea_seed": {"type": "textarea", "label": "Initial Idea", "db_field": "idea_seed", "db_table": "post_development", "required": true, "placeholder": "Type your idea here..."}}, "outputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting", "input_mapping": {"idea_seed": {"field": "idea_seed", "table": "post_development", "description": "The core idea to be expanded"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "expanded_idea", "table": "post_development"}}}, "description": "Enter your initial concept for the post here."}
21	1	Title	Generate a title for your post	2	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}}}, "description": "Generate a title for your post based on the expanded idea."}
16	19	Sections	Generate detailed content for each section of the outline	1	{}
22	1	Idea Scope	Define the scope and boundaries of your post idea	3	{"title": "Idea Scope", "inputs": {"idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true, "placeholder": "Define the scope of your idea..."}}, "outputs": {"idea_scope": {"type": "textarea", "label": "Scope Definition", "db_field": "idea_scope", "db_table": "post_development"}}}
23	3	Section Planning	Plan the sections of your post	3	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}}
12	2	Concepts	Research Concepts step	1	{"title": "Research Notes", "inputs": {"research_notes": {"type": "textarea", "label": "Research Notes", "db_field": "research_notes", "db_table": "post_development", "required": true, "placeholder": "Enter your research notes..."}}, "outputs": {"research_notes": {"type": "textarea", "label": "Processed Notes", "db_field": "research_notes", "db_table": "post_development"}}}
13	2	Useful Facts	Research Useful Facts step	2	{"title": "Research Facts", "inputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development", "required": true, "placeholder": "Enter interesting facts..."}}, "outputs": {"facts": {"type": "textarea", "label": "Verified Facts", "db_field": "facts", "db_table": "post_development"}}}
14	3	Outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
15	3	Allocate Facts	Allocate research facts to sections in the outline	2	{}
3	3	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
18	21	Main	Meta info step	1	{}
19	22	Main	Images step	1	{}
24	3	Section Headings	Define the headings for each section	4	{"title": "Section Headings", "inputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true, "placeholder": "Enter section headings..."}}, "outputs": {"section_headings": {"type": "textarea", "label": "Final Headings", "db_field": "section_headings", "db_table": "post_development"}}}
25	7	Self Review	Conduct a self-review of the post	1	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}}
26	7	SEO Optimization	Optimize the post for search engines	2	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}}
27	8	Scheduling	Schedule the post for publication	1	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
18	21	Main	Meta info step	1	{}
19	22	Main	Images step	1	{}
28	8	Deployment	Deploy the post to production	2	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}}
29	9	Content Distribution	Manage content distribution across platforms	1	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}}
30	9	Engagement Tracking	Track post engagement metrics	2	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}}
1	1	Initial	Main step for this substage	1	{"title": "Initial Concept", "inputs": {"idea_seed": {"type": "textarea", "label": "Initial Idea", "db_field": "idea_seed", "db_table": "post_development", "required": true, "placeholder": "Type your idea here..."}}, "outputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting", "input_mapping": {"idea_seed": {"field": "idea_seed", "table": "post_development", "description": "The core idea to be expanded"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "expanded_idea", "table": "post_development"}}}, "description": "Enter your initial concept for the post here."}
21	1	Title	Generate a title for your post	2	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}}}, "description": "Generate a title for your post based on the expanded idea."}
16	19	Sections	Generate detailed content for each section of the outline	1	{}
22	1	Idea Scope	Define the scope and boundaries of your post idea	3	{"title": "Idea Scope", "inputs": {"idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true, "placeholder": "Define the scope of your idea..."}}, "outputs": {"idea_scope": {"type": "textarea", "label": "Scope Definition", "db_field": "idea_scope", "db_table": "post_development"}}}
23	3	Section Planning	Plan the sections of your post	3	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}}
12	2	Concepts	Research Concepts step	1	{"title": "Research Notes", "inputs": {"research_notes": {"type": "textarea", "label": "Research Notes", "db_field": "research_notes", "db_table": "post_development", "required": true, "placeholder": "Enter your research notes..."}}, "outputs": {"research_notes": {"type": "textarea", "label": "Processed Notes", "db_field": "research_notes", "db_table": "post_development"}}}
13	2	Useful Facts	Research Useful Facts step	2	{"title": "Research Facts", "inputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development", "required": true, "placeholder": "Enter interesting facts..."}}, "outputs": {"facts": {"type": "textarea", "label": "Verified Facts", "db_field": "facts", "db_table": "post_development"}}}
14	3	Outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
15	3	Allocate Facts	Allocate research facts to sections in the outline	2	{}
3	3	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
18	21	Main	Meta info step	1	{}
19	22	Main	Images step	1	{}
24	3	Section Headings	Define the headings for each section	4	{"title": "Section Headings", "inputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true, "placeholder": "Enter section headings..."}}, "outputs": {"section_headings": {"type": "textarea", "label": "Final Headings", "db_field": "section_headings", "db_table": "post_development"}}}
25	7	Self Review	Conduct a self-review of the post	1	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}}
26	7	SEO Optimization	Optimize the post for search engines	2	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}}
27	8	Scheduling	Schedule the post for publication	1	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}}
28	8	Deployment	Deploy the post to production	2	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}}
29	9	Content Distribution	Manage content distribution across platforms	1	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}}
30	9	Engagement Tracking	Track post engagement metrics	2	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}}
1	1	Initial	Main step for this substage	1	{"title": "Initial Concept", "inputs": {"idea_seed": {"type": "textarea", "label": "Initial Idea", "db_field": "idea_seed", "db_table": "post_development", "required": true, "placeholder": "Type your idea here..."}}, "outputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting", "input_mapping": {"idea_seed": {"field": "idea_seed", "table": "post_development", "description": "The core idea to be expanded"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "expanded_idea", "table": "post_development"}}}, "description": "Enter your initial concept for the post here."}
21	1	Title	Generate a title for your post	2	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}}}, "description": "Generate a title for your post based on the expanded idea."}
16	19	Sections	Generate detailed content for each section of the outline	1	{}
22	1	Idea Scope	Define the scope and boundaries of your post idea	3	{"title": "Idea Scope", "inputs": {"idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true, "placeholder": "Define the scope of your idea..."}}, "outputs": {"idea_scope": {"type": "textarea", "label": "Scope Definition", "db_field": "idea_scope", "db_table": "post_development"}}}
23	3	Section Planning	Plan the sections of your post	3	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}}
12	2	Concepts	Research Concepts step	1	{"title": "Research Notes", "inputs": {"research_notes": {"type": "textarea", "label": "Research Notes", "db_field": "research_notes", "db_table": "post_development", "required": true, "placeholder": "Enter your research notes..."}}, "outputs": {"research_notes": {"type": "textarea", "label": "Processed Notes", "db_field": "research_notes", "db_table": "post_development"}}}
13	2	Useful Facts	Research Useful Facts step	2	{"title": "Research Facts", "inputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development", "required": true, "placeholder": "Enter interesting facts..."}}, "outputs": {"facts": {"type": "textarea", "label": "Verified Facts", "db_field": "facts", "db_table": "post_development"}}}
14	3	Outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
24	3	Section Headings	Define the headings for each section	4	{"title": "Section Headings", "inputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true, "placeholder": "Enter section headings..."}}, "outputs": {"section_headings": {"type": "textarea", "label": "Final Headings", "db_field": "section_headings", "db_table": "post_development"}}}
25	7	Self Review	Conduct a self-review of the post	1	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}}
26	7	SEO Optimization	Optimize the post for search engines	2	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}}
27	8	Scheduling	Schedule the post for publication	1	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}}
28	8	Deployment	Deploy the post to production	2	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}}
29	9	Content Distribution	Manage content distribution across platforms	1	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}}
30	9	Engagement Tracking	Track post engagement metrics	2	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}}
1	1	Initial	Main step for this substage	1	{"title": "Initial Concept", "inputs": {"idea_seed": {"type": "textarea", "label": "Initial Idea", "db_field": "idea_seed", "db_table": "post_development", "required": true, "placeholder": "Type your idea here..."}}, "outputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting", "input_mapping": {"idea_seed": {"field": "idea_seed", "table": "post_development", "description": "The core idea to be expanded"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "expanded_idea", "table": "post_development"}}}, "description": "Enter your initial concept for the post here."}
21	1	Title	Generate a title for your post	2	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}}}, "description": "Generate a title for your post based on the expanded idea."}
16	19	Sections	Generate detailed content for each section of the outline	1	{}
22	1	Idea Scope	Define the scope and boundaries of your post idea	3	{"title": "Idea Scope", "inputs": {"idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true, "placeholder": "Define the scope of your idea..."}}, "outputs": {"idea_scope": {"type": "textarea", "label": "Scope Definition", "db_field": "idea_scope", "db_table": "post_development"}}}
23	3	Section Planning	Plan the sections of your post	3	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}}
12	2	Concepts	Research Concepts step	1	{"title": "Research Notes", "inputs": {"research_notes": {"type": "textarea", "label": "Research Notes", "db_field": "research_notes", "db_table": "post_development", "required": true, "placeholder": "Enter your research notes..."}}, "outputs": {"research_notes": {"type": "textarea", "label": "Processed Notes", "db_field": "research_notes", "db_table": "post_development"}}}
13	2	Useful Facts	Research Useful Facts step	2	{"title": "Research Facts", "inputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development", "required": true, "placeholder": "Enter interesting facts..."}}, "outputs": {"facts": {"type": "textarea", "label": "Verified Facts", "db_field": "facts", "db_table": "post_development"}}}
14	3	Outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
15	3	Allocate Facts	Allocate research facts to sections in the outline	2	{}
3	3	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
18	21	Main	Meta info step	1	{}
19	22	Main	Images step	1	{}
24	3	Section Headings	Define the headings for each section	4	{"title": "Section Headings", "inputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true, "placeholder": "Enter section headings..."}}, "outputs": {"section_headings": {"type": "textarea", "label": "Final Headings", "db_field": "section_headings", "db_table": "post_development"}}}
25	7	Self Review	Conduct a self-review of the post	1	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}}
26	7	SEO Optimization	Optimize the post for search engines	2	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}}
27	8	Scheduling	Schedule the post for publication	1	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}}
28	8	Deployment	Deploy the post to production	2	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}}
29	9	Content Distribution	Manage content distribution across platforms	1	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}}
30	9	Engagement Tracking	Track post engagement metrics	2	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}}
1	1	Initial	Main step for this substage	1	{"title": "Initial Concept", "inputs": {"idea_seed": {"type": "textarea", "label": "Initial Idea", "db_field": "idea_seed", "db_table": "post_development", "required": true, "placeholder": "Type your idea here..."}}, "outputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting", "input_mapping": {"idea_seed": {"field": "idea_seed", "table": "post_development", "description": "The core idea to be expanded"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "expanded_idea", "table": "post_development"}}}, "description": "Enter your initial concept for the post here."}
21	1	Title	Generate a title for your post	2	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}}}, "description": "Generate a title for your post based on the expanded idea."}
16	19	Sections	Generate detailed content for each section of the outline	1	{}
22	1	Idea Scope	Define the scope and boundaries of your post idea	3	{"title": "Idea Scope", "inputs": {"idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true, "placeholder": "Define the scope of your idea..."}}, "outputs": {"idea_scope": {"type": "textarea", "label": "Scope Definition", "db_field": "idea_scope", "db_table": "post_development"}}}
23	3	Section Planning	Plan the sections of your post	3	{"title": "Section Planning", "inputs": {"section_planning": {"type": "textarea", "label": "Section Planning", "db_field": "section_planning", "db_table": "post_development", "required": true, "placeholder": "Plan your sections..."}}, "outputs": {"section_planning": {"type": "textarea", "label": "Section Plan", "db_field": "section_planning", "db_table": "post_development"}}}
12	2	Concepts	Research Concepts step	1	{"title": "Research Notes", "inputs": {"research_notes": {"type": "textarea", "label": "Research Notes", "db_field": "research_notes", "db_table": "post_development", "required": true, "placeholder": "Enter your research notes..."}}, "outputs": {"research_notes": {"type": "textarea", "label": "Processed Notes", "db_field": "research_notes", "db_table": "post_development"}}}
13	2	Useful Facts	Research Useful Facts step	2	{"title": "Research Facts", "inputs": {"interesting_facts": {"type": "textarea", "label": "Interesting Facts", "db_field": "interesting_facts", "db_table": "post_development", "required": true, "placeholder": "Enter interesting facts..."}}, "outputs": {"facts": {"type": "textarea", "label": "Verified Facts", "db_field": "facts", "db_table": "post_development"}}}
14	3	Outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
15	3	Allocate Facts	Allocate research facts to sections in the outline	2	{}
3	3	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
18	21	Main	Meta info step	1	{}
19	22	Main	Images step	1	{}
24	3	Section Headings	Define the headings for each section	4	{"title": "Section Headings", "inputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true, "placeholder": "Enter section headings..."}}, "outputs": {"section_headings": {"type": "textarea", "label": "Final Headings", "db_field": "section_headings", "db_table": "post_development"}}}
25	7	Self Review	Conduct a self-review of the post	1	{"title": "Self Review", "inputs": {"self_review": {"type": "textarea", "label": "Self Review Notes", "db_field": "self_review", "db_table": "post_development", "required": true, "placeholder": "Enter self review notes..."}}, "outputs": {"self_review": {"type": "textarea", "label": "Review Results", "db_field": "self_review", "db_table": "post_development"}}}
26	7	SEO Optimization	Optimize the post for search engines	2	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}}
27	8	Scheduling	Schedule the post for publication	1	{"title": "Publication Scheduling", "inputs": {"scheduling": {"type": "textarea", "label": "Schedule Details", "db_field": "scheduling", "db_table": "post_development", "required": true, "placeholder": "Enter publication schedule..."}}, "outputs": {"scheduling": {"type": "textarea", "label": "Scheduled Time", "db_field": "scheduling", "db_table": "post_development"}}}
28	8	Deployment	Deploy the post to production	2	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}}
29	9	Content Distribution	Manage content distribution across platforms	1	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}}
30	9	Engagement Tracking	Track post engagement metrics	2	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}}
1	1	Initial	Main step for this substage	1	{"title": "Initial Concept", "inputs": {"idea_seed": {"type": "textarea", "label": "Initial Idea", "db_field": "idea_seed", "db_table": "post_development", "required": true, "placeholder": "Type your idea here..."}}, "outputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting", "input_mapping": {"idea_seed": {"field": "idea_seed", "table": "post_development", "description": "The core idea to be expanded"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "expanded_idea", "table": "post_development"}}}, "description": "Enter your initial concept for the post here."}
\.


--
-- Data for Name: workflow_step_format; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_step_format (id, step_id, post_id, input_format_id, output_format_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workflow_step_input; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_step_input (id, step_id, post_id, input_id, field_name) FROM stdin;
\.


--
-- Data for Name: workflow_step_prompt; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_step_prompt (id, step_id, system_prompt_id, task_prompt_id, created_at, updated_at) FROM stdin;
126	53	89	94	2025-07-27 17:15:54.722288+01	2025-07-28 06:58:16.264019+01
124	55	89	88	2025-07-27 13:44:15.876656+01	2025-07-29 09:26:09.940232+01
127	41	89	69	2025-07-29 09:29:31.700289+01	2025-07-29 10:12:04.776353+01
128	50	89	69	2025-07-29 11:50:59.141355+01	2025-07-29 11:50:59.141355+01
\.


--
-- Data for Name: workflow_steps; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_steps (id, post_workflow_sub_stage_id, step_order, name, description, llm_action_id, input_field, output_field, status, started_at, completed_at, notes) FROM stdin;
\.


--
-- Data for Name: workflow_sub_stage_entity; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_sub_stage_entity (id, stage_id, name, description, sub_stage_order) FROM stdin;
1	10	idea	Initial concept	1
2	10	research	Research and fact-finding	2
3	10	structure	Outline and structure	3
7	8	preflight	Pre-publication checks	1
8	8	launch	Publishing	2
9	8	syndication	Syndication and distribution	3
22	54	images	Add images	3
19	54	Sections	Content writing and development	1
21	54	post_info	Add meta information	2
\.


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.category_id_seq', 1, true);


--
-- Name: image_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_format_id_seq', 2, true);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_id_seq', 161, true);


--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_prompt_example_id_seq', 1, true);


--
-- Name: image_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_setting_id_seq', 2, true);


--
-- Name: image_style_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_style_id_seq', 2, true);


--
-- Name: images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.images_id_seq', 1, false);


--
-- Name: llm_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_action_history_id_seq', 1, true);


--
-- Name: llm_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_action_id_seq', 63, true);


--
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 2, true);


--
-- Name: llm_format_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_format_template_id_seq', 9, true);


--
-- Name: llm_interaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_interaction_id_seq', 1, true);


--
-- Name: llm_model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_model_id_seq', 23, true);


--
-- Name: llm_prompt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 107, true);


--
-- Name: llm_prompt_part_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_prompt_part_id_seq', 40, true);


--
-- Name: llm_provider_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_provider_id_seq', 5, true);


--
-- Name: post_development_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_development_id_seq', 46, true);


--
-- Name: post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_id_seq', 53, true);


--
-- Name: post_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_images_id_seq', 1, false);


--
-- Name: post_section_elements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_section_elements_id_seq', 1, true);


--
-- Name: post_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_section_id_seq', 731, true);


--
-- Name: post_workflow_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_stage_id_seq', 7, true);


--
-- Name: post_workflow_step_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_step_action_id_seq', 30, true);


--
-- Name: post_workflow_sub_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_sub_stage_id_seq', 1, true);


--
-- Name: substage_action_default_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.substage_action_default_id_seq', 4, true);


--
-- Name: tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.tag_id_seq', 1, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.user_id_seq', 1, true);


--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_field_mapping_id_seq', 1163, true);


--
-- Name: workflow_field_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_field_mappings_id_seq', 2, true);


--
-- Name: workflow_format_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_format_template_id_seq', 42, true);


--
-- Name: workflow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_id_seq', 2, true);


--
-- Name: workflow_post_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_post_format_id_seq', 1, true);


--
-- Name: workflow_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_stage_entity_id_seq', 58, true);


--
-- Name: workflow_stage_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_stage_format_id_seq', 1, true);


--
-- Name: workflow_step_context_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_context_config_id_seq', 1, true);


--
-- Name: workflow_step_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_entity_id_seq', 57, true);


--
-- Name: workflow_step_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_format_id_seq', 5, true);


--
-- Name: workflow_step_input_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_input_id_seq', 4, true);


--
-- Name: workflow_step_prompt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_prompt_id_seq', 128, true);


--
-- Name: workflow_steps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_steps_id_seq', 1, false);


--
-- Name: workflow_sub_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_sub_stage_entity_id_seq', 22, true);


--
-- Name: category category_name_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_name_key UNIQUE (name);


--
-- Name: category category_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_pkey PRIMARY KEY (id);


--
-- Name: category category_slug_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_slug_key UNIQUE (slug);


--
-- Name: image_format image_format_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_format
    ADD CONSTRAINT image_format_pkey PRIMARY KEY (id);


--
-- Name: image_format image_format_title_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_format
    ADD CONSTRAINT image_format_title_key UNIQUE (title);


--
-- Name: image image_path_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_path_key UNIQUE (path);


--
-- Name: image image_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);


--
-- Name: image_prompt_example image_prompt_example_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_pkey PRIMARY KEY (id);


--
-- Name: image_setting image_setting_name_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_name_key UNIQUE (name);


--
-- Name: image_setting image_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_pkey PRIMARY KEY (id);


--
-- Name: image_style image_style_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_style
    ADD CONSTRAINT image_style_pkey PRIMARY KEY (id);


--
-- Name: image_style image_style_title_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_style
    ADD CONSTRAINT image_style_title_key UNIQUE (title);


--
-- Name: images images_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.images
    ADD CONSTRAINT images_pkey PRIMARY KEY (id);


--
-- Name: llm_action_history llm_action_history_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action_history
    ADD CONSTRAINT llm_action_history_pkey PRIMARY KEY (id);


--
-- Name: llm_action llm_action_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_pkey PRIMARY KEY (id);


--
-- Name: llm_config llm_config_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_pkey PRIMARY KEY (id);


--
-- Name: llm_format_template llm_format_template_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_format_template
    ADD CONSTRAINT llm_format_template_pkey PRIMARY KEY (id);


--
-- Name: llm_interaction llm_interaction_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_interaction
    ADD CONSTRAINT llm_interaction_pkey PRIMARY KEY (id);


--
-- Name: llm_model llm_model_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_model
    ADD CONSTRAINT llm_model_pkey PRIMARY KEY (id);


--
-- Name: llm_prompt_part llm_prompt_part_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt_part
    ADD CONSTRAINT llm_prompt_part_pkey PRIMARY KEY (id);


--
-- Name: llm_prompt llm_prompt_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt
    ADD CONSTRAINT llm_prompt_pkey PRIMARY KEY (id);


--
-- Name: llm_provider llm_provider_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_provider
    ADD CONSTRAINT llm_provider_pkey PRIMARY KEY (id);


--
-- Name: post_categories post_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_categories
    ADD CONSTRAINT post_categories_pkey PRIMARY KEY (post_id, category_id);


--
-- Name: post_development post_development_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_development
    ADD CONSTRAINT post_development_pkey PRIMARY KEY (id);


--
-- Name: post_development post_development_post_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_development
    ADD CONSTRAINT post_development_post_id_key UNIQUE (post_id);


--
-- Name: post_images post_images_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_images
    ADD CONSTRAINT post_images_pkey PRIMARY KEY (id);


--
-- Name: post_images post_images_post_id_image_type_section_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_images
    ADD CONSTRAINT post_images_post_id_image_type_section_id_key UNIQUE (post_id, image_type, section_id);


--
-- Name: post post_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_pkey PRIMARY KEY (id);


--
-- Name: post_section_elements post_section_elements_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section_elements
    ADD CONSTRAINT post_section_elements_pkey PRIMARY KEY (id);


--
-- Name: post_section post_section_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section
    ADD CONSTRAINT post_section_pkey PRIMARY KEY (id);


--
-- Name: post post_slug_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_slug_key UNIQUE (slug);


--
-- Name: post_tags post_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_pkey PRIMARY KEY (post_id, tag_id);


--
-- Name: post_workflow_stage post_workflow_stage_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_stage
    ADD CONSTRAINT post_workflow_stage_pkey PRIMARY KEY (id);


--
-- Name: post_workflow_stage post_workflow_stage_post_id_stage_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_stage
    ADD CONSTRAINT post_workflow_stage_post_id_stage_id_key UNIQUE (post_id, stage_id);


--
-- Name: post_workflow_step_action post_workflow_step_action_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_step_action
    ADD CONSTRAINT post_workflow_step_action_pkey PRIMARY KEY (id);


--
-- Name: post_workflow_sub_stage post_workflow_sub_stage_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_sub_stage
    ADD CONSTRAINT post_workflow_sub_stage_pkey PRIMARY KEY (id);


--
-- Name: post_workflow_sub_stage post_workflow_sub_stage_post_workflow_stage_id_sub_stage_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_sub_stage
    ADD CONSTRAINT post_workflow_sub_stage_post_workflow_stage_id_sub_stage_id_key UNIQUE (post_workflow_stage_id, sub_stage_id);


--
-- Name: substage_action_default substage_action_default_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.substage_action_default
    ADD CONSTRAINT substage_action_default_pkey PRIMARY KEY (id);


--
-- Name: substage_action_default substage_action_default_substage_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.substage_action_default
    ADD CONSTRAINT substage_action_default_substage_key UNIQUE (substage);


--
-- Name: tag tag_name_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_name_key UNIQUE (name);


--
-- Name: tag tag_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_pkey PRIMARY KEY (id);


--
-- Name: tag tag_slug_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_slug_key UNIQUE (slug);


--
-- Name: post_section_elements unique_element_per_section; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section_elements
    ADD CONSTRAINT unique_element_per_section UNIQUE (post_id, section_id, element_text);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: workflow_field_mapping workflow_field_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_pkey PRIMARY KEY (id);


--
-- Name: workflow_field_mappings workflow_field_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mappings
    ADD CONSTRAINT workflow_field_mappings_pkey PRIMARY KEY (id);


--
-- Name: workflow_format_template workflow_format_template_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_format_template
    ADD CONSTRAINT workflow_format_template_pkey PRIMARY KEY (id);


--
-- Name: workflow workflow_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_pkey PRIMARY KEY (id);


--
-- Name: workflow_post_format workflow_post_format_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_post_format
    ADD CONSTRAINT workflow_post_format_pkey PRIMARY KEY (id);


--
-- Name: workflow_post_format workflow_post_format_post_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_post_format
    ADD CONSTRAINT workflow_post_format_post_id_key UNIQUE (post_id);


--
-- Name: workflow workflow_post_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_post_id_key UNIQUE (post_id);


--
-- Name: workflow_stage_entity workflow_stage_entity_name_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_entity
    ADD CONSTRAINT workflow_stage_entity_name_key UNIQUE (name);


--
-- Name: workflow_stage_entity workflow_stage_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_entity
    ADD CONSTRAINT workflow_stage_entity_pkey PRIMARY KEY (id);


--
-- Name: workflow_stage_format workflow_stage_format_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_format
    ADD CONSTRAINT workflow_stage_format_pkey PRIMARY KEY (id);


--
-- Name: workflow_stage_format workflow_stage_format_stage_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_format
    ADD CONSTRAINT workflow_stage_format_stage_id_key UNIQUE (stage_id);


--
-- Name: workflow_step_context_config workflow_step_context_config_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_context_config
    ADD CONSTRAINT workflow_step_context_config_pkey PRIMARY KEY (id);


--
-- Name: workflow_step_entity workflow_step_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity
    ADD CONSTRAINT workflow_step_entity_pkey PRIMARY KEY (id);


--
-- Name: workflow_step_entity workflow_step_entity_sub_stage_id_name_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity
    ADD CONSTRAINT workflow_step_entity_sub_stage_id_name_key UNIQUE (sub_stage_id, name);


--
-- Name: workflow_step_format workflow_step_format_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_format
    ADD CONSTRAINT workflow_step_format_pkey PRIMARY KEY (id);


--
-- Name: workflow_step_input workflow_step_input_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_input
    ADD CONSTRAINT workflow_step_input_pkey PRIMARY KEY (id);


--
-- Name: workflow_step_input workflow_step_input_step_id_post_id_input_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_input
    ADD CONSTRAINT workflow_step_input_step_id_post_id_input_id_key UNIQUE (step_id, post_id, input_id);


--
-- Name: workflow_step_prompt workflow_step_prompt_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_prompt
    ADD CONSTRAINT workflow_step_prompt_pkey PRIMARY KEY (id);


--
-- Name: workflow_step_prompt workflow_step_prompt_step_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_prompt
    ADD CONSTRAINT workflow_step_prompt_step_id_key UNIQUE (step_id);


--
-- Name: workflow_steps workflow_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_pkey PRIMARY KEY (id);


--
-- Name: workflow_steps workflow_steps_post_workflow_sub_stage_id_step_order_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_post_workflow_sub_stage_id_step_order_key UNIQUE (post_workflow_sub_stage_id, step_order);


--
-- Name: workflow_sub_stage_entity workflow_sub_stage_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT workflow_sub_stage_entity_pkey PRIMARY KEY (id);


--
-- Name: workflow_sub_stage_entity workflow_sub_stage_entity_stage_id_name_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT workflow_sub_stage_entity_stage_id_name_key UNIQUE (stage_id, name);


--
-- Name: idx_format_template_name; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_format_template_name ON public.llm_format_template USING btree (name);


--
-- Name: idx_format_template_type; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_format_template_type ON public.llm_format_template USING btree (format_type);


--
-- Name: idx_image_path; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_image_path ON public.image USING btree (path);


--
-- Name: idx_images_created_at; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_images_created_at ON public.images USING btree (created_at);


--
-- Name: idx_llm_action_field; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_llm_action_field ON public.llm_action USING btree (field_name);


--
-- Name: idx_llm_action_history_status; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_llm_action_history_status ON public.llm_action_history USING btree (status);


--
-- Name: idx_post_created; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_created ON public.post USING btree (created_at);


--
-- Name: idx_post_development_post_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_development_post_id ON public.post_development USING btree (post_id);


--
-- Name: idx_post_images_image_type; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_images_image_type ON public.post_images USING btree (image_type);


--
-- Name: idx_post_images_post_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_images_post_id ON public.post_images USING btree (post_id);


--
-- Name: idx_post_images_section_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_images_section_id ON public.post_images USING btree (section_id);


--
-- Name: idx_post_section_elements_post_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_section_elements_post_id ON public.post_section_elements USING btree (post_id);


--
-- Name: idx_post_section_elements_section_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_section_elements_section_id ON public.post_section_elements USING btree (section_id);


--
-- Name: idx_post_section_elements_type; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_section_elements_type ON public.post_section_elements USING btree (element_type);


--
-- Name: idx_post_section_post_order; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_section_post_order ON public.post_section USING btree (post_id, section_order);


--
-- Name: idx_post_slug; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_slug ON public.post USING btree (slug);


--
-- Name: idx_post_status; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_status ON public.post USING btree (status);


--
-- Name: idx_post_workflow_stage_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_workflow_stage_post ON public.post_workflow_stage USING btree (post_id);


--
-- Name: idx_post_workflow_stage_stage; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_workflow_stage_stage ON public.post_workflow_stage USING btree (stage_id);


--
-- Name: idx_post_workflow_step_action_action_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_workflow_step_action_action_id ON public.post_workflow_step_action USING btree (action_id);


--
-- Name: idx_post_workflow_step_action_post_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_workflow_step_action_post_id ON public.post_workflow_step_action USING btree (post_id);


--
-- Name: idx_post_workflow_step_action_step_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_workflow_step_action_step_id ON public.post_workflow_step_action USING btree (step_id);


--
-- Name: idx_workflow_field_mapping_name; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_field_mapping_name ON public.workflow_field_mapping USING btree (field_name);


--
-- Name: idx_workflow_field_mapping_stage; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_field_mapping_stage ON public.workflow_field_mapping USING btree (stage_id);


--
-- Name: idx_workflow_field_mapping_step; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_field_mapping_step ON public.workflow_field_mapping USING btree (workflow_step_id, field_type);


--
-- Name: idx_workflow_field_mapping_substage; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_field_mapping_substage ON public.workflow_field_mapping USING btree (substage_id);


--
-- Name: idx_workflow_field_mapping_table; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_field_mapping_table ON public.workflow_field_mapping USING btree (table_name);


--
-- Name: idx_workflow_field_mapping_unique; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE UNIQUE INDEX idx_workflow_field_mapping_unique ON public.workflow_field_mapping USING btree (workflow_step_id, field_name, field_type) WHERE (workflow_step_id IS NOT NULL);


--
-- Name: idx_workflow_format_template_fields; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_format_template_fields ON public.workflow_format_template USING gin (fields);


--
-- Name: idx_workflow_format_template_name; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_format_template_name ON public.workflow_format_template USING btree (name);


--
-- Name: idx_workflow_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_post ON public.workflow USING btree (post_id);


--
-- Name: idx_workflow_post_format_post_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_post_format_post_id ON public.workflow_post_format USING btree (post_id);


--
-- Name: idx_workflow_post_format_template_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_post_format_template_id ON public.workflow_post_format USING btree (template_id);


--
-- Name: idx_workflow_stage_format_stage_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_stage_format_stage_id ON public.workflow_stage_format USING btree (stage_id);


--
-- Name: idx_workflow_stage_format_template_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_stage_format_template_id ON public.workflow_stage_format USING btree (template_id);


--
-- Name: idx_workflow_stage_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_stage_id ON public.workflow USING btree (stage_id);


--
-- Name: idx_workflow_step_context_config_step_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_step_context_config_step_id ON public.workflow_step_context_config USING btree (step_id);


--
-- Name: idx_workflow_step_format_input; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_step_format_input ON public.workflow_step_format USING btree (input_format_id);


--
-- Name: idx_workflow_step_format_output; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_step_format_output ON public.workflow_step_format USING btree (output_format_id);


--
-- Name: idx_workflow_step_format_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_step_format_post ON public.workflow_step_format USING btree (post_id);


--
-- Name: idx_workflow_step_format_step; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_step_format_step ON public.workflow_step_format USING btree (step_id);


--
-- Name: idx_workflow_step_format_unique; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE UNIQUE INDEX idx_workflow_step_format_unique ON public.workflow_step_format USING btree (step_id, post_id);


--
-- Name: idx_workflow_steps_action; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_steps_action ON public.workflow_steps USING btree (llm_action_id);


--
-- Name: idx_workflow_steps_status; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_steps_status ON public.workflow_steps USING btree (status);


--
-- Name: idx_workflow_steps_sub_stage; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_steps_sub_stage ON public.workflow_steps USING btree (post_workflow_sub_stage_id);


--
-- Name: unique_provider_model; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE UNIQUE INDEX unique_provider_model ON public.llm_model USING btree (provider_id, name);


--
-- Name: post_development trigger_sync_section_headings; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER trigger_sync_section_headings AFTER UPDATE OF section_headings ON public.post_development FOR EACH ROW EXECUTE FUNCTION public.sync_section_headings_to_sections();


--
-- Name: post_section trigger_sync_sections_to_headings; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER trigger_sync_sections_to_headings AFTER INSERT OR DELETE OR UPDATE ON public.post_section FOR EACH ROW EXECUTE FUNCTION public.sync_sections_to_section_headings();

ALTER TABLE public.post_section DISABLE TRIGGER trigger_sync_sections_to_headings;


--
-- Name: workflow_field_mapping trigger_update_workflow_field_mapping_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER trigger_update_workflow_field_mapping_updated_at BEFORE UPDATE ON public.workflow_field_mapping FOR EACH ROW EXECUTE FUNCTION public.update_workflow_field_mapping_updated_at();


--
-- Name: workflow_post_format trigger_workflow_post_format_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER trigger_workflow_post_format_updated_at BEFORE UPDATE ON public.workflow_post_format FOR EACH ROW EXECUTE FUNCTION public.update_workflow_post_format_updated_at();


--
-- Name: workflow_stage_format trigger_workflow_stage_format_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER trigger_workflow_stage_format_updated_at BEFORE UPDATE ON public.workflow_stage_format FOR EACH ROW EXECUTE FUNCTION public.update_workflow_stage_format_updated_at();


--
-- Name: image_format update_image_format_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_image_format_updated_at BEFORE UPDATE ON public.image_format FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: image_prompt_example update_image_prompt_example_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_image_prompt_example_updated_at BEFORE UPDATE ON public.image_prompt_example FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: image_setting update_image_setting_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_image_setting_updated_at BEFORE UPDATE ON public.image_setting FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: image_style update_image_style_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_image_style_updated_at BEFORE UPDATE ON public.image_style FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: image update_image_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_image_updated_at BEFORE UPDATE ON public.image FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: images update_images_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON public.images FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: llm_action update_llm_action_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_llm_action_updated_at BEFORE UPDATE ON public.llm_action FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: post_development update_post_development_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_post_development_updated_at BEFORE UPDATE ON public.post_development FOR EACH ROW EXECUTE FUNCTION public.update_post_development_updated_at_column();


--
-- Name: post_section_elements update_post_section_elements_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_post_section_elements_updated_at BEFORE UPDATE ON public.post_section_elements FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: post update_post_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_post_updated_at BEFORE UPDATE ON public.post FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user update_user_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON public."user" FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: workflow_format_template update_workflow_format_template_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_workflow_format_template_updated_at BEFORE UPDATE ON public.workflow_format_template FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: workflow_steps update_workflow_steps_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_workflow_steps_updated_at BEFORE UPDATE ON public.workflow_steps FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: workflow update_workflow_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_workflow_updated_at BEFORE UPDATE ON public.workflow FOR EACH ROW EXECUTE FUNCTION public.update_workflow_updated_at_column();


--
-- Name: llm_action fk_llm_action_provider; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT fk_llm_action_provider FOREIGN KEY (provider_id) REFERENCES public.llm_provider(id);


--
-- Name: workflow_sub_stage_entity fk_stage_id; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT fk_stage_id FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: image_prompt_example image_prompt_example_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_format_id_fkey FOREIGN KEY (format_id) REFERENCES public.image_format(id);


--
-- Name: image_prompt_example image_prompt_example_image_setting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_image_setting_id_fkey FOREIGN KEY (image_setting_id) REFERENCES public.image_setting(id);


--
-- Name: image_prompt_example image_prompt_example_style_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_style_id_fkey FOREIGN KEY (style_id) REFERENCES public.image_style(id);


--
-- Name: image_setting image_setting_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_format_id_fkey FOREIGN KEY (format_id) REFERENCES public.image_format(id);


--
-- Name: image_setting image_setting_style_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_style_id_fkey FOREIGN KEY (style_id) REFERENCES public.image_style(id);


--
-- Name: llm_action_history llm_action_history_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action_history
    ADD CONSTRAINT llm_action_history_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.llm_action(id);


--
-- Name: llm_action_history llm_action_history_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action_history
    ADD CONSTRAINT llm_action_history_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: llm_interaction llm_interaction_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_interaction
    ADD CONSTRAINT llm_interaction_prompt_id_fkey FOREIGN KEY (prompt_id) REFERENCES public.llm_prompt(id);


--
-- Name: llm_model llm_model_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_model
    ADD CONSTRAINT llm_model_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.llm_provider(id) ON DELETE CASCADE;


--
-- Name: llm_prompt_part llm_prompt_part_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt_part
    ADD CONSTRAINT llm_prompt_part_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.llm_action(id) ON DELETE CASCADE;


--
-- Name: llm_prompt llm_prompt_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt
    ADD CONSTRAINT llm_prompt_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.workflow_step_entity(id);


--
-- Name: post_categories post_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_categories
    ADD CONSTRAINT post_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.category(id) ON DELETE CASCADE;


--
-- Name: post_categories post_categories_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_categories
    ADD CONSTRAINT post_categories_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id) ON DELETE CASCADE;


--
-- Name: post_development post_development_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_development
    ADD CONSTRAINT post_development_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post post_header_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_header_image_id_fkey FOREIGN KEY (header_image_id) REFERENCES public.image(id);


--
-- Name: post_images post_images_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_images
    ADD CONSTRAINT post_images_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.images(id) ON DELETE CASCADE;


--
-- Name: post_images post_images_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_images
    ADD CONSTRAINT post_images_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id) ON DELETE CASCADE;


--
-- Name: post_images post_images_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_images
    ADD CONSTRAINT post_images_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.post_section(id) ON DELETE CASCADE;


--
-- Name: post_section_elements post_section_elements_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section_elements
    ADD CONSTRAINT post_section_elements_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post_section_elements post_section_elements_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section_elements
    ADD CONSTRAINT post_section_elements_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.post_section(id);


--
-- Name: post_section post_section_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section
    ADD CONSTRAINT post_section_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post_tags post_tags_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id) ON DELETE CASCADE;


--
-- Name: post_tags post_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag(id) ON DELETE CASCADE;


--
-- Name: post_workflow_stage post_workflow_stage_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_stage
    ADD CONSTRAINT post_workflow_stage_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: post_workflow_step_action post_workflow_step_action_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_step_action
    ADD CONSTRAINT post_workflow_step_action_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.llm_action(id);


--
-- Name: post_workflow_step_action post_workflow_step_action_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_step_action
    ADD CONSTRAINT post_workflow_step_action_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post_workflow_step_action post_workflow_step_action_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_step_action
    ADD CONSTRAINT post_workflow_step_action_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.workflow_step_entity(id);


--
-- Name: post_workflow_sub_stage post_workflow_sub_stage_post_workflow_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_sub_stage
    ADD CONSTRAINT post_workflow_sub_stage_post_workflow_stage_id_fkey FOREIGN KEY (post_workflow_stage_id) REFERENCES public.post_workflow_stage(id) ON DELETE CASCADE;


--
-- Name: substage_action_default substage_action_default_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.substage_action_default
    ADD CONSTRAINT substage_action_default_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.llm_action(id);


--
-- Name: workflow_field_mapping workflow_field_mapping_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id);


--
-- Name: workflow_field_mapping workflow_field_mapping_substage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_substage_id_fkey FOREIGN KEY (substage_id) REFERENCES public.workflow_sub_stage_entity(id);


--
-- Name: workflow_field_mapping workflow_field_mapping_workflow_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_workflow_step_id_fkey FOREIGN KEY (workflow_step_id) REFERENCES public.workflow_step_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_post_format workflow_post_format_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_post_format
    ADD CONSTRAINT workflow_post_format_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id) ON DELETE CASCADE;


--
-- Name: workflow_post_format workflow_post_format_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_post_format
    ADD CONSTRAINT workflow_post_format_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.workflow_format_template(id) ON DELETE CASCADE;


--
-- Name: workflow workflow_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: workflow_stage_format workflow_stage_format_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_format
    ADD CONSTRAINT workflow_stage_format_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_stage_format workflow_stage_format_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_format
    ADD CONSTRAINT workflow_stage_format_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.workflow_format_template(id) ON DELETE CASCADE;


--
-- Name: workflow workflow_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id);


--
-- Name: workflow_step_context_config workflow_step_context_config_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_context_config
    ADD CONSTRAINT workflow_step_context_config_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.workflow_step_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_step_entity workflow_step_entity_default_input_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity
    ADD CONSTRAINT workflow_step_entity_default_input_format_id_fkey FOREIGN KEY (default_input_format_id) REFERENCES public.workflow_format_template(id);


--
-- Name: workflow_step_entity workflow_step_entity_default_output_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity
    ADD CONSTRAINT workflow_step_entity_default_output_format_id_fkey FOREIGN KEY (default_output_format_id) REFERENCES public.workflow_format_template(id);


--
-- Name: workflow_step_entity workflow_step_entity_sub_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity
    ADD CONSTRAINT workflow_step_entity_sub_stage_id_fkey FOREIGN KEY (sub_stage_id) REFERENCES public.workflow_sub_stage_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_step_format workflow_step_format_input_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_format
    ADD CONSTRAINT workflow_step_format_input_format_id_fkey FOREIGN KEY (input_format_id) REFERENCES public.workflow_format_template(id) ON DELETE SET NULL;


--
-- Name: workflow_step_format workflow_step_format_output_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_format
    ADD CONSTRAINT workflow_step_format_output_format_id_fkey FOREIGN KEY (output_format_id) REFERENCES public.workflow_format_template(id) ON DELETE SET NULL;


--
-- Name: workflow_step_format workflow_step_format_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_format
    ADD CONSTRAINT workflow_step_format_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id) ON DELETE CASCADE;


--
-- Name: workflow_step_format workflow_step_format_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_format
    ADD CONSTRAINT workflow_step_format_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.workflow_step_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_step_input workflow_step_input_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_input
    ADD CONSTRAINT workflow_step_input_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.workflow_step_entity(id);


--
-- Name: workflow_step_prompt workflow_step_prompt_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_prompt
    ADD CONSTRAINT workflow_step_prompt_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.workflow_step_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_step_prompt workflow_step_prompt_system_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_prompt
    ADD CONSTRAINT workflow_step_prompt_system_prompt_id_fkey FOREIGN KEY (system_prompt_id) REFERENCES public.llm_prompt(id) ON DELETE CASCADE;


--
-- Name: workflow_step_prompt workflow_step_prompt_task_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_prompt
    ADD CONSTRAINT workflow_step_prompt_task_prompt_id_fkey FOREIGN KEY (task_prompt_id) REFERENCES public.llm_prompt(id) ON DELETE CASCADE;


--
-- Name: workflow_steps workflow_steps_llm_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_llm_action_id_fkey FOREIGN KEY (llm_action_id) REFERENCES public.llm_action(id);


--
-- Name: workflow_steps workflow_steps_post_workflow_sub_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_steps
    ADD CONSTRAINT workflow_steps_post_workflow_sub_stage_id_fkey FOREIGN KEY (post_workflow_sub_stage_id) REFERENCES public.post_workflow_sub_stage(id) ON DELETE CASCADE;


--
-- Name: workflow_sub_stage_entity workflow_sub_stage_entity_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT workflow_sub_stage_entity_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: TABLE category; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.category TO postgres;


--
-- Name: SEQUENCE category_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.category_id_seq TO postgres;


--
-- Name: TABLE image; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image TO postgres;


--
-- Name: TABLE image_format; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_format TO postgres;


--
-- Name: SEQUENCE image_format_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_format_id_seq TO postgres;


--
-- Name: SEQUENCE image_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_id_seq TO postgres;


--
-- Name: TABLE image_prompt_example; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_prompt_example TO postgres;


--
-- Name: SEQUENCE image_prompt_example_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_prompt_example_id_seq TO postgres;


--
-- Name: TABLE image_setting; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_setting TO postgres;


--
-- Name: SEQUENCE image_setting_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_setting_id_seq TO postgres;


--
-- Name: TABLE image_style; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_style TO postgres;


--
-- Name: SEQUENCE image_style_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_style_id_seq TO postgres;


--
-- Name: TABLE images; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.images TO postgres;


--
-- Name: TABLE llm_action; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_action TO postgres;


--
-- Name: TABLE llm_action_history; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_action_history TO postgres;


--
-- Name: SEQUENCE llm_action_history_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_action_history_id_seq TO postgres;


--
-- Name: SEQUENCE llm_action_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_action_id_seq TO postgres;


--
-- Name: TABLE llm_config; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_config TO postgres;


--
-- Name: SEQUENCE llm_config_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT,USAGE ON SEQUENCE public.llm_config_id_seq TO postgres;


--
-- Name: TABLE llm_format_template; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_format_template TO postgres;


--
-- Name: TABLE llm_interaction; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_interaction TO postgres;


--
-- Name: SEQUENCE llm_interaction_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_interaction_id_seq TO postgres;


--
-- Name: TABLE llm_model; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_model TO postgres;


--
-- Name: SEQUENCE llm_model_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_model_id_seq TO postgres;


--
-- Name: TABLE llm_prompt; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_prompt TO postgres;


--
-- Name: SEQUENCE llm_prompt_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_prompt_id_seq TO postgres;


--
-- Name: TABLE llm_prompt_part; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_prompt_part TO postgres;


--
-- Name: SEQUENCE llm_prompt_part_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_prompt_part_id_seq TO postgres;


--
-- Name: TABLE llm_provider; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_provider TO postgres;


--
-- Name: SEQUENCE llm_provider_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_provider_id_seq TO postgres;


--
-- Name: TABLE post; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post TO postgres;


--
-- Name: TABLE post_categories; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_categories TO postgres;


--
-- Name: TABLE post_development; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_development TO postgres;


--
-- Name: SEQUENCE post_development_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_development_id_seq TO postgres;


--
-- Name: SEQUENCE post_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_id_seq TO postgres;


--
-- Name: TABLE post_images; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_images TO postgres;


--
-- Name: TABLE post_section; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_section TO postgres;


--
-- Name: TABLE post_section_backup_20250109; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_section_backup_20250109 TO postgres;


--
-- Name: TABLE post_section_elements; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_section_elements TO postgres;


--
-- Name: SEQUENCE post_section_elements_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT,USAGE ON SEQUENCE public.post_section_elements_id_seq TO postgres;


--
-- Name: SEQUENCE post_section_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_section_id_seq TO postgres;


--
-- Name: TABLE post_tags; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_tags TO postgres;


--
-- Name: TABLE post_workflow_stage; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT ON TABLE public.post_workflow_stage TO PUBLIC;
GRANT ALL ON TABLE public.post_workflow_stage TO postgres;


--
-- Name: SEQUENCE post_workflow_stage_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_workflow_stage_id_seq TO postgres;


--
-- Name: TABLE post_workflow_step_action; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_workflow_step_action TO postgres;


--
-- Name: SEQUENCE post_workflow_step_action_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT,USAGE ON SEQUENCE public.post_workflow_step_action_id_seq TO postgres;


--
-- Name: TABLE post_workflow_sub_stage; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT ON TABLE public.post_workflow_sub_stage TO PUBLIC;
GRANT ALL ON TABLE public.post_workflow_sub_stage TO postgres;


--
-- Name: SEQUENCE post_workflow_sub_stage_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_workflow_sub_stage_id_seq TO postgres;


--
-- Name: TABLE substage_action_default; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.substage_action_default TO postgres;


--
-- Name: SEQUENCE substage_action_default_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.substage_action_default_id_seq TO postgres;


--
-- Name: TABLE tag; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.tag TO postgres;


--
-- Name: SEQUENCE tag_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.tag_id_seq TO postgres;


--
-- Name: TABLE "user"; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public."user" TO postgres;


--
-- Name: SEQUENCE user_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.user_id_seq TO postgres;


--
-- Name: TABLE workflow; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow TO postgres;


--
-- Name: TABLE workflow_field_mapping; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_field_mapping TO postgres;


--
-- Name: TABLE workflow_field_mappings; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_field_mappings TO postgres;


--
-- Name: TABLE workflow_format_template; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_format_template TO postgres;


--
-- Name: SEQUENCE workflow_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.workflow_id_seq TO postgres;


--
-- Name: TABLE workflow_post_format; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_post_format TO postgres;


--
-- Name: TABLE workflow_stage_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT ON TABLE public.workflow_stage_entity TO PUBLIC;
GRANT ALL ON TABLE public.workflow_stage_entity TO postgres;


--
-- Name: SEQUENCE workflow_stage_entity_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.workflow_stage_entity_id_seq TO postgres;


--
-- Name: TABLE workflow_stage_format; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_stage_format TO postgres;


--
-- Name: TABLE workflow_step_context_config; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_step_context_config TO postgres;


--
-- Name: TABLE workflow_step_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_step_entity TO postgres;


--
-- Name: TABLE workflow_step_entity_backup; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.workflow_step_entity_backup TO nickfiddes;


--
-- Name: TABLE workflow_step_format; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_step_format TO postgres;


--
-- Name: TABLE workflow_step_prompt; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_step_prompt TO postgres;


--
-- Name: TABLE workflow_steps; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_steps TO postgres;


--
-- Name: SEQUENCE workflow_steps_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT,USAGE ON SEQUENCE public.workflow_steps_id_seq TO postgres;


--
-- Name: TABLE workflow_sub_stage_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_sub_stage_entity TO postgres;


--
-- Name: SEQUENCE workflow_sub_stage_entity_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT,USAGE ON SEQUENCE public.workflow_sub_stage_entity_id_seq TO postgres;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: nickfiddes
--

ALTER DEFAULT PRIVILEGES FOR ROLE nickfiddes IN SCHEMA public GRANT ALL ON TABLES  TO postgres;


--
-- PostgreSQL database dump complete
--

