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
    provider_id integer NOT NULL,
    temperature double precision DEFAULT 0.7,
    max_tokens integer DEFAULT 1000,
    "order" integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    input_field character varying(128),
    output_field character varying(128)
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
    prompt_json jsonb,
    system_prompt text,
    parameters jsonb,
    "order" integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    idea_seed text,
    summary text,
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
    engagement_tracking text
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
    section_description text,
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
    image_id integer
);


ALTER TABLE public.post_section OWNER TO nickfiddes;

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
-- Name: post_substage_action; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_substage_action (
    id integer NOT NULL,
    post_id integer,
    substage character varying(64) NOT NULL,
    action_id integer,
    button_label text,
    button_order integer DEFAULT 0,
    input_field character varying(128),
    output_field character varying(128)
);


ALTER TABLE public.post_substage_action OWNER TO nickfiddes;

--
-- Name: post_substage_action_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.post_substage_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_substage_action_id_seq OWNER TO nickfiddes;

--
-- Name: post_substage_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.post_substage_action_id_seq OWNED BY public.post_substage_action.id;


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
    output_field character varying(128)
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
-- Name: post_substage_action id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_substage_action ALTER COLUMN id SET DEFAULT nextval('public.post_substage_action_id_seq'::regclass);


--
-- Name: post_workflow_stage id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_stage ALTER COLUMN id SET DEFAULT nextval('public.post_workflow_stage_id_seq'::regclass);


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

COPY public.llm_action (id, field_name, prompt_template, prompt_template_id, llm_model, provider_id, temperature, max_tokens, "order", created_at, updated_at, input_field, output_field) FROM stdin;
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

COPY public.llm_prompt (id, name, description, prompt_text, prompt_json, system_prompt, parameters, "order", created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_prompt_part; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_prompt_part (id, type, content, tags, "order", created_at, updated_at, name, action_id, description) FROM stdin;
\.


--
-- Data for Name: llm_provider; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_provider (id, name, type, api_url, auth_token, description, created_at, updated_at) FROM stdin;
1	Ollama (local)	local	http://localhost:11434	\N	Local Ollama server for fast, private inference.	2025-05-26 10:58:23.513987	2025-05-26 10:58:23.513987
2	OpenAI	openai	https://api.openai.com/v1	\N	OpenAI API for GPT-3.5, GPT-4, etc.	2025-05-26 11:06:00.780193	2025-05-26 11:06:00.780193
3	Anthropic	other	https://api.anthropic.com/v1	\N	Anthropic Claude API.	2025-05-26 11:06:01.915015	2025-05-26 11:06:01.915015
4	Gemini	other	https://generativelanguage.googleapis.com/v1beta	\N	Google Gemini API.	2025-05-26 11:06:02.450166	2025-05-26 11:06:02.450166
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post (id, title, slug, summary, created_at, updated_at, header_image_id, status, substage_id) FROM stdin;
\.


--
-- Data for Name: post_categories; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_categories (post_id, category_id) FROM stdin;
\.


--
-- Data for Name: post_development; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_development (id, post_id, basic_idea, idea_seed, summary, provisional_title, idea_scope, topics_to_cover, interesting_facts, tartans_products, section_planning, section_headings, section_order, main_title, subtitle, intro_blurb, conclusion, basic_metadata, tags, categories, image_captions, seo_optimization, self_review, peer_review, final_check, scheduling, deployment, verification, feedback_collection, content_updates, version_control, platform_selection, content_adaptation, distribution, engagement_tracking) FROM stdin;
\.


--
-- Data for Name: post_section; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section (id, post_id, section_order, section_heading, section_description, ideas_to_include, facts_to_include, first_draft, uk_british, highlighting, image_concepts, image_prompts, generation, optimization, watermarking, image_meta_descriptions, image_captions, image_prompt_example_id, generated_image_url, image_generation_metadata, image_id) FROM stdin;
\.


--
-- Data for Name: post_substage_action; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_substage_action (id, post_id, substage, action_id, button_label, button_order, input_field, output_field) FROM stdin;
32	16	idea	49	Action	0	\N	\N
33	17	idea	49	\N	0	idea_seed	basic_idea
36	19	research	48	\N	0	main_title	subtitle
9	15	idea	49	\N	0	basic_idea	idea_scope
38	19	content	48	\N	0	intro_blurb	conclusion
39	19	meta_info	49	\N	0	categories	basic_metadata
37	19	structure	49	\N	0	section_planning	section_headings
40	19	preflight	49	\N	0	self_review	final_check
41	19	launch	48	\N	0	deployment	verification
34	15	research	48	\N	0	idea_seed	interesting_facts
1	9	idea	3	Test3	3	input3	output3
35	19	idea	48	\N	0	idea_seed	basic_idea
43	20	research	54	\N	0	topics_to_cover	topics_to_cover
42	20	idea	53	\N	0	idea_seed	basic_idea
46	21	research	54	\N	0	basic_idea	interesting_facts
45	21	idea	48	\N	0	idea_seed	basic_idea
48	22	structure	1	\N	0	basic_idea	summary
44	2	research	54	\N	0	topics_to_cover	interesting_facts
49	22	research	54	\N	0	basic_idea	interesting_facts
47	22	idea	48	\N	0	idea_seed	basic_idea
50	23	idea	48	\N	0	idea_seed	basic_idea
51	23	research	54	\N	0	basic_idea	interesting_facts
52	24	idea	48	\N	0	idea_seed	basic_idea
53	24	research	54	\N	0	basic_idea	interesting_facts
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
\.


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.category_id_seq', 1, false);


--
-- Name: image_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_format_id_seq', 1, false);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_prompt_example_id_seq', 1, false);


