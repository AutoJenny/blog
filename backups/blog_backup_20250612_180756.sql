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
    prompt_json jsonb
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
    substage_id integer
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
    sections text
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
-- Name: post_section; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_section (
    id integer NOT NULL,
    post_id integer NOT NULL,
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
    status text DEFAULT 'draft'::text
);


ALTER TABLE public.post_section OWNER TO nickfiddes;

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
    CONSTRAINT post_section_elements_element_type_check CHECK (((element_type)::text = ANY ((ARRAY['fact'::character varying, 'idea'::character varying, 'theme'::character varying])::text[])))
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
-- Name: workflow_field_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workflow_field_mapping (
    id integer NOT NULL,
    field_name text NOT NULL,
    stage_id integer,
    substage_id integer,
    order_index integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.workflow_field_mapping OWNER TO postgres;

--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workflow_field_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_field_mapping_id_seq OWNER TO postgres;

--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workflow_field_mapping_id_seq OWNED BY public.workflow_field_mapping.id;


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
-- Name: workflow_step_entity; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_step_entity (
    id integer NOT NULL,
    sub_stage_id integer,
    name character varying(100) NOT NULL,
    description text,
    step_order integer NOT NULL,
    config jsonb DEFAULT '{}'::jsonb
);


ALTER TABLE public.workflow_step_entity OWNER TO nickfiddes;

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
-- Name: llm_action id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action ALTER COLUMN id SET DEFAULT nextval('public.llm_action_id_seq'::regclass);


--
-- Name: llm_action_history id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action_history ALTER COLUMN id SET DEFAULT nextval('public.llm_action_history_id_seq'::regclass);


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
-- Name: workflow_field_mapping id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_field_mapping ALTER COLUMN id SET DEFAULT nextval('public.workflow_field_mapping_id_seq'::regclass);


--
-- Name: workflow_stage_entity id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_stage_entity ALTER COLUMN id SET DEFAULT nextval('public.workflow_stage_entity_id_seq'::regclass);


--
-- Name: workflow_step_entity id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity ALTER COLUMN id SET DEFAULT nextval('public.workflow_step_entity_id_seq'::regclass);


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
\.


--
-- Data for Name: image_style; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.image_style (id, title, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_action; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_action (id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, "order", created_at, updated_at, input_field, output_field, provider_id, timeout) FROM stdin;
49	French poem	You are Start every response with "TITLE: NONSENSE".\nWrite in the style of Write entirely in French.\nTask: Write a short poem	42	llama3.1:70b	0.7	1000	0	2025-05-29 14:07:39.119426	2025-05-29 19:05:42.715892	\N	basic_idea	1	60
53	CLAN UI expander	Expert in the services and functionality of the CLAN.com web site, which specialises in authentic Scottish heritage products and information. Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.. Explain the service, functionality, and products available through https://clan.com/tartandesigner/ and its sub-pages.	47	deepseek-coder:latest	0.7	1000	0	2025-05-31 13:27:25.382108	2025-05-31 13:27:25.382108	\N	\N	1	60
54	50 facts	Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism. Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50.	49	llama3.1:70b	0.7	1000	0	2025-05-31 13:36:37.796867	2025-06-01 08:50:26.700821	\N	\N	1	421
60	section_structure_creator	Create a structured outline for a blog post with the following details:\n\nTitle: {{title}}\nBasic Idea: {{idea}}\nInteresting Facts:\n{{#each facts}}\n- {{this}}\n{{/each}}\n\nIMPORTANT: Your response must be a valid JSON array. Do not include any other text or explanation.\n\nExample format:\n[\n  {\n    "heading": "Introduction",\n    "theme": "Setting the context and importance",\n    "facts": ["Fact 1"],\n    "ideas": ["Key point 1"]\n  },\n  {\n    "heading": "Main Section",\n    "theme": "Core topic exploration",\n    "facts": ["Fact 2"],\n    "ideas": ["Key point 2"]\n  }\n]\n\nPlease provide your response in exactly this format, with no additional text.	55	mistral	0.7	2000	1	2025-06-08 09:36:05.843956	2025-06-08 20:01:53.716995	structure_input	structure_output	1	120
58	Section Structure Creator	[system] You are a professional content strategist. Your task is to create a logical structure for a blog post.\\n\\n[user] Create a section structure for a blog post with the following details:\\nTitle: {{title}}\\nMain Idea: {{idea}}\\nFacts to Include: {{facts|join(", ")}}\\n\\nReturn ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }. The output must be a JSON object with a single key "sections" containing an array of section objects. Each section object must have exactly these fields: "name" (string), "description" (string). Example output: { "sections": [ { "name": "Introduction", "description": "Overview of the topic and why it matters" }, { "name": "Historical Context", "description": "Background and evolution of the topic" } ] }	53	mistral	0.7	1000	0	2025-06-07 15:11:04.255234	2025-06-07 15:20:54.542883	\N	\N	1	60
56	Section Creator JSON	[system: ROLE] You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them. [user: FORMAT] Return ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }.  Example output: { "sections": [ { "name": "Introduction", "description": "Overview of the topic", "themes": ["history", "significance"], "facts": ["Fact 1", "Fact 2"] }, { "name": "Historical Evolution", "description": "How the topic evolved over time", "themes": ["evolution", "design"], "facts": ["Fact 3"] } ] }	52	llama3.1:70b	0.7	1000	0	2025-06-06 11:08:44.866521	2025-06-07 15:02:55.952842	\N	\N	1	60
59	Content Allocator	Allocate ideas and facts to sections	54	mistral	0.7	1000	0	2025-06-07 15:11:04.255234	2025-06-07 15:11:04.255234	\N	\N	1	60
61	content_allocator	Allocate the following ideas and facts to the provided sections.\\n\\nSections: {{sections}}\\nIdeas: {{ideas}}\\nFacts: {{facts}}\\n\\nReturn a JSON array of sections, each with:\\n- heading: Section title\\n- description: Section description\\n- ideas: Array of allocated ideas\\n- facts: Array of allocated facts	56	mistral	0.7	2000	2	2025-06-08 09:37:15.106556	2025-06-08 09:37:15.106556	allocation_input	allocation_output	1	120
48	Seed to basic	[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]	41	llama3.1:70b	0.7	1000	0	2025-05-29 14:01:44.088523	2025-06-09 16:09:26.033214	\N	basic_idea	1	60
14	Expand from seed idea to Scottish brief	[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting	26	llama3.1:70b	0.7	1000	0	2025-06-09 16:17:09.437403	2025-06-09 16:20:44.870693	\N	\N	1	60
\.


--
-- Data for Name: llm_action_history; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_action_history (id, action_id, post_id, input_text, output_text, status, error_message, created_at) FROM stdin;
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

COPY public.llm_prompt (id, name, description, prompt_text, system_prompt, parameters, "order", created_at, updated_at, part_ids, prompt_json) FROM stdin;
42	Nonsense French poem	\N	You are Start every response with "TITLE: NONSENSE".\nWrite in the style of Write entirely in French.\nTask: Write a short poem	\N	\N	0	2025-05-29 14:07:08.794264	2025-05-29 14:07:08.794264	[]	[{"name": "Title Imposer", "tags": ["Role"], "type": "system", "content": "Start every response with \\"TITLE: NONSENSE\\""}, {"name": "Poem", "tags": ["Operation"], "type": "user", "content": "Write a short poem"}, {"name": "French", "tags": ["Style"], "type": "user", "content": "Write entirely in French"}]
43	french2	\N	\N	\N	\N	0	2025-05-29 15:17:15.901967	2025-05-29 15:17:15.901967	[]	[{"name": "Title Imposer", "tags": ["Role"], "type": "system", "content": "Start every response with \\"TITLE: NONSENSE\\""}, {"name": "French", "tags": ["Style"], "type": "user", "content": "Write entirely in French"}, {"name": "Poem", "tags": ["Operation"], "type": "user", "content": "Write a short poem"}]
47	CLAN UI	\N	Expert in the services and functionality of the CLAN.com web site, which specialises in authentic Scottish heritage products and information. Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.. Explain the service, functionality, and products available through https://clan.com/tartandesigner/ and its sub-pages.	\N	\N	0	2025-05-31 13:26:44.964247	2025-05-31 13:26:44.964247	[]	[{"name": "CLAN.com UI & experience", "tags": ["Role"], "type": "system", "content": "Expert in the services and functionality of the CLAN.com web site, which specialises in authentic Scottish heritage products and information."}, {"name": "idea_seed expansion", "tags": ["Operation"], "type": "user", "content": "Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language."}, {"name": "Explain functionality", "tags": ["Operation"], "type": "user", "content": "Explain the service, functionality, and products available through https://clan.com/tartandesigner/ and its sub-pages"}]
48	50 facts	\N	Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism. Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail.	\N	\N	0	2025-05-31 13:36:17.602638	2025-05-31 13:36:17.602638	[]	[{"name": "Scottish cultural expert", "tags": ["Style"], "type": "system", "content": "Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism."}, {"name": "Research 50 ideas", "tags": ["Operation"], "type": "user", "content": "Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail."}]
49	fifty facts in list	\N	Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism. Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50.	\N	\N	0	2025-05-31 14:57:19.511274	2025-05-31 14:57:19.511274	[]	[{"name": "Scottish cultural expert", "tags": ["Style"], "type": "system", "content": "Expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism."}, {"name": "Research 50 ideas", "tags": ["Operation"], "type": "user", "content": "Use web searches to explore all aspects of the topic and make a list of exactly 50 interesting facts that this article could cover. Make these diverse, from whimsical to deeply significant, and from scientific to mythical. If fictional make this clear. Keep your answers concise whilst capturing all important detail. Present these facts in list form, numbered 1-50. Do not end the task until you have reached 50."}]
50	Section Creator	\N	You are an expert editorial planner for long-form articles. Your job is to design a clear, engaging, and logically structured set of sections for a new article, based on the provided title, idea, and facts.. Write for a general audience. Ensure the structure is accessible, engaging, and covers all provided themes and facts without overlap. You will be given:\n- A provisional title for broad orientation.\n- A basic idea describing the scope and themes to be explored.\n- A set of interesting facts, each of which must be included in exactly one section.\n\nYour tasks:\n1. Devise and name a coherent, engaging section structure for the article. Each section should have a title and a short description.\n2. Allocate every theme, idea, and fact to exactly one section. No item should be left unassigned or assigned to more than one section.\n3. Output a JSON object with a "sections" array. Each section must include:\n   - "name": Section title\n   - "description": Short summary of the section\n   - "themes": List of assigned themes/ideas (if any)\n   - "facts": List of assigned facts (if any)\n4. If any theme, idea, or fact cannot be assigned, include it in an "unassigned" section at the end of the array.\n\nBe robust: handle any subject matter, and ensure the output is valid JSON.	\N	\N	0	2025-06-05 08:14:33.826018	2025-06-05 08:14:33.826018	[]	[{"name": "Section Creator", "tags": ["Role"], "type": "system", "content": "You are an expert editorial planner for long-form articles. Your job is to design a clear, engaging, and logically structured set of sections for a new article, based on the provided title, idea, and facts."}, {"name": "Section Creator voice", "tags": ["Style"], "type": "system", "content": "Write for a general audience. Ensure the structure is accessible, engaging, and covers all provided themes and facts without overlap."}, {"name": "Section Creator instructions", "tags": ["Operation"], "type": "user", "content": "You will be given:\\n- A provisional title for broad orientation.\\n- A basic idea describing the scope and themes to be explored.\\n- A set of interesting facts, each of which must be included in exactly one section.\\n\\nYour tasks:\\n1. Devise and name a coherent, engaging section structure for the article. Each section should have a title and a short description.\\n2. Allocate every theme, idea, and fact to exactly one section. No item should be left unassigned or assigned to more than one section.\\n3. Output a JSON object with a \\"sections\\" array. Each section must include:\\n   - \\"name\\": Section title\\n   - \\"description\\": Short summary of the section\\n   - \\"themes\\": List of assigned themes/ideas (if any)\\n   - \\"facts\\": List of assigned facts (if any)\\n4. If any theme, idea, or fact cannot be assigned, include it in an \\"unassigned\\" section at the end of the array.\\n\\nBe robust: handle any subject matter, and ensure the output is valid JSON."}, {"name": "Section Creator format", "tags": ["Format"], "type": "user", "content": "Title: {{provisional_title}}\\nBasic Idea: {{basic_idea}}\\nInteresting Facts:\\n{{#each interesting_facts}}\\n- {{this}}\\n{{/each}}"}]
53	Section Structure Creator	\N	Return ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }. The output must be a JSON object with a single key "sections" containing an array of section objects. Each section object must have exactly these fields: "name" (string), "description" (string). Example output: { "sections": [ { "name": "Introduction", "description": "Overview of the topic and why it matters" }, { "name": "Historical Context", "description": "Background and evolution of the topic" } ] }	You are a professional content strategist. Your task is to create a logical structure for a blog post based on its title and main idea.	\N	0	2025-06-07 15:10:56.189911	2025-06-07 15:10:56.189911	[]	[{"type": "system", "content": "You are an expert content planner and structure creator. Your task is to analyze content and create a logical, hierarchical section structure that organizes the information effectively."}, {"type": "user", "content": "Create a section structure for the following content. The structure should be hierarchical, with main sections and subsections as needed. Each section should have a clear, descriptive title that reflects its content. The structure should be logical and flow naturally from one topic to the next."}, {"type": "data", "field": "input_text"}]
51	section_creator	Creates a detailed section plan for blog articles	You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them. You MUST return your response as a JSON object with a 'sections' array. Each section in the array MUST have these exact fields: 'name' (string), 'description' (string), 'themes' (array of strings), and 'facts' (array of strings). Do not include any other text or explanation in your response, only the JSON object. Example format: {"sections": [{"name": "Section Title", "description": "Section description", "themes": ["theme1"], "facts": ["fact1"]}]} Article Outline: {article_outline} Target Audience: {target_audience}	You are an expert content strategist with years of experience in creating engaging, well-structured blog content. Your task is to break down article outlines into logical, reader-friendly sections.	{"article_outline": "string", "target_audience": "string"}	1	2025-06-05 14:14:24.243168	2025-06-05 14:14:24.243168	[]	\N
52	Section Creator as JSON	\N	You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them.\\n\\nReturn ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }.\\n\\nExample output:\\n{\\n  "sections": [\\n    {\\n      "name": "Introduction",\\n      "description": "Overview of the topic",\\n      "themes": ["history", "significance"],\\n      "facts": ["Fact 1", "Fact 2"]\\n    },\\n    {\\n      "name": "Historical Evolution",\\n      "description": "How the topic evolved over time",\\n      "themes": ["evolution", "design"],\\n      "facts": ["Fact 3"]\\n    }\\n  ]\\n}\\n\\nArticle Outline: {{title}}\\nTarget Audience: {{idea}}\\nInteresting Facts:\\n{{#each interesting_facts}}\\n- {{this}}\\n{{/each}}	\N	\N	0	2025-06-06 11:07:38.692983	2025-06-06 11:07:38.692983	[]	[{"name": "Section Creator", "tags": ["Role"], "type": "system", "content": "You are a professional content strategist. Given the following article outline and target audience, create a detailed section plan that breaks down the content into logical, engaging sections. Each section should have a clear purpose and flow naturally into the next. Consider the readers' needs and how to best present the information to them."}, {"name": "Section Creator - Output JSON", "tags": ["Format"], "type": "user", "content": "Return ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }.\\n\\nExample output:\\n{\\n  \\"sections\\": [\\n    {\\n      \\"name\\": \\"Introduction\\",\\n      \\"description\\": \\"Overview of the topic\\",\\n      \\"themes\\": [\\"history\\", \\"significance\\"],\\n      \\"facts\\": [\\"Fact 1\\", \\"Fact 2\\"]\\n    },\\n    {\\n      \\"name\\": \\"Historical Evolution\\",\\n      \\"description\\": \\"How the topic evolved over time\\",\\n      \\"themes\\": [\\"evolution\\", \\"design\\"],\\n      \\"facts\\": [\\"Fact 3\\"]\\n    }\\n  ]\\n}"}]
54	Content Allocator	\N	[user] Allocate the following ideas and facts to the most appropriate sections:\\n\\nSections:\\n{{sections|tojson}}\\n\\nIdeas to Allocate:\\n{{ideas|join("\\n")}}\\n\\nFacts to Allocate:\\n{{facts|join("\\n")}}\\n\\nReturn ONLY valid JSON. Do not include any explanation, commentary, formatting, code blocks, or HTML. Output must begin with { and end with }. The output must be a JSON object with a single key "sections" containing an array of section objects. Each section object must have exactly these fields: "name" (string), "description" (string), "ideas" (array of strings), "facts" (array of strings). Each idea and fact must be allocated to exactly one section. Example output: { "sections": [ { "name": "Introduction", "description": "Overview of the topic and why it matters", "ideas": ["Main idea 1"], "facts": ["Fact 1", "Fact 2"] }, { "name": "Historical Context", "description": "Background and evolution of the topic", "ideas": ["Main idea 2"], "facts": ["Fact 3"] } ] }	You are a professional content strategist. Your task is to allocate ideas and facts to the most appropriate sections of a blog post.	\N	0	2025-06-07 15:11:01.233643	2025-06-07 15:11:01.233643	[]	\N
55	section_structure_creator	Creates a structured outline for blog posts based on title, basic idea, and interesting facts	Create a structured outline for a blog post with the following details:\n\nTitle: {{title}}\nBasic Idea: {{idea}}\nInteresting Facts:\n{{#each facts}}\n- {{this}}\n{{/each}}\n\nPlease provide a JSON array of sections, where each section has:\n- heading: A clear, engaging section title\n- theme: The main theme or focus of this section\n- facts: Array of relevant facts to include\n- ideas: Array of key points or ideas to cover\n\nThe sections should flow logically and build upon each other to tell a complete story.	You are an expert content strategist and blog post structure specialist. Your task is to create well-organized, engaging section structures for blog posts that effectively communicate the main idea while incorporating interesting facts in a natural way.	{"idea": "string", "facts": "array", "title": "string"}	1	2025-06-08 09:36:05.838612	2025-06-08 09:36:05.838612	[]	\N
56	content_allocator	Allocates ideas and facts to sections for a blog post	Allocate the following ideas and facts to the provided sections.\\n\\nSections: {{sections}}\\nIdeas: {{ideas}}\\nFacts: {{facts}}\\n\\nReturn a JSON array of sections, each with:\\n- heading: Section title\\n- description: Section description\\n- ideas: Array of allocated ideas\\n- facts: Array of allocated facts	You are an expert content strategist. Your job is to allocate ideas and facts to the most appropriate sections in a blog post outline.	{"facts": "array", "ideas": "array", "sections": "array"}	2	2025-06-08 09:37:15.10257	2025-06-08 09:37:15.10257	[]	\N
57	Scottish Idea Expansion	Expands an idea seed into a Scottish-themed brief	[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting	\N	\N	0	2025-06-09 16:16:45.779501	2025-06-09 16:16:45.779501	[]	\N
26	Scottish Idea Expansion	Expands an idea seed into a Scottish-themed brief	[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting	\N	\N	0	2025-06-09 16:20:24.839856	2025-06-09 16:20:24.839856	[]	\N
41	SEED to BASIC	\N	[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.\\n\\n[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.\\n\\nShort Idea:\\n{{idea_seed}}\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting	\N	\N	0	2025-05-29 14:01:15.808753	2025-05-29 14:01:15.808753	[]	[{"name": "Scottish Expert", "tags": ["Role"], "type": "system", "content": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism."}, {"name": "Idea Expansion", "tags": ["Operation"], "type": "user", "content": "Your task is to expand the following idea seed into a comprehensive basic idea for a blog post about Scottish history and culture.\\n\\nIdea Seed: {idea_seed}\\n\\nPlease provide:\\n1. A detailed basic idea that expands on the seed, focusing on Scottish history and culture\\n2. Focus on making it engaging and informative\\n3. Keep the core concept but add depth and structure\\n4. Ensure all content is accurate and authentic to Scottish history and culture\\n\\nWrite your response as a clear, well-structured paragraph. Do not include any formatting, JSON, or special characters."}]
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
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post (id, title, slug, summary, created_at, updated_at, header_image_id, status, substage_id) FROM stdin;
2	hand-fasting...	hand-fasting-1	\N	2025-05-04 09:47:22.571191	2025-05-04 16:15:45.445826	\N	draft	1
4	The Evolution of the Modern Scottish Kilt	kilt-evolution	<p>The <b>Scottish kilt</b>, a garment that has become synonymous with Highland culture and Scottish identity, has undergone significant evolution since its inception. From its origins as the <b>'great kilt'</b> or <b>'belted plaid'</b> to the modern form we recognize today, its journey reflects Scotland's rich history of tradition, adaptation, and resilience. This article explores the kilt's transformation through time, examining how historical events, practical needs, and cultural shifts have shaped this iconic symbol of Scottish heritage.</p>\n	2023-10-20 00:00:00	2025-05-18 16:25:20.775043	139	draft	1
5	English tartans	english-tartans	<p><strong>English tartans</strong> have a fascinating trajectory, intertwining with the better-known <strong>Scottish tartan</strong> tradition yet developing a character of their own. Although <strong>tartan</strong> is primarily identified with Scotland, England’s engagement with tartan spans from ancient use of <strong>checkered cloth</strong> by <strong>Celtic</strong> peoples to a modern revival of regional and national patterns. This comprehensive overview examines the emergence and development of tartans in England – from historical origins and regional examples to influences of the <strong>textile industry</strong>, expressions of <strong>national identity</strong>, and contemporary <strong>design movements</strong> – all while preserving every detail of the rich historical narrative.</p>	2025-04-18 00:00:00	2025-05-18 16:25:20.785179	\N	draft	1
6	The Tradition of the Scottish Quaich	quaich-traditions	<p>The <b>quaich</b>, Scotland's cherished <b>"cup of friendship,"</b> holds a special place in Scottish tradition, symbolising hospitality, unity, and trust. Originating centuries ago, its simple yet profound design—a shallow, two-handled bowl—embodies a rich history spanning <b>clan</b> gatherings, ceremonial rituals, royal celebrations, and contemporary <b>weddings</b>. This article explores the evolution of the quaich, delving into its earliest origins, cultural significance, craftsmanship, historical anecdotes, and enduring presence in modern Scottish culture.</p>\n	2023-10-27 00:00:00	2025-05-18 16:25:20.822509	150	draft	1
1	hand-fasting...	hand-fasting	\N	2025-05-03 16:05:45.941465	2025-05-21 22:58:00.655742	\N	deleted	1
11	dod hatching...	dod-hatching		2025-05-21 21:59:50.069028	2025-05-21 22:58:29.225706	\N	deleted	1
7	cat torture...	cat-torture		2025-05-21 21:44:07.808692	2025-05-21 22:58:52.977616	\N	deleted	1
10	Test idea for workflow redirect...	test-idea-for-workflow-redirect		2025-05-21 21:58:45.229565	2025-05-21 23:03:36.776851	\N	deleted	1
12	green eggs...	green-eggs		2025-05-21 22:30:01.563795	2025-05-21 23:03:52.645833	\N	deleted	1
8	treacle bending...	treacle-bending		2025-05-21 21:49:33.812708	2025-05-21 23:03:57.595772	\N	deleted	1
9	ankle worship...	ankle-worship		2025-05-21 21:55:27.127066	2025-05-26 19:59:56.038415	\N	deleted	1
13	dog eating...	dog-eating		2025-05-26 20:06:27.151898	2025-05-26 20:12:45.27793	\N	deleted	\N
14	mangle wrangling...	mangle-wrangling		2025-05-26 20:12:36.858356	2025-05-30 17:36:15.223207	\N	deleted	\N
19	story-telling...	story-telling		2025-05-30 19:48:28.625876	2025-05-31 10:29:47.174463	\N	deleted	\N
18	mangle-wrangling...	mangle-wrangling-1		2025-05-30 17:36:54.776857	2025-05-31 10:29:51.808228	\N	deleted	\N
16	dog breakfasts...	dog-breakfasts		2025-05-28 21:11:19.909206	2025-05-31 10:29:55.758615	\N	deleted	\N
15	cream distillation...	cream-distillation		2025-05-27 15:12:33.356259	2025-05-31 10:30:04.106987	\N	deleted	\N
17	gin distillation...	gin-distillation		2025-05-29 18:52:00.672093	2025-05-31 10:30:08.023655	\N	deleted	\N
3	tartan fabrics...	tartan-fabrics		2025-05-26 19:57:47.169588	2025-05-31 10:30:12.461337	\N	deleted	\N
21	kilts for weddings...	kilts-for-weddings		2025-05-31 15:07:56.315652	2025-06-01 08:53:21.567802	\N	draft	\N
20	tartan fabrics from CLAN.com, from stock or woven ...	tartan-fabrics-from-clan-com-from-stock-or-woven		2025-05-31 10:37:23.919744	2025-06-01 10:10:35.043437	\N	deleted	\N
24	test2...	test2		2025-06-01 10:25:59.24337	2025-06-01 11:29:58.053887	\N	deleted	\N
23	test...	test		2025-06-01 10:19:43.207523	2025-06-01 11:30:01.254093	\N	deleted	\N
22	story-telling...	story-telling-1		2025-06-01 10:10:53.766198	2025-06-08 22:55:22.330677	\N	draft	\N
\.


--
-- Data for Name: post_categories; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_categories (post_id, category_id) FROM stdin;
\.


--
-- Data for Name: post_development; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_development (id, post_id, basic_idea, provisional_title, idea_scope, topics_to_cover, interesting_facts, tartans_products, section_planning, section_headings, section_order, main_title, subtitle, intro_blurb, conclusion, basic_metadata, tags, categories, image_captions, seo_optimization, self_review, peer_review, final_check, scheduling, deployment, verification, feedback_collection, content_updates, version_control, platform_selection, content_adaptation, distribution, engagement_tracking, summary, idea_seed, provisional_title_primary, concepts, facts, outline, allocated_facts, sections) FROM stdin;
2	2	hand-fasting	Tying the Knot: Unraveling Scotland's Ancient Tradition of Hand-Fasting	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Explain the difference between hand-fasting and marriage",\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Analyze the social impact of hand-fasting on women's lives in Scotland's past",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans",\n  "Describe the role of the 'hand-fastening' ritual in Scottish wedding ceremonies",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings",\n  "Discuss the romanticization of hand-fasting in Scottish literature and art",\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Examine the cultural exchange between Scottish and Norse cultures regarding hand-fasting",\n  "Investigate the connection between hand-fasting and Scotland's ancient laws",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Describe the role of the 'priest' or 'officiant' in a traditional hand-fasting ceremony",\n  "Explore the regional variations of hand-fasting practices across Scotland",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Look at how hand-fasting has been used as a symbol of Scottish national identity",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Examine the influence of hand-fasting on modern wedding traditions worldwide",\n  "Investigate the connection between hand-fasting and Scotland's ancient festivals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Discuss the role of family and community in traditional hand-fasting ceremonies",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the historical context of hand-fasting during Scotland's clan wars",\n  "Look at how hand-fasting has been used as a symbol of loyalty and commitment",\n  "Examine the modern relevance of hand-fasting in contemporary relationships",\n  "Discuss the connection between hand-fasting and Scotland's ancient mythology",\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Analyze the cultural significance of hand-fasting in Scotland's Lowland culture",\n  "Describe the historical context of hand-fasting during Scotland's Enlightenment period",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities",\n  "Discuss the symbolism behind the use of specific materials or objects in hand-fasting rituals",\n  "Look at how hand-fasting has been used as a symbol of resistance against oppressive regimes"\n]	\N	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	\N	\N	[\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting",\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape",\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting",\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements",\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions",\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology",\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies",\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices"\n]	["Unraveling the Ancient Celtic Roots of Hand-Fasting","The Evolution of Hand-Fasting in Scotland's Historical Landscape","Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting","Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements","A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions","Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies","Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology","Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
3	7	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
4	8	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
5	9	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
6	11	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
7	12	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
10	17	TITLE: NONSENSE\n\nDans les alambics de la folie,\nOù la vapeur danse et s'envole,\nLa distillation du gin se déroule,\nUn rituel ancien, une magie qui évolue.\n\nLes baies de genièvre, parfumées et fines,\nSont ajoutées au mélange, un secret divin,\nLe feu crépite, la chaleur monte en spirale,\nEt l'alcool pur se dégage, comme un esprit qui s'envole.\n\nDans les verres froids, le gin sera versé,\nUn breuvage qui réchauffe et fait oublier,\nLes soucis du jour, les nuits sans sommeil,\nTout est oublié, dans ce liquide cristal.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	gin distillation	\N	\N	\N	\N	\N	\N
9	16	Here's a brief for a long-form blog article based on the idea of "dog breakfasts":\n\n**Title:** "The Unlikely Origins of 'Dog Breakfast': How Scotland's Gastronomic History Shaped a Curious Culinary Tradition"\n\n**Scope and Angle:** This article will delve into the fascinating history behind the Scottish tradition of serving "dog breakfasts" - a hearty, if unconventional, meal typically consisting of leftover food scraps, served to working-class people, particularly in rural areas. While this practice may seem unappetizing or even bizarre to modern readers, our exploration will reveal its roots in Scotland's rich cultural heritage and the country's historical struggles with poverty, food scarcity, and social inequality.\n\n**Tone:** Our tone will be engaging, informative, and respectful, acknowledging the complexities of Scotland's past while avoiding sensationalism or judgment. We'll strive to convey a sense of empathy and understanding for those who relied on dog breakfasts as a means of sustenance, highlighting the resourcefulness and resilience that defined these communities.\n\n**Core Ideas:**\n\n* Explore the etymology of "dog breakfast" and its possible connections to Scottish Gaelic phrases and customs\n* Discuss the historical context in which dog breakfasts emerged, including Scotland's agricultural economy, poverty rates, and limited access to nutritious food\n* Examine the social dynamics surrounding dog breakfasts, including their role in rural communities, workhouses, and other institutions\n* Highlight notable examples of dog breakfasts in Scottish literature, folklore, or oral traditions\n* Reflect on the legacy of dog breakfasts in modern Scotland, considering how this tradition has influenced contemporary attitudes towards food waste, sustainability, and social welfare\n\n**Authenticity and Accuracy:** As a specialist in Scottish history and culture, we'll prioritize academic rigor and attention to detail, ensuring that all claims are supported by credible sources and historical records. By doing so, we'll create an engaging narrative that not only entertains but also educates readers about this lesser-known aspect of Scotland's cultural heritage.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	dog breakfasts	\N	\N	\N	\N	\N	\N
13	20	I apologize but as your request is not clear enough about what kind of information you want to receive or which aspect(es) from CLAN website services should be included.  Based on the brief provided and considering it doesn’t specify how much detail we need, here's a general guideline based upon data I have above:\n\n**Title - "The Tartan Truth": Unraveling The Myths And Histories Of Scotland's Iconic Fabric" – an informative post on authentic Scottish heritage products and information. This brief outlines the scope, angle (engaging with inquisitive readers), tone(enthusiastic but not overbearing about history or mythology) , core ideas that could be developed into a full article:**\n\n1- **Scope - A comprehensive exploration of tartan fabrics and their histories. Including information on the origin, evolution in time (ancient to modern), common mythologies associated with them(s). Exploring specific design details for different fabric designs from history back to present times when they were made**\n2- **Angle - An engaging approach using academic rigour but still inviting readers. Drawing insights and facts along the way, making sense of tartan stories in detail while maintaining a conversational tone that is easy on the eyes (like walking through an intricate mosaic) – to make this article more than just reading**\n3- **Tone - A friendly yet knowledgeable approach with focus solely around authenticity and significance. Encouraging curiosity about history, culture & fabric while still challenging myths or misconceptions by presenting them in a meaningful way (with examples of clans exclusive patterns) – to make sure readers are not just watching but also experiencing the journey**\n4- **Brief - Suitable for an informative article aimed at encouraging curiosity about history, culture & fabric and its impact on tartan designs. It provides depth into each aspect while keeping it engaging with a conversational tone ensuring reader interaction is both enjoyable (viewing them in new ways) and enticing**\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Here is the expanded brief:\n\n**Title:** "The Tartan Truth: Unraveling the Myths and Histories of Scotland's Iconic Fabric"\n\n**Brief:** This article will delve into the fascinating world of tartan fabrics, separating fact from fiction and exploring the rich cultural heritage behind these iconic patterns. Using data from CLAN.com, a reputable source for authentic tartan fabrics, we'll examine the history of tartan in Scotland, from its ancient origins to its modern-day uses. We'll also debunk common myths surrounding tartans, such as the notion that specific patterns are exclusive to certain clans or families. With a focus on accuracy and authenticity, this article will appeal to both history buffs and those with a passing interest in Scottish culture. By exploring the stories behind different tartan designs, we'll reveal the intricate connections between Scotland's past, its people, and their textiles.\n\n**Scope:** This long-form blog post will cover:\n\n* A brief history of tartan in Scotland, including its ancient Celtic roots and evolution over time\n* An examination of common myths and misconceptions surrounding tartans\n* In-depth looks at specific tartan designs, their origins, and associated stories\n* The significance of tartan in Scottish culture, both historically and today\n\n**Angle:** Our approach will be informative yet engaging, blending academic rigor with a conversational tone that invites readers to explore the world of tartans. We'll draw on credible sources, including historical records and expert insights from textile historians.\n\n**Tone:** Friendly, knowledgeable, and enthusiastic – we aim to inspire curiosity about Scottish history and culture while dispelling myths and misconceptions. Our goal is to create a sense of wonder and appreciation for the intricate stories woven into every tartan fabric.\n\nThis brief should provide a solid foundation for crafting an engaging and informative article that explores the captivating world of tartans, revealing their significance in Scotland's rich cultural heritage.	\N	\N	\N	\N	\N	\N
11	18	**Brief: "The Forgotten Art of Mangle-Wrangling: Uncovering Scotland's Laundry History"**\n\nIn this long-form blog article, we'll delve into the fascinating history of laundry in Scotland, focusing on the often-overlooked practice of "mangle-wrangling." A mangle, for those unfamiliar, was a contraption used to wring out water from washed clothes – a laborious task that required great skill and strength. By exploring the evolution of mangling and its significance in Scottish households, particularly during the 18th and 19th centuries, we'll shed light on the daily lives of ordinary people and the impact of technological advancements on their routines.\n\n**Scope:** The article will cover the history of laundry practices in Scotland from the medieval period to the mid-20th century, with a focus on the mangle-wrangling era. We'll examine the social and economic contexts that influenced the development of mangling, as well as its eventual decline with the advent of mechanized washing machines.\n\n**Angle:** Rather than presenting a dry, academic account, we'll take a more narrative approach, weaving together stories of Scottish households, anecdotes from historical figures, and insights into the daily lives of those who relied on mangle-wrangling. By doing so, we'll humanize this often-overlooked aspect of history and make it relatable to modern readers.\n\n**Tone:** The tone will be engaging, informative, and occasionally humorous, with a touch of nostalgia for a bygone era. We'll avoid jargon and technical terms, opting for clear, concise language that makes the subject accessible to a broad audience.\n\n**Core ideas:**\n\n* Explore the evolution of laundry practices in Scotland from medieval times to the mid-20th century\n* Discuss the significance of mangle-wrangling as a domestic chore and its impact on household dynamics\n* Analyze the social and economic factors that influenced the development of mangling, including urbanization, industrialization, and technological advancements\n* Share stories of individuals who relied on mangle-wrangling, highlighting their experiences and perspectives\n* Reflect on the cultural significance of laundry practices in Scottish history and how they continue to influence our understanding of domestic life today\n\nBy exploring this forgotten aspect of Scotland's past, we'll not only uncover a fascinating chapter in the country's social history but also provide readers with a fresh perspective on the everyday lives of their ancestors.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	mangle-wrangling	\N	\N	\N	\N	\N	\N
8	15	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:\n\n**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"\n\n**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.\n\n**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.\n\n**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.\n\n**Core ideas:**\n\n* Introduce the basics of cream distillation and its role in Scottish whisky production\n* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations\n* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie\n* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers\n* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production\n\n**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	\N	\N	\N	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:\n\n**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"\n\n**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.\n\n**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.\n\n**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.\n\n**Core ideas:**\n\n* Introduce the basics of cream distillation and its role in Scottish whisky production\n* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations\n* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie\n* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers\n* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production\n\n**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	cream distillation	\N	\N	\N	\N	\N	\N
12	19	Here's a expanded brief for a long-form blog article based on the idea of "story-telling" in Scottish history and culture:\n\n**Title:** "Weaving the Tartan Tapestry: The Power of Storytelling in Scottish History and Culture"\n\n**Scope:** This article will delve into the rich tradition of storytelling in Scotland, exploring its significance in shaping the country's history, culture, and identity. From ancient Celtic myths to modern-day folk tales, we'll examine how stories have been used to convey values, preserve traditions, and make sense of the world.\n\n**Angle:** Rather than a dry, academic survey, this article will take a narrative approach, using anecdotes, examples, and vivid descriptions to bring Scotland's storytelling heritage to life. We'll draw on historical records, literary works, and oral traditions to illustrate the ways in which stories have been used to inspire, educate, and entertain across generations.\n\n**Tone:** Engaging, conversational, and informative, with a touch of warmth and humor. Our aim is to make complex historical and cultural concepts accessible to a broad audience, while still maintaining academic rigor and authenticity.\n\n**Core ideas:**\n\n* The role of storytelling in preserving Scotland's cultural heritage, including the transmission of myths, legends, and folk tales.\n* The use of stories as a means of social commentary, critique, and satire, with examples from Scottish literature and folklore.\n* The impact of historical events, such as the Jacobite risings and the Highland Clearances, on Scotland's storytelling traditions.\n* The ways in which storytelling has been used to promote national identity, community cohesion, and cultural pride.\n* The ongoing relevance of traditional storytelling in modern Scotland, including its influence on contemporary literature, art, and popular culture.\n\n**Key themes:**\n\n* The importance of oral tradition in Scottish culture\n* The relationship between storytelling and national identity\n* The role of stories in shaping historical memory and cultural heritage\n* The intersection of folklore, literature, and popular culture\n\nThis article will be a engaging, story-driven exploration of Scotland's rich cultural heritage, highlighting the power of storytelling to inspire, educate, and connect us with our past.	TITLE: NONSENSE\n\nVoici un court poème pour célébrer l'art du récit en Écosse :\n\nDans les Highlands brumeux, où les légendes naissent,\nLes conteurs écossais ont toujours leurs mots prêts.\nIls tissent des histoires de héros et de dragons,\nDe mythes celtes et de mystères qui nous font rêver.\n\nFionn mac Cumhaill, le grand guerrier, prend vie,\nEt les paysages mystiques de Stevenson s'étendent.\nLes satiristes écossais utilisent l'ironie pour critiquer,\nEt les histoires se transforment au fil du temps, reflétant notre société.\n\nL'Ecosse, terre de légendes et d'histoires vraies,\nOù la tradition orale est encore vivante aujourd'hui.\nLes conteurs, ces seanachaidh, préservent l'histoire,\nEt nous transportent dans un monde où mythe et réalité se mélangent.\n\nC'est ainsi que les Écossais ont toujours raconté leur histoire,\nUn patrimoine littéraire riche et diversifié qui nous émerveille.\nAlors laissons-nous emporter par ces récits enchanteurs,\nEt découvrons l'Écosse, terre de légendes et d'histoires vraies.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	story-telling	\N	\N	\N	\N	\N	\N
14	21	Here's a brief for a long-form blog article on kilts for weddings:\n\n**Title:** "The Kilted Wedding: Unwrapping the History and Tradition Behind Scotland's Most Iconic Attire"\n\n**Scope:** This article will delve into the fascinating history of kilts at Scottish weddings, exploring their cultural significance, traditional designs, and modern interpretations. From the origins of tartan to the symbolism of different kilt styles, we'll examine the intricacies of this beloved aspect of Scottish heritage.\n\n**Angle:** Rather than focusing solely on fashion or style tips, our article will take a more nuanced approach, situating kilts within their rich cultural context. We'll discuss how kilts have been an integral part of Scottish wedding traditions for centuries, and how they continue to play a meaningful role in modern ceremonies. By sharing stories, anecdotes, and historical examples, we'll bring the reader on a journey through time, highlighting the ways in which kilts have evolved to become an enduring symbol of Scottish identity.\n\n**Tone:** Our tone will be informative, yet engaging and conversational. We'll balance academic rigor with approachable language, making the subject matter accessible to readers without prior knowledge of Scottish history or culture. A touch of humor and personality will also be injected throughout the article, ensuring that it feels like a warm and inviting exploration of this captivating topic.\n\n**Core ideas:**\n\n* The origins of tartan and its significance in Scottish culture\n* Traditional kilt designs and their regional associations (e.g., Black Watch, Gordon)\n* Historical examples of kilts at Scottish weddings, including notable figures and events\n* Modern interpretations of kilts in wedding attire, including trends and innovations\n* The symbolism and meaning behind different kilt styles and accessories (e.g., sgian dubh, sporran)\n* Tips for incorporating kilts into a wedding ceremony or celebration, while respecting cultural traditions\n\nBy exploring the complex history and cultural significance of kilts at Scottish weddings, this article will offer readers a deeper understanding and appreciation of this beloved aspect of Scottish heritage. Whether you're a Scot looking to connect with your roots or simply someone interested in learning more about this iconic attire, our article promises to be an engaging and enlightening read.	\N	\N	\N	Here are 50 interesting facts about kilts at Scottish weddings:\n\n1. **Tartan origins**: The word "tartan" comes from the French word "tartane," meaning a type of woolen cloth.\n2. **Ancient roots**: The earliest known evidence of tartan patterns dates back to the 3rd century AD, in ancient Celtic art.\n3. **Clans and kinship**: In Scotland, tartan was used to identify specific clans or families, with each having its own unique pattern.\n4. **Wedding tradition**: Kilts have been a part of Scottish wedding attire for centuries, symbolizing family heritage and cultural identity.\n5. **Black Watch**: The Black Watch tartan is one of the most recognizable patterns, originally worn by the 42nd Royal Highland Regiment.\n6. **Regional associations**: Different regions in Scotland have their own unique tartans, such as the Gordon tartan from Aberdeenshire.\n7. **Sporran significance**: A sporran (a pouch worn at the waist) is a traditional part of kilt attire, used to carry personal items and symbolizing prosperity.\n8. **Kilt-making skills**: Traditional kilt-making requires great skill and attention to detail, with each kilt taking around 30-40 hours to complete.\n9. **Woolen heritage**: Kilts are typically made from wool, a nod to Scotland's rich sheep-farming history.\n10. **Tartan registers**: In the 18th century, tartans were formally registered and standardized to prevent imitation and ensure authenticity.\n11. **Kilted heroes**: Famous Scots like Robert Burns and Sir Walter Scott often wore kilts as a symbol of national pride.\n12. **Wedding attire**: Traditionally, the groom's kilt is matched with a sash or plaid (a long piece of fabric) in the same tartan.\n13. **Scottish regiments**: Many Scottish military regiments have their own unique kilts and tartans, such as the Royal Scots Dragoon Guards.\n14. **Cultural revival**: The 19th-century Highland Revival saw a resurgence in interest in traditional Scottish culture, including kilts and tartans.\n15. **Fashion influence**: Kilts have influenced fashion worldwide, with designers incorporating tartan patterns into their collections.\n16. **Wedding party attire**: In traditional Scottish weddings, the entire wedding party (including bridesmaids) may wear matching tartans or kilts.\n17. **Kilt accessories**: Sgian dubh (a small knife), dirks (long knives), and sporrans are common kilt accessories with cultural significance.\n18. **Ancient Celtic art**: Early Celtic art features intricate patterns similar to modern tartan designs.\n19. **Tartan textiles**: Kilts are often made from woven woolen fabric, which can be heavy and warm.\n20. **Kilted athletes**: Scottish athletes have worn kilts as part of their national team uniforms in various sports, including football and rugby.\n21. **Bagpipes and kilts**: The iconic combination of bagpipes and kilts is a staple of Scottish culture and wedding celebrations.\n22. **Wedding ceremony significance**: In traditional Scottish weddings, the kilt is often worn during the ceremony to symbolize family heritage.\n23. **Hand-fasting**: In ancient Celtic tradition, couples were "hand-fast" (married) while wearing matching tartans or kilts.\n24. **Tartan etiquette**: Specific rules govern the wearing of tartans and kilts, including which side to wear a sash or plaid.\n25. **Royal connections**: The British royal family has long been associated with Scottish culture, often wearing kilts on formal occasions.\n26. **Wedding attire evolution**: Modern kilt designs for weddings may incorporate new colors or patterns while maintaining traditional elements.\n27. **Kilt-making techniques**: Traditional kilt-making involves intricate pleating and folding to create the distinctive tartan pattern.\n28. **Historical kilts**: Kilts have been worn in Scotland since at least the 16th century, with early examples featuring more subdued colors.\n29. **Tartan symbolism**: Specific tartans are associated with different values or attributes, such as bravery (Black Watch) or loyalty (Gordon).\n30. **Wedding party kilts**: In some traditional weddings, the entire wedding party wears matching kilts in the same tartan.\n31. **Scottish heritage**: Kilts and tartans serve as a connection to Scotland's rich cultural heritage and history.\n32. **Modern twists**: Contemporary kilt designs may incorporate bold colors or modern patterns while maintaining traditional elements.\n33. **Cultural exchange**: Tartans have been adopted by cultures worldwide, including African and Asian communities.\n34. **Wedding fashion influence**: Kilts have influenced wedding attire globally, with many designers incorporating tartan patterns into their collections.\n35. **Famous kilted figures**: Sir Sean Connery and Billy Connolly are just two famous Scots who often wear kilts on formal occasions.\n36. **Kilted folklore**: In Scottish mythology, kilts were said to have magical properties, offering protection and strength to the wearer.\n37. **Wedding attire for all**: Modern kilt designs cater to a range of styles and preferences, including women's kilts and bespoke designs.\n38. **Tartan in art**: Tartans have been featured in various art forms, from textiles to music and literature.\n39. **Cultural significance**: Kilts serve as an important cultural symbol, representing Scottish heritage and national identity.\n40. **Kilt accessories**: Sashes, sporrans, and sgian dubh are all essential kilt accessories with historical and cultural significance.\n41. **Wedding attire evolution**: Modern kilt designs often blend traditional elements with modern styles and materials.\n42. **Royal tartans**: The British royal family has its own unique tartans, which are reserved for specific occasions.\n43. **Tartan registers**: In the 19th century, tartans were formally registered to standardize patterns and prevent imitation.\n44. **Kilt-making apprenticeships**: Traditional kilt-making skills are passed down through generations via formal apprenticeships.\n45. **Wedding party attire**: In some traditional Scottish weddings, the bride's dress may incorporate matching tartan elements or a sash.\n46. **Famous kilts in literature**: Kilts have been featured prominently in literary works like Sir Walter Scott's novels.\n47. **Tartan textiles**: Modern textile technology has made it possible to create intricate and accurate tartan patterns on various fabrics.\n48. **Kilted music festivals**: Scottish music festivals often feature kilted performers, showcasing traditional culture.\n49. **Cultural traditions**: Kilts are an integral part of Scottish cultural heritage, reflecting the country's rich history and identity.\n50. **Global recognition**: The image of a Scotsman in a kilt is instantly recognizable worldwide, symbolizing Scottish culture and national pride.\n\nThese 50 facts cover a range of topics, from the origins of tartan to modern interpretations of kilts at weddings, while highlighting the cultural significance and symbolism behind this iconic attire.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	kilts for weddings	\N	\N	\N	\N	\N	\N
16	23	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	test	\N	\N	\N	\N	\N	\N
17	24	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	test2	\N	\N	\N	\N	\N	\N
1	1	Idea seed: The impact of Jacobite Risings on Scotland's language and culture.\n\nThe Jacobite Risings of 1715 and 1745 were pivotal moments in Scottish history, but their cultural significance extends far beyond the battles fought on Culloden Moor or the intrigues within the Palace of Holyrood. This article will delve into how these rebellions influenced the evolution of Scotland's language and culture, often in unexpected ways. One angle to explore is how the Jacobite leaders' French connections shaped Scottish art and architecture, particularly in the realm of decorative arts and interior design. For example, the lavish furnishings and ornate details found in some Scottish castles reflect the Gallic tastes imposed by their former rulers. Another theme could be the linguistic impact of Jacobitism on modern-day Scotland, where Gaelic and Scots remain important cultural touchstones. The influence of Gaelic poetry and storytelling on Scottish literature is also worth examining, particularly in relation to famous Jacobite-era writers such as James Macpherson and Alexander Pope. By investigating these interconnected threads, this article aims to uncover a more nuanced understanding of how the Jacobite Risings have left an enduring legacy in Scotland's cultural landscape.	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  {\n    "title": "The Ancient Kingdoms of Scotland",\n    "description": "A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.",\n    "contents": [\n      "Pictish culture and society",\n      "The rise of the Dál Riata dynasty",\n      "Viking invasions and their impact on Scotland"\n    ]\n  },\n  {\n    "title": "Medieval Scotland: Kingdoms and Feudalism",\n    "description": "An exploration of Scotland's medieval kingdoms, nobility, and feudal system.",\n    "contents": [\n      "The Kingdom of Alba and the development of Scottish identity",\n      "Feudal relationships between Scottish lords and the monarch",\n      "The role of the Church in medieval Scottish society"\n    ]\n  },\n  {\n    "title": "The Wars of Scottish Independence",\n    "description": "A detailed account of Scotland's struggles for independence from England, including key battles and figures.",\n    "contents": [\n      "The First War of Scottish Independence (1296-1357)",\n      "Robert the Bruce: his life, campaigns, and legacy",\n      "Key battles: Stirling Bridge, Falkirk, Bannockburn"\n    ]\n  },\n  {\n    "title": "Tartanry and Highland Culture",\n    "description": "An examination of Scotland's iconic tartans, clans, and traditional Highland culture.",\n    "contents": [\n      "Origins and meaning of Scottish tartans",\n      "The significance of clan structure and kinship in Highland society",\n      "Traditional Highland music, dance, and art"\n    ]\n  },\n  {\n    "title": "Scotland's Contribution to the British Empire",\n    "description": "An exploration of Scotland's role in shaping the British Empire, including key figures and events.",\n    "contents": [\n      "The 'Darien Scheme' and its impact on Scottish politics",\n      "Scottish explorers: James Bruce and Mungo Park",\n      "Scotland's military contributions to the Napoleonic Wars"\n    ]\n  },\n  {\n    "title": "Modern Scotland: Industrialization, Nationalism, and Devolution",\n    "description": "A discussion of Scotland's modern history, including key economic, cultural, and political developments.",\n    "contents": [\n      "Industrialization and urbanization in Scotland",\n      "The rise of Scottish nationalism and the SNP",\n      "Devolution and the Scottish Parliament"\n    ]\n  },\n  {\n    "title": "Scottish Culture and Identity Today",\n    "description": "An examination of contemporary Scottish culture, including literature, music, art, and festivals.",\n    "contents": [\n      "Modern Scottish literature: authors and themes",\n      "The role of traditional music in modern Scotland",\n      "Celebrations: Hogmanay, Burns Night, Celtic Connections"\n    ]\n  }\n]	\N	Here is the detailed content for each section of the outline, maintaining a consistent style and tone throughout:\n\n```json\n{\n  "The Ancient Kingdoms of Scotland": {\n    "description": "A detailed examination of the Picts, Scots, and Vikings who shaped Scotland's early history.",\n    "contents": [\n      {\n        "title": "Pictish culture and society",\n        "text": "The Picts were a group of people who lived in Scotland during the Late Iron Age and Early Medieval periods. Their name is derived from the Latin word 'picti,' meaning 'painted people.' This refers to their practice of body painting, which was a common custom among many ancient cultures. The Picts left behind a rich legacy of art, including intricate stone carvings and metalwork. Despite their impressive artistic achievements, the Picts left no written records, making it difficult for historians to reconstruct their society with certainty. Nevertheless, archaeological evidence suggests that they were organized into smaller groups or 'nations,' each with its own distinct culture and traditions."\n      },\n      {\n        "title": "The rise of the Dál Riata dynasty",\n        "text": "As the Roman Empire declined, Scotland was invaded by various groups from Ireland. One such group, the Dál Riata, eventually established a powerful dynasty that would shape Scotland's early history. The Dál Riata were skilled warriors and traders who built a strong kingdom in western Scotland. They also developed a system of writing, using an adaptation of the Ogham alphabet to record their language and history. Under the Dál Riata, Scotland began to take on a more distinct identity, with its own culture, laws, and institutions."\n      },\n      {\n        "title": "Viking invasions and their impact on Scotland",\n        "text": "In the late 8th century, Viking raiders from Scandinavia invaded Scotland, bringing destruction and chaos in their wake. The Vikings were skilled warriors who quickly established themselves as a dominant force in Scottish politics. They often fought alongside native Scots against other rival groups, but they also brought their own culture, language, and customs to the region. Despite the disruption caused by the Viking invasions, Scotland's ancient kingdoms would eventually emerge stronger than ever, shaped by the complex interactions between the Picts, Scots, and Vikings."\n    ]\n  },\n  "Medieval Scotland: Kingdoms and Feudalism": {\n    "description": "An exploration of Scotland's medieval kingdoms, nobility, and feudal system.",\n    "contents": [\n      {\n        "title": "The Kingdom of Alba and the development of Scottish identity",\n        "text": "As the Dál Riata dynasty declined, a new kingdom emerged in eastern Scotland: the Kingdom of Alba. The name 'Alba' means 'dawn' or 'white,' reflecting the kingdom's association with light and hope. Under the Kingdom of Alba, Scotland began to take on a more unified identity, with its own monarch, laws, and institutions. This period saw the rise of Scottish nationalism, as Scots sought to assert their independence from neighboring kingdoms."\n      },\n      {\n        "title": "Feudal relationships between Scottish lords and the monarch",\n        "text": "In medieval Scotland, society was organized around a complex system of feudal relationships. Lords owed allegiance to the monarch, who in turn protected them and their lands. In exchange for protection, lords were expected to provide military service, tribute, or other forms of support. This system allowed the Kingdom of Alba to expand its borders through strategic alliances and military campaigns. However, it also created tensions between lords and the monarch, as they jockeyed for power and influence."\n      },\n      {\n        "title": "The role of the Church in medieval Scottish society",\n        "text": "The Christian Church played a central role in medieval Scottish society, providing education, healthcare, and spiritual guidance to the population. The Church also served as a unifying force, binding together disparate groups within Scotland's complex feudal system. Monasteries and abbeys became centers of learning and culture, where monks and scholars preserved ancient knowledge and developed new artistic and literary traditions."\n    ]\n  },\n  "The Wars of Scottish Independence": {\n    "description": "A detailed account of Scotland's struggles for independence from England, including key battles and figures.",\n    "contents": [\n      {\n        "title": "The First War of Scottish Independence (1296-1357)",\n        "text": "In the late 13th century, Edward I of England invaded Scotland, sparking a decades-long conflict that would shape Scotland's history. The war saw numerous battles, including Stirling Bridge and Falkirk, where Scottish forces emerged victorious but ultimately succumbed to English pressure. This period also saw the emergence of key figures like William Wallace and Robert the Bruce, who would become iconic heroes in Scotland's struggle for independence."\n      },\n      {\n        "title": "Robert the Bruce: his life, campaigns, and legacy",\n        "text": "Robert the Bruce was a Scottish nobleman who rose to prominence during the Wars of Scottish Independence. He initially supported English rule but later turned against them, leading the charge at Bannockburn in 1314. This decisive victory marked a turning point in Scotland's struggle for independence, as the country began to assert its sovereignty over England. Bruce's legacy endures to this day, symbolizing Scotland's enduring spirit of resistance and self-determination."\n      },\n      {\n        "title": "Key battles: Stirling Bridge, Falkirk, Bannockburn",\n        "text": "The Wars of Scottish Independence saw numerous pivotal battles, each with its own unique significance. Stirling Bridge was a crucial early victory for the Scots, showcasing their military prowess and strategic thinking. Falkirk marked a turning point in English fortunes, as they regained momentum after initial setbacks. Bannockburn, however, remains Scotland's most iconic battle, where Robert the Bruce led his forces to an historic triumph over the English."\n    ]\n  },\n  "Tartanry and Highland Culture": {\n    "description": "An examination of Scotland's iconic tartans, clans, and traditional Highland culture.",\n    "contents": [\n      {\n        "title": "Origins and meaning of Scottish tartans",\n        "text": "Scottish tartans have a rich history, dating back to the Middle Ages. Originally, these intricate patterns served as markers of clan identity and status. Each tartan was associated with specific regions or families, reflecting their unique cultural heritage. Over time, the significance of tartans has evolved, serving as symbols of national pride and community spirit."\n      },\n      {\n        "title": "The significance of clan structure and kinship in Highland society",\n        "text": "In traditional Highland culture, clans played a central role in defining identity and social hierarchy. Clans were organized around shared ancestry, with each family tracing their lineage back to a common ancestor. This system fostered strong bonds between family members and reinforced the importance of loyalty, honor, and hospitality."\n      },\n      {\n        "title": "Traditional Highland music, dance, and art",\n        "text": "Highland culture is renowned for its rich musical heritage, with traditional instruments like the bagpipes and fiddle dominating Scotland's folk scene. Traditional dances like the ceilidh and Highland fling are still celebrated today, reflecting the country's deep connection to its cultural roots. Scottish art also boasts a stunning array of textiles, metalwork, and other crafts that showcase the region's artistic prowess."\n    ]\n  },\n  "Scotland's Contribution to the British Empire": {\n    "description": "An exploration of Scotland's role in shaping the British Empire, including key figures and events.",\n    "contents": [\n      {\n        "title": "The 'Darien Scheme' and its impact on Scottish politics",\n        "text": "In the early 18th century, Scotland proposed a bold venture to establish a colony in Panama, known as the Darien Scheme. Although the plan ultimately failed, it reflected Scotland's growing ambitions within the British Empire. The failure of the Darien Scheme led to a period of economic hardship and social unrest in Scotland, prompting calls for greater autonomy or even independence from England."\n      },\n      {\n        "title": "Scottish explorers: James Bruce and Mungo Park",\n        "text": "Scotland has produced many notable explorers who contributed significantly to the British Empire's expansion. James Bruce was a renowned geographer and explorer who traveled extensively in Africa, discovering several major rivers. Mungo Park, another prominent Scottish explorer, ventured into West Africa, mapping new territories and encountering diverse cultures."\n      },\n      {\n        "title": "Scotland's military contributions to the Napoleonic Wars",\n        "text": "During the Napoleonic Wars, Scotland played a significant role in British military campaigns. Many Scots served as soldiers or officers in key battles, contributing to crucial victories like Waterloo. This period also saw the rise of Scottish nationalism, as Scots sought greater recognition and influence within the British Empire."\n    ]\n  },\n  "Modern Scotland: Industrialization, Nationalism, and Devolution": {\n    "description": "A discussion of Scotland's modern history, including key economic, cultural, and political developments.",\n    "contents": [\n      {\n        "title": "Industrialization and urbanization in Scotland",\n        "text": "In the 19th century, Scotland underwent rapid industrialization, driven by coal mining, steel production, and textile manufacturing. This led to significant urban growth, as people flocked to cities like Glasgow and Edinburgh for work and opportunities. However, this period also saw the rise of social inequalities and poverty in Scotland."\n      },\n      {\n        "title": "The rise of Scottish nationalism and the SNP",\n        "text": "In the 20th century, Scottish nationalism experienced a resurgence, driven by calls for greater autonomy or independence from England. The Scottish National Party (SNP) emerged as a major force, advocating for devolution and self-governance. This movement has continued to grow in influence, shaping Scotland's politics and identity."\n      },\n      {\n        "title": "Devolution and the Scottish Parliament",\n        "text": "In 1999, Scotland gained its own parliament through the Devolution Act, marking a significant shift in the country's governance. The Scottish Parliament is responsible for making laws on various domestic issues, including healthcare, education, and justice. This has led to increased autonomy for Scotland within the UK, allowing the country to develop its unique policies and priorities."\n    ]\n  },\n  "Scottish Culture and Identity Today": {\n    "description": "An examination of contemporary Scottish culture, including literature, music, art, and festivals.",\n    "contents": [\n      {\n        "title": "Modern Scottish literature: authors and themes",\n        "text": "Scotland has produced a thriving literary scene in recent decades, with writers like Irvine Welsh, James Kelman, and Janice Galloway achieving international recognition. Themes of identity, social justice, and national pride dominate contemporary Scottish literature, reflecting the country's evolving cultural landscape."\n      },\n      {\n        "title": "The role of traditional music in modern Scotland",\n        "text": "Traditional Scottish music continues to play a vital role in shaping the country's culture and identity. From bagpipe bands to ceilidh sessions, music remains an integral part of Scottish heritage, with many festivals celebrating its rich tradition."\n      },\n      {\n        "title": "Celebrations: Hogmanay, Burns Night, Celtic Connections",\n        "text": "Scotland's calendar is filled with vibrant cultural celebrations, each reflecting the country's unique history and traditions. Hogmanay marks the start of a new year, while Burns Night honors Scotland's beloved poet Robert Burns. Celtic Connections is a major festival showcasing traditional music from across the world."\n    ]\n  }\n}\n```
15	22	In Scotland, the art of storytelling has been woven into the very fabric of its culture for centuries. This tradition of oral narrative is not merely a quaint relic of the past but an integral component of Scottish identity. As we delve into the realm of Scottish story-telling, we'll explore how this ancient practice evolved from the medieval bards to the modern-day ceilidh hosts, and examine the significance of tales like Tam o' Shanter and The Three Sisters in shaping Scotland's unique cultural heritage. This blog article will delve into the historical context of Scotland's oral tradition, tracing its roots to the Gaelic-speaking communities of the Highlands and Islands, where poetry, music, and storytelling were intertwined as a means of preserving history, myth, and social commentary. We'll also examine how the Industrial Revolution transformed the way stories were told and consumed in Scotland, with the rise of urban folk festivals and literary movements such as the Scottish Renaissance of the early 20th century. By exploring the diverse strands that comprise Scotland's story-telling tapestry, we can gain a deeper understanding not only of its rich cultural heritage but also of the enduring power of oral narrative to unite, educate, and inspire communities.	["Weaving Words, Winding Paths: The Forgotten History of Scottish Folklore and its Modern Revival", "Telling Tales of Tartan: Unpacking the Enduring Power of Scottish Oral Tradition", "The Story Keepers of Scotland: Uncovering the Hidden Histories that Bind the Nation", "The Bardic Voice of Scotland: Exploring the Evolution of Storytelling in the Highlands and Lowlands", "Scotland's Sonic Sagas: How Traditional Storytelling Shaped the Nation's Cultural Identity"]	\N	\N	[\n"Scotland's oral tradition dates back to pre-Christian times, influenced by ancient Celtic cultures."\n"The earliest known Scottish story-teller is thought to be the 7th-century saint, Columba, who brought Christianity and literature to Scotland from Ireland."\n"Medieval Scottish bards were trained in poetry, music, and storytelling from a young age, often becoming associated with noble families."\n"Bards used their art to praise kings, commemorate battles, and share tales of mythological heroes like Cú Chulainn and Fionn mac Cumhaill."\n"The most famous Scottish bard of the 8th century was Dallan Forgaill, who wrote poetry in both Gaelic and Latin."\n"Scottish folklore is rich in supernatural creatures such as the Kelpie (a water spirit), the Loch Ness Monster, and the Selkie (a seal-human shapeshifter)."\n"The medieval Scottish tale of 'Tam o' Shanter' was first published in 1790 by Robert Burns, a celebrated poet and songwriter."\n"Robert Burns himself claimed to have learned many of his stories from an elderly woman who lived near Ayr, Scotland."\n"Scottish Gaelic, the language spoken by Scotland's Highland and Island communities, is still spoken today by around 60,000 people worldwide."\n"The Scottish Renaissance of the early 20th century saw a revival in interest in traditional folk tales and poetry."\n"The movement was led by writers such as Hugh MacDiarmid and Sorley MacLean, who sought to promote Gaelic culture and language."\n"Tam o' Shanter's tale is often seen as a warning about the dangers of excessive drinking, rather than just a humorous anecdote."\n"The Three Sisters, a famous Scottish folktale, tells the story of three sisters who outwit their wicked stepmother by using their cunning and intelligence."\n"In the 19th century, Scottish folk tales were collected and published by scholars such as John Francis Campbell and Andrew Lang."\n"Campbell's 'The Gaelic Otherworld' is considered a seminal work on Scotland's oral tradition, covering mythology, folklore, and fairy stories."\n"The Three Sisters are often associated with the myth of the triple goddess, representing maidenhood, motherhood, and cronehood."\n"Scotland's Industrial Revolution had a profound impact on its folk culture, leading to urbanization and changes in storytelling styles."\n"In the 19th century, Scottish folk tales were influenced by European Romanticism and the rise of interest in fairy stories and folklore."\n"The Scottish Gaelic term 'sealladh' refers to a glimpse or vision of supernatural beings or events from another realm."\n"Scottish storytelling often employs magical realism, blurring the lines between fact and fantasy."\n"Folklorist Katharine Briggs wrote extensively on Scotland's oral tradition, including its connections with European folklore and mythology."\n"The Scottish bardic tradition emphasized the importance of memory, with bards trained to remember vast amounts of poetry and music."\n"Many Scottish folk tales feature shape-shifting animals or supernatural beings as protagonists or antagonists."\n"Scottish Gaelic folklore is replete with examples of 'thin places,' where the veil between worlds is said to be at its thinnest."\n"The term 'Cailleach' refers to a type of Scottish goddess associated with winter, fertility, and the land."\n"Scotland's ancient Celtic art often featured intricate knotwork patterns, which were believed to have spiritual significance."\n"Folklorist James F. Collie collected many Scottish tales during the early 20th century, including those from Gaelic-speaking communities."\n"Some of Scotland's most famous folktales are based on real historical events or figures, such as the tale of Macbeth and his wife, Lady Gruoch."\n"The ancient Celtic festival of Samhain marked the beginning of winter and was associated with divination and ancestor worship."\n"Scottish folklore often features 'faeries' or supernatural beings with magical powers, which are said to inhabit specific locations or landscapes."\n"Some Scottish stories feature a type of benevolent spirit known as the 'Càirnich,' who is believed to protect children from harm."\n"The term 'ceilidh' refers to a traditional Scottish social gathering, often featuring music, dancing, and storytelling."\n"Scotland's oral tradition was heavily influenced by Christianity, with many folktales incorporating Christian themes or motifs."\n"Some of Scotland's most famous poets, such as Robert Burns and Hugh MacDiarmid, drew on folk tales for inspiration in their work."\n"The Scottish Gaelic term 'bean nighe' refers to a type of supernatural woman associated with weaving, prophecy, and fate."\n"Many Scottish folktales feature the theme of 'thin places,' where the boundary between worlds is said to be at its most permeable."\n"Folklorist Andrew Lang published several collections of Scottish folk tales in the late 19th century, including 'The Blue Fairy Book.'"\n"The Three Sisters' tale has been retold and adapted numerous times, including in films, novels, and stage plays."\n"Scotland's industrialization had a significant impact on its storytelling traditions, with many folktales reflecting the struggles of urban working-class life."\n"Some Scottish stories feature the Loch Ness Monster as a benevolent guardian of the loch and its inhabitants."\n"The ancient Celtic art of Scotland often featured depictions of sacred animals, such as the Cernunnos (Horned God) or the Selkie."\n"Scotland's oral tradition has been influenced by other cultures, including those from Ireland, Wales, and England."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), which is said to possess supernatural powers."\n"The term 'seanchaí' refers to an Irish or Scottish storyteller who specializes in oral storytelling and preserves folklore."\n"Folklorist John Francis Campbell's 'The Gaelic Otherworld' remains a seminal work on Scotland's oral tradition, covering mythology, folklore, and fairy stories."\n"Scotland's Industrial Revolution led to the development of new forms of storytelling, such as urban folk festivals and literary movements like the Scottish Renaissance."\n"The Three Sisters' tale has been interpreted in various ways over time, including as a commentary on the struggles of women in patriarchal societies."\n"Some Scottish stories feature the concept of 'sìth,' or faerie, realms which exist alongside human society but are not visible to all."\n"Folklorist Katharine Briggs wrote extensively on Scotland's oral tradition, exploring its connections with European folklore and mythology."\n"The term ' bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' which is associated with winter, fertility, and the land."\n"Scotland's oral tradition has been shaped by its unique cultural heritage, including its Celtic roots, Christianity, and industrialization."\n"The Three Sisters' tale has been retold in various forms, including short stories, novels, and stage plays, often adapting to changing social norms and values."\n"Some Scottish folktales feature the theme of 'thin places,' where the boundary between worlds is said to be at its most permeable, and supernatural beings are more likely to appear."\n"The term 'ceilidh' (traditional Scottish social gathering) refers to a lively and interactive form of storytelling that emphasizes participation over passive listening."\n"Scotland's oral tradition has been influenced by various cultures, including those from Ireland, Wales, England, and other European countries."\n"Some Scottish folktales feature the concept of 'dual worlds,' where human and supernatural realms coexist but are not always accessible to all."\n"The Three Sisters' tale has been seen as a commentary on the struggles of women in patriarchal societies, with some interpretations emphasizing its feminist themes."\n"Folklorist James F. Collie's work helped to preserve Scotland's oral tradition by collecting tales from Gaelic-speaking communities and documenting their significance."\n"Some Scottish stories feature the theme of 'the Otherworld,' where the living can interact with supernatural beings or experience otherworldly events."\n"The ancient Celtic art of Scotland often featured depictions of sacred animals, such as the Cernunnos (Horned God) or the Selkie, which were believed to possess spiritual significance."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The term 'seanchaí' refers to an Irish or Scottish storyteller who specializes in oral storytelling and preserves folklore, often relying on memory rather than written records."\n"Folklorist Andrew Lang's collections of Scottish folk tales helped popularize the genre and introduce it to a wider audience."\n"Some Scottish stories feature the Loch Ness Monster as a benevolent guardian of the loch and its inhabitants, rather than just a fearsome predator."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, emphasizing cultural exchange and shared traditions."\n"Scotland's oral tradition has been shaped by Christianity, with many folktales incorporating Christian themes or motifs, reflecting the country's complex cultural heritage."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land, often depicted as an old crone or hag."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Folklorist John Francis Campbell's work helped preserve Scotland's oral tradition by documenting tales from Gaelic-speaking communities and highlighting their significance."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"The term 'ceilidh' (traditional Scottish social gathering) emphasizes participation over passive listening, encouraging active engagement with storytelling traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to protect its owner from harm and possess supernatural powers."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land, often depicted as an old crone or hag."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"Folklorist James F. Collie's work helped preserve Scotland's oral tradition by collecting tales from Gaelic-speaking communities and documenting their significance."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, reflecting cultural exchange and shared traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"Folklorist John Francis Campbell's work helped preserve Scotland's oral tradition by documenting tales from Gaelic-speaking communities and highlighting their significance."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, reflecting cultural exchange and shared traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"Folklorist James F. Collie's work helped preserve Scotland's oral tradition by collecting tales from Gaelic-speaking communities and documenting their significance."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, reflecting cultural exchange and shared traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"Folklorist John Francis Campbell's work helped preserve Scotland's oral tradition by documenting tales from Gaelic-speaking communities and highlighting their significance."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, reflecting cultural exchange and shared traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"Folklorist James F. Collie's work helped preserve Scotland's oral tradition by collecting tales from Gaelic-speaking communities and documenting their significance."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, reflecting cultural exchange and shared traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."\n"Folklorist John Francis Campbell's work helped preserve Scotland's oral tradition by documenting tales from Gaelic-speaking communities and highlighting their significance."\n"The term 'bean nighe' (supernatural woman associated with weaving) is also found in Irish folklore and mythology, reflecting cultural exchange and shared traditions."\n"Scotland's oral tradition has been influenced by various cultures and historical events, reflecting the country's complex cultural heritage and geographical location."\n"Some Scottish folktales feature a type of magical object known as the 'fáinne geal' (white ring), said to possess supernatural powers and protect its owner from harm."\n"The Three Sisters' tale has been seen as a commentary on women's struggles in patriarchal societies, with some interpretations emphasizing its feminist themes and significance."\n"Some Scottish stories feature the Loch Ness Monster as a guardian of the loch and its inhabitants, rather than just a fearsome predator or myth."\n"Scotland's oral tradition has been shaped by Christianity, reflecting the country's complex cultural heritage and historical events."\n"The term 'seanchaí' (Irish or Scottish storyteller) emphasizes the importance of memory in preserving folklore and cultural traditions."\n"Some Scottish folktales feature a type of supernatural being known as the 'Cailleach,' associated with winter, fertility, and the land."\n"The Three Sisters' tale has been retold in various forms over time, adapting to changing social norms and values while maintaining its core themes and motifs."\n"Some Scottish stories feature the concept of 'thin places,' where supernatural beings are more likely to appear due to a permeable boundary between worlds."	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	story-telling	Weaving Words: Uncovering the Hidden History of Gaelic Storytelling	["Scottish Oral Tradition", "Medieval Scottish Epic Tales", "Folk Songs and Ballads", "Highland Clans", "Scottish Immigration", "Sir Walter Scott", "Traveling Storytellers", "Folklore Studies", "Literary Theory", "Cultural Anthropology", "Scottish Identity", "Cultural Memory", "Community Cohesion"]	\N	[\n  {\n    "title": "The Gaelic Roots of Scottish Storytelling",\n    "description": "Explore the historical context of Scotland's oral tradition, tracing its roots to the Gaelic-speaking communities of the Highlands and Islands.",\n    "contents": [\n      "Poetry and storytelling in ancient Celtic culture",\n      "Gaelic oral traditions: myth, legend, and history",\n      "The role of bards in preserving cultural heritage"\n    ]\n  },\n  {\n    "title": "Tam o' Shanter and the Evolution of Scottish Folk Tales",\n    "description": "Examine the significance of tales like Tam o' Shanter in shaping Scotland's unique cultural heritage.",\n    "contents": [\n      "The story of Tam o' Shanter: origins, themes, and interpretations",\n      "Other notable folk tales in Scottish literature (e.g. The Three Sisters)",\n      "Folk tale archetypes and motifs in Scottish storytelling"\n    ]\n  },\n  {\n    "title": "Oral Tradition and Social Commentary",\n    "description": "Analyze the role of oral narrative in preserving history, myth, and social commentary.",\n    "contents": [\n      "The use of folklore to critique societal norms",\n      "Social issues addressed through folk tales (e.g. poverty, inequality)",\n      "Folkloric examples of resistance and rebellion"\n    ]\n  },\n  {\n    "title": "The Industrial Revolution's Impact on Storytelling",\n    "description": "Examine how the rise of urbanization and industrialization transformed the way stories were told and consumed in Scotland.",\n    "contents": [\n      "Folk festivals and storytelling in urban settings (e.g. ceilidhs)",\n      "Literary movements: Scottish Renaissance, Romanticism, etc.",\n      "The role of print culture and literacy in disseminating folk tales"\n    ]\n  },\n  {\n    "title": "Modern-Day Scottish Storytelling",\n    "description": "Explore the ongoing significance of oral narrative in modern Scotland, highlighting contemporary examples and innovations.",\n    "contents": [\n      "Ceilidh hosting: contemporary practices and traditions",\n      "Folk music, dance, and storytelling festivals (e.g. Celtic Connections)",\n      "Digital platforms for sharing Scottish folk tales and stories"\n    ]\n  },\n  {\n    "title": "The Enduring Power of Oral Narrative",\n    "description": "Discuss the ways in which oral storytelling continues to unite, educate, and inspire communities in Scotland.",\n    "contents": [\n      "Community engagement through folk music and dance",\n      "Storytelling as a tool for preserving cultural heritage",\n      "Oral tradition's role in contemporary Scottish education"\n    ]\n  }\n]	\N	\N
\.


--
-- Data for Name: post_section; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section (id, post_id, section_order, section_heading, ideas_to_include, facts_to_include, first_draft, uk_british, highlighting, image_concepts, image_prompts, generation, optimization, watermarking, image_meta_descriptions, image_captions, image_prompt_example_id, generated_image_url, image_generation_metadata, image_id, section_description, status) FROM stdin;
2	15	0	Introduction	["history", "significance"]	["The quaich is a traditional Scottish drinking vessel."]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Overview of the quaich	draft
3	15	0	Historical Evolution	["evolution", "design"]	["The design of the quaich has evolved over centuries."]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	How the quaich evolved over time	draft
4	15	0	Cultural Significance	["ceremonies", "traditions"]	["It is often used in ceremonies and celebrations.", "Quaichs are often given as gifts to mark special occasions."]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	The role of quaichs in ceremonies	draft
41	22	1	The Gaelic Roots of Scottish Storytelling	["Poetry and storytelling in ancient Celtic culture", "Gaelic oral traditions: myth, legend, and history", "The role of bards in preserving cultural heritage"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Explore the historical context of Scotland's oral tradition, tracing its roots to the Gaelic-speaking communities of the Highlands and Islands.	draft
42	22	2	Tam o' Shanter and the Evolution of Scottish Folk Tales	["The story of Tam o' Shanter: origins, themes, and interpretations", "Other notable folk tales in Scottish literature (e.g. The Three Sisters)", "Folk tale archetypes and motifs in Scottish storytelling"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Examine the significance of tales like Tam o' Shanter in shaping Scotland's unique cultural heritage.	draft
43	22	3	Oral Tradition and Social Commentary	["The use of folklore to critique societal norms", "Social issues addressed through folk tales (e.g. poverty, inequality)", "Folkloric examples of resistance and rebellion"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Analyze the role of oral narrative in preserving history, myth, and social commentary.	draft
44	22	4	The Industrial Revolution's Impact on Storytelling	["Folk festivals and storytelling in urban settings (e.g. ceilidhs)", "Literary movements: Scottish Renaissance, Romanticism, etc.", "The role of print culture and literacy in disseminating folk tales"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Examine how the rise of urbanization and industrialization transformed the way stories were told and consumed in Scotland.	draft
45	22	5	Modern-Day Scottish Storytelling	["Ceilidh hosting: contemporary practices and traditions", "Folk music, dance, and storytelling festivals (e.g. Celtic Connections)", "Digital platforms for sharing Scottish folk tales and stories"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Explore the ongoing significance of oral narrative in modern Scotland, highlighting contemporary examples and innovations.	draft
46	22	6	The Enduring Power of Oral Narrative	["Community engagement through folk music and dance", "Storytelling as a tool for preserving cultural heritage", "Oral tradition's role in contemporary Scottish education"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Discuss the ways in which oral storytelling continues to unite, educate, and inspire communities in Scotland.	draft
47	22	0	Test Section	\N	\N	Test Content	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Test Description	draft
\.


--
-- Data for Name: post_section_elements; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section_elements (id, post_id, section_id, element_type, element_text, element_order, created_at, updated_at) FROM stdin;
1	15	2	fact	* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers	8	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
2	15	2	fact	* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production	9	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
3	15	2	fact	* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations	10	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
4	15	2	fact	* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie	11	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
5	15	2	fact	* Introduce the basics of cream distillation and its role in Scottish whisky production	12	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
6	15	2	fact	**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.	13	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
7	15	2	fact	**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	14	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
8	15	2	fact	**Core ideas:**	15	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
9	15	2	fact	**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.	16	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
10	15	2	fact	**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"	17	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
11	15	2	fact	**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.	18	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
12	15	2	fact	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:	19	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
13	15	3	fact	* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers	8	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
14	15	3	fact	* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production	9	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
15	15	3	fact	* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations	10	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
16	15	3	fact	* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie	11	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
17	15	3	fact	* Introduce the basics of cream distillation and its role in Scottish whisky production	12	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
18	15	3	fact	**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.	13	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
19	15	3	fact	**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	14	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
20	15	3	fact	**Core ideas:**	15	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
21	15	3	fact	**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.	16	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
22	15	3	fact	**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"	17	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
23	15	3	fact	**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.	18	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
24	15	3	fact	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:	19	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
25	15	4	fact	* Analyze the impact on whisky styles and flavor profiles, using expert insights from modern distillers and whisky writers	8	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
26	15	4	fact	* Discuss the decline of cream distillation and its legacy in contemporary Scottish whisky production	9	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
27	15	4	fact	* Explore the historical context: how cream distillation emerged as a response to changes in taxation and trade regulations	10	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
28	15	4	fact	* Highlight key figures and distilleries associated with the development of cream distillation, such as Glenfiddich and Balvenie	11	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
29	15	4	fact	* Introduce the basics of cream distillation and its role in Scottish whisky production	12	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
30	15	4	fact	**Angle:** Our approach will be to uncover the stories behind this lost art, highlighting the pioneering distillers who experimented with cream distillation in the 19th century. We'll examine the science behind the process and how it influenced the development of distinctive whisky styles, such as the smooth, honeyed drams of Speyside.	13	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
31	15	4	fact	**Authenticity and accuracy:** As an expert in Scottish history and culture, I'll ensure that all information is thoroughly researched and verified, adhering to academic standards while making the content engaging and easy to understand.	14	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
32	15	4	fact	**Core ideas:**	15	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
33	15	4	fact	**Scope:** This article will delve into the little-known process of cream distillation, an innovative technique used by Scottish whisky producers to create smoother, more refined spirits. By exploring the historical context and cultural significance of cream distillation, we'll reveal its impact on the evolution of Scotland's iconic whisky industry.	16	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
34	15	4	fact	**Title:** "The Forgotten Art of Cream Distillation: Uncovering Scotland's Rich History in Whisky Production"	17	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
35	15	4	fact	**Tone:** Engaging, informative, and richly descriptive, this article will transport readers to Scotland's whisky country, immersing them in the sights, sounds, and aromas of traditional distilleries. With a dash of storytelling flair, we'll bring the history of cream distillation to life, making it accessible to both whisky enthusiasts and curious newcomers.	18	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
36	15	4	fact	Here's a brief for a long-form blog article on the topic of "cream distillation" through the lens of Scottish history and culture:	19	2025-06-09 08:04:49.235362	2025-06-09 08:04:49.235362
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
\.


--
-- Data for Name: post_workflow_step_action; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_workflow_step_action (id, post_id, step_id, action_id, input_field, output_field, button_label, button_order) FROM stdin;
1	16	1	49	\N	\N	Action	0
2	17	1	49	idea_seed	basic_idea	\N	0
3	15	1	49	basic_idea	idea_scope	\N	0
4	9	1	\N	input3	output3	Test3	3
5	19	1	48	idea_seed	basic_idea	\N	0
6	20	1	53	idea_seed	basic_idea	\N	0
7	21	1	48	idea_seed	basic_idea	\N	0
8	22	1	48	idea_seed	basic_idea	\N	0
9	23	1	48	idea_seed	basic_idea	\N	0
10	24	1	48	idea_seed	basic_idea	\N	0
19	19	3	49	section_planning	section_headings	\N	0
20	22	3	\N	basic_idea	summary	\N	0
21	19	4	48	intro_blurb	conclusion	\N	0
23	19	7	49	self_review	final_check	\N	0
24	19	8	48	deployment	verification	\N	0
11	19	12	48	main_title	subtitle	\N	0
12	15	12	48	idea_seed	interesting_facts	\N	0
13	20	12	54	topics_to_cover	topics_to_cover	\N	0
14	21	12	54	basic_idea	interesting_facts	\N	0
15	2	12	54	topics_to_cover	interesting_facts	\N	0
16	22	12	54	basic_idea	interesting_facts	\N	0
17	23	12	54	basic_idea	interesting_facts	\N	0
18	24	12	54	basic_idea	interesting_facts	\N	0
22	19	5	49	\N	topics_to_cover	\N	\N
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
4	plan	58
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
\.


--
-- Data for Name: workflow_field_mapping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workflow_field_mapping (id, field_name, stage_id, substage_id, order_index) FROM stdin;
33	idea_seed	10	1	1
1	basic_idea	10	1	2
2	provisional_title	10	1	3
3	idea_scope	10	1	4
4	topics_to_cover	10	2	1
5	interesting_facts	10	2	2
7	section_planning	10	3	1
8	section_headings	10	3	2
9	section_order	10	3	3
10	main_title	11	4	1
11	subtitle	11	4	2
12	intro_blurb	11	4	3
13	conclusion	11	4	4
14	basic_metadata	11	5	1
15	tags	11	5	2
16	categories	11	5	3
17	image_captions	11	6	1
19	self_review	8	7	1
20	peer_review	8	7	2
21	final_check	8	7	3
18	seo_optimization	8	7	4
6	tartans_products	8	7	8
22	scheduling	8	8	1
23	deployment	8	8	2
24	verification	8	8	3
25	feedback_collection	8	9	1
26	content_updates	8	9	2
27	version_control	8	9	3
28	platform_selection	8	9	4
29	content_adaptation	8	9	5
30	distribution	8	9	6
31	engagement_tracking	8	9	7
\.


--
-- Data for Name: workflow_stage_entity; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_stage_entity (id, name, description, stage_order) FROM stdin;
8	publishing	Publishing	8
10	planning	Planning phase	1
11	authoring	Authoring phase	2
54	writing	Content writing and development	2
\.


--
-- Data for Name: workflow_step_entity; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_step_entity (id, sub_stage_id, name, description, step_order, config) FROM stdin;
1	1	Main	Main step for this substage	1	{}
3	3	Main	Main step for this substage	1	{}
4	4	Main	Main step for this substage	1	{}
5	5	Main	Main step for this substage	1	{}
6	6	Main	Main step for this substage	1	{}
7	7	Main	Main step for this substage	1	{}
8	8	Main	Main step for this substage	1	{}
9	9	Main	Main step for this substage	1	{}
10	1	basic_idea	Enter the basic idea for your post	1	{}
11	1	provisional_title	Enter a provisional title for your post	2	{}
12	2	concepts	Research Concepts step	1	{}
13	2	facts	Research Facts step	2	{"prompt": "test prompt"}
14	3	outline	Generate a detailed blog post outline based on the expanded idea.	1	{}
15	3	allocate_facts	Allocate research facts to sections in the outline	2	{}
16	19	sections	Generate detailed content for each section of the outline	1	{}
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
4	11	content	Content authoring	1
5	11	meta_info	Metadata and SEO	2
6	11	images	Image creation	3
7	8	preflight	Pre-publication checks	1
8	8	launch	Publishing	2
9	8	syndication	Syndication and distribution	3
19	54	content	Content writing and development	1
\.


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.category_id_seq', 1, true);


--
-- Name: image_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_format_id_seq', 1, true);


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

SELECT pg_catalog.setval('public.image_setting_id_seq', 1, true);


--
-- Name: image_style_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_style_id_seq', 1, true);


--
-- Name: llm_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_action_history_id_seq', 1, true);


--
-- Name: llm_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_action_id_seq', 61, true);


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

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 57, true);


--
-- Name: llm_prompt_part_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_prompt_part_id_seq', 40, true);


--
-- Name: llm_provider_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_provider_id_seq', 4, true);


--
-- Name: post_development_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_development_id_seq', 17, true);


--
-- Name: post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_id_seq', 24, true);


--
-- Name: post_section_elements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_section_elements_id_seq', 296, true);


--
-- Name: post_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_section_id_seq', 47, true);


--
-- Name: post_workflow_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_stage_id_seq', 3, true);


--
-- Name: post_workflow_step_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_step_action_id_seq', 24, true);


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
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workflow_field_mapping_id_seq', 33, true);


--
-- Name: workflow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_id_seq', 1, true);


--
-- Name: workflow_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_stage_entity_id_seq', 54, true);


--
-- Name: workflow_step_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_entity_id_seq', 16, true);


--
-- Name: workflow_steps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_steps_id_seq', 1, false);


--
-- Name: workflow_sub_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_sub_stage_entity_id_seq', 19, true);


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
-- Name: workflow_field_mapping workflow_field_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_pkey PRIMARY KEY (id);


--
-- Name: workflow workflow_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_pkey PRIMARY KEY (id);


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
-- Name: idx_image_path; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_image_path ON public.image USING btree (path);


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
-- Name: idx_post_slug; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_slug ON public.post USING btree (slug);


--
-- Name: idx_post_status; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_status ON public.post USING btree (status);


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
-- Name: idx_workflow_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_post ON public.workflow USING btree (post_id);


--
-- Name: idx_workflow_stage_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_stage_id ON public.workflow USING btree (stage_id);


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
-- Name: llm_action update_llm_action_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_llm_action_updated_at BEFORE UPDATE ON public.llm_action FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


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
-- Name: llm_action llm_action_prompt_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_prompt_template_id_fkey FOREIGN KEY (prompt_template_id) REFERENCES public.llm_prompt(id);


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
-- Name: post_section post_section_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_section
    ADD CONSTRAINT post_section_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image(id);


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
-- Name: workflow_field_mapping workflow_field_mapping_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: workflow workflow_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: workflow workflow_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow
    ADD CONSTRAINT workflow_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id);


--
-- Name: workflow_step_entity workflow_step_entity_sub_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_step_entity
    ADD CONSTRAINT workflow_step_entity_sub_stage_id_fkey FOREIGN KEY (sub_stage_id) REFERENCES public.workflow_sub_stage_entity(id) ON DELETE CASCADE;


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
-- Name: TABLE post_section; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_section TO postgres;


--
-- Name: TABLE post_section_elements; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_section_elements TO postgres;


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
-- Name: SEQUENCE workflow_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.workflow_id_seq TO postgres;


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
-- Name: TABLE workflow_step_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_step_entity TO postgres;


--
-- Name: TABLE workflow_steps; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_steps TO postgres;


--
-- Name: TABLE workflow_sub_stage_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_sub_stage_entity TO postgres;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: nickfiddes
--

ALTER DEFAULT PRIVILEGES FOR ROLE nickfiddes IN SCHEMA public GRANT ALL ON TABLES  TO postgres;


--
-- PostgreSQL database dump complete
--

