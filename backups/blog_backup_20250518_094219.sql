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
    'archived'
);


ALTER TYPE public.post_status OWNER TO nickfiddes;

--
-- Name: poststatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.poststatus AS ENUM (
    'draft',
    'in_process',
    'published',
    'archived'
);


ALTER TYPE public.poststatus OWNER TO postgres;

--
-- Name: workflow_stage; Type: TYPE; Schema: public; Owner: nickfiddes
--

CREATE TYPE public.workflow_stage AS ENUM (
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


ALTER TYPE public.workflow_stage OWNER TO nickfiddes;

--
-- Name: workflowstage; Type: TYPE; Schema: public; Owner: postgres
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


ALTER TYPE public.workflowstage OWNER TO postgres;

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

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
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    model_name character varying(100) NOT NULL,
    api_base character varying(200) NOT NULL,
    auth_token character varying(200),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
-- Name: llm_prompt; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.llm_prompt (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    prompt_text text NOT NULL,
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
-- Name: post; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    content text,
    summary text,
    published boolean DEFAULT false,
    deleted boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    published_at timestamp without time zone,
    header_image_id integer,
    llm_metadata jsonb,
    seo_metadata jsonb,
    syndication_status jsonb,
    status public.post_status DEFAULT 'draft'::public.post_status NOT NULL,
    conclusion text,
    footer text
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
-- Name: post_tags; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.post_tags (
    post_id integer NOT NULL,
    tag_id integer NOT NULL
);


ALTER TABLE public.post_tags OWNER TO nickfiddes;

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
-- Name: workflow_status; Type: TABLE; Schema: public; Owner: nickfiddes
--

CREATE TABLE public.workflow_status (
    id integer NOT NULL,
    post_id integer NOT NULL,
    conceptualisation character varying(32) DEFAULT 'not_started'::character varying,
    authoring character varying(32) DEFAULT 'not_started'::character varying,
    meta_status character varying(32) DEFAULT 'not_started'::character varying,
    images character varying(32) DEFAULT 'not_started'::character varying,
    validation character varying(32) DEFAULT 'not_started'::character varying,
    publishing character varying(32) DEFAULT 'not_started'::character varying,
    syndication character varying(32) DEFAULT 'not_started'::character varying,
    log text,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.workflow_status OWNER TO nickfiddes;

--
-- Name: workflow_status_id_seq; Type: SEQUENCE; Schema: public; Owner: nickfiddes
--

CREATE SEQUENCE public.workflow_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_status_id_seq OWNER TO nickfiddes;

--
-- Name: workflow_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nickfiddes
--

ALTER SEQUENCE public.workflow_status_id_seq OWNED BY public.workflow_status.id;


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
-- Name: llm_config id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_config ALTER COLUMN id SET DEFAULT nextval('public.llm_config_id_seq'::regclass);


--
-- Name: llm_interaction id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_interaction ALTER COLUMN id SET DEFAULT nextval('public.llm_interaction_id_seq'::regclass);


--
-- Name: llm_prompt id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt ALTER COLUMN id SET DEFAULT nextval('public.llm_prompt_id_seq'::regclass);


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
-- Name: tag id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.tag ALTER COLUMN id SET DEFAULT nextval('public.tag_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: workflow_status id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_status ALTER COLUMN id SET DEFAULT nextval('public.workflow_status_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
2a69ac33fec9
\.


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

COPY public.llm_action (id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, "order", created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_action_history; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_action_history (id, action_id, post_id, input_text, output_text, status, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_config (id, provider_type, model_name, api_base, auth_token, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_interaction; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_interaction (id, prompt_id, input_text, output_text, parameters_used, interaction_metadata, created_at) FROM stdin;
\.


--
-- Data for Name: llm_prompt; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.llm_prompt (id, name, description, prompt_text, system_prompt, parameters, "order", created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post (id, title, slug, content, summary, published, deleted, created_at, updated_at, published_at, header_image_id, llm_metadata, seo_metadata, syndication_status, status, conclusion, footer) FROM stdin;
\.


--
-- Data for Name: post_categories; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_categories (post_id, category_id) FROM stdin;
\.


--
-- Data for Name: post_development; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_development (id, post_id, basic_idea, provisional_title, idea_scope, topics_to_cover, interesting_facts, tartans_products, section_planning, section_headings, section_order, main_title, subtitle, intro_blurb, conclusion, basic_metadata, tags, categories, image_captions, seo_optimization, self_review, peer_review, final_check, scheduling, deployment, verification, feedback_collection, content_updates, version_control, platform_selection, content_adaptation, distribution, engagement_tracking) FROM stdin;
\.


--
-- Data for Name: post_section; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_section (id, post_id, section_order, section_heading, ideas_to_include, facts_to_include, first_draft, uk_british, highlighting, image_concepts, image_prompts, generation, optimization, watermarking, image_meta_descriptions, image_captions, image_prompt_example_id, generated_image_url, image_generation_metadata, image_id) FROM stdin;
\.


--
-- Data for Name: post_tags; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.post_tags (post_id, tag_id) FROM stdin;
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
-- Data for Name: workflow_status; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_status (id, post_id, conceptualisation, authoring, meta_status, images, validation, publishing, syndication, log, last_updated) FROM stdin;
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
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 1, false);


--
-- Name: llm_interaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_interaction_id_seq', 1, false);


--
-- Name: llm_prompt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 1, false);


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
-- Name: tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.tag_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: workflow_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_status_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


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
-- Name: llm_config llm_config_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_pkey PRIMARY KEY (id);


--
-- Name: llm_interaction llm_interaction_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_interaction
    ADD CONSTRAINT llm_interaction_pkey PRIMARY KEY (id);


--
-- Name: llm_prompt llm_prompt_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.llm_prompt
    ADD CONSTRAINT llm_prompt_pkey PRIMARY KEY (id);


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
-- Name: post_tags post_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_pkey PRIMARY KEY (post_id, tag_id);


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
-- Name: workflow_status workflow_status_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_status
    ADD CONSTRAINT workflow_status_pkey PRIMARY KEY (id);


--
-- Name: workflow_status workflow_status_post_id_key; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_status
    ADD CONSTRAINT workflow_status_post_id_key UNIQUE (post_id);


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
-- Name: idx_workflow_status_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_status_post ON public.workflow_status USING btree (post_id);


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
-- Name: llm_config update_llm_config_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_llm_config_updated_at BEFORE UPDATE ON public.llm_config FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: post update_post_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_post_updated_at BEFORE UPDATE ON public.post FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user update_user_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON public."user" FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


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
-- Name: workflow_status workflow_status_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_status
    ADD CONSTRAINT workflow_status_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: TABLE alembic_version; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.alembic_version TO nickfiddes;
GRANT ALL ON TABLE public.alembic_version TO PUBLIC;


--
-- Name: TABLE category; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.category TO PUBLIC;
GRANT ALL ON TABLE public.category TO postgres;


--
-- Name: SEQUENCE category_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.category_id_seq TO postgres;


--
-- Name: TABLE image; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image TO PUBLIC;
GRANT ALL ON TABLE public.image TO postgres;


--
-- Name: TABLE image_format; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_format TO PUBLIC;
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

GRANT ALL ON TABLE public.image_prompt_example TO PUBLIC;
GRANT ALL ON TABLE public.image_prompt_example TO postgres;


--
-- Name: SEQUENCE image_prompt_example_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_prompt_example_id_seq TO postgres;


--
-- Name: TABLE image_setting; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_setting TO PUBLIC;
GRANT ALL ON TABLE public.image_setting TO postgres;


--
-- Name: SEQUENCE image_setting_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_setting_id_seq TO postgres;


--
-- Name: TABLE image_style; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.image_style TO PUBLIC;
GRANT ALL ON TABLE public.image_style TO postgres;


--
-- Name: SEQUENCE image_style_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.image_style_id_seq TO postgres;


--
-- Name: TABLE llm_action; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_action TO PUBLIC;
GRANT ALL ON TABLE public.llm_action TO postgres;


--
-- Name: TABLE llm_action_history; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_action_history TO PUBLIC;
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

GRANT ALL ON TABLE public.llm_config TO PUBLIC;
GRANT ALL ON TABLE public.llm_config TO postgres;


--
-- Name: SEQUENCE llm_config_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_config_id_seq TO postgres;


--
-- Name: TABLE llm_interaction; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_interaction TO PUBLIC;
GRANT ALL ON TABLE public.llm_interaction TO postgres;


--
-- Name: SEQUENCE llm_interaction_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_interaction_id_seq TO postgres;


--
-- Name: TABLE llm_prompt; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.llm_prompt TO PUBLIC;
GRANT ALL ON TABLE public.llm_prompt TO postgres;


--
-- Name: SEQUENCE llm_prompt_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.llm_prompt_id_seq TO postgres;


--
-- Name: TABLE post; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post TO PUBLIC;
GRANT ALL ON TABLE public.post TO postgres;


--
-- Name: TABLE post_categories; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_categories TO PUBLIC;
GRANT ALL ON TABLE public.post_categories TO postgres;


--
-- Name: TABLE post_development; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_development TO PUBLIC;
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

GRANT ALL ON TABLE public.post_section TO PUBLIC;
GRANT ALL ON TABLE public.post_section TO postgres;


--
-- Name: SEQUENCE post_section_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.post_section_id_seq TO postgres;


--
-- Name: TABLE post_tags; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.post_tags TO PUBLIC;
GRANT ALL ON TABLE public.post_tags TO postgres;


--
-- Name: TABLE tag; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.tag TO PUBLIC;
GRANT ALL ON TABLE public.tag TO postgres;


--
-- Name: SEQUENCE tag_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.tag_id_seq TO postgres;


--
-- Name: TABLE "user"; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public."user" TO PUBLIC;
GRANT ALL ON TABLE public."user" TO postgres;


--
-- Name: SEQUENCE user_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.user_id_seq TO postgres;


--
-- Name: TABLE workflow_status; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_status TO PUBLIC;
GRANT ALL ON TABLE public.workflow_status TO postgres;


--
-- Name: SEQUENCE workflow_status_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON SEQUENCE public.workflow_status_id_seq TO postgres;


--
-- PostgreSQL database dump complete
--