--
-- Name: image_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_setting_id_seq', 1, false);


--
-- Name: image_style_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.image_style_id_seq', 1, false);


--
-- Name: llm_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_action_history_id_seq', 1, false);


--
-- Name: llm_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_action_id_seq', 1, false);


--
-- Name: llm_interaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_interaction_id_seq', 1, false);


--
-- Name: llm_model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_model_id_seq', 23, true);


--
-- Name: llm_prompt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 1, false);


--
-- Name: llm_prompt_part_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_prompt_part_id_seq', 1, false);


--
-- Name: llm_provider_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_provider_id_seq', 4, true);


--
-- Name: post_development_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_development_id_seq', 1, false);


--
-- Name: post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_id_seq', 1, false);


--
-- Name: post_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_section_id_seq', 1, false);


--
-- Name: post_substage_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_substage_action_id_seq', 53, true);


--
-- Name: post_workflow_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_stage_id_seq', 1, true);


--
-- Name: post_workflow_sub_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.post_workflow_sub_stage_id_seq', 1, true);


--
-- Name: substage_action_default_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.substage_action_default_id_seq', 1, true);


--
-- Name: tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.tag_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workflow_field_mapping_id_seq', 33, true);


--
-- Name: workflow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_id_seq', 1, false);


--
-- Name: workflow_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_stage_entity_id_seq', 17, true);


--
-- Name: workflow_sub_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_sub_stage_entity_id_seq', 9, true);


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
-- Name: post_substage_action post_substage_action_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_substage_action
    ADD CONSTRAINT post_substage_action_pkey PRIMARY KEY (id);


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
-- Name: workflow_sub_stage_entity workflow_sub_stage_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT workflow_sub_stage_entity_pkey PRIMARY KEY (id);


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
-- Name: idx_post_slug; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_slug ON public.post USING btree (slug);


--
-- Name: idx_post_status; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_post_status ON public.post USING btree (status);


--
-- Name: idx_workflow_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_post ON public.workflow USING btree (post_id);


--
-- Name: idx_workflow_stage_id; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_stage_id ON public.workflow USING btree (stage_id);


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
-- Name: post update_post_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_post_updated_at BEFORE UPDATE ON public.post FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user update_user_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON public."user" FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: workflow update_workflow_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_workflow_updated_at BEFORE UPDATE ON public.workflow FOR EACH ROW EXECUTE FUNCTION public.update_workflow_updated_at_column();


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
-- Name: llm_action llm_action_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.llm_provider(id);


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
-- Name: post_workflow_sub_stage post_workflow_sub_stage_post_workflow_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_sub_stage
    ADD CONSTRAINT post_workflow_sub_stage_post_workflow_stage_id_fkey FOREIGN KEY (post_workflow_stage_id) REFERENCES public.post_workflow_stage(id) ON DELETE CASCADE;


--
-- Name: post_workflow_sub_stage post_workflow_sub_stage_sub_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_workflow_sub_stage
    ADD CONSTRAINT post_workflow_sub_stage_sub_stage_id_fkey FOREIGN KEY (sub_stage_id) REFERENCES public.workflow_sub_stage_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_field_mapping workflow_field_mapping_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: workflow_field_mapping workflow_field_mapping_substage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_substage_id_fkey FOREIGN KEY (substage_id) REFERENCES public.workflow_sub_stage_entity(id) ON DELETE CASCADE;


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
-- Name: workflow_sub_stage_entity workflow_sub_stage_entity_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT workflow_sub_stage_entity_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: TABLE category; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.category TO postgres;


--
-- Name: TABLE image; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image TO postgres;


--
-- Name: TABLE image_format; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_format TO postgres;


--
-- Name: TABLE image_prompt_example; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_prompt_example TO postgres;


--
-- Name: TABLE image_setting; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_setting TO postgres;


--
-- Name: TABLE image_style; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_style TO postgres;


--
-- Name: TABLE llm_action; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_action TO postgres;


--
-- Name: TABLE llm_action_history; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_action_history TO postgres;


--
-- Name: TABLE llm_interaction; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_interaction TO postgres;


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
-- Name: TABLE llm_prompt_part; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_prompt_part TO postgres;


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
-- Name: TABLE post_section; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_section TO postgres;


--
-- Name: TABLE post_substage_action; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_substage_action TO postgres;


--
-- Name: SEQUENCE post_substage_action_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_substage_action_id_seq TO postgres;


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
-- Name: TABLE "user"; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public."user" TO postgres;


--
-- Name: TABLE workflow; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow TO postgres;


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
-- Name: TABLE workflow_sub_stage_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT ON TABLE public.workflow_sub_stage_entity TO PUBLIC;
GRANT ALL ON TABLE public.workflow_sub_stage_entity TO postgres;


--
-- Name: SEQUENCE workflow_sub_stage_entity_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.workflow_sub_stage_entity_id_seq TO postgres;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: nickfiddes
--

ALTER DEFAULT PRIVILEGES FOR ROLE nickfiddes IN SCHEMA public GRANT ALL ON TABLES  TO postgres;


--
-- PostgreSQL database dump complete
--

