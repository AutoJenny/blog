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
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
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
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
ff2e0abbead0
\.


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.category (id, name, slug, description) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image (id, filename, original_filename, path, alt_text, caption, image_prompt, notes, image_metadata, watermarked, watermarked_path, created_at, updated_at) FROM stdin;
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

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


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

SELECT pg_catalog.setval('public.post_id_seq', 2, true);


--
-- Name: post_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.post_section_id_seq', 9, true);


--
-- Name: tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tag_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


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
-- PostgreSQL database dump complete
--

