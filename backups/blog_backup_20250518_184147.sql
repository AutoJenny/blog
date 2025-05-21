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
-- Name: category; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.category (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    slug character varying(50) NOT NULL,
    description text
);


ALTER TABLE public.category OWNER TO postgres;

--
-- Name: category_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.category_id_seq OWNER TO postgres;

--
-- Name: category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.category_id_seq OWNED BY public.category.id;


--
-- Name: image; Type: TABLE; Schema: public; Owner: postgres
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
    image_metadata json,
    watermarked boolean,
    watermarked_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.image OWNER TO postgres;

--
-- Name: image_format; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.image_format (
    id integer NOT NULL,
    title character varying(100) NOT NULL,
    description character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    width integer,
    height integer,
    steps integer,
    guidance_scale double precision,
    extra_settings text
);


ALTER TABLE public.image_format OWNER TO postgres;

--
-- Name: image_format_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.image_format_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_format_id_seq OWNER TO postgres;

--
-- Name: image_format_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.image_format_id_seq OWNED BY public.image_format.id;


--
-- Name: image_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_id_seq OWNER TO postgres;

--
-- Name: image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;


--
-- Name: image_prompt_example; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.image_prompt_example (
    id integer NOT NULL,
    description text NOT NULL,
    style_id integer NOT NULL,
    format_id integer NOT NULL,
    provider character varying(50) NOT NULL,
    image_setting_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.image_prompt_example OWNER TO postgres;

--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.image_prompt_example_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_prompt_example_id_seq OWNER TO postgres;

--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.image_prompt_example_id_seq OWNED BY public.image_prompt_example.id;


--
-- Name: image_setting; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.image_setting (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    style_id integer NOT NULL,
    format_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    width integer,
    height integer,
    steps integer,
    guidance_scale double precision,
    extra_settings text
);


ALTER TABLE public.image_setting OWNER TO postgres;

--
-- Name: image_setting_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.image_setting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_setting_id_seq OWNER TO postgres;

--
-- Name: image_setting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.image_setting_id_seq OWNED BY public.image_setting.id;


--
-- Name: image_style; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.image_style (
    id integer NOT NULL,
    title character varying(100) NOT NULL,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.image_style OWNER TO postgres;

--
-- Name: image_style_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.image_style_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.image_style_id_seq OWNER TO postgres;

--
-- Name: image_style_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.image_style_id_seq OWNED BY public.image_style.id;


--
-- Name: llm_action; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_action (
    id integer NOT NULL,
    prompt_template text NOT NULL,
    llm_model character varying(128) NOT NULL,
    temperature double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    field_name character varying(128) NOT NULL,
    max_tokens integer,
    prompt_template_id integer NOT NULL,
    "order" integer NOT NULL
);


ALTER TABLE public.llm_action OWNER TO postgres;

--
-- Name: llm_action_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_action_history (
    id integer NOT NULL,
    action_id integer NOT NULL,
    input_text text NOT NULL,
    output_text text,
    post_id integer NOT NULL,
    status character varying(50),
    error_message text,
    created_at timestamp without time zone
);


ALTER TABLE public.llm_action_history OWNER TO postgres;

--
-- Name: llm_action_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_action_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_action_history_id_seq OWNER TO postgres;

--
-- Name: llm_action_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_action_history_id_seq OWNED BY public.llm_action_history.id;


--
-- Name: llm_action_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_action_id_seq OWNER TO postgres;

--
-- Name: llm_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_action_id_seq OWNED BY public.llm_action.id;


--
-- Name: llm_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_config (
    id integer NOT NULL,
    provider_type character varying(50) NOT NULL,
    model_name character varying(100) NOT NULL,
    api_base character varying(200) NOT NULL,
    auth_token character varying(200),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.llm_config OWNER TO postgres;

--
-- Name: llm_config_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_config_id_seq OWNER TO postgres;

--
-- Name: llm_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_config_id_seq OWNED BY public.llm_config.id;


--
-- Name: llm_interaction; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_interaction (
    id integer NOT NULL,
    prompt_id integer,
    input_text text NOT NULL,
    output_text text,
    parameters_used json,
    interaction_metadata json,
    created_at timestamp without time zone
);


ALTER TABLE public.llm_interaction OWNER TO postgres;

--
-- Name: llm_interaction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_interaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_interaction_id_seq OWNER TO postgres;

--
-- Name: llm_interaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_interaction_id_seq OWNED BY public.llm_interaction.id;


--
-- Name: llm_prompt; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_prompt (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    prompt_text text NOT NULL,
    system_prompt text,
    parameters json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    "order" integer NOT NULL
);


ALTER TABLE public.llm_prompt OWNER TO postgres;

--
-- Name: llm_prompt_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_prompt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.llm_prompt_id_seq OWNER TO postgres;

--
-- Name: llm_prompt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_prompt_id_seq OWNED BY public.llm_prompt.id;


--
-- Name: post; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.post (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    content text,
    summary text,
    published boolean,
    deleted boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    published_at timestamp without time zone,
    header_image_id integer,
    llm_metadata json,
    seo_metadata json,
    syndication_status json
);


ALTER TABLE public.post OWNER TO postgres;

--
-- Name: post_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.post_categories (
    post_id integer NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.post_categories OWNER TO postgres;

--
-- Name: post_development; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.post_development OWNER TO postgres;

--
-- Name: post_development_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.post_development_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_development_id_seq OWNER TO postgres;

--
-- Name: post_development_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.post_development_id_seq OWNED BY public.post_development.id;


--
-- Name: post_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.post_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_id_seq OWNER TO postgres;

--
-- Name: post_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.post_id_seq OWNED BY public.post.id;


--
-- Name: post_section; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.post_section (
    id integer NOT NULL,
    post_id integer NOT NULL,
    section_order integer,
    section_heading text,
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
    ideas_to_include text,
    facts_to_include text,
    image_prompt_example_id integer,
    generated_image_url character varying(512),
    image_generation_metadata json
);


ALTER TABLE public.post_section OWNER TO postgres;

--
-- Name: post_section_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.post_section_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_section_id_seq OWNER TO postgres;

--
-- Name: post_section_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.post_section_id_seq OWNED BY public.post_section.id;


--
-- Name: post_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.post_tags (
    post_id integer NOT NULL,
    tag_id integer NOT NULL
);


ALTER TABLE public.post_tags OWNER TO postgres;

--
-- Name: tag; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tag (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    slug character varying(50) NOT NULL,
    description text
);


ALTER TABLE public.tag OWNER TO postgres;

--
-- Name: tag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tag_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tag_id_seq OWNER TO postgres;

--
-- Name: tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tag_id_seq OWNED BY public.tag.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public."user" OWNER TO postgres;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO postgres;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
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
-- Name: category id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category ALTER COLUMN id SET DEFAULT nextval('public.category_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: image_format id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_format ALTER COLUMN id SET DEFAULT nextval('public.image_format_id_seq'::regclass);


--
-- Name: image_prompt_example id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_prompt_example ALTER COLUMN id SET DEFAULT nextval('public.image_prompt_example_id_seq'::regclass);


--
-- Name: image_setting id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_setting ALTER COLUMN id SET DEFAULT nextval('public.image_setting_id_seq'::regclass);


--
-- Name: image_style id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_style ALTER COLUMN id SET DEFAULT nextval('public.image_style_id_seq'::regclass);


--
-- Name: llm_action id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action ALTER COLUMN id SET DEFAULT nextval('public.llm_action_id_seq'::regclass);


--
-- Name: llm_action_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action_history ALTER COLUMN id SET DEFAULT nextval('public.llm_action_history_id_seq'::regclass);


--
-- Name: llm_config id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_config ALTER COLUMN id SET DEFAULT nextval('public.llm_config_id_seq'::regclass);


--
-- Name: llm_interaction id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_interaction ALTER COLUMN id SET DEFAULT nextval('public.llm_interaction_id_seq'::regclass);


--
-- Name: llm_prompt id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_prompt ALTER COLUMN id SET DEFAULT nextval('public.llm_prompt_id_seq'::regclass);


--
-- Name: post id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post ALTER COLUMN id SET DEFAULT nextval('public.post_id_seq'::regclass);


--
-- Name: post_development id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_development ALTER COLUMN id SET DEFAULT nextval('public.post_development_id_seq'::regclass);


--
-- Name: post_section id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_section ALTER COLUMN id SET DEFAULT nextval('public.post_section_id_seq'::regclass);


--
-- Name: tag id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag ALTER COLUMN id SET DEFAULT nextval('public.tag_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: workflow_status id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_status ALTER COLUMN id SET DEFAULT nextval('public.workflow_status_id_seq'::regclass);


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.category (id, name, slug, description) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image (id, filename, original_filename, path, alt_text, caption, image_prompt, notes, image_metadata, watermarked, watermarked_path, created_at, updated_at) FROM stdin;
139	kilt-evolution_header.jpg	\N	../../app/static/images/posts/kilt-evolution_header.jpg	Collage of kilt styles over the centuries.	The kilt has evolved constantly from its earliest origins.	Collage representing the evolution of the Scottish kilt through centuries, showing styles from early wraps to modern tailored kilts. Blend historical illustrations and photographic elements. Aspect ratio 16:9.	Initial header concept.	{"description": "Header image", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Collage representing the evolution of the Scottish kilt through centuries, showing styles from early wraps to modern tailored kilts. Blend historical illustrations and photographic elements. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_header.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_header.jpg", "uploaded_path_relative": "/blog/kilt-evolution_header.jpg"}, "metadata": {"alt": "Collage of kilt styles over the centuries.", "blog_caption": "The kilt has evolved constantly from its earliest origins."}, "syndication": {"instagram": {"status": "pending", "caption": "From battlefield necessity to global fashion icon! \\u2728 Explore the incredible journey of the Scottish kilt through the ages. #KiltHistory #ScottishFashion #Tartan #HighlandWear #Scotland #CelticStyle #MenswearEvolution", "hashtags": ["KiltHistory", "ScottishFashion", "Tartan", "HighlandWear", "Scotland", "CelticStyle", "MenswearEvolution"]}, "facebook": {"status": "pending", "caption": "Did you know the kilt evolved significantly over centuries? From the practical 'f\\u00e9ileadh m\\u00f2r' of the Highlands to a symbol of identity and even high fashion, its story is fascinating. Learn more about the evolution of this iconic garment on the blog! [Link Placeholder]"}}, "notes": "Initial header concept."}	f	\N	2025-05-18 16:25:20.645009	2025-05-18 16:25:20.645013
140	kilt-evolution_early-highland-dress.jpg	\N	../../app/static/images/posts/kilt-evolution_early-highland-dress.jpg	Pictish warrior in tunic and brat cloak on a cliff with standing stones.	Early Highland attire: A Pictish warrior embodying resilience in practical woollen tunic and cloak.	Illustration of an early Highlander (Pict or Gael) pre-16th century, wearing a simple woollen tunic ('léine') and brat cloak fastened with a brooch, standing in a rugged Highland landscape. Focus on practical, layered clothing. Historically accurate. Aspect ratio 16:9.	\N	{"description": "Early Forms of Highland Dress", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Illustration of an early Highlander (Pict or Gael) pre-16th century, wearing a simple woollen tunic ('l\\u00e9ine') and brat cloak fastened with a brooch, standing in a rugged Highland landscape. Focus on practical, layered clothing. Historically accurate. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_early-highland-dress.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_early-highland-dress.jpg", "uploaded_path_relative": "/blog/kilt-evolution_early-highland-dress.jpg"}, "metadata": {"alt": "Pictish warrior in tunic and brat cloak on a cliff with standing stones.", "blog_caption": "Early Highland attire: A Pictish warrior embodying resilience in practical woollen tunic and cloak."}, "syndication": {"instagram": {"status": "pending", "caption": "Before the familiar kilt: Early Highland dress prioritized practicality for rugged terrain. Think layered woollen tunics & cloaks! #HighlandHistory #AncientScotland #Picts #Gaels #ScottishClothing #CelticHistory", "hashtags": ["HighlandHistory", "AncientScotland", "Picts", "Gaels", "ScottishClothing", "CelticHistory"]}, "facebook": {"status": "pending", "caption": "Journey back before the 16th century! Early Highland attire focused on survival in rugged landscapes, featuring practical woollen tunics (l\\u00e9ine) and cloaks (brat). These garments laid the groundwork for later iconic styles. #ScottishHistory #CelticFashion"}}, "notes": null}	f	\N	2025-05-18 16:25:20.66228	2025-05-18 16:25:20.662283
141	kilt-evolution_great-kilt-origins.jpg	\N	../../app/static/images/posts/kilt-evolution_great-kilt-origins.jpg	16th-century Highlander pleating and belting a large féileadh mòr tartan wrap.	The versatile féileadh mòr: A 16th-century Highlander dons the great kilt for protection and practicality.	A 16th-century Highlander in a realistic setting, demonstrating how to pleat and belt the large 'féileadh mòr' (great kilt) made of several yards of tartan cloth. Focus on the process and the versatile nature of the garment. Historical accuracy in clothing and environment. Aspect ratio 16:9.	\N	{"description": "Origins of the Great Kilt", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "A 16th-century Highlander in a realistic setting, demonstrating how to pleat and belt the large 'f\\u00e9ileadh m\\u00f2r' (great kilt) made of several yards of tartan cloth. Focus on the process and the versatile nature of the garment. Historical accuracy in clothing and environment. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_great-kilt-origins.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_great-kilt-origins.jpg", "uploaded_path_relative": "/blog/kilt-evolution_great-kilt-origins.jpg"}, "metadata": {"alt": "16th-century Highlander pleating and belting a large f\\u00e9ileadh m\\u00f2r tartan wrap.", "blog_caption": "The versatile f\\u00e9ileadh m\\u00f2r: A 16th-century Highlander dons the great kilt for protection and practicality."}, "syndication": {"instagram": {"status": "pending", "caption": "Meet the F\\u00e9ileadh M\\u00f2r! The 16th-century 'great kilt' was a versatile marvel \\u2013 cloak by day, blanket by night. #GreatKilt #FeileadhMor #ScottishHistory #TartanTuesday #HighlandDress #Kilt", "hashtags": ["GreatKilt", "FeileadhMor", "ScottishHistory", "TartanTuesday", "HighlandDress", "Kilt"]}, "facebook": {"status": "pending", "caption": "The original 'Great Kilt' or F\\u00e9ileadh M\\u00f2r emerged in the 16th century. This single large piece of tartan was skillfully pleated and belted, serving multiple practical purposes for Highlanders. #ScottishHeritage #KiltEvolution #FeileadhMor"}}, "notes": null}	f	\N	2025-05-18 16:25:20.672373	2025-05-18 16:25:20.67238
142	kilt-evolution_great-kilt-significance.jpg	\N	../../app/static/images/posts/kilt-evolution_great-kilt-significance.jpg	17th-century MacLeod chief distributing tartan plaids to clansmen during a gathering.	Tartan as identity: A 17th-century clan chief reinforces kinship through the distribution of plaids.	Illustration depicting a 17th-century Highland clan chief, perhaps MacDonald or Campbell, distributing specific tartan plaids (féileadh mòr) to his loyal clansmen during an outdoor gathering. Emphasize the tartan patterns as symbols of identity and allegiance. Detailed historical attire and setting. Aspect ratio 16:9.	\N	{"description": "Cultural Significance of the Great Kilt", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Illustration depicting a 17th-century Highland clan chief, perhaps MacDonald or Campbell, distributing specific tartan plaids (f\\u00e9ileadh m\\u00f2r) to his loyal clansmen during an outdoor gathering. Emphasize the tartan patterns as symbols of identity and allegiance. Detailed historical attire and setting. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_great-kilt-significance.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_great-kilt-significance.jpg", "uploaded_path_relative": "/blog/kilt-evolution_great-kilt-significance.jpg"}, "metadata": {"alt": "17th-century MacLeod chief distributing tartan plaids to clansmen during a gathering.", "blog_caption": "Tartan as identity: A 17th-century clan chief reinforces kinship through the distribution of plaids."}, "syndication": {"instagram": {"status": "pending", "caption": "Tartan wasn't just fabric; it was identity! In the 17th century, specific patterns signified clan allegiance, like visual badges of honour. #ClanTartan #ScottishClans #HighlandCulture #TartanHistory #ScotlandIsNow", "hashtags": ["ClanTartan", "ScottishClans", "HighlandCulture", "TartanHistory", "ScotlandIsNow"]}, "facebook": {"status": "pending", "caption": "By the 17th century, tartan evolved into a powerful symbol of clan identity and loyalty. Chiefs distributed specific patterns, reinforcing kinship and social structure within the Highlands. #ScottishHistory #Tartan #ClanLife"}}, "notes": null}	f	\N	2025-05-18 16:25:20.68492	2025-05-18 16:25:20.684929
143	kilt-evolution_kilt-adaptations-practicality.jpg	\N	../../app/static/images/posts/kilt-evolution_kilt-adaptations-practicality.jpg	Highland hunter around 1700 tucking the upper part of his féileadh mòr into his belt.	Adapting for action: A Highland hunter modifies the great kilt for greater freedom of movement circa 1700.	Realistic depiction of a Highland hunter or soldier around the late 17th/early 18th century, actively tucking the upper shoulder plaid part of his féileadh mòr into his belt to create a more practical, skirt-like lower half for better movement. Show action or purpose (hunting/marching). Accurate historical detail. Aspect ratio 16:9.	\N	{"description": "Adaptations for Practicality", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Realistic depiction of a Highland hunter or soldier around the late 17th/early 18th century, actively tucking the upper shoulder plaid part of his f\\u00e9ileadh m\\u00f2r into his belt to create a more practical, skirt-like lower half for better movement. Show action or purpose (hunting/marching). Accurate historical detail. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_kilt-adaptations-practicality.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_kilt-adaptations-practicality.jpg", "uploaded_path_relative": "/blog/kilt-evolution_kilt-adaptations-practicality.jpg"}, "metadata": {"alt": "Highland hunter around 1700 tucking the upper part of his f\\u00e9ileadh m\\u00f2r into his belt.", "blog_caption": "Adapting for action: A Highland hunter modifies the great kilt for greater freedom of movement circa 1700."}, "syndication": {"instagram": {"status": "pending", "caption": "Adapting for action! Late 17th-century Highlanders started tucking away the top plaid of the great kilt for practicality, paving the way for the modern kilt form. #KiltEvolution #HighlandLife #ScottishHistory #Adaptation #FeileadhMor", "hashtags": ["KiltEvolution", "HighlandLife", "ScottishHistory", "Adaptation", "FeileadhMor"]}, "facebook": {"status": "pending", "caption": "Practicality drives change! As life demanded more dynamic movement, Highlanders began adapting the bulky F\\u00e9ileadh M\\u00f2r by tucking the upper plaid, a key step towards the 'small kilt' we know today. #ScottishInnovation #KiltHistory #HighlandDress"}}, "notes": null}	f	\N	2025-05-18 16:25:20.733539	2025-05-18 16:25:20.733566
144	kilt-evolution_small-kilt-emergence.jpg	\N	../../app/static/images/posts/kilt-evolution_small-kilt-emergence.jpg	18th-century ironworker wearing the knee-length féileadh beag (small kilt) while working at a forge.	The birth of the modern kilt: An ironworker demonstrates the practicality of the féileadh beag around 1720.	Scene in an early 18th-century Highland ironworks (around 1720s), showing workers wearing the newly developed 'féileadh beag' (small kilt) – the pre-pleated, knee-length skirt without the shoulder plaid. Focus on the practicality for industrial work, perhaps near a forge or furnace. Link to Thomas Rawlinson's innovation. Aspect ratio 16:9.	\N	{"description": "Emergence of the Small Kilt", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Scene in an early 18th-century Highland ironworks (around 1720s), showing workers wearing the newly developed 'f\\u00e9ileadh beag' (small kilt) \\u2013 the pre-pleated, knee-length skirt without the shoulder plaid. Focus on the practicality for industrial work, perhaps near a forge or furnace. Link to Thomas Rawlinson's innovation. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_small-kilt-emergence.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_small-kilt-emergence.jpg", "uploaded_path_relative": "/blog/kilt-evolution_small-kilt-emergence.jpg"}, "metadata": {"alt": "18th-century ironworker wearing the knee-length f\\u00e9ileadh beag (small kilt) while working at a forge.", "blog_caption": "The birth of the modern kilt: An ironworker demonstrates the practicality of the f\\u00e9ileadh beag around 1720."}, "syndication": {"instagram": {"status": "pending", "caption": "The modern kilt takes shape! Around 1720, the 'F\\u00e9ileadh Beag' or small kilt emerged, separating the pleated skirt from the shoulder plaid \\u2013 a practical evolution for workers and soldiers. #SmallKilt #FeileadhBeag #KiltHistory #ScottishInnovation #18thCentury", "hashtags": ["SmallKilt", "FeileadhBeag", "KiltHistory", "ScottishInnovation", "18thCentury"]}, "facebook": {"status": "pending", "caption": "Innovation corner: The early 18th century saw the emergence of the 'F\\u00e9ileadh Beag' (small kilt). Often credited to industrialist Thomas Rawlinson, this separated skirt design offered greater practicality, influencing kilt design forever. #KiltFacts #ScottishHeritage #IndustrialHistory"}}, "notes": null}	f	\N	2025-05-18 16:25:20.7398	2025-05-18 16:25:20.739809
145	kilt-evolution_highland-dress-suppression.jpg	\N	../../app/static/images/posts/kilt-evolution_highland-dress-suppression.jpg	Highland woman secretly weaving tartan by candlelight while Redcoats patrol outside, circa 1760.	Defiance in the shadows: Secretly weaving banned tartan during the Dress Act suppression (1746-1782).	Atmospheric, slightly clandestine scene inside a dimly lit Highland cottage, circa 1760. A determined Highland woman secretly weaves tartan on a small loom by candlelight, while the shadow of a patrolling Redcoat soldier is visible outside the window. Convey resilience and cultural defiance during the Dress Act (1746-1782). Aspect ratio 16:9.	\N	{"description": "Suppression of Highland Dress", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Atmospheric, slightly clandestine scene inside a dimly lit Highland cottage, circa 1760. A determined Highland woman secretly weaves tartan on a small loom by candlelight, while the shadow of a patrolling Redcoat soldier is visible outside the window. Convey resilience and cultural defiance during the Dress Act (1746-1782). Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_highland-dress-suppression.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_highland-dress-suppression.jpg", "uploaded_path_relative": "/blog/kilt-evolution_highland-dress-suppression.jpg"}, "metadata": {"alt": "Highland woman secretly weaving tartan by candlelight while Redcoats patrol outside, circa 1760.", "blog_caption": "Defiance in the shadows: Secretly weaving banned tartan during the Dress Act suppression (1746-1782)."}, "syndication": {"instagram": {"status": "pending", "caption": "A symbol forbidden! After Culloden, the Dress Act of 1746 banned tartan & kilts. But Highland culture persisted in secret acts of defiance, like weaving by candlelight. #DressAct #HighlandHistory #ScottishResilience #Tartan #Jacobite #ForbiddenFashion", "hashtags": ["DressAct", "HighlandHistory", "ScottishResilience", "Tartan", "Jacobite", "ForbiddenFashion"]}, "facebook": {"status": "pending", "caption": "A dark chapter: The Dress Act (1746-1782) aimed to suppress Highland culture by banning tartan and the kilt following the Jacobite rising. Yet, the spirit endured through acts of quiet defiance and cultural preservation. #WearWhatYouWant #ScottishHistory #CulturalSuppression #Resilience"}}, "notes": null}	f	\N	2025-05-18 16:25:20.743851	2025-05-18 16:25:20.74387
146	kilt-evolution_romantic-revival-renaissance.jpg	\N	../../app/static/images/posts/kilt-evolution_romantic-revival-renaissance.jpg	Sir Walter Scott in Royal Stewart tartan leading nobles during King George IV's 1822 Edinburgh visit.	Romantic revival: Sir Walter Scott orchestrates a tartan spectacle for King George IV in 1822 Edinburgh.	Grand, celebratory scene depicting Sir Walter Scott, adorned in prominent Royal Stewart tartan, orchestrating the 1822 visit of King George IV to Edinburgh. Show Lowland nobles, previously dismissive, now wearing kilts and tartan. Highlight the pageantry and romanticism transforming the kilt's image. Accurate depiction of Holyrood Palace or Edinburgh setting. Aspect ratio 16:9.	\N	{"description": "Romantic Revival and Cultural Renaissance", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Grand, celebratory scene depicting Sir Walter Scott, adorned in prominent Royal Stewart tartan, orchestrating the 1822 visit of King George IV to Edinburgh. Show Lowland nobles, previously dismissive, now wearing kilts and tartan. Highlight the pageantry and romanticism transforming the kilt's image. Accurate depiction of Holyrood Palace or Edinburgh setting. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_romantic-revival-renaissance.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_romantic-revival-renaissance.jpg", "uploaded_path_relative": "/blog/kilt-evolution_romantic-revival-renaissance.jpg"}, "metadata": {"alt": "Sir Walter Scott in Royal Stewart tartan leading nobles during King George IV's 1822 Edinburgh visit.", "blog_caption": "Romantic revival: Sir Walter Scott orchestrates a tartan spectacle for King George IV in 1822 Edinburgh."}, "syndication": {"instagram": {"status": "pending", "caption": "Tartan's big comeback! Thanks to Sir Walter Scott & King George IV's 1822 visit, the kilt was reborn in a wave of romantic revival, transforming into a symbol of Scottish identity & pageantry. #TartanRevival #SirWalterScott #RoyalVisit #ScottishRomanticism #KiltStyle", "hashtags": ["TartanRevival", "SirWalterScott", "RoyalVisit", "ScottishRomanticism", "KiltStyle", "19thCentury"]}, "facebook": {"status": "pending", "caption": "From suppression to spectacle! The late 18th and 19th centuries saw a Romantic revival of Highland culture, heavily influenced by writers like Sir Walter Scott and cemented by King George IV's famous 1822 visit to Edinburgh, where tartan took centre stage. #ScottishRenaissance #KiltHistory #Romanticism #WalterScott"}}, "notes": null}	f	\N	2025-05-18 16:25:20.750491	2025-05-18 16:25:20.750495
147	kilt-evolution_military-adoption-influence.jpg	\N	../../app/static/images/posts/kilt-evolution_military-adoption-influence.jpg	Black Watch soldier in government sett kilt charging across a WWI battlefield with a bagpiper.	Courage in tartan: A Black Watch soldier embodies the kilt's military legacy during World War I.	Dynamic, gritty scene from a World War I battlefield (e.g., Western Front). A determined Black Watch soldier in his dark Government Sett kilt advances, perhaps alongside a piper. Convey the juxtaposition of traditional Highland dress in modern warfare, emphasizing bravery and regimental pride. Aspect ratio 16:9.	\N	{"description": "Military Adoption and Global Influence", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Dynamic, gritty scene from a World War I battlefield (e.g., Western Front). A determined Black Watch soldier in his dark Government Sett kilt advances, perhaps alongside a piper. Convey the juxtaposition of traditional Highland dress in modern warfare, emphasizing bravery and regimental pride. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_military-adoption-influence.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_military-adoption-influence.jpg", "uploaded_path_relative": "/blog/kilt-evolution_military-adoption-influence.jpg"}, "metadata": {"alt": "Black Watch soldier in government sett kilt charging across a WWI battlefield with a bagpiper.", "blog_caption": "Courage in tartan: A Black Watch soldier embodies the kilt's military legacy during World War I."}, "syndication": {"instagram": {"status": "pending", "caption": "Courage in tartan! Highland regiments like the Black Watch famously wore kilts into battle, becoming global symbols of Scottish bravery and identity, even on WW1 fields. #HighlandRegiment #BlackWatch #MilitaryKilt #ScottishSoldier #WWI #Courage", "hashtags": ["HighlandRegiment", "BlackWatch", "MilitaryKilt", "ScottishSoldier", "WWI", "Courage"]}, "facebook": {"status": "pending", "caption": "The kilt went global largely thanks to its adoption by the British Army's Highland regiments. Their distinct tartans and battlefield bravery, from Napoleonic Wars to WWI, made the kilt an internationally recognized symbol. #MilitaryHistory #ScottishRegiments #Kilt #Tartan"}}, "notes": null}	f	\N	2025-05-18 16:25:20.752153	2025-05-18 16:25:20.752156
148	kilt-evolution_formal-everyday-attire.jpg	\N	../../app/static/images/posts/kilt-evolution_formal-everyday-attire.jpg	1950s Scottish wedding scene with groom in Prince Charlie kilt outfit and guests dancing a ceilidh.	From battlefield to ballroom: Kilts become central to 20th-century formal and celebratory wear.	Joyful, slightly nostalgic scene of a Scottish wedding reception or ceilidh in the 1950s/60s. Focus on guests wearing kilts (e.g., Prince Charlie outfits) for formal celebration, dancing, and socializing. Capture the post-war popularization of the kilt for non-military formal events. Aspect ratio 16:9.	\N	{"description": "Kilts in Formal and Everyday Attire", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "Joyful, slightly nostalgic scene of a Scottish wedding reception or ceilidh in the 1950s/60s. Focus on guests wearing kilts (e.g., Prince Charlie outfits) for formal celebration, dancing, and socializing. Capture the post-war popularization of the kilt for non-military formal events. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_formal-everyday-attire.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_formal-everyday-attire.jpg", "uploaded_path_relative": "/blog/kilt-evolution_formal-everyday-attire.jpg"}, "metadata": {"alt": "1950s Scottish wedding scene with groom in Prince Charlie kilt outfit and guests dancing a ceilidh.", "blog_caption": "From battlefield to ballroom: Kilts become central to 20th-century formal and celebratory wear."}, "syndication": {"instagram": {"status": "pending", "caption": "From battlefield to ballroom! Post-WWII, the kilt became a staple of formal wear for weddings, ceilidhs, and celebrations, solidifying its place in 20th-century Scottish social life. #KiltOutfit #Ceilidh #ScottishWedding #FormalWear #VintageScotland #PrinceCharlie", "hashtags": ["KiltOutfit", "Ceilidh", "ScottishWedding", "FormalWear", "VintageScotland", "PrinceCharlie"]}, "facebook": {"status": "pending", "caption": "The 20th century saw the kilt firmly established as celebratory wear. Popularised by returning soldiers and embraced by the diaspora, it became synonymous with Scottish weddings, formal events, and cultural pride. #ScottishCulture #KiltStyle #20thCenturyFashion"}}, "notes": null}	f	\N	2025-05-18 16:25:20.753736	2025-05-18 16:25:20.753738
149	kilt-evolution_modern-innovations-fashion.jpg	\N	../../app/static/images/posts/kilt-evolution_modern-innovations-fashion.jpg	Gender-fluid model on a neon runway wearing a deconstructed, futuristic tartan kilt.	The kilt reimagined: 21st-century fashion fuses tartan tradition with avant-garde and inclusive design.	High-fashion runway scene featuring a model (could be gender-fluid) wearing a modern, avant-garde kilt interpretation. Think unconventional materials (leather, denim, tech fabrics), deconstructed design, or bold contemporary tartan patterns. Emphasize the fusion of tradition and modern fashion trends, challenging norms. Dynamic lighting and runway setting. Aspect ratio 16:9.	\N	{"description": "Modern Innovations and Fashion Trends", "status": "approved", "prompt_status": "complete", "generation_status": "complete", "watermark_status": "pending", "prompt": "High-fashion runway scene featuring a model (could be gender-fluid) wearing a modern, avant-garde kilt interpretation. Think unconventional materials (leather, denim, tech fabrics), deconstructed design, or bold contemporary tartan patterns. Emphasize the fusion of tradition and modern fashion trends, challenging norms. Dynamic lighting and runway setting. Aspect ratio 16:9.", "source_details": {"filename_local": "kilt-evolution_modern-innovations-fashion.jpg", "post_slug": "kilt-evolution", "local_dir": "/images/posts/kilt-evolution/", "public_url": "https://static.clan.com/media/blog/kilt-evolution_modern-innovations-fashion.jpg", "uploaded_path_relative": "/blog/kilt-evolution_modern-innovations-fashion.jpg"}, "metadata": {"alt": "Gender-fluid model on a neon runway wearing a deconstructed, futuristic tartan kilt.", "blog_caption": "The kilt reimagined: 21st-century fashion fuses tartan tradition with avant-garde and inclusive design."}, "syndication": {"instagram": {"status": "pending", "caption": "The kilt, but make it fashion! \\u26a1\\ufe0f Today's designers reimagine tartan and the kilt form with modern materials, cuts, and a challenge to traditional norms. Tradition meets runway! #ModernKilt #TartanFashion #AvantGarde #ScottishDesign #FashionForward #Inclusivity", "hashtags": ["ModernKilt", "TartanFashion", "AvantGarde", "ScottishDesign", "FashionForward", "Inclusivity", "RunwayStyle"]}, "facebook": {"status": "pending", "caption": "The kilt continues to evolve! 21st-century fashion embraces the kilt, experimenting with new materials, challenging gender norms, and blending streetwear influences with heritage. What do you think of modern kilt designs? #Kilt #FashionTrends #ScottishStyle #ContemporaryDesign"}}, "notes": null}	f	\N	2025-05-18 16:25:20.755153	2025-05-18 16:25:20.755155
150	quaich-traditions_header-collage.jpg	\N	../../app/static/images/posts/quaich-traditions_header-collage.jpg	A collection of various Scottish quaichs from different eras	The Scottish Quaich: A journey through history, tradition, and symbolism.	A collection of various Scottish quaichs from different eras – wood, pewter, silver – arranged artistically on a background of subtle tartan, representing the scope of the article. Soft, inviting lighting. Aspect ratio 16:9.	Needs final image generation.	{"description": "Header image", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A collection of various Scottish quaichs from different eras \\u2013 wood, pewter, silver \\u2013 arranged artistically on a background of subtle tartan, representing the scope of the article. Soft, inviting lighting. Aspect ratio 16:9.", "source_details": {"filename_local": "quaich-traditions_header-collage.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_header-collage.jpg", "uploaded_path_relative": "/blog/quaich-traditions_header-collage.jpg"}, "metadata": {"alt": "A collection of various Scottish quaichs from different eras", "blog_caption": "The Scottish Quaich: A journey through history, tradition, and symbolism."}, "syndication": {"instagram": {"status": "pending", "caption": "Sl\\u00e0inte! Exploring the rich history of the Scottish Quaich, the 'cup of friendship'. From clans to kings to modern weddings. #Quaich #ScottishTradition #CupOfFriendship #Celtic #Scotland #History", "hashtags": ["Quaich", "ScottishTradition", "CupOfFriendship", "Celtic", "Scotland", "History", "Pewter", "Silver"]}, "facebook": {"status": "pending", "caption": "What is a Quaich? Discover the story behind Scotland's traditional two-handled 'cup of friendship', a symbol of hospitality and trust for centuries. Learn more on the blog! [Link Placeholder]"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.756573	2025-05-18 16:25:20.756575
151	quaich-traditions_early-origins-wooden.jpg	\N	../../app/static/images/posts/quaich-traditions_early-origins-wooden.jpg	Early hand-carved wooden quaich by a hearth	A simple wooden quaich reflects early Highland values of peace and trust.	A rustic medieval Scottish setting depicting a simple, hand-carved wooden quaich resting on a rough wooden table near a warm, stone-built hearth. Early Scottish Highlanders gather around in traditional tartan cloaks, symbolically exchanging the quaich to represent friendship, trust, and peace. Include warm, candlelit tones and accurate historical details of Highland clothing and furnishings.	Needs final image generation.	{"description": "Early Origins", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A rustic medieval Scottish setting depicting a simple, hand-carved wooden quaich resting on a rough wooden table near a warm, stone-built hearth. Early Scottish Highlanders gather around in traditional tartan cloaks, symbolically exchanging the quaich to represent friendship, trust, and peace. Include warm, candlelit tones and accurate historical details of Highland clothing and furnishings.", "source_details": {"filename_local": "quaich-traditions_early-origins-wooden.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_early-origins-wooden.jpg", "uploaded_path_relative": "/blog/quaich-traditions_early-origins-wooden.jpg"}, "metadata": {"alt": "Early hand-carved wooden quaich by a hearth", "blog_caption": "A simple wooden quaich reflects early Highland values of peace and trust."}, "syndication": {"instagram": {"status": "pending", "caption": "Back to basics! Early Scottish quaichs were often carved from wood, symbolising peace & trust. The two handles meant no hidden weapons! #Quaich #MedievalScotland #Woodworking #CelticHistory #ScottishCraft", "hashtags": ["Quaich", "MedievalScotland", "Woodworking", "CelticHistory", "ScottishCraft"]}, "facebook": {"status": "pending", "caption": "The origins of the Quaich lie in medieval Scotland, often crafted from simple wood or horn. Its unique two-handled design was practical - promoting trust during shared drinks. #ScottishHistory #QuaichFacts #CelticTradition"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.757773	2025-05-18 16:25:20.757775
152	quaich-traditions_clan-unity-hospitality.jpg	\N	../../app/static/images/posts/quaich-traditions_clan-unity-hospitality.jpg	Clan chieftain toasts with a quaich at a 17th-century Highland gathering	The quaich: central to clan gatherings, fostering unity and hospitality.	A vibrant scene at a Scottish Highland clan gathering in the 17th century. At its center, a clan chieftain raises an ornately carved wooden quaich in a ceremonial toast surrounded by warriors, elders, and clansfolk in historically accurate clan tartans. Emphasize expressions of unity, pride, and camaraderie, with detailed Highland attire, symbolic banners, and traditional Celtic decor.	Needs final image generation.	{"description": "Clan Unity and Hospitality", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A vibrant scene at a Scottish Highland clan gathering in the 17th century. At its center, a clan chieftain raises an ornately carved wooden quaich in a ceremonial toast surrounded by warriors, elders, and clansfolk in historically accurate clan tartans. Emphasize expressions of unity, pride, and camaraderie, with detailed Highland attire, symbolic banners, and traditional Celtic decor.", "source_details": {"filename_local": "quaich-traditions_clan-unity-hospitality.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_clan-unity-hospitality.jpg", "uploaded_path_relative": "/blog/quaich-traditions_clan-unity-hospitality.jpg"}, "metadata": {"alt": "Clan chieftain toasts with a quaich at a 17th-century Highland gathering", "blog_caption": "The quaich: central to clan gatherings, fostering unity and hospitality."}, "syndication": {"instagram": {"status": "pending", "caption": "A symbol of unity! The quaich was essential at Highland clan gatherings, shared to build trust and celebrate together. #ClanLife #ScottishGathering #Quaich #HighlandCulture #Scotland", "hashtags": ["ClanLife", "ScottishGathering", "Quaich", "HighlandCulture", "Scotland", "Hospitality"]}, "facebook": {"status": "pending", "caption": "More than just a cup! In clan gatherings, sharing the quaich was a powerful ritual signifying mutual respect, resolving conflicts, and celebrating together. #ScottishTradition #ClanUnity #QuaichHistory"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.759154	2025-05-18 16:25:20.759155
153	quaich-traditions_design-evolution.jpg	\N	../../app/static/images/posts/quaich-traditions_design-evolution.jpg	Collection showing quaich evolution from wood to ornate silver	From simple wood to intricate silver: the evolution of quaich craftsmanship.	A beautifully detailed illustration showcasing the historical progression of Scottish quaich designs from simple wooden and horn quaichs to intricately crafted silver and pewter versions. Depict various examples arranged chronologically on an antique Scottish tartan cloth, clearly highlighting evolving craftsmanship, materials, decorative Celtic motifs, and engraved patterns.	Needs final image generation.	{"description": "Evolution of Design", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A beautifully detailed illustration showcasing the historical progression of Scottish quaich designs from simple wooden and horn quaichs to intricately crafted silver and pewter versions. Depict various examples arranged chronologically on an antique Scottish tartan cloth, clearly highlighting evolving craftsmanship, materials, decorative Celtic motifs, and engraved patterns.", "source_details": {"filename_local": "quaich-traditions_design-evolution.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_design-evolution.jpg", "uploaded_path_relative": "/blog/quaich-traditions_design-evolution.jpg"}, "metadata": {"alt": "Collection showing quaich evolution from wood to ornate silver", "blog_caption": "From simple wood to intricate silver: the evolution of quaich craftsmanship."}, "syndication": {"instagram": {"status": "pending", "caption": "Watch the quaich evolve! From humble wood & horn to elegant pewter & stunning silver adorned with Celtic designs. Scottish craftsmanship through the ages. #ScottishCraftsmanship #Quaich #DesignHistory #CelticArt #Pewter #Silver #Scotland", "hashtags": ["ScottishCraftsmanship", "Quaich", "DesignHistory", "CelticArt", "Pewter", "Silver", "Scotland", "Antiques"]}, "facebook": {"status": "pending", "caption": "The design of the quaich tells a story of evolving craftsmanship. Starting with wood, techniques like stave-building emerged, followed by luxurious silver and popular pewter versions, often featuring beautiful Celtic details. #QuaichDesign #ScottishArtisans #CelticDesign"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.760527	2025-05-18 16:25:20.760528
154	quaich-traditions_wedding-ceremony.jpg	\N	../../app/static/images/posts/quaich-traditions_wedding-ceremony.jpg	Couple sharing whisky from a quaich during their Scottish wedding	A central part of Scottish weddings, the quaich seals the couple's commitment.	A warmly lit, intimate depiction of a traditional Scottish wedding ceremony set in a rustic Highland chapel or castle. A bride and groom in traditional Scottish wedding attire (kilt and dress) joyfully share whisky from an ornate silver quaich. Family and friends surround them, smiling and celebrating, highlighting the quaich’s role as a symbol of shared joy and commitment.	Needs final image generation.	{"description": "The Quaich in Ceremony and Celebration", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A warmly lit, intimate depiction of a traditional Scottish wedding ceremony set in a rustic Highland chapel or castle. A bride and groom in traditional Scottish wedding attire (kilt and dress) joyfully share whisky from an ornate silver quaich. Family and friends surround them, smiling and celebrating, highlighting the quaich\\u2019s role as a symbol of shared joy and commitment.", "source_details": {"filename_local": "quaich-traditions_wedding-ceremony.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_wedding-ceremony.jpg", "uploaded_path_relative": "/blog/quaich-traditions_wedding-ceremony.jpg"}, "metadata": {"alt": "Couple sharing whisky from a quaich during their Scottish wedding", "blog_caption": "A central part of Scottish weddings, the quaich seals the couple's commitment."}, "syndication": {"instagram": {"status": "pending", "caption": "Sealing the vows with a sip! The quaich is a beautiful tradition in Scottish weddings, symbolizing the couple's commitment to share life's journey together. \\u2764\\ufe0f #ScottishWedding #WeddingTradition #QuaichCeremony #CupOfFriendship #LoveAndWhisky", "hashtags": ["ScottishWedding", "WeddingTradition", "QuaichCeremony", "CupOfFriendship", "LoveAndWhisky", "CelticWedding"]}, "facebook": {"status": "pending", "caption": "From weddings and births to farewells, the quaich has long marked significant life events in Scotland, symbolizing shared moments and collective memory. The wedding ceremony is a particularly cherished tradition. #ScottishCustoms #Quaich #LifeEvents #WeddingIdeas"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.761794	2025-05-18 16:25:20.761795
155	quaich-traditions_royal-gift.jpg	\N	../../app/static/images/posts/quaich-traditions_royal-gift.jpg	King James VI presenting an ornate silver quaich as a gift	Royal approval: King James VI gifting a quaich highlights its diplomatic importance.	A historically accurate and majestic scene from the Scottish royal court in the late 16th century, showing King James VI presenting a luxurious, intricately decorated silver quaich as a diplomatic gift to a visiting dignitary. Include richly detailed period costumes, royal regalia, ornate throne setting, and realistic expressions conveying goodwill and diplomacy.	Needs final image generation.	{"description": "Quaich and Royal Connections", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A historically accurate and majestic scene from the Scottish royal court in the late 16th century, showing King James VI presenting a luxurious, intricately decorated silver quaich as a diplomatic gift to a visiting dignitary. Include richly detailed period costumes, royal regalia, ornate throne setting, and realistic expressions conveying goodwill and diplomacy.", "source_details": {"filename_local": "quaich-traditions_royal-gift.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_royal-gift.jpg", "uploaded_path_relative": "/blog/quaich-traditions_royal-gift.jpg"}, "metadata": {"alt": "King James VI presenting an ornate silver quaich as a gift", "blog_caption": "Royal approval: King James VI gifting a quaich highlights its diplomatic importance."}, "syndication": {"instagram": {"status": "pending", "caption": "Fit for a king! \\ud83d\\udc51 Scottish monarchs like James VI used the quaich as a significant gift, cementing alliances and showcasing Scottish hospitality to royalty and dignitaries. #RoyalScotland #KingJamesVI #Quaich #DiplomaticGift #ScottishHistory #Silverware", "hashtags": ["RoyalScotland", "KingJamesVI", "Quaich", "DiplomaticGift", "ScottishHistory", "Silverware", "16thCentury"]}, "facebook": {"status": "pending", "caption": "The quaich's influence reached the highest courts. King James VI famously gifted quaichs, and later royal visits by Queen Victoria helped solidify its status as a treasured symbol of Scottish heritage recognised by royalty. #ScottishRoyalty #QuaichHistory #HistoricalObjects"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.763497	2025-05-18 16:25:20.763499
156	quaich-traditions_whisky-pairing.jpg	\N	../../app/static/images/posts/quaich-traditions_whisky-pairing.jpg	Pewter quaich filled with whisky resting on an oak barrel	A perfect pairing: The quaich often held whisky, Scotland's famous spirit.	A cozy, authentic Scottish scene inside a historical whisky distillery tasting room. A polished pewter quaich, prominently placed on an oak barrel, holds golden whisky illuminated warmly by natural window light. Surround it with whisky bottles, barley sheaves, and rustic distillery equipment, highlighting the timeless Scottish pairing of quaich and whisky.	Needs final image generation.	{"description": "Quaich Traditions and Whisky", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A cozy, authentic Scottish scene inside a historical whisky distillery tasting room. A polished pewter quaich, prominently placed on an oak barrel, holds golden whisky illuminated warmly by natural window light. Surround it with whisky bottles, barley sheaves, and rustic distillery equipment, highlighting the timeless Scottish pairing of quaich and whisky.", "source_details": {"filename_local": "quaich-traditions_whisky-pairing.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_whisky-pairing.jpg", "uploaded_path_relative": "/blog/quaich-traditions_whisky-pairing.jpg"}, "metadata": {"alt": "Pewter quaich filled with whisky resting on an oak barrel", "blog_caption": "A perfect pairing: The quaich often held whisky, Scotland's famous spirit."}, "syndication": {"instagram": {"status": "pending", "caption": "Name a more iconic duo... \\ud83d\\ude09 The quaich and Scotch whisky! Sharing a dram from the 'cup of friendship' is a cornerstone of Scottish hospitality. Sl\\u00e0inte! \\ud83e\\udd43 #QuaichAndWhisky #ScotchWhisky #ScottishHospitality #WhiskyTasting #Slainte #Scotland #Distillery", "hashtags": ["QuaichAndWhisky", "ScotchWhisky", "ScottishHospitality", "WhiskyTasting", "Slainte", "Scotland", "Distillery", "Pewter"]}, "facebook": {"status": "pending", "caption": "What's traditionally served in a quaich? Often, it's Scotland's national drink \\u2013 whisky! This pairing enhances the symbolism of warmth and welcome, a tradition often kept alive in distilleries today. #WhiskyFacts #Quaich #ScottishDrinks #Hospitality"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.764825	2025-05-18 16:25:20.764827
157	quaich-traditions_decline-revival.jpg	\N	../../app/static/images/posts/quaich-traditions_decline-revival.jpg	Split image showing a stored quaich vs. one used in a modern festival	From quiet preservation during decline to vibrant celebration in its revival.	An evocative illustration symbolizing both cultural decline and revival. On one side, a shadowed Scottish Highland cottage interior with a simple wooden quaich stored carefully on a shelf, symbolizing suppressed cultural traditions during the 18th-century Highland Clearances. On the other, bright revival imagery showcasing Scottish pride with restored quaich traditions amid Highland festivals and celebrations in vivid tartan colors.	Needs final image generation.	{"description": "Cultural Decline and Revival", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "An evocative illustration symbolizing both cultural decline and revival. On one side, a shadowed Scottish Highland cottage interior with a simple wooden quaich stored carefully on a shelf, symbolizing suppressed cultural traditions during the 18th-century Highland Clearances. On the other, bright revival imagery showcasing Scottish pride with restored quaich traditions amid Highland festivals and celebrations in vivid tartan colors.", "source_details": {"filename_local": "quaich-traditions_decline-revival.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_decline-revival.jpg", "uploaded_path_relative": "/blog/quaich-traditions_decline-revival.jpg"}, "metadata": {"alt": "Split image showing a stored quaich vs. one used in a modern festival", "blog_caption": "From quiet preservation during decline to vibrant celebration in its revival."}, "syndication": {"instagram": {"status": "pending", "caption": "A story of resilience! \\ud83d\\udd25 Though Highland culture faced suppression, traditions like the quaich persisted quietly, ready for a vibrant revival in later centuries. #CulturalRevival #ScottishResilience #Quaich #HighlandHistory #Jacobite #ScotlandStrong", "hashtags": ["CulturalRevival", "ScottishResilience", "Quaich", "HighlandHistory", "Jacobite", "ScotlandStrong"]}, "facebook": {"status": "pending", "caption": "Like many aspects of Highland culture, the quaich faced decline during periods of upheaval. But the tradition was preserved and saw a strong revival, becoming a cherished national symbol once again. #ScottishHeritage #CulturalHistory #Revival"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.766249	2025-05-18 16:25:20.766251
158	quaich-traditions_contemporary-culture.jpg	\N	../../app/static/images/posts/quaich-traditions_contemporary-culture.jpg	Modern couple celebrating with a silver quaich at their wedding	The quaich tradition lives on in contemporary Scottish celebrations like weddings.	A cheerful, contemporary Scottish wedding reception scene in a modern venue with subtle traditional touches. A couple dressed in modern formal attire joyfully holds a sleek, polished silver quaich, capturing a modern continuation of the ancient tradition. Guests celebrate in the background, showing the quaich’s enduring symbolism of unity and friendship.	Needs final image generation.	{"description": "The Quaich in Contemporary Scottish Culture", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A cheerful, contemporary Scottish wedding reception scene in a modern venue with subtle traditional touches. A couple dressed in modern formal attire joyfully holds a sleek, polished silver quaich, capturing a modern continuation of the ancient tradition. Guests celebrate in the background, showing the quaich\\u2019s enduring symbolism of unity and friendship.", "source_details": {"filename_local": "quaich-traditions_contemporary-culture.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_contemporary-culture.jpg", "uploaded_path_relative": "/blog/quaich-traditions_contemporary-culture.jpg"}, "metadata": {"alt": "Modern couple celebrating with a silver quaich at their wedding", "blog_caption": "The quaich tradition lives on in contemporary Scottish celebrations like weddings."}, "syndication": {"instagram": {"status": "pending", "caption": "Tradition endures! The quaich remains a beloved part of modern Scottish life, especially at weddings, anniversaries, and as meaningful gifts connecting Scots worldwide to their heritage. #ModernScotland #ScottishTradition #Quaich #WeddingGift #Heritage #FamilyHeirloom", "hashtags": ["ModernScotland", "ScottishTradition", "Quaich", "WeddingGift", "Heritage", "FamilyHeirloom", "Diaspora"]}, "facebook": {"status": "pending", "caption": "The quaich isn't just history! It's actively used in contemporary Scottish culture, especially weddings, and cherished as gifts and connections to ancestry by Scots around the globe. #LivingTradition #ScottishCultureToday #QuaichLove"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.767514	2025-05-18 16:25:20.767515
159	quaich-traditions_modern-diplomacy.jpg	\N	../../app/static/images/posts/quaich-traditions_modern-diplomacy.jpg	Scottish official presenting an engraved quaich to a diplomat	A modern symbol of goodwill: The quaich used in international diplomacy.	A formal diplomatic ceremony at a modern Scottish government building or historic site, showing a Scottish official warmly presenting a gleaming, engraved quaich to an international representative. Capture respectful, friendly interactions, modern business attire, official flags, and expressions conveying genuine goodwill, emphasizing the quaich’s role in contemporary diplomacy.	Needs final image generation.	{"description": "Quaich as a Modern Symbol of Friendship and Diplomacy", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A formal diplomatic ceremony at a modern Scottish government building or historic site, showing a Scottish official warmly presenting a gleaming, engraved quaich to an international representative. Capture respectful, friendly interactions, modern business attire, official flags, and expressions conveying genuine goodwill, emphasizing the quaich\\u2019s role in contemporary diplomacy.", "source_details": {"filename_local": "quaich-traditions_modern-diplomacy.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_modern-diplomacy.jpg", "uploaded_path_relative": "/blog/quaich-traditions_modern-diplomacy.jpg"}, "metadata": {"alt": "Scottish official presenting an engraved quaich to a diplomat", "blog_caption": "A modern symbol of goodwill: The quaich used in international diplomacy."}, "syndication": {"instagram": {"status": "pending", "caption": "Scotland's cup of friendship goes global! \\ud83e\\udd1d Today, the quaich is often presented as a diplomatic gift, symbolising goodwill, mutual respect, and partnership on the international stage. #ScottishDiplomacy #Quaich #FriendshipCup #InternationalRelations #ScotlandTheWorld", "hashtags": ["ScottishDiplomacy", "Quaich", "FriendshipCup", "InternationalRelations", "ScotlandTheWorld", "GlobalScot"]}, "facebook": {"status": "pending", "caption": "From clan symbol to international gesture! The quaich is now frequently used in modern diplomacy by Scottish leaders to represent friendship and build connections across borders. #Symbolism #ScotlandOnTheWorldStage #Diplomacy"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.768814	2025-05-18 16:25:20.768816
160	quaich-traditions_collecting-quaichs.jpg	\N	../../app/static/images/posts/quaich-traditions_collecting-quaichs.jpg	Museum display showing a collection of antique and modern quaichs	Prized by collectors: Antique and modern quaichs displayed in a museum setting.	A museum-quality display illustrating various antique and modern quaichs arranged meticulously within a glass showcase in a Scottish cultural heritage museum. Quaichs range from antique silver pieces adorned with intricate Celtic engraving to contemporary minimalist designs, accurately reflecting different historical periods. Include subtle museum lighting to emphasize craftsmanship and cultural value.	Needs final image generation.	{"description": "Collecting Quaichs", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A museum-quality display illustrating various antique and modern quaichs arranged meticulously within a glass showcase in a Scottish cultural heritage museum. Quaichs range from antique silver pieces adorned with intricate Celtic engraving to contemporary minimalist designs, accurately reflecting different historical periods. Include subtle museum lighting to emphasize craftsmanship and cultural value.", "source_details": {"filename_local": "quaich-traditions_collecting-quaichs.jpg", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": "https://static.clan.com/media/blog/quaich-traditions_collecting-quaichs.jpg", "uploaded_path_relative": "/blog/quaich-traditions_collecting-quaichs.jpg"}, "metadata": {"alt": "Museum display showing a collection of antique and modern quaichs", "blog_caption": "Prized by collectors: Antique and modern quaichs displayed in a museum setting."}, "syndication": {"instagram": {"status": "pending", "caption": "Collecting history! Antique silver quaichs are highly sought after, while modern artisans keep the tradition alive with new designs. A beautiful blend of heritage and craft. #QuaichCollecting #AntiqueSilver #ScottishAntiques #ModernCraft #MuseumDisplay #Collectible", "hashtags": ["QuaichCollecting", "AntiqueSilver", "ScottishAntiques", "ModernCraft", "MuseumDisplay", "Collectible", "CelticArt"]}, "facebook": {"status": "pending", "caption": "Quaichs are not just functional; they're collectible works of art! From historic silver pieces to contemporary designs, they represent centuries of Scottish craftsmanship and culture. #ScottishCollectibles #Quaich #ArtHistory #Craftsmanship"}}, "notes": "Needs final image generation."}	f	\N	2025-05-18 16:25:20.770783	2025-05-18 16:25:20.770784
161	quaich-traditions_enduring-legacy.png	\N	../../app/static/images/posts/quaich-traditions_enduring-legacy.png	Hands of different generations holding a silver quaich against Highland scenery	The enduring power of the quaich, passed through generations.	A visually poetic image symbolizing the enduring legacy and cultural power of the quaich, featuring an elegant silver quaich gently held by hands of different generations—a child’s hand alongside an older adult’s—set against a softly blurred backdrop of Scottish Highlands scenery. This serene image highlights unity, heritage, and continuity through generations.	Needs final image generation for conclusion.	{"description": "Conclusion", "status": "pending_review", "prompt_status": "complete", "generation_status": "pending", "watermark_status": "pending", "prompt": "A visually poetic image symbolizing the enduring legacy and cultural power of the quaich, featuring an elegant silver quaich gently held by hands of different generations\\u2014a child\\u2019s hand alongside an older adult\\u2019s\\u2014set against a softly blurred backdrop of Scottish Highlands scenery. This serene image highlights unity, heritage, and continuity through generations.", "source_details": {"filename_local": "quaich-traditions_enduring-legacy.png", "post_slug": "quaich-traditions", "local_dir": "/images/posts/quaich-traditions/", "public_url": null, "uploaded_path_relative": null}, "metadata": {"alt": "Hands of different generations holding a silver quaich against Highland scenery", "blog_caption": "The enduring power of the quaich, passed through generations."}, "syndication": {"instagram": {"status": "pending", "caption": "Generations united by tradition. The Scottish quaich endures as a powerful symbol of friendship, hospitality, and cultural continuity. A legacy held in hand. #EnduringLegacy #ScottishHeritage #Quaich #FamilyTradition #Generations #Scotland", "hashtags": ["EnduringLegacy", "ScottishHeritage", "Quaich", "FamilyTradition", "Generations", "Scotland", "Symbol"]}, "facebook": {"status": "pending", "caption": "The quaich's journey reflects Scotland's own story. From practical cup to cherished emblem, it continues to connect generations through its simple, powerful message of unity and goodwill. #ScottishTradition #Quaich #Legacy #Friendship"}}, "notes": "Needs final image generation for conclusion."}	f	\N	2025-05-18 16:25:20.772085	2025-05-18 16:25:20.772087
\.


--
-- Data for Name: image_format; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image_format (id, title, description, created_at, updated_at, width, height, steps, guidance_scale, extra_settings) FROM stdin;
34	Landscape	1536 × 1024 landscape	2025-05-07 09:42:01.592101	2025-05-07 09:42:01.59211	\N	\N	\N	\N	\N
\.


--
-- Data for Name: image_prompt_example; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image_prompt_example (id, description, style_id, format_id, provider, image_setting_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: image_setting; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image_setting (id, name, style_id, format_id, created_at, updated_at, width, height, steps, guidance_scale, extra_settings) FROM stdin;
1	CLAN inkwash landscape	6	34	2025-05-07 15:48:35.09994	2025-05-07 15:48:35.099946	\N	\N	\N	\N	\N
\.


--
-- Data for Name: image_style; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image_style (id, title, description, created_at, updated_at) FROM stdin;
6	Pen & Ink	Create a traditional pen and watercolor illustration in the style of an 18th-century field sketch. Use fine, inked linework for figures and landscape elements, layered with visible, expressive watercolor brushstrokes. Emphasize the brush texture — each stroke should feel hand-painted, with pigment visibly thinning out or fraying toward the edges. The color should pool, bleed, and fade naturally, leaving irregular white margins and areas where the paint appears to have dried unevenly on textured paper. Maintain a light, warm, naturalistic color palette — earthy reds, mossy greens, ochres, and greys — and leave ample white space around the borders, as if the image were painted into a travel journal. The scene should appear partially unfinished at the margins, evoking the spontaneity of an observational field study.	2025-05-07 09:16:43.971883	2025-05-07 09:18:47.721516
\.


--
-- Data for Name: llm_action; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_action (id, prompt_template, llm_model, temperature, created_at, updated_at, field_name, max_tokens, prompt_template_id, "order") FROM stdin;
3	You are an expert historical researcher and cultural writer specializing in Scottish history, traditions, and heritage. Your task is to expand the basic idea of {{basic_idea}} into an around 50 (fifty) ideas that outline and describe the full scope of an in-depth blog article about that topic in Scottish culture. Suggest (for example) different historical angles, cultural significance, social impact, key events or periods, folklore, notable figures, and/or modern relevance. Focus on breadth of ideas without writing the actual article — this list will as a guide for what should be covered in a full blog post. Keep each idea succinct but be imaginative, including both grand scale ideas and micro ideas. Return only a JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	llama3.1:70b	0.7	2025-05-03 15:34:47.074891	2025-05-05 12:06:48.184004	Idea Scope from Basic Idea	3000	7	0
4	You are a professional copywriter and editor specializing in digital publishing and historical blogging.\n\nYour task is to generate one catchy and engaging blog title suitable for a wide audience from the ideas provided below. This is especially those interested in Scottish culture and heritage. The title should be compelling, relevant to the content, and appropriate for web publication.\n\nReturn only the title with no explanation, commentary, or additional text. Do NOT enclose it in quote marks.\n\n\nYour topic is the following:\n\t1.\tThe basic idea of: {{basic_idea}}\n\t2.\tTheses topics and angles:\n{{idea_scope}}	llama3.1:70b	0.7	2025-05-04 11:31:21.820742	2025-05-05 12:07:38.035082	Generate blog title	1000	8	1
5	You are a researcher specialising in finding curious facts for blog articles for specialist audiences. You have been commissioned to assist with an article about {{basic_idea}} which will examine in depth these ideas {{idea_scope}}.\n\nPlease do a deep dive into this topic and provide a list of up to ten unusual and interesting facts that people might not know, to make this article worth reading. \n\nReturn only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.”	llama3.1:70b	0.9	2025-05-04 12:37:27.007623	2025-05-05 12:07:38.037454	Generate Interesting facts	1000	9	2
6	You are an experienced editor and content strategist. Your task is to analyze the blog post title and content below intended for a blog article on Scottish culture and heritage.\nGroup and organize the content into a logical structure by identifying distinct thematic sections.\nReturn only a JSON array of paragraph titles that represent the structure of the final article.\nEach title should be concise, descriptive, and reflect a key theme from the text.\nDo not include any explanation, commentary, or full text of the paragraphs. Return only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.\n---\n\nTitle: {{provisional_title}}\n\nScope of ideas:\n{{idea_scope}}\n\nSome interesting facts: 	llama3.1:70b	0.7	2025-05-04 12:57:21.257811	2025-05-05 12:07:03.636227	Outlining section headings	1000	10	3
7	You are a professional historical writer specializing in Scottish culture and heritage.\nYour task is to write 2–3 well-written paragraphs for a blog article based on a specific section. IMPORTANT: you must write very specifically only about the sub-themes of this section heading, and AVOID duplicating or overlapping with topics in other sections. Before starting to write anything, consider exactly how this section DISTINCTLY DIFFERS from other sections and focus only on those ideas.\n\nYou are given:\n\t•\tThe overall subject of the blog post, which is: {{basic_idea}}\n\n\t•\tGeneral background context about the topic, describing the range of content the full blog will cover, which is: {{idea_scope}}\n\n\t•\tThe current section title to write under, which is: {{section_heading}}\n\n\t•\tConcepts and angles that should guide this section (but that you may also add to and expand) which are: {{ideas_to_include}}\n\n\t•\tSome interesting factual points that MUST be included in this section (do not omit any!) which are: {{facts_to_include}}\n\nWrite clear, informative, and engaging text that suits a public-facing blog while respecting historical accuracy. Use only UK-British spellings and idioms, avoiding Americanisms (eg colour not color, and 's' not 'z' in words like authorise). \nEnsure that all the <SECTION IDEAS> and <SECTION FACTS> are incorporated meaningfully into the text.\nDo not include any commentary, headings, titles, or formatting — return only the body paragraphs in plain text.	llama3.1:70b	0.7	2025-05-05 10:02:43.403787	2025-05-05 13:51:59.463239	Write Section first draft	1000	12	6
1	You are a researcher specialising in sub-editing blog articles for specialist audiences. You have been commissioned to assist with a Scottish-interest article about {{basic_idea}} which will examine in depth these ideas: {{idea_scope}}.\n\nYou are given:\n- A list of section headings for a blog post about {{basic_idea}}, with the blog title "{{provisional_title}}", which discusses the following ideas and themes: {{idea_scope}}.\n\nYou must now distribute (to the most appropriate section) each fact from the list of interesting facts in JSON array format, given below.\n\nYour task:\n- Allocate each fact to the most appropriate section heading, using your best judgment.\n- Each fact must be assigned to exactly one section (no duplicates, no omissions).\n- Output a single JSON object where each key is a section heading from {{section_order}}, and the value is an array of facts allocated to that section (can be empty if no facts fit).\n- Do not invent or modify facts or headings.\n- The output must be valid JSON, with all facts used exactly once.\n\nExample output:\n{\n  "Introduction": ["Fact 1"],\n  "History": ["Fact 2", "Fact 3"],\n  "Modern Usage": []\n}\n\nBegin.\n\nSection Headings:\n{{section_order}}\n\nInteresting Facts:\n{{interesting_facts}}\n\nOutput:	llama3.1:70b	0.7	2025-05-05 12:42:51.539754	2025-05-05 13:24:33.181218	Allocate facts to sections	3000	5	4
2	You are a researcher specialising in sub-editing blog articles for specialist audiences. You have been commissioned to assist with a Scottish-interest article about {{basic_idea}} which will examine in depth these ideas.\n\nYou are given:\n- A list of section headings for a blog post about {{basic_idea}}, with the blog title "{{provisional_title}}", which discusses the ideas and themes listed below.\n\nYou must now distribute (to the most appropriate section) each idea from the list of ideas in JSON array format, given below.\n\nYour task:\n- Allocate each idea to the most appropriate section heading, using your best judgment.\n- Each idea must be assigned to exactly one section (no duplicates, no omissions).\n- Output a single JSON object where each key is a section heading from {{section_order}}, and the value is an array of ideas allocated to that section (can be empty if no ideas fit).\n- Do not invent or modify ideas or headings.\n- The output must be valid JSON, with all ideas used exactly once.\n\nExample output:\n{\n  "Introduction": ["idea 1"],\n  "History": ["idea 2", "idea 3"],\n  "Modern Usage": []\n}\n\nBegin.\n\nSection Headings:\n{{section_order}}\n\nIdeas:\n{{idea_scope}}\n\nOutput:	llama3.1:70b	0.7	2025-05-05 12:43:10.893882	2025-05-05 13:24:40.632198	Allocate ideas to sections	1000	11	5
8	You are a creative assistant generating a captivating illustration idea for a section of a Scottish-interest blog article. The image must be historically and culturally authentic, relevant to the specific section, and visually distinct from other sections of the article.\n\nYou will be given:\n\t•\tThe article title, which is: {{provisional_title}}\n\n\t•\tA summary of the article’s overall scope and themes, which are: {{idea_scope}}\n\n\t•\tA list of all section titles in the article, which are: \n{{section_order}}\n\n\t•\tThe specific section title that this will illustrate, which is: {{section_heading}}\n\n\t•\tThe full text of that section, which is: \n{{first_draft}}\n\n--\nYour task is to produce a single image concept suitable for illustration. The image should be:\n\t•\tRooted in Scottish history, culture, and environment\n\t•\tDistinct from concepts that might be used for other sections\n\t•\tVisually compelling and engaging for a general audience\n\t•\tSuitable for use as a featured image or embedded illustration\n\nFormat your response as follows:\n\nSection Illustration Prompt:\n<Detailed, descriptive scene for the image generation model, 1-3 sentences. Focus on visual composition, mood, setting, time period, and any symbolic elements relevant to this section’s theme. Use clear and evocative language suitable for stable diffusion or similar tools. Avoid repetition of other sections’ themes.>	llama3.1:70b	0.7	2025-05-06 14:30:29.002166	2025-05-06 14:30:29.002173	Devise image concept	1000	13	0
\.


--
-- Data for Name: llm_action_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_action_history (id, action_id, input_text, output_text, post_id, status, error_message, created_at) FROM stdin;
1	2	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Explain the difference between hand-fasting and marriage",\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Analyze the social impact of hand-fasting on women's lives in Scotland's past",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans",\n  "Describe the role of the 'hand-fastening' ritual in Scottish wedding ceremonies",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings",\n  "Discuss the romanticization of hand-fasting in Scottish literature and art",\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Examine the cultural exchange between Scottish and Norse cultures regarding hand-fasting",\n  "Investigate the connection between hand-fasting and Scotland's ancient laws",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Describe the role of the 'priest' or 'officiant' in a traditional hand-fasting ceremony",\n  "Explore the regional variations of hand-fasting practices across Scotland",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Look at how hand-fasting has been used as a symbol of Scottish national identity",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Examine the influence of hand-fasting on modern wedding traditions worldwide",\n  "Investigate the connection between hand-fasting and Scotland's ancient festivals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Discuss the role of family and community in traditional hand-fasting ceremonies",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the historical context of hand-fasting during Scotland's clan wars",\n  "Look at how hand-fasting has been used as a symbol of loyalty and commitment",\n  "Examine the modern relevance of hand-fasting in contemporary relationships",\n  "Discuss the connection between hand-fasting and Scotland's ancient mythology",\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Analyze the cultural significance of hand-fasting in Scotland's Lowland culture",\n  "Describe the historical context of hand-fasting during Scotland's Enlightenment period",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities",\n  "Discuss the symbolism behind the use of specific materials or objects in hand-fasting rituals",\n  "Look at how hand-fasting has been used as a symbol of resistance against oppressive regimes"\n]	**Assigning Facts to Section Titles**\n=====================================\n\nHere's the assigned output in JSON format:\n\n```json\n{\n  "Introduction": "The idea of this article is to explore the rich cultural heritage of Scotland.",\n  "History and Traditions": "The tradition of Ceilidh (a social gathering with music, dance, and storytelling) dates back to the 18th century.",\n  "Festivals and Celebrations": "Hogmanay, the Scottish New Year's Eve celebration, is a major event in Scotland, often featuring live music, dancing, and fireworks.",\n  "Music and Arts": "Scotland has produced many renowned authors, including Sir Walter Scott and Robert Burns, who are celebrated for their contributions to literature.",\n  "Cuisine and Drink": "Haggis, neeps, and tatties (mashed turnips and potatoes) is Scotland's national dish, traditionally served on Burns Night."\n}\n```\n\nPlease let me know if you need any further assistance.	2	success	\N	2025-05-05 12:43:23.489268
2	1	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	[\n  "Hand-fasting was originally a pagan ritual where couples would tie their hands together with a ribbon or cord to symbolize unity and commitment for a year and a day",\n  "In ancient Celtic tradition, hand-fasting was believed to be a way of testing compatibility before committing to marriage",\n  "The earliest recorded evidence of hand-fasting in Scotland dates back to the 7th century, where it was mentioned in the Irish mythological text 'Tochmarc Emire'",\n  "Hand-fasting was not just for romantic partners; it was also used to seal alliances between clans and families",\n  "In medieval Scotland, hand-fasting was considered a valid form of marriage, with the couple being considered husband and wife after completing the ritual",\n  "The term 'hand-fastening' comes from the Old English words 'hand' and 'fæstan', which means 'to bind or tie'",\n  "Hand-fasting was not limited to Scotland; it was also practiced in other Celtic countries, including Ireland and Wales",\n  "During the Jacobite risings, hand-fasting became a symbol of resistance against British rule and oppression",\n  "In some Scottish Highland clans, hand-fasting was believed to have magical powers, with the couple being bound together by spiritual forces",\n  "Despite its pagan origins, hand-fasting survived the introduction of Christianity in Scotland and continued to be practiced in secret"\n]	2	success	\N	2025-05-05 12:43:41.120208
12	7	I'm happy to help! However, I notice that you haven't provided me with the specific section title, concepts, and factual points that I should write about. Please provide me with this information so I can assist you with writing a well-informed and engaging blog post on hand-fasting in Scottish culture.\n\nOnce I receive this information, I'll do my best to craft 2-3 paragraphs of clear, informative, and engaging text that suits a public-facing blog while respecting historical accuracy.	In Scottish culture, hand-fasting is deeply rooted in ancient Celtic traditions and mythology. This poignant ritual originated as a pagan practice that took place during the spring equinox, a time of great significance for the Celts, who believed it ensured fertility and prosperity for the coming year. By performing hand-fasting ceremonies at this auspicious moment, couples sought to harness the power of nature's renewal and embark on their new life together with hope and promise.\n\nIn ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree. This symbolic act was believed to strengthen the bond between the couple, while also invoking the protection and blessings of the natural world. The role of these spiritual leaders underscores the significance of hand-fasting as a deeply meaningful and ritualistic practice that wove together the threads of love, community, and spirituality.\n\nThe connection between hand-fasting and Scotland's ancient mythology runs deep, with many stories and legends featuring this poignant ritual. By exploring the roots of hand-fasting in Celtic tradition, we gain a profound appreciation for the rich cultural heritage of Scotland and the enduring power of this beautiful and evocative ceremony.	2	success	\N	2025-05-05 14:21:50.003681
16	7	In the misty dawn of Scotland's ancient past, hand-fasting was born from the mystical roots of Celtic tradition and mythology. This sacred ritual, which entwined the destinies of two individuals, was originally a pagan ceremony conducted during the spring equinox to invoke fertility and prosperity upon the land. As the seasons awakened from their winter slumber, the Celts would gather to perform this ancient rite, ensuring the continued cycle of life and growth.\n\nAt the heart of these ceremonies stood the druids, revered spiritual leaders who wielded the power to authorise and sanctify the union of two souls. With deliberate reverence, they would tie the couple's hands together using a cord crafted from the bark of a sacred tree – an act that symbolised the binding of their fates and sealed their commitment to one another. This ancient ritual was deeply embedded in Celtic mythology, where the intricate web of life and death, fate and destiny, was believed to be woven by the gods themselves.\n\nThe connection between hand-fasting and Scotland's ancient mythology runs deep, with echoes of this primordial ritual still resonating through the country's rich cultural heritage. The sacred trees, whose bark was used in the hand-fasting ceremonies, were believed to hold the power of the land and its ancestors – a testament to the profound respect the Celts held for the natural world and their place within it. As we delve into the mysteries of this ancient practice, we begin to unravel the intricate tapestry of Scotland's past, where myth and reality blend seamlessly together.	At its core, hand-fasting is a ritual steeped in ancient Celtic tradition and mythology. The origins of this practice can be traced back to pagan Celtic rituals that took place during the spring equinox, where hand-fasting ceremonies were performed to ensure fertility and prosperity for the coming year. These early ceremonies often featured items coloured red, a symbol of vitality and life force, which was deeply significant in Celtic culture.\n\nIn ancient Scotland, hand-fasting ceremonies were typically conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree. This act of binding was believed to forge a powerful symbolic bond between the two individuals, representing their commitment to one another and to the natural world around them. The use of natural materials in these rituals added an extra layer of significance, as it underscored the connection between human relationships and the cycles of nature.\n\nAs we delve deeper into the ancient Celtic roots of hand-fasting, it becomes clear that this practice was closely tied to Scotland's rich mythological heritage. In Celtic mythology, the sacred marriage between god and goddess was often seen as a symbol of cosmic harmony and balance. Hand-fasting ceremonies may have been seen as a way for couples to emulate this divine union, aligning their own relationship with the natural order of the universe. By examining these ancient roots, we can gain a deeper understanding of the cultural significance that hand-fasting has held in Scottish culture for centuries.	2	success	\N	2025-05-05 15:26:37.231732
3	1	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	Here is the output:\n\n```json\n{\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting": [\n    "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n    "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree"\n  ],\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape": [\n    "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n    "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n  ],\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements": [\n    "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing"\n  ],\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions": [],\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies": [],\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry"\n  ],\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices": [\n    "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n    "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n  ]\n}\n```\n\nNote that I have assigned each fact to exactly one section, using my best judgment. Some facts could potentially fit into multiple sections, but I have chosen what seems to be the most relevant or accurate placement for each fact.	2	success	\N	2025-05-05 13:07:35.767458
4	1	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	Here is the JSON output:\n\n```\n{\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting": [\n    "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n    "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree"\n  ],\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape": [\n    "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n    "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n  ],\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements": [\n    "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions": [\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion"\n  ],\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies": [],\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry"\n  ],\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices": [\n    "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n    "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n  ]\n}\n```\n\nNote: I assigned facts that didn't fit into one specific category to the most relevant section based on their content.	2	success	\N	2025-05-05 13:11:33.91751
5	1	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	Here is the allocated JSON object:\n\n```\n{\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting": [\n    "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n    "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree"\n  ],\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape": [\n    "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n    "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n  ],\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting": [\n    "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements": [\n    "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions": [\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n    "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n  ],\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies": [],\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry"\n  ],\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices": [\n    "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n    "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n  ]\n}\n```\n\nNote that I've allocated some facts to multiple sections, but this is because they fit under more than one category. However, upon re-reading your instructions, I realized that each fact should be assigned to exactly one section. Here is the revised output:\n\n```\n{\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting": [\n    "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n    "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree"\n  ],\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape": [\n    "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion"\n  ],\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting": [\n    "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions": [\n    "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n  ],\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies": [],\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry"\n  ],\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices": [\n    "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n    "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n  ],\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements": []\n}\n```	2	success	\N	2025-05-05 13:14:14.548026
11	7		I'm happy to help! However, I notice that you haven't provided me with the specific section title, concepts, and factual points that I should write about. Please provide me with this information so I can assist you with writing a well-informed and engaging blog post on hand-fasting in Scottish culture.\n\nOnce I receive this information, I'll do my best to craft 2-3 paragraphs of clear, informative, and engaging text that suits a public-facing blog while respecting historical accuracy.	2	success	\N	2025-05-05 13:52:36.320869
6	1	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	Here is the allocated JSON object:\n\n```\n{\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting": [\n    "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n    "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree"\n  ],\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape": [\n    "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n    "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n    "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n  ],\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n    "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n  ],\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements": [\n    "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing"\n  ],\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions": [],\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies": [],\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology": [\n    "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry"\n  ],\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices": [\n    "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n    "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n  ]\n}\n```	2	success	\N	2025-05-05 13:18:58.031961
7	2	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Explain the difference between hand-fasting and marriage",\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Analyze the social impact of hand-fasting on women's lives in Scotland's past",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans",\n  "Describe the role of the 'hand-fastening' ritual in Scottish wedding ceremonies",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings",\n  "Discuss the romanticization of hand-fasting in Scottish literature and art",\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Examine the cultural exchange between Scottish and Norse cultures regarding hand-fasting",\n  "Investigate the connection between hand-fasting and Scotland's ancient laws",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Describe the role of the 'priest' or 'officiant' in a traditional hand-fasting ceremony",\n  "Explore the regional variations of hand-fasting practices across Scotland",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Look at how hand-fasting has been used as a symbol of Scottish national identity",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Examine the influence of hand-fasting on modern wedding traditions worldwide",\n  "Investigate the connection between hand-fasting and Scotland's ancient festivals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Discuss the role of family and community in traditional hand-fasting ceremonies",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the historical context of hand-fasting during Scotland's clan wars",\n  "Look at how hand-fasting has been used as a symbol of loyalty and commitment",\n  "Examine the modern relevance of hand-fasting in contemporary relationships",\n  "Discuss the connection between hand-fasting and Scotland's ancient mythology",\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Analyze the cultural significance of hand-fasting in Scotland's Lowland culture",\n  "Describe the historical context of hand-fasting during Scotland's Enlightenment period",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities",\n  "Discuss the symbolism behind the use of specific materials or objects in hand-fasting rituals",\n  "Look at how hand-fasting has been used as a symbol of resistance against oppressive regimes"\n]	Here is the output:\n\n```\n{\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting": [\n    "Define hand-fasting in Scottish culture and its ancient origins",\n    "Describe the role of hand-fasting in Celtic tradition and mythology",\n    "Examine the connection between hand-fasting and Scotland's ancient mythology"\n  ],\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape": [\n    "Discuss the historical context of hand-fasting in Scotland's medieval period",\n    "Investigate the influence of Christianity on the practice of hand-fasting",\n    "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n    "Analyze the impact of the Reformation on the decline of hand-fasting",\n    "Describe the historical context of hand-fasting during Scotland's clan wars"\n  ],\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting": [\n    "Examine the symbolism behind the hand-fasting ceremony",\n    "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n    "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n    "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n    "Explore the cultural significance of hand-fasting in Scotland's Lowland culture"\n  ],\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements": [\n    "Explain the difference between hand-fasting and marriage",\n    "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n    "Look at how hand-fasting was used to seal alliances and agreements between clans"\n  ],\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions": [\n    "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n    "Describe the historical significance of hand-fasting in Scotland's royal courts",\n    "Analyze the significance of hand-fasting during Scotland's Jacobite risings"\n  ],\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies": [\n    "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns"\n  ],\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology": [\n    "Explore the cultural significance of hand-fasting in Scottish folklore",\n    "Examine the connection between hand-fasting and Scotland's ancient festivals"\n  ],\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices": [\n    "Describe the modern resurgence of interest in hand-fasting ceremonies",\n    "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n    "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n    "Explore the role of hand-fasting in modern Scottish pagan and druidic communities"\n  ]\n}\n```\n\nNote that some ideas could fit into multiple categories, but I have assigned each idea to what seems to be its most relevant section.	2	success	\N	2025-05-05 13:24:54.900661
8	7	In ancient Scottish culture, hand-fasting was a ritualistic ceremony that signified a commitment between two individuals, often with the intention of marriage. This practice had its roots in Celtic tradition and mythology, where it was believed to have originated as a way to seal alliances and agreements between clans. The ritual typically involved the binding of the couple's hands together using ribbons or cords, symbolizing their union and pledge to one another.\n\nThe significance of hand-fasting in Scottish culture cannot be overstated, particularly during Scotland's medieval period. It was often used as a trial marriage or 'betrothal', allowing couples to test their compatibility before committing to a lifelong partnership. This practice also gave women a degree of agency and autonomy, as they could choose to end the hand-fasting if they felt the relationship was not suitable. Notable historical figures such as Robert Burns practiced hand-fasting, highlighting its widespread acceptance and cultural significance.\n\nThe symbolism behind the hand-fasting ceremony is rich and multifaceted. The use of ribbons or cords represented the binding of two individuals together, while the act of tying their hands signified a commitment to one another. In some cases, specific dates or seasons were chosen for hand-fasting ceremonies, such as during ancient festivals like Samhain or Beltane. These rituals were often conducted by a 'priest' or 'officiant', who would oversee the ceremony and ensure its legitimacy. Despite the introduction of Christian marriage rites, hand-fasting survived as a distinct cultural practice, reflecting the enduring importance of this tradition in Scottish heritage.	In Scotland's medieval period, hand-fasting played a significant role in securing alliances between clans and families. This ancient Celtic practice was often used to forge strategic bonds between rival groups, thereby promoting peace and stability throughout the Highlands. By publicly declaring their commitment to one another through hand-fasting, clan leaders could demonstrate their loyalty and reinforce social ties, ultimately strengthening their position within Scotland's complex network of kinship and allegiance.\n\nDuring this time, hand-fasting was also employed as a means of testing the compatibility of potential partners before formalising their union through marriage. This trial period allowed couples to assess their suitability for one another, taking into account factors such as temperament, fertility, and economic viability. In cases where the relationship proved unsuccessful, the couple could part ways without incurring significant social or financial penalties. Notably, Robert Burns, Scotland's national bard, famously used hand-fasting as a means of formalising his own relationships, highlighting the practice's enduring significance within Scottish culture.\n\nThe symbolism behind hand-fasting rituals also held great importance during this period. The use of ribbons or cords to bind the couple's hands together signified their commitment to one another, while the choice of specific dates or seasons for hand-fasting ceremonies often carried additional meaning. For example, some couples would choose to be hand-fastened during the summer solstice, a time associated with fertility and abundance in Celtic mythology. By tapping into these deeper cultural associations, hand-fasting ceremonies took on a profound significance that extended far beyond their practical applications as tools for forging alliances or testing partnerships.	2	success	\N	2025-05-05 13:26:25.978914
9	7		Here is a draft of the blog article section on hand-fasting:\n\nIn ancient Scotland, hand-fasting was a significant ritual that symbolised commitment and loyalty between two people. This practice, also known as 'hand-fastening', involved tying the couple's hands together with ribbons or cords to seal their union. The origins of hand-fasting are rooted in Celtic tradition and mythology, where it was believed to possess spiritual significance. According to historical records, hand-fasting was a common practice among Scotland's medieval clans, particularly during times of war and strife.\n\nOne of the most interesting aspects of hand-fasting is its distinction from marriage. While marriage was often viewed as a formal contract between families, hand-fasting was seen as a personal commitment between two individuals. This subtle difference highlights the importance placed on individual agency and autonomy in ancient Scottish culture. Hand-fasting also played a significant role in Scotland's Jacobite risings, where it was used as a symbol of loyalty and resistance against oppressive regimes. Notable historical figures such as Robert Burns even practiced hand-fasting, further solidifying its place in Scottish folklore.\n\nThe symbolism behind the hand-fasting ceremony is equally fascinating. The use of ribbons or cords represented the binding together of two people, while the act of tying their hands signified a promise to work together and support one another. In some regions of Scotland, specific dates or seasons were chosen for hand-fasting ceremonies, often coinciding with ancient festivals and harvest celebrations. As we explore the rich cultural heritage surrounding hand-fasting, it becomes clear that this ancient practice continues to captivate our imagination and inspire new generations of Scots and non-Scots alike.	2	success	\N	2025-05-05 13:44:03.95735
10	7		In Scotland's medieval period, hand-fasting was a widely accepted practice that served as a trial marriage or 'betrothal' between two individuals. This ancient custom allowed couples to live together for a year and a day before deciding whether to formalise their union through marriage. The hand-fasting ceremony typically involved the couple clasping hands, with their wrists bound by a ribbon or cord, symbolising their commitment to one another. This temporary union was not only a test of compatibility but also provided an opportunity for couples to assess each other's suitability as partners.\n\nHand-fasting played a significant role in Scotland's clan system, where alliances between families were forged through strategic marriages. The practice allowed clans to form tentative agreements without committing to a lifelong bond, thereby reducing the risk of conflict or dishonour. In addition, hand-fasting provided an opportunity for women to experience married life before making a long-term commitment. This flexibility was particularly important in a society where marriage was often viewed as a means of securing economic and social stability.\n\nThe historical record suggests that hand-fasting was widely practiced among Scotland's aristocracy, including notable figures such as Robert Burns. The poet's own experiences with hand-fasting are well-documented, having undergone the ritual with his future wife Jean Armour in 1786. Although the practice declined with the introduction of Christian marriage rites, hand-fasting continued to be observed in some parts of Scotland, particularly in the Highlands and Islands. Its legacy can still be seen in modern Scottish wedding ceremonies, where couples often incorporate elements of the ancient custom as a way of honouring their cultural heritage.	2	success	\N	2025-05-05 13:45:21.002864
13	7	In Scottish culture, hand-fasting is deeply rooted in ancient Celtic traditions and mythology. This poignant ritual originated as a pagan practice that took place during the spring equinox, a time of great significance for the Celts, who believed it ensured fertility and prosperity for the coming year. By performing hand-fasting ceremonies at this auspicious moment, couples sought to harness the power of nature's renewal and embark on their new life together with hope and promise.\n\nIn ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree. This symbolic act was believed to strengthen the bond between the couple, while also invoking the protection and blessings of the natural world. The role of these spiritual leaders underscores the significance of hand-fasting as a deeply meaningful and ritualistic practice that wove together the threads of love, community, and spirituality.\n\nThe connection between hand-fasting and Scotland's ancient mythology runs deep, with many stories and legends featuring this poignant ritual. By exploring the roots of hand-fasting in Celtic tradition, we gain a profound appreciation for the rich cultural heritage of Scotland and the enduring power of this beautiful and evocative ceremony.	In ancient Scotland, hand-fasting was a deeply ingrained tradition with roots firmly planted in Celtic culture and mythology. This pagan ritual was intricately tied to the cycle of nature, with ceremonies often taking place during the spring equinox to ensure fertility and prosperity for the couple and their community. The Celts believed that this sacred bond between two individuals would bring forth abundance and fruitfulness, much like the blossoming flowers and trees that marked the arrival of spring.\n\nAt its core, hand-fasting was a symbolic union between two people, with the ritual itself steeped in rich Celtic tradition. Items coloured red were always included in these ceremonies, signifying passion, vitality, and the life-giving forces of nature. The druids or spiritual leaders who conducted these rituals would tie the couple's hands together with a cord made from the bark of a sacred tree, such as the oak or ash, believed to possess magical properties that would strengthen their bond. This act of binding was not merely physical but also spiritual, representing the intertwining of two souls.\n\nThe connection between hand-fasting and Scotland's ancient mythology runs deep, with echoes of this practice found in the stories of old. The Celts believed in a complex pantheon of gods and goddesses who oversaw various aspects of life, including love and fertility. Hand-fasting ceremonies were often invoked to appease these deities, ensuring their blessings upon the union. As such, hand-fasting was not just a human institution but a sacred contract between two individuals, witnessed by the natural world and endorsed by the gods themselves.	2	success	\N	2025-05-05 14:25:54.602539
14	7	In ancient Scotland, hand-fasting was a deeply ingrained tradition with roots firmly planted in Celtic culture and mythology. This pagan ritual was intricately tied to the cycle of nature, with ceremonies often taking place during the spring equinox to ensure fertility and prosperity for the couple and their community. The Celts believed that this sacred bond between two individuals would bring forth abundance and fruitfulness, much like the blossoming flowers and trees that marked the arrival of spring.\n\nAt its core, hand-fasting was a symbolic union between two people, with the ritual itself steeped in rich Celtic tradition. Items coloured red were always included in these ceremonies, signifying passion, vitality, and the life-giving forces of nature. The druids or spiritual leaders who conducted these rituals would tie the couple's hands together with a cord made from the bark of a sacred tree, such as the oak or ash, believed to possess magical properties that would strengthen their bond. This act of binding was not merely physical but also spiritual, representing the intertwining of two souls.\n\nThe connection between hand-fasting and Scotland's ancient mythology runs deep, with echoes of this practice found in the stories of old. The Celts believed in a complex pantheon of gods and goddesses who oversaw various aspects of life, including love and fertility. Hand-fasting ceremonies were often invoked to appease these deities, ensuring their blessings upon the union. As such, hand-fasting was not just a human institution but a sacred contract between two individuals, witnessed by the natural world and endorsed by the gods themselves.	In the misty dawn of Scotland's ancient past, hand-fasting was born from the mystical roots of Celtic tradition and mythology. This sacred ritual, which entwined the destinies of two individuals, was originally a pagan ceremony conducted during the spring equinox to invoke fertility and prosperity upon the land. As the seasons awakened from their winter slumber, the Celts would gather to perform this ancient rite, ensuring the continued cycle of life and growth.\n\nAt the heart of these ceremonies stood the druids, revered spiritual leaders who wielded the power to authorise and sanctify the union of two souls. With deliberate reverence, they would tie the couple's hands together using a cord crafted from the bark of a sacred tree – an act that symbolised the binding of their fates and sealed their commitment to one another. This ancient ritual was deeply embedded in Celtic mythology, where the intricate web of life and death, fate and destiny, was believed to be woven by the gods themselves.\n\nThe connection between hand-fasting and Scotland's ancient mythology runs deep, with echoes of this primordial ritual still resonating through the country's rich cultural heritage. The sacred trees, whose bark was used in the hand-fasting ceremonies, were believed to hold the power of the land and its ancestors – a testament to the profound respect the Celts held for the natural world and their place within it. As we delve into the mysteries of this ancient practice, we begin to unravel the intricate tapestry of Scotland's past, where myth and reality blend seamlessly together.	2	success	\N	2025-05-05 14:29:01.241644
15	7		The evolution of hand-fasting in Scotland's historical landscape is a complex and multifaceted tale that spans centuries. The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that, with roots in ancient Celtic and pagan traditions. As Christianity spread throughout Scotland during the medieval period, hand-fasting began to take on a new significance, particularly among the Highland clans. The ritual became a way of solidifying alliances, securing land rights, and demonstrating loyalty to one's kin.\n\nThe influence of Christianity on hand-fasting practices was significant, as the church attempted to regulate and suppress what it saw as a pagan practice. However, hand-fasting continued to thrive, particularly in rural areas where traditional customs remained strong. During the Jacobite era, hand-fasting became a potent symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion. This association with the Jacobite movement helped to ensure the survival of hand-fasting despite the introduction of Christian marriage rites. In fact, during this period, hand-fasting became an important way for couples to demonstrate their devotion to one another and to their clan.\n\nThe 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual. However, this legislation had limited success in eradicating the practice, particularly among the Highland clans who continued to view hand-fasting as an essential part of their cultural heritage. The Reformation's impact on hand-fasting was more significant, as the Protestant Church's emphasis on monogamy and formal marriage rites helped to decline the popularity of hand-fasting. Nevertheless, hand-fasting continued to play a role in Scottish culture, particularly during times of conflict such as Scotland's clan wars, where it served as a powerful symbol of loyalty and commitment.	2	success	\N	2025-05-05 14:32:56.410022
17	7	The evolution of hand-fasting in Scotland's historical landscape is a complex and multifaceted tale that spans centuries. The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that, with roots in ancient Celtic and pagan traditions. As Christianity spread throughout Scotland during the medieval period, hand-fasting began to take on a new significance, particularly among the Highland clans. The ritual became a way of solidifying alliances, securing land rights, and demonstrating loyalty to one's kin.\n\nThe influence of Christianity on hand-fasting practices was significant, as the church attempted to regulate and suppress what it saw as a pagan practice. However, hand-fasting continued to thrive, particularly in rural areas where traditional customs remained strong. During the Jacobite era, hand-fasting became a potent symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion. This association with the Jacobite movement helped to ensure the survival of hand-fasting despite the introduction of Christian marriage rites. In fact, during this period, hand-fasting became an important way for couples to demonstrate their devotion to one another and to their clan.\n\nThe 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual. However, this legislation had limited success in eradicating the practice, particularly among the Highland clans who continued to view hand-fasting as an essential part of their cultural heritage. The Reformation's impact on hand-fasting was more significant, as the Protestant Church's emphasis on monogamy and formal marriage rites helped to decline the popularity of hand-fasting. Nevertheless, hand-fasting continued to play a role in Scottish culture, particularly during times of conflict such as Scotland's clan wars, where it served as a powerful symbol of loyalty and commitment.	As we explore the evolution of hand-fasting in Scotland's historical landscape, it becomes clear that this ancient practice was intricately woven into the fabric of Scottish society. The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that. During the medieval period, hand-fasting was an integral part of Celtic tradition and mythology, with couples undergoing the ritual as a way of formalising their commitment to one another.\n\nHowever, with the introduction of Christianity, the practice of hand-fasting began to evolve. The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual. Despite this, hand-fasting continued to thrive, particularly in the Highlands where it remained an important part of clan culture. During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion.\n\nThe impact of the Reformation on hand-fasting was significant, leading to a decline in its practice as Christian marriage rites became more widespread. However, despite this, hand-fasting continued to survive in some form, particularly during times of social and political upheaval such as Scotland's clan wars. In these contexts, hand-fasting served as a way for couples to formalise their commitment to one another without necessarily adhering to the formalities of Christian marriage. This adaptability was key to the enduring legacy of hand-fasting in Scottish culture, allowing it to evolve and endure despite significant changes in Scotland's historical landscape.	2	success	\N	2025-05-05 15:27:39.29355
18	7		The symbolism surrounding hand-fasting is a rich tapestry of cultural significance, woven from threads of Scottish folklore, mythology, and tradition. At its core, hand-fasting represents a deep commitment to one another, often sealed with the use of ribbons or cords that symbolize the binding nature of the partnership. In Scottish Highland culture, these ribbons were frequently made from the hair of the couple, signifying their intertwined fates and destinies. This practice was not unique to romantic partnerships, however – hand-fasting was also used to seal business agreements, alliances between clans, and even friendships, underscoring its importance as a ritual that transcended love alone.\n\nIn Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry. This connection imbues the practice with a deeper layer of meaning, linking it to the cycles of nature and the creative forces that shape human experience. The use of specific dates or seasons for hand-fasting ceremonies also holds significance, often coinciding with ancient festivals like Imbolc or Lughnasadh. These timing choices were thought to amplify the ritual's power, harnessing the energies of the natural world to consecrate the partnership.\n\nBeyond its connections to mythology and nature, hand-fasting holds distinct cultural significances in both Scottish Highland and Lowland cultures. In the Highlands, it was often seen as a way to strengthen clan ties and forge alliances between families, while in the Lowlands, it was more closely tied to agricultural cycles and the rhythms of rural life. Despite these regional variations, however, hand-fasting remains a potent symbol of commitment and loyalty across Scotland, speaking to a deeper sense of community and shared values that transcends geography and cultural heritage.	2	success	\N	2025-05-05 15:28:14.878492
19	7		In Scotland's medieval period, hand-fasting played a crucial role as a social contract, securing alliances and agreements between clans. It was often used to seal arrangements such as trade agreements, military alliances, and even marriage contracts. This form of commitment allowed families to strengthen their ties with other powerful clans, solidifying their positions within the complex web of Scottish society. Hand-fasting in this context served as a public declaration of intent, demonstrating a willingness to collaborate and cooperate for mutual benefit.\n\nAs a trial marriage or 'betrothal', hand-fasting also provided a unique opportunity for couples to test their compatibility before making a lifelong commitment. This allowed them to assess whether they were suited for each other, both socially and economically, reducing the risk of an ill-suited match that could jeopardize family alliances. In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing – a valuable safeguard in a society where illegitimacy could have serious repercussions.\n\nThe distinction between hand-fasting and marriage is crucial here; while both involved commitment and ceremony, they served different purposes. Hand-fasting was often seen as a more flexible arrangement, allowing for renegotiation or dissolution if circumstances changed. Marriage, on the other hand, was viewed as a permanent union. By using hand-fasting to secure alliances and agreements, families could navigate the complexities of Scottish society with greater ease, ensuring that their interests were protected while maintaining social harmony.	2	success	\N	2025-05-05 15:28:51.990799
21	7		One of Scotland's most beloved literary figures, Robert Burns, is perhaps one of the most famous Scots to have participated in a hand-fasting ceremony. In 1788, Burns tied the knot with Jean Armour in a traditional Scottish hand-fastening ritual, which was a common practice among the country's rural communities at the time. This ancient Celtic custom allowed couples to commit to each other for a year and a day, after which they could either formalise their union through marriage or part ways amicably.\n\nBurns' decision to opt for a hand-fasting ceremony has been interpreted by some as a reflection of his commitment to Scottish tradition and culture. As a proud advocate for the preservation of Scotland's folk heritage, Burns likely saw hand-fastening as a way to connect with his country's rich cultural past. Moreover, this ceremony allowed him to make a public declaration of his love for Jean Armour without immediately committing to marriage – a decision that may have been influenced by the societal norms and expectations surrounding marriage at the time.\n\nBurns' experience with hand-fasting has also been immortalised in his own writing, with references to the custom appearing in several of his poems. For example, in "Highland Mary", Burns describes the ritual as a sacred bond between two people, underscoring its importance in Scottish cultural tradition. Through his own life and work, Burns helped to popularise hand-fasting as a symbol of Scottish national identity, cementing its place in the country's rich cultural heritage.	2	success	\N	2025-05-05 15:29:56.827197
20	7		As we delve into Scotland's rich history, it becomes apparent that hand-fasting traditions were shaped by a complex array of events and influences. The Jacobite risings, which took place in the late 17th and early 18th centuries, played a significant role in shaping the cultural significance of hand-fasting. During this time, Highland clans would often engage in hand-fasting ceremonies as a way of solidifying alliances and securing loyalty among their members. This practice was particularly prevalent during times of war, when clan leaders sought to strengthen their bonds with one another.\n\nAnother key event that influenced hand-fasting traditions in Scotland was the country's emigration patterns. As Scots left their homeland to settle in other parts of the world, they brought their cultural practices and traditions with them. Hand-fasting, in particular, became an important way for Scottish expatriates to connect with their heritage and maintain a sense of community in their new surroundings. This led to the spread of hand-fasting practices worldwide, as Scottish emigrants adapted and modified the tradition to suit their new environments.\n\nThe royal courts of Scotland also played a significant role in shaping hand-fasting traditions. In medieval times, members of the nobility would often engage in hand-fasting ceremonies as a way of formalising alliances and securing power. This practice was particularly prevalent during the reign of Queen Mary Stuart, who famously engaged in a hand-fasting ceremony with her cousin, Henry Stuart, Lord Darnley. The royal court's adoption of hand-fasting helped to solidify its place in Scottish culture, cementing its significance as a symbol of loyalty and commitment.	2	success	\N	2025-05-05 15:29:23.575678
22	7		In Scottish folklore, hand-fasting is woven into a rich tapestry of myth and legend, often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry. This connection highlights the deep cultural significance of hand-fasting in Scotland's ancient traditions. As a symbol of commitment and devotion, hand-fasting is said to have been blessed by Brigid herself, imbuing it with her sacred power. In this context, the ritual takes on a spiritual dimension, transcending mere mortal bonds to become a union sanctioned by the divine.\n\nThe connection between hand-fasting and Scotland's ancient festivals is another thread in this rich folklore tapestry. Many of these festivals, such as Imbolc and Lughnasadh, celebrate themes of love, fertility, and harvest, all of which are closely tied to the ideals of hand-fasting. During these celebrations, hand-fasting ceremonies would often take place, solidifying bonds between couples under the watchful eyes of their community and the blessing of the land itself. This communal aspect of hand-fasting underscores its importance as a social glue, binding families and communities together in a shared celebration of love and commitment.\n\nIn exploring the mythical ties that bind hand-fasting to Scottish folklore, we glimpse a culture where love, poetry, and nature were deeply intertwined. The reverence for Brigid, patron goddess of these themes, speaks to a society that valued the sacred and the beautiful, seeking to infuse its most intimate relationships with the magic of myth and legend. As a result, hand-fasting in Scottish folklore takes on an almost mystical quality, evoking the power of ancient traditions and the enduring force of love itself.	2	success	\N	2025-05-05 15:30:26.951712
23	7		In recent years, there has been a notable resurgence of interest in traditional hand-fasting ceremonies, with many couples incorporating this ancient practice into their modern Scottish weddings. This revival can be attributed, in part, to the Victorian era's romanticization of Scottish culture, which helped to popularize hand-fasting as a motif in literature and art. As a result, hand-fasting has become a sought-after way for couples to connect with their Celtic heritage and add a touch of nostalgia to their special day.\n\nBeyond its appeal as a wedding ritual, hand-fasting has also been reinterpreted by modern pagan and druidic communities as a way to celebrate the cycles of nature and honor their ancestors. Today, some modern pagans and Wiccans still practice hand-fasting as a way to connect with their Celtic roots and mark important life milestones, such as solstices and equinoxes. This reinterpretation of traditional hand-fasting practices not only breathes new life into an ancient custom but also highlights the enduring appeal of this symbolic act.\n\nFrom a feminist perspective, hand-fasting has also taken on new significance in modern times. As a practice that was historically used to seal alliances and agreements between clans, hand-fasting can be seen as a symbol of female agency and autonomy. In contemporary Scotland, some women are embracing hand-fasting as a way to reclaim their cultural heritage and assert their independence, highlighting the complex and multifaceted nature of this ancient custom. As hand-fasting continues to evolve and adapt to modern times, it remains a powerful symbol of commitment, community, and connection to the past.	2	success	\N	2025-05-05 15:31:01.444964
24	3	Test input	[\n  "Hand-fasting as a Pagan ritual in ancient Scotland",\n  "The role of hand-fasting in Scottish folklore and mythology",\n  "Origins of hand-fasting: tracing its roots to Celtic and Norse traditions",\n  "A brief history of hand-fasting from the Iron Age to the Middle Ages",\n  "Hand-fasting as a symbol of unity and strength in Scottish clans",\n  "The significance of hand-fasting in Scottish Highland culture",\n  "How hand-fasting was used to secure alliances between rival clans",\n  "The impact of Christianity on hand-fasting practices in Scotland",\n  "The survival of hand-fasting traditions despite Christian influence",\n  "Hand-fasting as a form of trial marriage or ' temporary union'",\n  "Examples of famous Scottish couples who practiced hand-fasting",\n  "Notable historical figures who participated in hand-fasting ceremonies",\n  "Hand-fasting and the role of women in ancient Scottish society",\n  "The connection between hand-fasting and the Celtic festival of Lughnasadh",\n  "Hand-fasting as a symbol of fertility and prosperity in Scottish agriculture",\n  "The role of the 'hand-faster' or officiant in traditional ceremonies",\n  "How hand-fasting was used to formalize business partnerships and agreements",\n  "A comparison of hand-fasting with other forms of ancient Celtic marriage",\n  "Hand-fasting as a form of social bonding and community building",\n  "The significance of the 'year and a day' rule in hand-fasting contracts",\n  "How hand-fasting influenced modern Scottish wedding traditions",\n  "Examples of hand-fasting in Scottish literature and art",\n  "The romanticization of hand-fasting in 18th-century Scottish culture",\n  "Hand-fasting as a source of inspiration for modern artists and writers",\n  "The cultural significance of hand-fasting in modern Scotland",\n  "How hand-fasting reflects the values of Scottish society past and present",\n  "A look at modern-day hand-fasting ceremonies in Scotland",\n  "The role of hand-fasting in contemporary Scottish pagan and witchcraft communities",\n  "Hand-fasting as a symbol of commitment in LGBTQ+ relationships",\n  "Examples of non-traditional hand-fasting ceremonies around the world",\n  "The impact of social media on modern perceptions of hand-fasting",\n  "A comparison of hand-fasting with other forms of alternative marriage",\n  "Hand-fasting and its relationship to Scottish national identity",\n  "How hand-fasting has influenced cultural heritage tourism in Scotland",\n  "Examples of historical sites associated with hand-fasting ceremonies",\n  "The importance of preserving hand-fasting traditions for future generations",\n  "A discussion of the challenges facing modern practitioners of hand-fasting",\n  "Hand-fasting as a form of resistance against mainstream culture",\n  "The connection between hand-fasting and Scottish folk music and dance",\n  "Examples of traditional Scottish foods associated with hand-fasting ceremonies",\n  "The role of nature and the outdoors in traditional hand-fasting rituals",\n  "A look at modern-day interpretations of ancient hand-fasting symbols",\n  "Hand-fasting as a symbol of spiritual growth and self-discovery"\n]	1	success	\N	2025-05-06 16:52:56.2022
25	8		Section Illustration Prompt:\n\nIn a misty, ancient Celtic forest, a serene couple stands before a majestic, gnarled tree, its branches twisted with age. The druidic figure officiating their hand-fasting ceremony holds aloft a vibrant red cord made from the sacred tree's bark, as the first light of dawn breaks through the canopy above, casting dappled shadows on the forest floor. Amidst this mystical setting, the air is filled with an otherworldly energy, as if the spirits of Celtic mythology are gathered to witness the union.\n\nThis illustration concept captures the essence of Scotland's ancient Celtic roots and the mystique surrounding hand-fasting ceremonies. By incorporating symbolic elements such as the red cord and the sacred tree, the image invites viewers to step into a mystical world where human relationships are intertwined with nature and the cosmos. The dreamy atmosphere and soft lighting evoke a sense of timelessness, drawing the audience into the heart of Scotland's rich cultural heritage.	2	success	\N	2025-05-06 18:03:06.901099
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_config (id, provider_type, model_name, api_base, auth_token, created_at, updated_at) FROM stdin;
1	ollama	llama3.1:70b	http://localhost:11434	\N	2025-05-01 07:03:20.613924	2025-05-01 07:33:20.294464
\.


--
-- Data for Name: llm_interaction; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_interaction (id, prompt_id, input_text, output_text, parameters_used, interaction_metadata, created_at) FROM stdin;
\.


--
-- Data for Name: llm_prompt; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_prompt (id, name, description, prompt_text, system_prompt, parameters, created_at, updated_at, "order") FROM stdin;
11	Allocate Ideas to Sections	Allocate each idea to its most relevant section	You are a researcher specialising in sub-editing blog articles for specialist audiences. You have been commissioned to assist with a Scottish-interest article about {{basic_idea}} which will examine in depth these ideas.\n\nYou are given:\n- A list of section headings for a blog post about {{basic_idea}}, with the blog title "{{provisional_title}}", which discusses the ideas and themes listed below.\n\nYou must now distribute (to the most appropriate section) each idea from the list of ideas in JSON array format, given below.\n\nYour task:\n- Allocate each idea to the most appropriate section heading, using your best judgment.\n- Each idea must be assigned to exactly one section (no duplicates, no omissions).\n- Output a single JSON object where each key is a section heading from {{section_order}}, and the value is an array of ideas allocated to that section (can be empty if no ideas fit).\n- Do not invent or modify ideas or headings.\n- The output must be valid JSON, with all ideas used exactly once.\n\nExample output:\n{\n  "Introduction": ["idea 1"],\n  "History": ["idea 2", "idea 3"],\n  "Modern Usage": []\n}\n\nBegin.\n\nSection Headings:\n{{section_order}}\n\nIdeas:\n{{idea_scope}}\n\nOutput:	\N	\N	2025-05-04 14:30:59.400632	2025-05-05 13:23:13.166973	3
9	Interesting facts	Generate Interesting facts	You are a researcher specialising in finding curious facts for blog articles for specialist audiences. You have been commissioned to assist with an article about {{basic_idea}} which will examine in depth these ideas {{idea_scope}}.\n\nPlease do a deep dive into this topic and provide a list of up to ten unusual and interesting facts that people might not know, to make this article worth reading. \n\nReturn only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.”	\N	\N	2025-05-04 12:36:41.74155	2025-05-05 13:23:26.124861	1
5	Allocate Facts to Sections	Allocate each fact to its most relevant section	You are a researcher specialising in sub-editing blog articles for specialist audiences. You have been commissioned to assist with a Scottish-interest article about {{basic_idea}} which will examine in depth these ideas: {{idea_scope}}.\n\nYou are given:\n- A list of section headings for a blog post about {{basic_idea}}, with the blog title "{{provisional_title}}", which discusses the following ideas and themes: {{idea_scope}}.\n\nYou must now distribute (to the most appropriate section) each fact from the list of interesting facts in JSON array format, given below.\n\nYour task:\n- Allocate each fact to the most appropriate section heading, using your best judgment.\n- Each fact must be assigned to exactly one section (no duplicates, no omissions).\n- Output a single JSON object where each key is a section heading from {{section_order}}, and the value is an array of facts allocated to that section (can be empty if no facts fit).\n- Do not invent or modify facts or headings.\n- The output must be valid JSON, with all facts used exactly once.\n\nExample output:\n{\n  "Introduction": ["Fact 1"],\n  "History": ["Fact 2", "Fact 3"],\n  "Modern Usage": []\n}\n\nBegin.\n\nSection Headings:\n{{section_order}}\n\nInteresting Facts:\n{{interesting_facts}}\n\nOutput:	\N	\N	2025-05-04 12:37:27.007623	2025-05-05 13:23:13.165621	2
8	Catchy title	Expand the basic idea and scope into an engaging title	You are a professional copywriter and editor specializing in digital publishing and historical blogging.\n\nYour task is to generate one catchy and engaging blog title suitable for a wide audience from the ideas provided below. This is especially those interested in Scottish culture and heritage. The title should be compelling, relevant to the content, and appropriate for web publication.\n\nReturn only the title with no explanation, commentary, or additional text. Do NOT enclose it in quote marks.\n\n\nYour topic is the following:\n\t1.\tThe basic idea of: {{basic_idea}}\n\t2.\tTheses topics and angles:\n{{idea_scope}}	\N	\N	2025-05-04 11:30:44.517966	2025-05-05 13:23:03.832602	4
10	Structuring section headings	Thematic section	You are an experienced editor and content strategist. Your task is to analyze the blog post title and content below intended for a blog article on Scottish culture and heritage.\nGroup and organize the content into a logical structure by identifying distinct thematic sections.\nReturn only a JSON array of paragraph titles that represent the structure of the final article.\nEach title should be concise, descriptive, and reflect a key theme from the text.\nDo not include any explanation, commentary, or full text of the paragraphs. Return only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.\n---\n\nTitle: {{provisional_title}}\n\nScope of ideas:\n{{idea_scope}}\n\nSome interesting facts: 	\N	\N	2025-05-04 12:56:29.9372	2025-05-05 13:23:03.833402	5
7	Basic Idea to Idea Scope	Expand Basic Idea to Idea Scope	You are an expert historical researcher and cultural writer specializing in Scottish history, traditions, and heritage. Your task is to expand the basic idea of {{basic_idea}} into an around 50 (fifty) ideas that outline and describe the full scope of an in-depth blog article about that topic in Scottish culture. Suggest (for example) different historical angles, cultural significance, social impact, key events or periods, folklore, notable figures, and/or modern relevance. Focus on breadth of ideas without writing the actual article — this list will as a guide for what should be covered in a full blog post. Keep each idea succinct but be imaginative, including both grand scale ideas and micro ideas. Return only a valid JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	\N	\N	2025-05-04 11:18:41.267767	2025-05-05 13:23:08.776355	0
12	Author Section first draft		You are a professional historical writer specializing in Scottish culture and heritage.\nYour task is to write 2–3 well-written paragraphs for a blog article based on a specific section. IMPORTANT: you must write very specifically only about the sub-themes of this section heading, and AVOID duplicating or overlapping with topics in other sections. Before starting to write anything, consider exactly how this section DISTINCTLY DIFFERS from other sections and focus only on those ideas.\n\nYou are given:\n\t•\tThe overall subject of the blog post, which is: {{basic_idea}}\n\n\t•\tGeneral background context about the topic, describing the range of content the full blog will cover, which is: {{idea_scope}}\n\n\t•\tThe current section title to write under, which is: {{section_heading}}\n\n\t•\tConcepts and angles that should guide this section (but that you may also add to and expand) which are: {{ideas_to_include}}\n\n\t•\tSome interesting factual points that MUST be included in this section (do not omit any!) which are: {{facts_to_include}}\n\nWrite clear, informative, and engaging text that suits a public-facing blog while respecting historical accuracy. Use only UK-British spellings and idioms, avoiding Americanisms (eg colour not color, and 's' not 'z' in words like authorise). \nEnsure that all the ideas and facts mentioned above are incorporated meaningfully into the text.\nDo not include any commentary, headings, titles, or formatting — return only the body paragraphs in plain text.	\N	\N	2025-05-05 10:01:54.864346	2025-05-05 14:04:21.476545	6
13	Devise image concept	Devise image concept	You are a creative assistant generating a captivating illustration idea for a section of a Scottish-interest blog article. The image must be historically and culturally authentic, relevant to the specific section, and visually distinct from other sections of the article.\n\nYou will be given:\n\t•\tThe article title, which is: {{provisional_title}}\n\n\t•\tA summary of the article’s overall scope and themes, which are: {{idea_scope}}\n\n\t•\tA list of all section titles in the article, which are: \n{{section_order}}\n\n\t•\tThe specific section title that this will illustrate, which is: {{section_heading}}\n\n\t•\tThe full text of that section, which is: \n{{first_draft}}\n\n--\nYour task is to produce a single image concept suitable for illustration. The image should be:\n\t•\tRooted in Scottish history, culture, and environment\n\t•\tDistinct from concepts that might be used for other sections\n\t•\tVisually compelling and engaging for a general audience\n\t•\tSuitable for use as a featured image or embedded illustration\n\nFormat your response as follows:\n\nSection Illustration Prompt:\n<Detailed, descriptive scene for the image generation model, 1-3 sentences. Focus on visual composition, mood, setting, time period, and any symbolic elements relevant to this section’s theme. Use clear and evocative language suitable for stable diffusion or similar tools. Avoid repetition of other sections’ themes.>	\N	\N	2025-05-06 14:26:46.167752	2025-05-06 14:26:46.167759	0
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.post (id, title, slug, content, summary, published, deleted, created_at, updated_at, published_at, header_image_id, llm_metadata, seo_metadata, syndication_status) FROM stdin;
1	hand-fasting...	hand-fasting		\N	f	t	2025-05-03 16:05:45.941465	2025-05-04 09:47:14.925021	\N	\N	\N	\N	\N
2	hand-fasting...	hand-fasting-1		\N	f	f	2025-05-04 09:47:22.571191	2025-05-04 16:15:45.445826	\N	\N	\N	\N	\N
4	The Evolution of the Modern Scottish Kilt	kilt-evolution	\N	<p>The <b>Scottish kilt</b>, a garment that has become synonymous with Highland culture and Scottish identity, has undergone significant evolution since its inception. From its origins as the <b>'great kilt'</b> or <b>'belted plaid'</b> to the modern form we recognize today, its journey reflects Scotland's rich history of tradition, adaptation, and resilience. This article explores the kilt's transformation through time, examining how historical events, practical needs, and cultural shifts have shaped this iconic symbol of Scottish heritage.</p>\n	f	f	2023-10-20 00:00:00	2025-05-18 16:25:20.775043	\N	139	\N	\N	\N
5	English tartans	english-tartans	\N	<p><strong>English tartans</strong> have a fascinating trajectory, intertwining with the better-known <strong>Scottish tartan</strong> tradition yet developing a character of their own. Although <strong>tartan</strong> is primarily identified with Scotland, England’s engagement with tartan spans from ancient use of <strong>checkered cloth</strong> by <strong>Celtic</strong> peoples to a modern revival of regional and national patterns. This comprehensive overview examines the emergence and development of tartans in England – from historical origins and regional examples to influences of the <strong>textile industry</strong>, expressions of <strong>national identity</strong>, and contemporary <strong>design movements</strong> – all while preserving every detail of the rich historical narrative.</p>	f	f	2025-04-18 00:00:00	2025-05-18 16:25:20.785179	\N	\N	\N	\N	\N
6	The Tradition of the Scottish Quaich	quaich-traditions	\N	<p>The <b>quaich</b>, Scotland's cherished <b>"cup of friendship,"</b> holds a special place in Scottish tradition, symbolising hospitality, unity, and trust. Originating centuries ago, its simple yet profound design—a shallow, two-handled bowl—embodies a rich history spanning <b>clan</b> gatherings, ceremonial rituals, royal celebrations, and contemporary <b>weddings</b>. This article explores the evolution of the quaich, delving into its earliest origins, cultural significance, craftsmanship, historical anecdotes, and enduring presence in modern Scottish culture.</p>\n	f	f	2023-10-27 00:00:00	2025-05-18 16:25:20.822509	\N	150	\N	\N	\N
\.


--
-- Data for Name: post_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.post_categories (post_id, category_id) FROM stdin;
\.


--
-- Data for Name: post_development; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.post_development (id, post_id, basic_idea, provisional_title, idea_scope, topics_to_cover, interesting_facts, tartans_products, section_planning, section_headings, section_order, main_title, subtitle, intro_blurb, conclusion, basic_metadata, tags, categories, image_captions, seo_optimization, self_review, peer_review, final_check, scheduling, deployment, verification, feedback_collection, content_updates, version_control, platform_selection, content_adaptation, distribution, engagement_tracking) FROM stdin;
1	1	hand-fasting	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
2	2	hand-fasting	Tying the Knot: Unraveling Scotland's Ancient Tradition of Hand-Fasting	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Explain the difference between hand-fasting and marriage",\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Analyze the social impact of hand-fasting on women's lives in Scotland's past",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans",\n  "Describe the role of the 'hand-fastening' ritual in Scottish wedding ceremonies",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings",\n  "Discuss the romanticization of hand-fasting in Scottish literature and art",\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Examine the cultural exchange between Scottish and Norse cultures regarding hand-fasting",\n  "Investigate the connection between hand-fasting and Scotland's ancient laws",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Describe the role of the 'priest' or 'officiant' in a traditional hand-fasting ceremony",\n  "Explore the regional variations of hand-fasting practices across Scotland",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Look at how hand-fasting has been used as a symbol of Scottish national identity",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Examine the influence of hand-fasting on modern wedding traditions worldwide",\n  "Investigate the connection between hand-fasting and Scotland's ancient festivals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Discuss the role of family and community in traditional hand-fasting ceremonies",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the historical context of hand-fasting during Scotland's clan wars",\n  "Look at how hand-fasting has been used as a symbol of loyalty and commitment",\n  "Examine the modern relevance of hand-fasting in contemporary relationships",\n  "Discuss the connection between hand-fasting and Scotland's ancient mythology",\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Analyze the cultural significance of hand-fasting in Scotland's Lowland culture",\n  "Describe the historical context of hand-fasting during Scotland's Enlightenment period",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities",\n  "Discuss the symbolism behind the use of specific materials or objects in hand-fasting rituals",\n  "Look at how hand-fasting has been used as a symbol of resistance against oppressive regimes"\n]	\N	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	\N	\N	[\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting",\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape",\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting",\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements",\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions",\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology",\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies",\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices"\n]	["Unraveling the Ancient Celtic Roots of Hand-Fasting","The Evolution of Hand-Fasting in Scotland's Historical Landscape","Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting","Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements","A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions","Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies","Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology","Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices"]	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: post_section; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.post_section (id, post_id, section_order, section_heading, first_draft, uk_british, highlighting, image_concepts, image_prompts, generation, optimization, watermarking, image_meta_descriptions, image_captions, ideas_to_include, facts_to_include, image_prompt_example_id, generated_image_url, image_generation_metadata) FROM stdin;
5	2	3	Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements	In Scotland's medieval period, hand-fasting played a crucial role as a social contract, securing alliances and agreements between clans. It was often used to seal arrangements such as trade agreements, military alliances, and even marriage contracts. This form of commitment allowed families to strengthen their ties with other powerful clans, solidifying their positions within the complex web of Scottish society. Hand-fasting in this context served as a public declaration of intent, demonstrating a willingness to collaborate and cooperate for mutual benefit.\n\nAs a trial marriage or 'betrothal', hand-fasting also provided a unique opportunity for couples to test their compatibility before making a lifelong commitment. This allowed them to assess whether they were suited for each other, both socially and economically, reducing the risk of an ill-suited match that could jeopardize family alliances. In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing – a valuable safeguard in a society where illegitimacy could have serious repercussions.\n\nThe distinction between hand-fasting and marriage is crucial here; while both involved commitment and ceremony, they served different purposes. Hand-fasting was often seen as a more flexible arrangement, allowing for renegotiation or dissolution if circumstances changed. Marriage, on the other hand, was viewed as a permanent union. By using hand-fasting to secure alliances and agreements, families could navigate the complexities of Scottish society with greater ease, ensuring that their interests were protected while maintaining social harmony.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Explain the difference between hand-fasting and marriage",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans"\n]	[\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing"\n]	\N	\N	\N
6	2	4	A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions	As we delve into Scotland's rich history, it becomes apparent that hand-fasting traditions were shaped by a complex array of events and influences. The Jacobite risings, which took place in the late 17th and early 18th centuries, played a significant role in shaping the cultural significance of hand-fasting. During this time, Highland clans would often engage in hand-fasting ceremonies as a way of solidifying alliances and securing loyalty among their members. This practice was particularly prevalent during times of war, when clan leaders sought to strengthen their bonds with one another.\n\nAnother key event that influenced hand-fasting traditions in Scotland was the country's emigration patterns. As Scots left their homeland to settle in other parts of the world, they brought their cultural practices and traditions with them. Hand-fasting, in particular, became an important way for Scottish expatriates to connect with their heritage and maintain a sense of community in their new surroundings. This led to the spread of hand-fasting practices worldwide, as Scottish emigrants adapted and modified the tradition to suit their new environments.\n\nThe royal courts of Scotland also played a significant role in shaping hand-fasting traditions. In medieval times, members of the nobility would often engage in hand-fasting ceremonies as a way of formalising alliances and securing power. This practice was particularly prevalent during the reign of Queen Mary Stuart, who famously engaged in a hand-fasting ceremony with her cousin, Henry Stuart, Lord Darnley. The royal court's adoption of hand-fasting helped to solidify its place in Scottish culture, cementing its significance as a symbol of loyalty and commitment.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings"\n]	[]	\N	\N	\N
3	2	1	The Evolution of Hand-Fasting in Scotland's Historical Landscape	As we explore the evolution of hand-fasting in Scotland's historical landscape, it becomes clear that this ancient practice was intricately woven into the fabric of Scottish society. The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that. During the medieval period, hand-fasting was an integral part of Celtic tradition and mythology, with couples undergoing the ritual as a way of formalising their commitment to one another.\n\nHowever, with the introduction of Christianity, the practice of hand-fasting began to evolve. The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual. Despite this, hand-fasting continued to thrive, particularly in the Highlands where it remained an important part of clan culture. During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion.\n\nThe impact of the Reformation on hand-fasting was significant, leading to a decline in its practice as Christian marriage rites became more widespread. However, despite this, hand-fasting continued to survive in some form, particularly during times of social and political upheaval such as Scotland's clan wars. In these contexts, hand-fasting served as a way for couples to formalise their commitment to one another without necessarily adhering to the formalities of Christian marriage. This adaptability was key to the enduring legacy of hand-fasting in Scottish culture, allowing it to evolve and endure despite significant changes in Scotland's historical landscape.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Describe the historical context of hand-fasting during Scotland's clan wars"\n]	[\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual"\n]	\N	\N	\N
8	2	6	Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology	In Scottish folklore, hand-fasting is woven into a rich tapestry of myth and legend, often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry. This connection highlights the deep cultural significance of hand-fasting in Scotland's ancient traditions. As a symbol of commitment and devotion, hand-fasting is said to have been blessed by Brigid herself, imbuing it with her sacred power. In this context, the ritual takes on a spiritual dimension, transcending mere mortal bonds to become a union sanctioned by the divine.\n\nThe connection between hand-fasting and Scotland's ancient festivals is another thread in this rich folklore tapestry. Many of these festivals, such as Imbolc and Lughnasadh, celebrate themes of love, fertility, and harvest, all of which are closely tied to the ideals of hand-fasting. During these celebrations, hand-fasting ceremonies would often take place, solidifying bonds between couples under the watchful eyes of their community and the blessing of the land itself. This communal aspect of hand-fasting underscores its importance as a social glue, binding families and communities together in a shared celebration of love and commitment.\n\nIn exploring the mythical ties that bind hand-fasting to Scottish folklore, we glimpse a culture where love, poetry, and nature were deeply intertwined. The reverence for Brigid, patron goddess of these themes, speaks to a society that valued the sacred and the beautiful, seeking to infuse its most intimate relationships with the magic of myth and legend. As a result, hand-fasting in Scottish folklore takes on an almost mystical quality, evoking the power of ancient traditions and the enduring force of love itself.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Examine the connection between hand-fasting and Scotland's ancient festivals"\n]	[\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry"\n]	\N	\N	\N
7	2	5	Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies	One of Scotland's most beloved literary figures, Robert Burns, is perhaps one of the most famous Scots to have participated in a hand-fasting ceremony. In 1788, Burns tied the knot with Jean Armour in a traditional Scottish hand-fastening ritual, which was a common practice among the country's rural communities at the time. This ancient Celtic custom allowed couples to commit to each other for a year and a day, after which they could either formalise their union through marriage or part ways amicably.\n\nBurns' decision to opt for a hand-fasting ceremony has been interpreted by some as a reflection of his commitment to Scottish tradition and culture. As a proud advocate for the preservation of Scotland's folk heritage, Burns likely saw hand-fastening as a way to connect with his country's rich cultural past. Moreover, this ceremony allowed him to make a public declaration of his love for Jean Armour without immediately committing to marriage – a decision that may have been influenced by the societal norms and expectations surrounding marriage at the time.\n\nBurns' experience with hand-fasting has also been immortalised in his own writing, with references to the custom appearing in several of his poems. For example, in "Highland Mary", Burns describes the ritual as a sacred bond between two people, underscoring its importance in Scottish cultural tradition. Through his own life and work, Burns helped to popularise hand-fasting as a symbol of Scottish national identity, cementing its place in the country's rich cultural heritage.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns"\n]	[]	\N	\N	\N
4	2	2	Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting	The symbolism surrounding hand-fasting is a rich tapestry of cultural significance, woven from threads of Scottish folklore, mythology, and tradition. At its core, hand-fasting represents a deep commitment to one another, often sealed with the use of ribbons or cords that symbolize the binding nature of the partnership. In Scottish Highland culture, these ribbons were frequently made from the hair of the couple, signifying their intertwined fates and destinies. This practice was not unique to romantic partnerships, however – hand-fasting was also used to seal business agreements, alliances between clans, and even friendships, underscoring its importance as a ritual that transcended love alone.\n\nIn Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry. This connection imbues the practice with a deeper layer of meaning, linking it to the cycles of nature and the creative forces that shape human experience. The use of specific dates or seasons for hand-fasting ceremonies also holds significance, often coinciding with ancient festivals like Imbolc or Lughnasadh. These timing choices were thought to amplify the ritual's power, harnessing the energies of the natural world to consecrate the partnership.\n\nBeyond its connections to mythology and nature, hand-fasting holds distinct cultural significances in both Scottish Highland and Lowland cultures. In the Highlands, it was often seen as a way to strengthen clan ties and forge alliances between families, while in the Lowlands, it was more closely tied to agricultural cycles and the rhythms of rural life. Despite these regional variations, however, hand-fasting remains a potent symbol of commitment and loyalty across Scotland, speaking to a deeper sense of community and shared values that transcends geography and cultural heritage.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the cultural significance of hand-fasting in Scotland's Lowland culture"\n]	[\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships"\n]	\N	\N	\N
9	2	7	Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices	In recent years, there has been a notable resurgence of interest in traditional hand-fasting ceremonies, with many couples incorporating this ancient practice into their modern Scottish weddings. This revival can be attributed, in part, to the Victorian era's romanticization of Scottish culture, which helped to popularize hand-fasting as a motif in literature and art. As a result, hand-fasting has become a sought-after way for couples to connect with their Celtic heritage and add a touch of nostalgia to their special day.\n\nBeyond its appeal as a wedding ritual, hand-fasting has also been reinterpreted by modern pagan and druidic communities as a way to celebrate the cycles of nature and honor their ancestors. Today, some modern pagans and Wiccans still practice hand-fasting as a way to connect with their Celtic roots and mark important life milestones, such as solstices and equinoxes. This reinterpretation of traditional hand-fasting practices not only breathes new life into an ancient custom but also highlights the enduring appeal of this symbolic act.\n\nFrom a feminist perspective, hand-fasting has also taken on new significance in modern times. As a practice that was historically used to seal alliances and agreements between clans, hand-fasting can be seen as a symbol of female agency and autonomy. In contemporary Scotland, some women are embracing hand-fasting as a way to reclaim their cultural heritage and assert their independence, highlighting the complex and multifaceted nature of this ancient custom. As hand-fasting continues to evolve and adapt to modern times, it remains a powerful symbol of commitment, community, and connection to the past.	\N	\N	\N	\N	\N	\N	\N	\N	\N	[\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities"\n]	[\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	\N	\N	\N
2	2	0	Unraveling the Ancient Celtic Roots of Hand-Fasting	At its core, hand-fasting is a ritual steeped in ancient Celtic tradition and mythology. The origins of this practice can be traced back to pagan Celtic rituals that took place during the spring equinox, where hand-fasting ceremonies were performed to ensure fertility and prosperity for the coming year. These early ceremonies often featured items coloured red, a symbol of vitality and life force, which was deeply significant in Celtic culture.\n\nIn ancient Scotland, hand-fasting ceremonies were typically conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree. This act of binding was believed to forge a powerful symbolic bond between the two individuals, representing their commitment to one another and to the natural world around them. The use of natural materials in these rituals added an extra layer of significance, as it underscored the connection between human relationships and the cycles of nature.\n\nAs we delve deeper into the ancient Celtic roots of hand-fasting, it becomes clear that this practice was closely tied to Scotland's rich mythological heritage. In Celtic mythology, the sacred marriage between god and goddess was often seen as a symbol of cosmic harmony and balance. Hand-fasting ceremonies may have been seen as a way for couples to emulate this divine union, aligning their own relationship with the natural order of the universe. By examining these ancient roots, we can gain a deeper understanding of the cultural significance that hand-fasting has held in Scottish culture for centuries.	\N	\N	Section Illustration Prompt:\n\nIn a misty, ancient Celtic forest, a serene couple stands before a majestic, gnarled tree, its branches twisted with age. The druidic figure officiating their hand-fasting ceremony holds aloft a vibrant red cord made from the sacred tree's bark, as the first light of dawn breaks through the canopy above, casting dappled shadows on the forest floor. Amidst this mystical setting, the air is filled with an otherworldly energy, as if the spirits of Celtic mythology are gathered to witness the union.\n\nThis illustration concept captures the essence of Scotland's ancient Celtic roots and the mystique surrounding hand-fasting ceremonies. By incorporating symbolic elements such as the red cord and the sacred tree, the image invites viewers to step into a mystical world where human relationships are intertwined with nature and the cosmos. The dreamy atmosphere and soft lighting evoke a sense of timelessness, drawing the audience into the heart of Scotland's rich cultural heritage.	\N	\N	\N	\N	\N	\N	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Examine the connection between hand-fasting and Scotland's ancient mythology"\n]	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "Hand-fasting ceremonies always included items coloured red",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree"\n]	\N	\N	\N
10	4	0	Early Origins: The Great Kilt	<p>The earliest form of the kilt, known as the <b>'great kilt'</b> or <b>'feileadh mór'</b> in Gaelic, emerged in the 16th century. This versatile garment consisted of a large piece of tartan fabric, typically 4-6 yards in length, which was gathered and belted around the wearer's body. The lower portion formed a skirt-like garment, while the upper portion could be arranged as a cloak or draped over the shoulder. This early version served multiple purposes: clothing, blanket, and even temporary shelter, making it perfectly suited to the Highland way of life and climate.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
11	4	1	The Birth of the Modern Kilt	<p>The transformation to the modern kilt, or <b>'feileadh beag'</b> (small kilt), is often attributed to Thomas Rawlinson, an English Quaker who operated an ironworks in the Highlands during the 1720s. Observing his Highland workers struggling with the bulky great kilt around hot furnaces, he collaborated with the local chief to create a more practical garment. By removing the upper portion and creating permanent pleats, they developed what would become the foundation of the modern kilt. This adaptation made the garment more suitable for industrial work while retaining its distinctive appearance.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
12	4	2	Proscription and Revival	<p>Following the Jacobite Rising of 1745, the British government banned Highland dress, including kilts, through the <b>Dress Act of 1746</b>. This proscription, lasting until 1782, aimed to suppress Highland culture and clan loyalties. Paradoxically, this period of suppression may have contributed to the kilt's mystique and its later romantic revival. When the ban was lifted, the kilt had evolved from everyday wear to a symbol of Scottish identity and resistance to cultural suppression.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
13	4	3	Victorian Influence and Romanticization	<p>The kilt experienced a significant revival during the Victorian era, largely due to Queen Victoria's fascination with Highland culture and Sir Walter Scott's romantic depictions of Scottish life. This period saw the codification of many modern kilt traditions, including the association of specific tartans with particular clans. The <b>Highland societies</b> established during this time helped preserve and standardize kilt-wearing customs, though some argue this led to a somewhat idealized version of Highland dress.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
14	4	4	Military Adoption and Influence	<p>The incorporation of kilts into <b>Highland regiment uniforms</b> significantly influenced their development and prestige. Military kilts featured standardized pleating and specific tartans, setting precedents that would influence civilian dress. The bravery of kilted regiments in various conflicts enhanced the garment's martial reputation, though practical concerns eventually led to kilts being retired from combat use after World War I. However, their ceremonial role in military dress continues to this day.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
15	4	5	Modern Innovations and Adaptations	<p>Contemporary kilt-making has embraced both tradition and innovation. Modern kilts maintain the basic form developed in the 18th century but incorporate new materials, patterns, and construction techniques. <b>Fashion designers</b> have reinterpreted the kilt for contemporary wardrobes, while traditional craftsmen continue to hand-pleat and tailor kilts using time-honored methods. This balance between preservation and adaptation ensures the kilt's relevance in modern fashion while maintaining its cultural significance.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
16	4	6	Cultural Significance Today	<p>The kilt has transcended its Highland origins to become a powerful symbol of Scottish identity worldwide. Worn at weddings, graduations, and other formal occasions, it represents both personal and national pride. The garment has also influenced global fashion, with kilt-inspired designs appearing in contemporary collections. Despite these modern interpretations, traditional kilt-making remains a valued craft, with skilled artisans maintaining centuries-old techniques while adapting to current demands.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
17	5	0	Ancient History	<p>Long before clan tartans became a symbol of Scottish Highland clans, the peoples of what is now England were familiar with tartan-like patterns. <strong>Celtic</strong> inhabitants of the British Isles wore <strong>checkered</strong> garments; a reddish checkered tunic known as a <strong>bracca</strong> was documented among Celtic tribes, and the very word reflects its appearance. (The Welsh term <strong>brech</strong> and Gaelic <strong>breac</strong> both mean “checkered” or “speckled,” indicating that woven checks were part of ancient Celtic textile traditions.) Notably, the oldest physical evidence of tartan in Britain – a wool fragment found near Falkirk – dates to around the 3rd century AD. This fragment’s simple black-and-white checked pattern is identical to the traditional <strong>Northumberland tartan</strong>, suggesting such patterns were known in Roman-era Britain. Indeed, what later came to be called the Northumberland or “<strong>Shepherd’s Plaid</strong>” tartan was originally woven from the natural black and white fleece of sheep, without dyes, as a practical checkered cloth for shepherds.</p>\n<p>Through the medieval and early modern periods, tartan or plaids were not a mainstream feature of English dress. Tartan weaving and wearing largely persisted in the Scottish Highlands, where it became associated with clan identity, while in England it remained rare outside of border regions. Descriptions from the 16th–17th centuries note Highlanders wearing “mottled” or “sundrie coloured” plaids, but in England such boldly checked textiles held little cultural prominence. This began to change in the 18th and 19th centuries when tartan’s symbolic power grew – ironically due in part to English intervention. After the Jacobite Rising, the British government’s <strong>Dress Act of 1746</strong> banned Highland dress (including tartans) in Scotland in an attempt to suppress the clan culture. The ban was repealed in 1782, thanks largely to the lobbying of the <strong>Highland Society of London</strong> (an <strong>organisation</strong> of Scottish nobles in England), which sought to restore pride in Highland traditions. Thus, even as tartan was becoming a symbol of Scottish heritage, some of its champions were based in England, setting the stage for a broader adoption of tartan in Britain.</p>	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
18	5	1	Regional Examples	<p>In the 19th and 20th centuries, distinct tartans emerged to represent various regions of England, often inspired by local heritage or as modern creations to celebrate regional identity. One early example is the <strong>Northumberland tartan</strong>, also known as the Border tartan or <strong>Shepherd’s Plaid</strong>. This simple black-and-white check is steeped in history: it was traditionally worn by shepherds along the Anglo-Scottish Borders and later became associated with the Percy family, Dukes of Northumberland, who adopted it as the official tartan for their pipers in 1760. Textile historians even traced this pattern to the 3rd-century Falkirk fragment, indicating the design was known as far back as Roman times. Over the years, Northumberland’s shepherd’s check was reproduced using vegetable dyes in natural greens and browns, but its core symbolism lies in its antiquity and rustic origins – a direct link to the landscape and livelihoods of northern England.</p>\n<p>Moving southwest, <strong>Cornwall</strong> provides a notable case of a modern tartan tradition invented to express <strong>Celtic identity</strong> within England. The <strong>Cornish National Tartan</strong> was first created in 1963 by Cornish poet E.E. Morton Nance. Morton Nance explicitly viewed tartan as part of the heritage of <em>all</em> Celtic peoples, not just the Scots. He designed Cornwall’s tartan with <strong>colours</strong> rich in symbolism: a white cross on black background taken from <strong>Saint Piran’s flag</strong> (the flag of Cornwall) to represent Cornish patron saint St. Piran and the mining heritage, black and gold for the ancient kings of Dumnonia, red for the legs and beak of the <strong>Cornish chough</strong> (the national bird of Cornwall), and blue for the surrounding sea. The Cornish National tartan quickly became a proud emblem of Cornish identity, worn at Celtic gatherings (Morton Nance himself debuted it at the 1963 Celtic Congress). Its popularity led to the creation of a variant <strong>Cornish Hunting Tartan</strong> in 1984 – a subdued version with a dark green base, incorporating all the same colours in a muted form. This hunting tartan, designed collaboratively by the Redwood and Charnock families, was intended as a less bright alternative for everyday wear. It preserved the symbolism of the original while adding its own twist: the use of <strong>royal blue and gold</strong>, said to reflect the colours worn by Cornish wrestlers, connecting to another aspect of local culture.</p>\n<p>Inspired by the success of Cornwall’s tartans, other counties followed suit in the late 20th century. In the 1980s, residents of <strong>Devon</strong> — Cornwall’s neighbour — commissioned their own tartan. The <strong>Devon tartan</strong> (sometimes called “Devon Original”) was designed by Roy Sheard in 1989–1990, directly motivated by the enthusiasm for Cornwall’s St. Piran tartan. Woven at Coldharbour Mill, it was formally presented to the Mayor of Barnstaple in 1991 as Devon’s district tartan. A contemporary poem lauds how the tartan “retrieved” Devon’s beauty in its weave, indicating that the colours were chosen to evoke the county’s landscape — from its green countryside to perhaps the sea blue of its two coasts — and to celebrate Devon’s heritage. Further north, <strong>Yorkshire</strong> — England’s largest historic county — received its own tartan in 2005. <strong>The Spirit of Yorkshire</strong> tartan was designed by John C.C. Buckingham of Simpsons of Skipton, aiming to capture the beauty of Yorkshire and the hard work and enterprise of its people. While not an “ancient” tartan, this design served as a modern tribute to regional pride, and its registered description notes that it <strong>recognises</strong> the determination of Yorkshire folk.</p>\n<p>Even major cities have embraced tartan. Notably, the <strong>City of London</strong> – perhaps the most unexpected place to find a tartan – now has an official tartan of its own. In 2012, the Lord Mayor of London, Sir Roger Gifford (an enthusiast with Scottish roots), approved the <strong>City of London tartan</strong> for use in his office. This civic tartan incorporates the colours of England’s patron saint and the City’s heraldry: it features the red and white of <strong>St. George’s Cross</strong>, together with silver-grey derived from the City of London’s coat of arms. The design was registered with the Scottish Register of Tartans, making it an “official” tartan for England’s capital city. Although initially intended for use by City officials, practically anyone may wear it – a reminder that tartan patterns, even those with nominal restrictions, are ultimately open for all to enjoy. From northern frontiers like Northumberland and regional identities in Cornwall, to counties like Devon and Yorkshire and even the heart of London, English locales have adopted tartans as symbols of local heritage in the modern era.</p>\n<p>Below is a summary table of notable English tartans, their origins, status and symbolism:</p>\n<table>\n<thead>\n<tr>\n<th>Tartan</th>\n<th>Region</th>\n<th>Date / Designer</th>\n<th>Status</th>\n<th>Symbolism</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n<td>Northumberland (Border tartan)</td>\n<td>Northumberland (Borders)</td>\n<td>Ancient – traditional pattern (fragment c. 270 AD); designer unknown</td>\n<td>District tartan (historic; official pipers’ tartan of Percy family)</td>\n<td>Black-and-white <strong>shepherd’s check</strong> woven from undyed sheep’s wool, one of the oldest known tartans (traced to Roman Britain). Symbolic of the region’s pastoral life and antiquity.</td>\n</tr>\n<tr>\n<td>Cornish National</td>\n<td>Cornwall</td>\n<td>1963 – E. E. Morton Nance</td>\n<td>National tartan (cultural symbol of Cornwall)</td>\n<td>White cross on black for <strong>St. Piran’s flag</strong>; black &amp; gold for ancient Cornish kings; red for the <strong>Cornish chough</strong>’s legs/beak; blue for the surrounding sea. Celebrates Cornwall’s Celtic heritage.</td>\n</tr>\n<tr>\n<td>Cornish Hunting</td>\n<td>Cornwall</td>\n<td>1984 – S. Redwood &amp; B. Charnock</td>\n<td>“Hunting” tartan (alternate Cornish tartan for informal wear)</td>\n<td>Subdued version of Cornish tartan with a dark green base; incorporates all original colours. <strong>Royal blue and gold</strong> accents <strong>honour</strong> the colours of traditional Cornish wrestling attire.</td>\n</tr>\n<tr>\n<td>Devon</td>\n<td>Devon</td>\n<td>1990 – Roy Sheard</td>\n<td>District tartan (county tartan; presented to Devon officials)</td>\n<td>Colours inspired by Devon’s landscape and heritage – a tartan created to celebrate Devon’s beauty, following Cornwall’s example. Serves as a modern emblem of local pride.</td>\n</tr>\n<tr>\n<td>Yorkshire (The Spirit of)</td>\n<td>Yorkshire (England)</td>\n<td>2005 – John C.C. Buckingham</td>\n<td>District tartan (registered; unofficial county emblem)</td>\n<td>Designed to celebrate Yorkshire’s beauty and the “hardwork, determination and enterprise” of its people. Embodies the landscape (e.g. dales, moors) and industrious spirit of Yorkshire.</td>\n</tr>\n<tr>\n<td>City of London</td>\n<td>City of London</td>\n<td>2012 – Approved by Lord Mayor Roger Gifford</td>\n<td>City tartan (official tartan of the City of London Corporation)</td>\n<td>Red &amp; white of <strong>St. George’s Cross</strong> and silver-grey from the City’s coat of arms. <strong>Symbolises</strong> London’s English patronage and heraldic colours; created as a modern civic tradition.</td>\n</tr>\n</tbody>\n</table>	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
19	5	2	Textile Industry	<p>The proliferation of tartans beyond Scotland was closely tied to developments in the <strong>textile industry</strong> and changing technology. By the time tartan fever struck in the 19th century (during the reign of <strong>Queen Victoria</strong>), Britain – including the industrial heartlands of England – had the capacity to produce tartan on a large scale. The <strong>Industrial Revolution</strong> introduced <strong>power looms</strong> and mass production to weaving, which meant tartan patterns no longer had to be handwoven in the Highlands; they could be manufactured in mills anywhere. English textile mills in places like Lancashire and Yorkshire were well-positioned to contribute to the booming tartan trade. Indeed, the mid-19th century saw natural plant dyes giving way to <strong>synthetic chemical dyes</strong>, which were easier to use and allowed for brighter, more vivid tartan colours. This technological shift greatly expanded tartan’s palette and popularity. As one source notes, by the 1850s the advent of chemical dyes produced stronger, darker colours and helped fuel a “booming tartan industry” to meet growing demand. No longer limited by the local availability of plants or minerals for dyes, weavers (Scottish and English alike) could create eye-catching tartans in any hue, feeding a craze for tartan cloth that spread across Britain and beyond.</p>\n<p>The <strong>commercialisation</strong> of tartan was significantly influenced by English enterprise and patronage. After the repeal of the tartan ban in 1782, tartan rapidly transitioned from a banned rebel cloth to a celebrated symbol of Scottish (and British) identity. Market forces took over: enterprising businesses (some based in England) <strong>realised</strong> that there was money to be made in tartan fashion and souvenirs. By the 1820s, tailors in Edinburgh and London were responding to a surge of interest. The visit of King George IV to Edinburgh in 1822 – orchestrated by Sir Walter Scott – famously <strong>popularised</strong> tartan attire among the elites. Sir Walter Scott himself donned tartan trews (trousers) on occasion in England; one account even claims he wore Northumberland checked trousers in London, sparking “checks” as a trendy pattern in fashionable society. Production scaled up to meet such trends. Firms like William Wilson &amp; Sons of Bannockburn (Scotland) catalogued dozens of setts, and London outlets eagerly sold tartan garments and fabrics to English customers caught up in the romantic Highland vogue.</p>\n<p>By Victorian times, <strong>Queen Victoria and Prince Albert</strong> further boosted tartan’s profile through their personal enthusiasm. They purchased Balmoral Castle in 1848 and redecorated it extensively in tartan; Prince Albert personally designed the <strong>Balmoral tartan</strong> (a grey-based sett still used exclusively by the royal family) and Queen Victoria commissioned tartan garments, carpets, and décor, effectively turning Balmoral into a showcase of plaid. Their patronage underscored tartan’s status as a fashionable fabric. Under royal influence, tartan moved from Highland regiments into mainstream British fashion, with England’s textile mills helping supply the cloth. The once-humble checked wool of Gaelic peasants thus became a coveted product of a modern industry. The arrival of aniline dyes in the late 19th century made tartans even more vibrant and varied, and by this time tartan was being woven not just in Scotland but in English mills and around the world. As <strong>artificial dyes and power looms</strong> proliferated, tartan patterns also became easier to reproduce anywhere, breaking the regional link between tartans and their local natural dyes. This technological democratisation meant that tartans could be (and were) created for new purposes – companies, events, cities – far from their Highland origins. In short, industrial innovation, much of it centred in Britain and often driven by English manufacturers or entrepreneurs, was crucial in transforming tartan from a local tradition into a global commodity.</p>	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
20	5	3	National Identity	<p>Throughout the 19th and 20th centuries, tartan evolved into a potent symbol of <strong>national and regional identities</strong> – and not just for Scotland. For the English, tartan was initially an object of fascination and romanticism, tied to Britain’s view of Highland Scotland. Over time, however, certain tartans came to be used in expressions of English identity as well, merging Scottish tradition with English symbolism. A striking modern example is the <strong>English National Tartan</strong>, a pattern designed to represent England in the same way that Scotland, Ireland, and Wales each have national tartans. The English National Tartan is woven in bold blue, red and yellow tones with white and purple over-stripes. Its design encodes national icons: it deliberately embeds the red cross of <strong>St. George</strong> (England’s patron saint) in its pattern, and incorporates royal purple lines symbolising over a thousand years of English monarchical tradition. In essence, it takes a Scottish medium – tartan – and infuses it with distinctly English heraldic imagery. The very creation of an English National Tartan underscores an important point: tartan, though Scottish in origin, has been embraced as a broader British heritage symbol that English people can also claim and reinterpret.</p>\n<p>Historically, the English did not have clan tartans, but they did use tartan to express loyalty and unity in other ways. Military uniforms offer one example. Many <strong>British Army</strong> regiments recruited from Scotland or Ireland continued to wear tartan trews or kilts in their dress uniforms well into the 19th century. English-raised regiments did not typically have tartan uniforms (since tartan was seen as Highland dress), but when Highland regiments became part of the British Army, their tartans – such as Government Sett or <strong>Black Watch tartan</strong> – became part of the British military identity, <strong>honoured</strong> across the UK. At court, Queen Victoria’s love of tartan set trends that trickled into English society. It became fashionable for English nobles to decorate country homes in tartan and to wear tartan shawls or trews at social functions, signaling their participation in the mystique of the Highlands. Prince Albert’s <strong>Balmoral tartan</strong> was a royal tartan but effectively also an English one, since it was designed by a German prince for a British (largely English-led) monarchy. Likewise, the widespread use of the bright red <strong>Royal Stewart tartan</strong> as a sort of “universal” tartan owes much to its adoption by the royal family – and it’s now commonly worn by people of all backgrounds across the UK as a patriotic British symbol.</p>\n<p>In England proper, tartan often signifies a sense of <strong>cultural crossover</strong> – an acknowledgment of the shared history within the United Kingdom. For instance, when English people wear a tartan kilt to a wedding or a cultural event, they may be signaling British unity or personal ancestral links to Scotland, Ireland, or Wales. It’s uncommon for someone to wear a specific Scottish clan’s tartan without a personal connection (that would “raise eyebrows,” as one curator noted), but there are many non-clan tartans available for general use. In fact, contrary to popular myth, there are no strict rules preventing anyone (English or otherwise) from wearing most tartans – nearly all tartan designs are unrestricted and can be worn by anyone who likes them. This openness has allowed tartan to become part of English life in subtle ways: from school uniforms with tartan skirts, to Anglican church choirs donning tartan cassocks, to the choice of <strong>tartan accessories</strong> (ties, scarves, etc.) by English individuals as fashion statements that nod to a broader British heritage.</p>\n<p>Interestingly, English involvement was crucial in the great <strong>Highland Revival</strong> of the 19th century that cemented tartan as a national symbol. As mentioned, the <strong>Highland Society of London</strong> (founded 1778) played a pivotal role in ending the Proscription Act so that tartan could be worn again. That same society and other enthusiasts – many based in England – encouraged Highland chiefs to define clan tartans. The craze for tartans truly took off after King George IV’s 1822 visit, during which Scottish nobility (prompted by Sir Walter Scott) hastened to outfit themselves in distinctive tartans to greet the king. In the decades after, numerous tartan pattern books were published (some, like <strong>Vestiarium Scoticum</strong>, of dubious authenticity), and by the Victorian era the idea of specific tartans for specific clans or districts was widely accepted. It’s notable that this codification of tartans happened when Scotland was firmly integrated in the United Kingdom, with encouragement from the British (often English) establishment. What had been a regional Highland folk costume transformed into the <strong>symbolic national dress of Scotland</strong>, with the enthusiastic approval of the English monarchy and public. This demonstrates a kind of cross-cultural fertilisation: English interest helped elevate tartan to a symbol of national identity (for Scotland and Britain), and in turn tartan offered English people a romanticised link to a shared past.</p>\n<p>Today, England’s relationship with tartan is largely one of respect and imaginative adoption rather than ancestral claim. Aside from newer creations like county tartans or the St. George’s tartan, most English individuals who wear tartan do so as a celebration of the UK’s collective heritage or fashion preferences, not because they have their “own” centuries-old tartan pattern (as many Scots might with clan tartans). Even so, the emergence of English regional tartans in recent decades shows a desire to localise the tartan tradition. In places like Cornwall and Northumbria, tartans are now a part of expressing local identity – Cornish tartan kilts are worn at festivals and weddings, Northumberland’s check adorns everything from scarves to regional souvenirs. These symbols operate in parallel to flags and other emblems, enriching England’s tapestry of local identities with a pattern borrowed from the Highlands but tailored to English stories.</p>	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
21	5	4	Modern Design Movements	<p>In modern times, tartan has transcended its origins to become a global fashion statement – and English designers and subcultures have been at the forefront of this movement. One of the most influential figures in reinterpreting tartan through fashion is British designer <strong>Vivienne Westwood</strong>. In the late 20th century, Westwood and her contemporaries in the <strong>punk</strong> movement gave tartan a provocative new role. During the 1970s punk era in London, tartan was appropriated as a symbol of rebellion against conventional British society. Westwood famously incorporated tartan into her punk designs – most iconically, she and Malcolm McLaren introduced elements of the traditional kilt into punk attire. At their Seditionaries boutique, they draped tartan <strong>kilts</strong> over black bondage suits, transforming the kilt from a Highland aristocratic garment into a subversive punk uniform. This included the use of <strong>Royal Stewart tartan</strong> torn, safety-pinned, and reimagined as punk trousers or skirts – effectively giving a “middle finger” to British high society by turning a royal tartan on its head (as noted in one commentary on her work). Through Westwood’s influence, tartan became a staple of punk fashion, seen on iconic punk rock figures throughout the UK. What had once symbolised clan loyalty or royal pageantry was now a badge of counterculture defiance, seen on the streets of London, from King’s Road to Camden. The punk appropriation of tartan is a powerful example of how a traditional design was re-contextualised by English youth culture: tartan’s rules and connotations were upended, yet its visual impact remained – loud, plaid, and impossible to ignore.</p>\n<p>Beyond punk, tartan has remained perennially stylish. British fashion houses have continually found fresh inspiration in tartan, ensuring it remains in vogue. The luxury brand <strong>Burberry</strong> – an English company – introduced its famous <strong>Burberry check</strong> in the 1920s, originally as a lining for trench coats. This camel, black, red, and white plaid has since become one of the most recognisable tartans in the world, synonymous with British style and the Burberry label. Though not called a “tartan” by the company, the Burberry check is essentially a tartan sett; it demonstrates how an English brand took a tartan pattern and leveraged it for global branding success. In the late 20th century, the Burberry check even developed subcultural associations of its own (both aspirational and, at one point, “chav” street fashion in the UK), showing how dynamic the life of a tartan pattern can be in the public imagination.</p>\n<p>Contemporary fashion designers – both in England and internationally – often feature tartan on the runway, especially in autumn/winter collections, as a nod to heritage patterns reimagined in modern silhouettes. British designer <strong>Alexander McQueen</strong> (known for blending his Scottish ancestry with radical fashion) created entire collections around tartan, such as his 1995 “<strong>Highland Rape</strong>” show which used shredded tartan to comment on history, and his later “<strong>Widows of Culloden</strong>” collection (2006) featuring dramatic tartan gowns. Even outside of specifically British designers, tartan shows up in global couture and streetwear: Japanese punk and Lolita fashions incorporate tartan skirts; American preppy style has its own plaid variations; and tartan prints cycle through trends in everything from high-end suits to trainers. In 2023, tartan was celebrated in a major exhibition at the V&amp;A Dundee, highlighting its influence across design, from architecture to anime. The exhibit noted how tartan’s strong grid provides a framework “open to infinite possibility” for designers to play with.</p>\n<p>In England today, one might see tartan in the most traditional of contexts – for example, a bagpiper in London wearing a Scottish regimental kilt, or a newlywed couple incorporating a family tartan in their wedding attire – or in the most cutting-edge ways, like a London fashionista pairing a tartan skirt with a leather jacket. The pattern has proven remarkably adaptable. Modern design movements in England have tended to treat tartan as a kind of cultural palette: designers know its historical baggage (rebellion, tradition, clan, kitsch) and exploit those associations to make artistic or political statements. Whether it’s used to invoke nostalgia, as in interior designs that give an English cottage a “Highland cosy” feel with tartan throws, or to shock and subvert, as in punk and high fashion, tartan remains an endlessly intriguing motif. The continual reinvention of tartan by English designers and subcultures underlines a key point: tartan may originate from Scotland, but it resonates far beyond – in England it has been a canvas for expression, innovation, and identity, from the mills of the Industrial Revolution to the runways of London Fashion Week.</p>	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
22	6	0	Early Origins: Ancient Beginnings and Symbolic Meaning	<p>The <b>quaich</b>, derived from the Gaelic word <b>"cuach"</b> meaning cup, traces its origins to medieval Scotland. Archaeological evidence suggests early quaichs date back as far as the 16th century, though some theories posit even earlier roots. Initially carved from simple materials such as <b>wood</b>, <b>horn</b>, and <b>bone</b>, early quaichs represented more than mere drinking vessels; they symbolised peace, friendship, and trust, integral values within and between clans. Their distinctive <b>two-handled design</b> encouraged mutual trust, as both hands were visible, discouraging concealed weapons or hidden intentions.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
23	6	1	Symbol of Clan Unity and Hospitality	<p>Historically, the <b>quaich</b> became an essential feature in Highland <b>clan gatherings</b>. As clans formed alliances, resolved conflicts, or celebrated milestones, the shared drinking from a single quaich symbolised unity, trust, and mutual respect. Chieftains used larger ceremonial quaichs to signify status and generosity, while smaller quaichs passed among family and clan members reinforced bonds and kinship. This communal sharing ritual was fundamental to reinforcing social structures and building trust in communities defined by complex interpersonal relationships.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
24	6	2	Evolution of Design: Materials and Craftsmanship	<p>Initially, quaichs were crafted from locally available materials like <b>wood</b> and <b>horn</b>. Wooden quaichs, often turned from solid pieces of timber, were the most common. The technique of <b>"stave-built"</b> quaichs—using slats of wood bound by willow hoops—emerged later, demonstrating increased sophistication. By the 17th century, metal quaichs began to appear, first as luxury items among Scottish nobility, crafted in <b>silver</b> and adorned with intricate <b>Celtic</b> designs. <b>Pewter</b> quaichs became popular among the broader populace, more affordable yet elegant. By the 18th and 19th centuries, quaich craftsmanship had evolved significantly, incorporating detailed engraving, embellishments, and symbolic motifs, reflecting a blend of traditional and contemporary influences.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
25	6	3	Quaich and Royal Connections	<p>The <b>quaich's</b> significance extended beyond clan culture to the royal courts of Scotland and later Great Britain. Monarchs historically recognised its symbolic power, using ornate quaichs to cement alliances and friendships with visitors and dignitaries. Notably, <b>King James VI</b> of Scotland (later James I of England) is said to have embraced the tradition enthusiastically, gifting quaichs to foreign guests. Later royal visits, particularly by <b>Queen Victoria</b> and Prince Albert, brought renewed attention to Scottish customs, solidifying the quaich's status as a cherished symbol of Scottish heritage. Today, royal quaichs remain prized artifacts, often presented during state visits and ceremonial occasions, underscoring continued respect for the tradition at the highest levels.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
26	6	4	Quaich Traditions and Whisky: A Timeless Pairing	<p>Integral to the <b>quaich's</b> tradition is its association with Scotland's famous spirit: <b>whisky</b>. Historically, whisky became the beverage most commonly shared from quaichs, enhancing their symbolic significance as vessels of warmth and conviviality. This pairing helped cement Scotland's global reputation for hospitality, as visitors were warmly welcomed through a shared dram. Modern whisky-tasting rituals often incorporate the quaich, with distilleries and whisky societies preserving this tradition. This enduring pairing underscores the quaich's cultural resonance beyond its physical form, blending tangible heritage with Scotland's iconic drink.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
27	6	5	Cultural Decline and Revival	<p>During the 18th and 19th centuries, Scotland experienced significant social and political upheaval, including the suppression of Highland culture following the <b>Jacobite rebellions</b>. The <b>quaich</b>, along with other symbols of Gaelic heritage, suffered a decline in public prominence. Despite this, the tradition quietly persisted in rural and Highland communities, preserved by families committed to their ancestral customs. By the late 19th and early 20th centuries, a <b>cultural revival</b> began, partly influenced by renewed interest in Scottish history, folklore, and nationalism. The quaich regained popularity as a national symbol, supported by renewed scholarly attention and a growing tourism industry eager to celebrate authentic Scottish traditions.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
28	6	6	The Quaich in Contemporary Scottish Culture	<p>Today, the <b>quaich</b> remains firmly embedded in Scottish life, extending beyond historical ceremony into contemporary celebrations and international relations. <b>Weddings</b> frequently include a quaich ceremony, reinforcing its timeless message of unity and partnership. Quaichs have become popular gifts for milestone events such as anniversaries, retirements, and graduations, symbolising ongoing goodwill. Scottish <b>diaspora</b> communities worldwide cherish quaichs as meaningful connections to their ancestral roots, passing down family heirlooms through generations. Its simplicity, symbolism, and elegance ensure the quaich continues to resonate deeply, both in Scotland and internationally.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
29	6	7	Quaich as a Modern Symbol of Friendship and Diplomacy	<p>In recent decades, the <b>quaich</b> has evolved into an international symbol of friendship and <b>diplomacy</b>. Scotland's government and civic leaders frequently present quaichs during diplomatic exchanges, highlighting their role as tangible gestures of goodwill and mutual respect. Major international events, conferences, and sporting tournaments held in Scotland often feature ceremonial presentations involving quaichs, symbolising trust, shared goals, and intercultural harmony. This modern diplomatic role underscores how deeply the quaich's symbolism has permeated beyond its traditional clan origins, becoming a universally recognisable symbol of friendship.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
30	6	8	Collecting Quaichs: Preservation and Modern Appeal	<p>The <b>quaich's</b> rich history, beautiful craftsmanship, and symbolic resonance have made it highly collectible. Antique quaichs, especially those crafted from <b>silver</b> or engraved with historical significance, attract significant interest among <b>collectors</b>, historians, and enthusiasts worldwide. Modern artisans continue to produce quaichs using traditional techniques while integrating contemporary styles and materials, such as stainless steel or ceramic. These modern adaptations ensure the quaich remains accessible and relevant to a diverse audience. Museums, galleries, and cultural centers across Scotland prominently display quaich collections, celebrating their historical significance and educating visitors on their cultural value.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
31	6	9	The Quaich in Ceremony and Celebration	<p>Quaichs featured prominently in significant life events and celebrations, marking births, <b>weddings</b>, funerals, and farewells. In marriage ceremonies, newlyweds traditionally drank from the <b>quaich</b>, symbolising their commitment to share life's joys and sorrows. <b>Baptisms</b> often involved a quaich as a vessel for blessing and welcoming newborns into the community. The quaich also featured in farewell ceremonies, offering departing friends a final symbolic gesture of goodwill and remembrance. Its presence in these personal rites reinforced its symbolic meaning of friendship, unity, and collective memory.</p>\n	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: post_tags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.post_tags (post_id, tag_id) FROM stdin;
\.


--
-- Data for Name: tag; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tag (id, name, slug, description) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."user" (id, username, email, password_hash, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workflow_status; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_status (id, post_id, conceptualisation, authoring, meta_status, images, validation, publishing, syndication, log, last_updated) FROM stdin;
\.


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.category_id_seq', 1, false);


--
-- Name: image_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_format_id_seq', 34, true);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_id_seq', 161, true);


--
-- Name: image_prompt_example_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_prompt_example_id_seq', 1, false);


--
-- Name: image_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_setting_id_seq', 1, true);


--
-- Name: image_style_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_style_id_seq', 6, true);


--
-- Name: llm_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_action_history_id_seq', 25, true);


--
-- Name: llm_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_action_id_seq', 8, true);


--
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 1, true);


--
-- Name: llm_interaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_interaction_id_seq', 1, false);


--
-- Name: llm_prompt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 13, true);


--
-- Name: post_development_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.post_development_id_seq', 2, true);


--
-- Name: post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.post_id_seq', 6, true);


--
-- Name: post_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.post_section_id_seq', 31, true);


--
-- Name: tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tag_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: workflow_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_status_id_seq', 1, false);


--
-- Name: category category_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_name_key UNIQUE (name);


--
-- Name: category category_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_pkey PRIMARY KEY (id);


--
-- Name: category category_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_slug_key UNIQUE (slug);


--
-- Name: image_format image_format_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_format
    ADD CONSTRAINT image_format_pkey PRIMARY KEY (id);


--
-- Name: image_format image_format_title_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_format
    ADD CONSTRAINT image_format_title_key UNIQUE (title);


--
-- Name: image image_path_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_path_key UNIQUE (path);


--
-- Name: image image_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);


--
-- Name: image_prompt_example image_prompt_example_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_pkey PRIMARY KEY (id);


--
-- Name: image_setting image_setting_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_name_key UNIQUE (name);


--
-- Name: image_setting image_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_pkey PRIMARY KEY (id);


--
-- Name: image_style image_style_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_style
    ADD CONSTRAINT image_style_pkey PRIMARY KEY (id);


--
-- Name: image_style image_style_title_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_style
    ADD CONSTRAINT image_style_title_key UNIQUE (title);


--
-- Name: llm_action_history llm_action_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action_history
    ADD CONSTRAINT llm_action_history_pkey PRIMARY KEY (id);


--
-- Name: llm_action llm_action_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_pkey PRIMARY KEY (id);


--
-- Name: llm_config llm_config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_pkey PRIMARY KEY (id);


--
-- Name: llm_interaction llm_interaction_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_interaction
    ADD CONSTRAINT llm_interaction_pkey PRIMARY KEY (id);


--
-- Name: llm_prompt llm_prompt_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_prompt
    ADD CONSTRAINT llm_prompt_pkey PRIMARY KEY (id);


--
-- Name: post_categories post_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_categories
    ADD CONSTRAINT post_categories_pkey PRIMARY KEY (post_id, category_id);


--
-- Name: post_development post_development_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_development
    ADD CONSTRAINT post_development_pkey PRIMARY KEY (id);


--
-- Name: post_development post_development_post_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_development
    ADD CONSTRAINT post_development_post_id_key UNIQUE (post_id);


--
-- Name: post post_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_pkey PRIMARY KEY (id);


--
-- Name: post_section post_section_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_section
    ADD CONSTRAINT post_section_pkey PRIMARY KEY (id);


--
-- Name: post post_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_slug_key UNIQUE (slug);


--
-- Name: post_tags post_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_pkey PRIMARY KEY (post_id, tag_id);


--
-- Name: tag tag_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_name_key UNIQUE (name);


--
-- Name: tag tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_pkey PRIMARY KEY (id);


--
-- Name: tag tag_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_slug_key UNIQUE (slug);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
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
-- Name: idx_workflow_status_post; Type: INDEX; Schema: public; Owner: nickfiddes
--

CREATE INDEX idx_workflow_status_post ON public.workflow_status USING btree (post_id);


--
-- Name: user update_user_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON public."user" FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: image_prompt_example image_prompt_example_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_format_id_fkey FOREIGN KEY (format_id) REFERENCES public.image_format(id);


--
-- Name: image_prompt_example image_prompt_example_image_setting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_image_setting_id_fkey FOREIGN KEY (image_setting_id) REFERENCES public.image_setting(id);


--
-- Name: image_prompt_example image_prompt_example_style_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_prompt_example
    ADD CONSTRAINT image_prompt_example_style_id_fkey FOREIGN KEY (style_id) REFERENCES public.image_style(id);


--
-- Name: image_setting image_setting_format_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_format_id_fkey FOREIGN KEY (format_id) REFERENCES public.image_format(id);


--
-- Name: image_setting image_setting_style_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image_setting
    ADD CONSTRAINT image_setting_style_id_fkey FOREIGN KEY (style_id) REFERENCES public.image_style(id);


--
-- Name: llm_action_history llm_action_history_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action_history
    ADD CONSTRAINT llm_action_history_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.llm_action(id);


--
-- Name: llm_action_history llm_action_history_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action_history
    ADD CONSTRAINT llm_action_history_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: llm_action llm_action_prompt_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_prompt_template_id_fkey FOREIGN KEY (prompt_template_id) REFERENCES public.llm_prompt(id);


--
-- Name: llm_interaction llm_interaction_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_interaction
    ADD CONSTRAINT llm_interaction_prompt_id_fkey FOREIGN KEY (prompt_id) REFERENCES public.llm_prompt(id);


--
-- Name: post_categories post_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_categories
    ADD CONSTRAINT post_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.category(id);


--
-- Name: post_categories post_categories_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_categories
    ADD CONSTRAINT post_categories_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post_development post_development_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_development
    ADD CONSTRAINT post_development_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post post_header_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_header_image_id_fkey FOREIGN KEY (header_image_id) REFERENCES public.image(id);


--
-- Name: post_section post_section_image_prompt_example_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_section
    ADD CONSTRAINT post_section_image_prompt_example_id_fkey FOREIGN KEY (image_prompt_example_id) REFERENCES public.image_prompt_example(id);


--
-- Name: post_section post_section_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_section
    ADD CONSTRAINT post_section_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post_tags post_tags_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id);


--
-- Name: post_tags post_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post_tags
    ADD CONSTRAINT post_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag(id);


--
-- Name: TABLE "user"; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public."user" TO PUBLIC;


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

