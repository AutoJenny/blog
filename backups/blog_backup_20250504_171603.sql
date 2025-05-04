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
    prompt_template_id integer NOT NULL
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
    updated_at timestamp without time zone
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
    facts_to_include text
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
58314d0e0047
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
-- Data for Name: llm_action; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_action (id, prompt_template, llm_model, temperature, created_at, updated_at, field_name, max_tokens, prompt_template_id) FROM stdin;
6	You are an experienced editor and content strategist. Your task is to analyze the blog post title and content below intended for a blog article on Scottish culture and heritage.\nGroup and organize the content into a logical structure by identifying distinct thematic sections.\nReturn only a JSON array of paragraph titles that represent the structure of the final article.\nEach title should be concise, descriptive, and reflect a key theme from the text.\nDo not include any explanation, commentary, or full text of the paragraphs. Return only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.\n---\n\nTitle: {{provisional_title}}\n\nScope of ideas:\n{{idea_scope}}\n\nSome interesting facts: 	llama3.1:70b	0.7	2025-05-04 12:57:21.257811	2025-05-04 13:15:38.601902	Outlining section headings	1000	10
3	You are an expert historical researcher and cultural writer specializing in Scottish history, traditions, and heritage. Your task is to expand the basic idea of {{basic_idea}} into an around 50 (fifty) ideas that outline and describe the full scope of an in-depth blog article about that topic in Scottish culture. Suggest (for example) different historical angles, cultural significance, social impact, key events or periods, folklore, notable figures, and/or modern relevance. Focus on breadth of ideas without writing the actual article — this list will as a guide for what should be covered in a full blog post. Keep each idea succinct but be imaginative, including both grand scale ideas and micro ideas. Return only a JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	llama3.1:70b	0.7	2025-05-03 15:34:47.074891	2025-05-04 14:40:15.628692	Idea Scope from Basic Idea	3000	7
4	You are a professional copywriter and editor specializing in digital publishing and historical blogging.\n\nYour task is to generate one catchy and engaging blog title suitable for a wide audience from the ideas provided below. This is especially those interested in Scottish culture and heritage. The title should be compelling, relevant to the content, and appropriate for web publication.\n\nReturn only the title with no explanation, commentary, or additional text. Do NOT enclose it in quote marks.\n\n\nYour topic is the following:\n\t1.\tThe basic idea of: {{basic_idea}}\n\t2.\tTheses topics and angles:\n{{idea_scope}}	llama3.1:70b	0.7	2025-05-04 11:31:21.820742	2025-05-04 11:39:17.573338	Generate blog title	1000	8
5	You are a researcher specialising in finding curious facts for blog articles for specialist audiences. You have been commissioned to assist with an article about {{basic_idea}} which will examine in depth these ideas {{idea_scope}}.\n\nPlease do a deep dive into this topic and provide a list of up to ten unusual and interesting facts that people might not know, to make this article worth reading. \n\nReturn only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.”	llama3.1:70b	0.9	2025-05-04 12:37:27.007623	2025-05-04 13:15:28.400889	Interesting facts	1000	9
\.


--
-- Data for Name: llm_action_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_action_history (id, action_id, input_text, output_text, post_id, status, error_message, created_at) FROM stdin;
1	3		However, I don't see an input topic provided. Please share the topic you'd like me to write about, and I'll craft a short, meaningful poem for you.\n\nIf you're feeling stuck, here are some prompts to get you started:\n\n* A season or time of year\n* A personal experience or memory\n* A natural wonder or landscape\n* A social issue or cause\n* An emotion or feeling\n\nLet me know when you have a topic in mind, and I'll begin writing your poem!	1	success	\N	2025-05-04 09:45:17.860751
2	3		However, I don't see a "Basic Idea" provided. Could you please give me a basic idea or theme for the poem? It could be anything: nature, love, hope, freedom, etc.\n\nIf not, I can suggest some prompts to get started:\n\n* A peaceful morning\n* A walk on the beach\n* The beauty of stars at night\n* A cup of hot coffee on a chilly day\n* A child's laughter\n\nLet me know if any of these resonate with you, or feel free to provide your own idea!	2	success	\N	2025-05-04 09:49:22.380804
3	3		I'd be happy to! However, I don't see a basic idea specified. Could you please provide one?\n\nIf not, I can suggest some prompts:\n\n* Nature\n* Love\n* Hope\n* Dreams\n* Inspiration\n\nPlease choose one, or give me your own idea, and I'll write a short poem for you!	2	success	\N	2025-05-04 09:50:50.734394
4	3		\N	2	error	Error processing prompt template: expected token 'end of print statement', got 'Idea'	2025-05-04 10:11:08.965936
5	3		\N	2	error	Error processing prompt template: expected token 'end of print statement', got 'Idea'	2025-05-04 10:24:41.684244
6	3		\N	2	error	Error processing prompt template: expected token 'end of print statement', got 'Idea'	2025-05-04 10:27:19.786837
7	3		\N	2	error	Error processing prompt template: expected token 'end of print statement', got 'Idea'	2025-05-04 10:32:41.455518
8	3		Here is a short poem about hand-fasting:\n\nTied by threads of love and fate,\nOur hands entwined, a sacred state.\nIn ancient ritual, we make our vow,\nTo stand together, through all life's plow.\n\nThe cord that binds us, strong and true,\nA symbol of commitment, shining through.\nWith every knot, our hearts beat as one,\nTogether bound, beneath the sun.\n\nMay our love be woven like a braid,\nStronger with each passing day.\nAnd when our hands are finally laid to rest,\nOur bond will remain, forever blessed.	2	success	\N	2025-05-04 10:33:24.831177
9	3		\N	2	error	Error processing prompt template: unexpected char '\\x7f' at 22	2025-05-04 11:11:35.222267
10	3		Entwined fingers, a symbol true,\nOf love and commitment, forever anew.\nA cord or ribbon, wrapped 'round with care,\n Binding hearts together, a promise to share.\n\nIn ancient traditions, this ritual was born,\nA way to seal vows, on a wedding morn.\nThe couple's hands, clasped tight as one,\nAs they pledge their love, beneath the sun.\n\nTheir fingers intertwined, a knot is tied,\nA physical representation, of their hearts inside.\nThrough joys and struggles, through laughter and tears,\nTheir bond will remain, for all their years.\n\nThe hand-fasting cord, a reminder every day,\nOf the vows they made, in a loving way.\nA symbol of unity, a promise to stand,\nTogether forever, hand in hand.\n\nAs the cord is wrapped, their love shines bright,\nA beacon of hope, on this sacred night.\nTheir hearts beating as one, their love will grow,\nIn this eternal bond, their spirits will glow.\n\nThe hand-fasting ritual, a beautiful sight,\nA celebration of love, that shines so bright.\nA promise to cherish, to honor and adore,\nForever entwined, in love's sweet core.	2	success	\N	2025-05-04 11:14:57.115407
11	3		This in-depth blog article delves into the rich cultural heritage of hand-fasting, an ancient Celtic tradition that has its roots in Scotland's pagan past. We'll explore the historical evolution of hand-fasting from its early beginnings as a ritualistic promise of marriage, to its Christianization and subsequent absorption into Scottish folk customs. Through a nuanced examination of medieval records, 17th-century marriage contracts, and folklore collections, we'll uncover the social significance of hand-fasting in Scotland's rural communities, where it served as a vital means of securing alliances, resolving disputes, and ensuring family prosperity. Key events and periods to be covered include the Viking invasions, the Wars of Scottish Independence, and the 18th-century Clearances, all of which influenced the development and practice of hand-fasting. The article will also delve into the cultural symbolism surrounding the ritual, including the use of ribbons, cords, and other binding materials, as well as its connections to ancient Celtic festivals and deities. Notable figures such as Mary Queen of Scots and Robert Burns will be featured, highlighting their own experiences with hand-fasting and its impact on Scottish literature and art. Additionally, we'll explore how hand-fasting has influenced modern wedding customs, from the revival of pagan and folk practices in contemporary Scotland to its adoption by couples worldwide seeking a unique and meaningful way to formalize their commitment. Throughout the article, we'll draw upon the work of Scottish historians, folklorists, and cultural experts to provide a comprehensive understanding of hand-fasting's enduring significance in Scotland's rich cultural heritage.	2	success	\N	2025-05-04 11:19:51.174432
12	3		Here's an expanded outline for a comprehensive blog article on hand-fasting in Scottish culture:\n\n**Historical Angles:**\n\n* Origins: Explore the ancient Celtic and Pagan roots of hand-fasting, including its connection to fertility rituals and agricultural cycles.\n* Medieval period: Discuss how hand-fasting was used as a trial marriage or betrothal agreement among the nobility and aristocracy.\n* Jacobite era: Examine the role of hand-fasting in secret marriages during the 18th-century Jacobite risings.\n\n**Cultural Significance:**\n\n* Symbolism: Delve into the symbolism behind hand-fasting, including the binding of hands as a representation of commitment, unity, and loyalty.\n* Community involvement: Discuss how hand-fasting was often a communal affair, involving friends, family, and neighbors in the ritual.\n* Social status: Explore how hand-fasting reflected social standing, with more elaborate ceremonies for higher-ranking individuals.\n\n**Social Impact:**\n\n* Marriage laws: Explain how hand-fasting influenced Scottish marriage laws, including the 1560 Reformation's introduction of formal marriage ceremonies.\n* Women's rights: Discuss how hand-fasting allowed women some agency in choosing their partners and negotiating marriage terms.\n* Family dynamics: Examine how hand-fasting affected family relationships, including the role of kinship ties and inheritance.\n\n**Key Events or Periods:**\n\n* The 13th-century "Black Death" and its impact on hand-fasting practices\n* The 16th-century Reformation and the rise of Protestantism's influence on Scottish marriage customs\n* The 19th-century Romantic movement and the revival of interest in hand-fasting as a symbol of Scottish heritage\n\n**Folklore and Mythology:**\n\n* Explore Celtic mythology surrounding hand-fasting, including stories of the god Cernunnos and the goddess Brigid.\n* Discuss the role of the "hand-fastening" ceremony in Scottish folklore, including its association with fairies and supernatural beings.\n\n**Notable Figures:**\n\n* Mary Queen of Scots and her hand-fasting to Henry Stuart, Lord Darnley\n* The famous 17th-century Scottish witch, Janet Horne, who was accused of using hand-fasting as a form of dark magic\n* Sir Walter Scott's depiction of hand-fasting in his novels, such as "Ivanhoe" and "The Bride of Lammermoor"\n\n**Modern Relevance:**\n\n* Contemporary Pagan and Wiccan practices that incorporate hand-fasting rituals\n* The use of hand-fasting in modern Scottish weddings and commitment ceremonies\n* Hand-fasting as a symbol of Scottish cultural heritage, including its representation in art, literature, and film.\n\nThis outline provides a solid foundation for exploring the complexities and nuances of hand-fasting in Scottish culture. By delving into these various aspects, your blog article can offer a rich and engaging exploration of this fascinating topic.	2	success	\N	2025-05-04 11:25:38.37256
13	3		Here's an outline of potential bullet points to cover in an in-depth blog article about hand-fasting in Scottish culture:\n\n**Historical Angles:**\n\n* Ancient Celtic and Pictish origins of hand-fasting\n* Influence of Christianity on hand-fasting practices in Scotland\n* Evolution of hand-fasting during the Middle Ages, Renaissance, and Enlightenment periods\n* Comparison with similar customs in other European cultures (e.g., Welsh and Irish)\n\n**Cultural Significance:**\n\n* Symbolism of binding hands as a representation of commitment, loyalty, and unity\n* Importance of hand-fasting in Scottish folklore, mythology, and fairy tales\n* Role of hand-fasting in traditional Scottish weddings, including Highland and Lowland customs\n\n**Social Impact:**\n\n* Hand-fasting as a means of securing alliances between families and clans\n* Economic implications of hand-fasting, such as dowries and land ownership\n* Social status and class implications of hand-fasting among different strata of Scottish society\n\n**Key Events or Periods:**\n\n* The Act of Proscription (1746) and its impact on traditional Highland practices, including hand-fasting\n* The Victorian era's romanticization of Scottish culture and the revival of hand-fasting as a wedding tradition\n* Modern-day revivals of hand-fasting in Scotland, particularly among neo-pagans and cultural heritage enthusiasts\n\n**Folklore:**\n\n* Stories of famous hand-fastings, such as those between Robert the Bruce and Elizabeth de Burgh or Mary Queen of Scots and Francis II of France\n* Superstitions surrounding hand-fasting, including luck, fertility, and protection from evil spirits\n* Connection to Scottish mythology, such as the story of the Selkies (seal people)\n\n**Notable Figures:**\n\n* Historical figures who participated in hand-fastings, such as clan leaders, monarchs, or notable Scots\n* Literary and artistic depictions of hand-fasting in works by Robert Burns, Sir Walter Scott, and other Scottish writers\n\n**Modern Relevance:**\n\n* Contemporary uses of hand-fasting in weddings, commitment ceremonies, and pagan rituals\n* Influence of Scottish cultural heritage on modern Western wedding traditions\n* Intersection with LGBTQ+ rights and same-sex marriage debates\n\n**Other Potential Angles:**\n\n* Archaeological evidence of ancient hand-fasting practices\n* Connection to other Scottish customs, such as ceilidhs, Highland games, or tartan traditions\n* Comparison with similar customs in other cultures, such as African or Native American communities\n\nThis outline should provide a comprehensive foundation for an in-depth blog article about the rich history and cultural significance of hand-fasting in Scotland.	2	success	\N	2025-05-04 11:32:41.84245
14	4		"Tied Together: The Ancient Scottish Tradition of Hand-Fasting"	2	success	\N	2025-05-04 11:33:03.921645
15	3		Here is an expanded outline of potential angles and points to cover in a comprehensive blog article about hand-fasting in Scottish culture:\n\n**Historical Angles:**\n\n• Origins of hand-fasting in ancient Celtic cultures\n• Influence of Christianity on hand-fasting traditions\n• Medieval and Renaissance-era hand-fasting practices\n• Jacobite era and the role of hand-fasting in clan politics\n\n**Cultural Significance:**\n\n• Symbolism of binding hands as a representation of commitment\n• Hand-fasting as a symbol of unity and cooperation between families or clans\n• Role of hand-fasting in Scottish folklore and mythology\n• Connection to other Celtic traditions, such as knotwork and symbolism\n\n**Social Impact:**\n\n• Historical context of hand-fasting as a means of securing alliances and marriage agreements\n• Social status and class implications of hand-fasting\n• Hand-fasting as a way to formalize relationships between women and men in patriarchal society\n• Influence on Scottish wedding traditions and modern-day hand-fasting ceremonies\n\n**Key Events or Periods:**\n\n• The 16th-century Acts of the Parliament of Scotland, which attempted to regulate hand-fasting practices\n• The Jacobite Risings and their impact on hand-fasting as a symbol of loyalty and allegiance\n• The Victorian era's romanticization of Scottish culture and its influence on modern hand-fasting traditions\n\n**Folklore:**\n\n• Stories of mythical figures and gods who used hand-fasting in ancient Celtic mythology\n• Tales of Scottish clans and families using hand-fasting to seal alliances and agreements\n• Superstitions surrounding the act of hand-fasting, such as the importance of timing and location\n\n**Notable Figures:**\n\n• Historical accounts of notable Scots who participated in hand-fasting ceremonies, such as Mary Queen of Scots or Rob Roy MacGregor\n• Writers and artists who romanticized hand-fasting in their works, such as Robert Burns or Sir Walter Scott\n• Modern-day Scottish figures who have incorporated hand-fasting into their own wedding ceremonies\n\n**Modern Relevance:**\n\n• Contemporary hand-fasting practices and ceremonies in Scotland and beyond\n• Influence of modern pagan and Wiccan traditions on the revival of hand-fasting\n• Use of hand-fasting as a symbol of commitment and unity in LGBTQ+ communities\n• Adaptation of hand-fasting into non-traditional wedding ceremonies and rituals	2	success	\N	2025-05-04 11:40:15.125293
16	4		Tying the Knot: Unraveling Scotland's Ancient Tradition of Hand-Fasting	2	success	\N	2025-05-04 12:00:44.543856
17	5		• In ancient Celtic cultures, hand-fasting was not only a symbol of commitment but also a way to ensure fertility, as the binding of hands was believed to bring good luck and prosperity to the couple's future offspring.\n\n• The earliest recorded evidence of hand-fasting in Scotland dates back to the 10th century, when it was mentioned in the Scottish Gaelic poem "Aislinge Meic Conglinne" (The Vision of MacConglinne).\n\n• In medieval Scotland, hand-fasting was often used as a way for clans to secure alliances and marriages, with the binding of hands serving as a symbol of unity and cooperation between families.\n\n• The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to declare their intention to marry before witnesses, but this did not stop the practice from continuing in secret.\n\n• In Scottish folklore, it was believed that if a couple's hands were bound with a ribbon or cord made from wool, they would be protected from evil spirits and curses.\n\n• The Jacobite Risings of the 17th and 18th centuries saw hand-fasting become a powerful symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the practice to pledge their support for Charles Edward Stuart (Bonnie Prince Charlie).\n\n• Robert Burns, Scotland's national poet, wrote about hand-fasting in his poem "The Jolly Beggars", describing it as a way for couples to show their love and commitment to each other.\n\n• In some parts of Scotland, particularly the Highlands, hand-fasting was believed to have magical properties, with the binding of hands thought to bring good luck and prosperity to the couple's future endeavors.\n\n• The Victorian era's romanticization of Scottish culture led to a resurgence in interest in hand-fasting, with many writers and artists depicting it as a picturesque and charming aspect of Highland life.\n\n• In modern times, hand-fasting has been incorporated into wedding ceremonies by couples from diverse cultural backgrounds, including LGBTQ+ communities, who see the practice as a powerful symbol of commitment, unity, and love.	2	success	\N	2025-05-04 12:45:34.52352
18	6		Here is the JSON array of paragraph titles that represent the structure of the final article:\n\n```\n[\n  "Unraveling the Ancient Roots of Hand-Fasting",\n  "The Evolution of Hand-Fasting in Scottish Culture",\n  "A Symbol of Unity and Cooperation",\n  "Securing Alliances and Marriage Agreements",\n  "Regulation and Rebellion: The Impact of the Acts of Parliament",\n  "Romanticizing the Past: Victorian-Era Influences on Modern Hand-Fasting",\n  "Mythical Tales and Superstitions Surrounding Hand-Fasting",\n  "Notable Scots Who Tied the Knot with Hand-Fasting",\n  "Reviving Ancient Traditions in Modern Times",\n  "Hand-Fasting Beyond Scotland: Global Adaptations and Interpretations"\n]\n```	2	success	\N	2025-05-04 12:58:12.00059
19	6	Here is the JSON array of paragraph titles that represent the structure of the final article:\n\n```\n[\n  "Unraveling the Ancient Roots of Hand-Fasting",\n  "The Evolution of Hand-Fasting in Scottish Culture",\n  "A Symbol of Unity and Cooperation",\n  "Securing Alliances and Marriage Agreements",\n  "Regulation and Rebellion: The Impact of the Acts of Parliament",\n  "Romanticizing the Past: Victorian-Era Influences on Modern Hand-Fasting",\n  "Mythical Tales and Superstitions Surrounding Hand-Fasting",\n  "Notable Scots Who Tied the Knot with Hand-Fasting",\n  "Reviving Ancient Traditions in Modern Times",\n  "Hand-Fasting Beyond Scotland: Global Adaptations and Interpretations"\n]\n```	[\n  "Unraveling the Ancient Celtic Roots of Hand-Fasting",\n  "The Evolution of Hand-Fasting in Scotland's Historical Landscape",\n  "Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting",\n  "Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements",\n  "A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions",\n  "Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology",\n  "Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies",\n  "Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices"\n]	2	success	\N	2025-05-04 13:16:36.046891
27	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	[\n  "Hand-fasting origins in ancient Celtic rituals",\n  "Early Christian influences on hand-fasting ceremonies",\n  "Medieval Scottish law and hand-fasting as a form of marriage contract",\n  "The role of clans and family ties in traditional hand-fasting practices",\n  "Symbolism of the binding ribbon or cord in hand-fasting",\n  "Different types of hand-fasting ceremonies: temporary, permanent, and conditional",\n  "Hand-fasting during times of war and its impact on Scottish society",\n  "Folklore surrounding hand-fasting and the supernatural",\n  "Notable historical figures who participated in hand-fasting ceremonies",\n  "Royal hand-fastings throughout Scottish history",\n  "The significance of hand-fasting in Scottish literature and poetry",\n  "Hand-fasting as a symbol of unity during times of conflict",\n  "Regional variations of hand-fasting across Scotland",\n  "Cultural exchange: how other cultures influenced Scottish hand-fasting traditions",\n  "The impact of the Reformation on hand-fasting practices in Scotland",\n  "Persecution and prohibition of hand-fasting ceremonies during certain periods",\n  "Revival of interest in hand-fasting during the Romantic era",\n  "Modern neo-pagan and Celtic Reconstructionist interpretations of hand-fasting",\n  "Hand-fasting as a feminist symbol of equality in relationships",\n  "Contemporary use of hand-fasting in non-traditional wedding ceremonies",\n  "Cultural appropriation: sensitive adoption of hand-fasting practices by non-Scottish communities",\n  "Comparative analysis with other cultures' forms of temporary or trial marriage",\n  "Ancient Celtic festivals and their connection to hand-fasting rituals",\n  "Seasonal significance of hand-fasting ceremonies in Scottish folklore",\n  "The role of music, poetry, and storytelling in traditional hand-fasting celebrations",\n  "Scottish art and craftsmanship inspired by hand-fasting symbolism",\n  "The psychology behind the commitment of hand-fasting",\n  "Historical records of hand-fasting among royalty and nobility",\n  "Social class differences in hand-fasting practices throughout history",\n  "Hand-fasting as a means of securing alliances between clans or families",\n  "Warrior culture: hand-fasting among Scottish warriors and mercenaries",\n  "Rites of passage: coming-of-age and hand-fasting in Scottish tradition",\n  "The symbolism of the hand-fasting ribbon in different colors",\n  "Regional tales of cursed or unlucky hand-fastings",\n  "Celebrity hand-fastings throughout history and their cultural impact",\n  "Influence of hand-fasting on modern wedding traditions",\n  "Hand-fasting as a symbol of devotion during times of plague or hardship",\n  "Archaeological evidence supporting ancient Celtic hand-fasting practices",\n  "Ancient Celtic gods and goddesses associated with love, marriage, and fertility",\n  "Pagan Celtic calendar: dates significant to hand-fasting rituals",\n  "The significance of the number seven in Scottish hand-fasting traditions",\n  "Hand-fasting among the Scots-Irish diaspora communities",\n  "Tartan patterns and their connection to specific clans or families in hand-fasting ceremonies",\n  "Music and song associated with traditional hand-fasting celebrations",\n  "Scottish folklore surrounding love, courtship, and marriage",\n  "The significance of whisky and other drinks in hand-fasting rituals"\n]	2	success	\N	2025-05-04 14:54:55.735696
20	5	• In ancient Celtic cultures, hand-fasting was not only a symbol of commitment but also a way to ensure fertility, as the binding of hands was believed to bring good luck and prosperity to the couple's future offspring.\n\n• The earliest recorded evidence of hand-fasting in Scotland dates back to the 10th century, when it was mentioned in the Scottish Gaelic poem "Aislinge Meic Conglinne" (The Vision of MacConglinne).\n\n• In medieval Scotland, hand-fasting was often used as a way for clans to secure alliances and marriages, with the binding of hands serving as a symbol of unity and cooperation between families.\n\n• The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to declare their intention to marry before witnesses, but this did not stop the practice from continuing in secret.\n\n• In Scottish folklore, it was believed that if a couple's hands were bound with a ribbon or cord made from wool, they would be protected from evil spirits and curses.\n\n• The Jacobite Risings of the 17th and 18th centuries saw hand-fasting become a powerful symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the practice to pledge their support for Charles Edward Stuart (Bonnie Prince Charlie).\n\n• Robert Burns, Scotland's national poet, wrote about hand-fasting in his poem "The Jolly Beggars", describing it as a way for couples to show their love and commitment to each other.\n\n• In some parts of Scotland, particularly the Highlands, hand-fasting was believed to have magical properties, with the binding of hands thought to bring good luck and prosperity to the couple's future endeavors.\n\n• The Victorian era's romanticization of Scottish culture led to a resurgence in interest in hand-fasting, with many writers and artists depicting it as a picturesque and charming aspect of Highland life.\n\n• In modern times, hand-fasting has been incorporated into wedding ceremonies by couples from diverse cultural backgrounds, including LGBTQ+ communities, who see the practice as a powerful symbol of commitment, unity, and love.	[\n  "Hand-fasting was originally a pagan Celtic ritual that took place during the spring equinox to ensure fertility and prosperity",\n  "In ancient Scotland, hand-fasting ceremonies were often conducted by druids or other spiritual leaders who would tie the couple's hands together with a cord made from the bark of a sacred tree",\n  "The earliest written records of hand-fasting in Scotland date back to the 13th century, but it is believed to have been practiced for centuries before that",\n  "During the Jacobite era, hand-fasting became a symbol of loyalty and allegiance to the Stuart cause, with many Highland clans using the ritual to seal their commitment to the rebellion",\n  "In some parts of Scotland, hand-fasting was seen as a way to legitimize children born out of wedlock, providing them with inheritance rights and social standing",\n  "The 16th-century Acts of the Parliament of Scotland attempted to regulate hand-fasting practices by requiring couples to obtain a formal marriage license before undergoing the ritual",\n  "Hand-fasting was not just limited to romantic partnerships - it was also used to seal business agreements, alliances between clans, and even friendships",\n  "In Scottish folklore, hand-fasting is often associated with the goddess Brigid, who was revered as a patron of love, fertility, and poetry",\n  "The Victorian era's romanticization of Scottish culture helped to revive interest in hand-fasting, which became a popular motif in literature and art of the time",\n  "Today, hand-fasting is still practiced by some modern pagans and Wiccans as a way to connect with their Celtic heritage and celebrate the cycles of nature"\n]	2	success	\N	2025-05-04 13:17:39.876076
21	3	Here is an expanded outline of potential angles and points to cover in a comprehensive blog article about hand-fasting in Scottish culture:\n\n**Historical Angles:**\n\n• Origins of hand-fasting in ancient Celtic cultures\n• Influence of Christianity on hand-fasting traditions\n• Medieval and Renaissance-era hand-fasting practices\n• Jacobite era and the role of hand-fasting in clan politics\n\n**Cultural Significance:**\n\n• Symbolism of binding hands as a representation of commitment\n• Hand-fasting as a symbol of unity and cooperation between families or clans\n• Role of hand-fasting in Scottish folklore and mythology\n• Connection to other Celtic traditions, such as knotwork and symbolism\n\n**Social Impact:**\n\n• Historical context of hand-fasting as a means of securing alliances and marriage agreements\n• Social status and class implications of hand-fasting\n• Hand-fasting as a way to formalize relationships between women and men in patriarchal society\n• Influence on Scottish wedding traditions and modern-day hand-fasting ceremonies\n\n**Key Events or Periods:**\n\n• The 16th-century Acts of the Parliament of Scotland, which attempted to regulate hand-fasting practices\n• The Jacobite Risings and their impact on hand-fasting as a symbol of loyalty and allegiance\n• The Victorian era's romanticization of Scottish culture and its influence on modern hand-fasting traditions\n\n**Folklore:**\n\n• Stories of mythical figures and gods who used hand-fasting in ancient Celtic mythology\n• Tales of Scottish clans and families using hand-fasting to seal alliances and agreements\n• Superstitions surrounding the act of hand-fasting, such as the importance of timing and location\n\n**Notable Figures:**\n\n• Historical accounts of notable Scots who participated in hand-fasting ceremonies, such as Mary Queen of Scots or Rob Roy MacGregor\n• Writers and artists who romanticized hand-fasting in their works, such as Robert Burns or Sir Walter Scott\n• Modern-day Scottish figures who have incorporated hand-fasting into their own wedding ceremonies\n\n**Modern Relevance:**\n\n• Contemporary hand-fasting practices and ceremonies in Scotland and beyond\n• Influence of modern pagan and Wiccan traditions on the revival of hand-fasting\n• Use of hand-fasting as a symbol of commitment and unity in LGBTQ+ communities\n• Adaptation of hand-fasting into non-traditional wedding ceremonies and rituals	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	2	success	\N	2025-05-04 14:34:28.09691
22	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	\N	2	error	LLM request timed out after 60 seconds. Model llama3.1:70b may still be loading - please wait a moment and try again. If this persists, try preloading the model or using a different model.	2025-05-04 14:38:05.112044
23	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	\N	2	error	LLM request timed out after 60 seconds. Model llama3.1:70b may still be loading - please wait a moment and try again. If this persists, try preloading the model or using a different model.	2025-05-04 14:41:36.236411
24	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	\N	2	error	LLM request timed out after 60 seconds. Model llama3.1:70b may still be loading - please wait a moment and try again. If this persists, try preloading the model or using a different model.	2025-05-04 14:44:31.490438
25	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	\N	2	error	LLM request timed out after 60 seconds. Model llama3.1:70b may still be loading - please wait a moment and try again. If this persists, try preloading the model or using a different model.	2025-05-04 14:46:39.909525
26	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	\N	2	error	LLM request timed out after 60 seconds. Model llama3.1:70b may still be loading - please wait a moment and try again. If this persists, try preloading the model or using a different model.	2025-05-04 14:47:23.242913
28	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	[\n  "Historical origins of hand-fasting in ancient Celtic culture",\n  "Evolution of hand-fasting from pagan to Christian traditions",\n  "Comparison of hand-fasting with other European betrothal customs",\n  "The role of hand-fasting in Scottish clan alliances and politics",\n  "Social class and hand-fasting: accessibility and exclusivity",\n  "Hand-fasting as a temporary or trial marriage arrangement",\n  "The significance of the 'year and a day' tradition in hand-fasting",\n  "Ceremonial aspects: rituals, blessings, and witnesses",\n  "Symbolism of the hand-fasting cord or ribbon",\n  "Variations in hand-fasting practices across Scottish regions",\n  "Notable historical figures who underwent hand-fasting ceremonies",\n  "Hand-fasting in literature and folklore: examples from Scottish mythology",\n  "Music and dance associated with hand-fasting celebrations",\n  "Food and drink traditions at hand-fasting gatherings",\n  "Influence of hand-fasting on modern Scottish wedding customs",\n  "Relevance of hand-fasting to contemporary alternative weddings",\n  "Feminist perspectives on the historical significance of hand-fasting",\n  "Pagan revivalism and the resurgence of interest in hand-fasting",\n  "Hand-fasting as a symbol of commitment in LGBTQ+ relationships",\n  "The impact of Christianity on hand-fasting traditions",\n  "Historical records of hand-fasting ceremonies in Scottish parish registers",\n  "Artifacts and relics associated with hand-fasting rituals",\n  "Regional dialects and language used in hand-fasting ceremonies",\n  "Cultural exchange: influences from other cultures on Scottish hand-fasting",\n  "The role of family and community in hand-fasting arrangements",\n  "Hand-fasting as a means of securing property and inheritance rights",\n  "Marriage laws and the decline of hand-fasting in Scotland",\n  "Rebellious or non-conformist uses of hand-fasting throughout history",\n  "Examples of hand-fasting in Scottish folklore and fairy tales",\n  "The significance of the 'hand-fasting stone' in some ceremonies",\n  "Intersections with other cultural practices, such as 'beating the bounds'",\n  "Symbolism of specific colors or fabrics used in hand-fasting rituals",\n  "Seasonal associations: hand-fasting ceremonies at specific times of year",\n  "Hand-fasting and fertility symbolism",\n  "The role of nature and outdoor settings in hand-fasting ceremonies",\n  "Examples of hand-fasting in modern Scottish fiction and media",\n  "Historical illustrations or artwork depicting hand-fasting scenes",\n  "Comparison with other forms of non-traditional partnership recognition",\n  "The psychology of commitment: insights from hand-fasting traditions",\n  "Cross-cultural comparisons: hand-fasting equivalents in other cultures",\n  "Reenactments and historical recreations of hand-fasting ceremonies",\n  "Innovative or avant-garde uses of hand-fasting in modern art",\n  "Therapeutic applications: using hand-fasting as a commitment ritual"\n]	2	success	\N	2025-05-04 14:57:54.031695
32	3	["test1", "test2"]	[\n  "Hand-fasting as an ancient Celtic tradition",\n  "Origins in pre-Christian Scotland and its connection to nature worship",\n  "The role of hand-fasting in medieval Scottish weddings",\n  "Cultural significance: symbolizing commitment, loyalty, and unity",\n  "Social impact: binding families and clans through marriage",\n  "Historical accounts of hand-fasting ceremonies from the 14th century",\n  "Influence of Christianity on hand-fasting traditions",\n  "Hand-fasting as a trial marriage or ' temporary union'",\n  "The role of the village elder or 'fairy wife' in performing hand-fastings",\n  "Ceremonial elements: ribbons, cords, and other symbolic materials",\n  "Scottish folklore: stories of lovers bound by hand-fasting magic",\n  "Notable historical figures who participated in hand-fasting ceremonies",\n  "The impact of the Jacobite risings on hand-fasting traditions",\n  "Hand-fasting as a symbol of resistance against English rule",\n  "Cultural exchange: how Scottish hand-fasting influenced other cultures",\n  "Modern pagan and Wiccan interpretations of hand-fasting",\n  "Same-sex hand-fastings in ancient Celtic societies",\n  "The role of hand-fasting in modern Scottish weddings and commitment ceremonies",\n  "Comparative analysis with other cultural binding traditions",\n  "Hand-fasting as a feminist symbol of partnership and equality",\n  "Rituals and customs: the significance of the 'hand-fasting knot'",\n  "Music and poetry: traditional songs and verses associated with hand-fastings",\n  "Food and drink: symbolic feasting and toasting in hand-fasting ceremonies",\n  "Regional variations: differences in hand-fasting traditions across Scotland",\n  "The connection between hand-fasting and Scottish mythology",\n  "Archaeological evidence of hand-fasting rituals at ancient sites",\n  "Hand-fasting as a form of protection against evil spirits or curses",\n  "Influence on literature: how hand-fasting has inspired writers and poets",\n  "Symbolism of the 'hand-fasting cord': strength, unity, and loyalty",\n  "Historical records of hand-fastings during times of war and conflict",\n  "The role of women in hand-fasting ceremonies as leaders or officiants",\n  "Cultural revival: modern efforts to revive traditional hand-fasting practices",\n  "Interfaith hand-fastings: blending Scottish traditions with other faiths",\n  "Hand-fasting as a symbol of national identity and pride",\n  "The connection between hand-fasting and Scottish clan heritage",\n  "Royal hand-fastings: instances of monarchs participating in the tradition",\n  "Historical accounts of hand-fasting ceremonies at specific castles or sites",\n  "Folkloric associations with hand-fasting: fairies, spirits, and supernatural beings",\n  "Scottish Gaelic terminology associated with hand-fasting rituals",\n  "Hand-fasting as a form of spiritual bonding and unity",\n  "Modern psychological perspectives on the significance of hand-fasting",\n  "Social media and technology: how modern couples are reinterpreting hand-fasting"\n]	2	success	\N	2025-05-04 15:48:29.272156
34	3	["test1", "test2"]	[\n  "Define hand-fasting in Scottish culture and its ancient origins",\n  "Explain the difference between hand-fasting and marriage",\n  "Discuss the historical context of hand-fasting in Scotland's medieval period",\n  "Describe the role of hand-fasting in Celtic tradition and mythology",\n  "Explore the cultural significance of hand-fasting in Scottish folklore",\n  "Analyze the social impact of hand-fasting on women's lives in Scotland's past",\n  "Delve into the history of hand-fasting as a trial marriage or 'betrothal'",\n  "Examine the symbolism behind the hand-fasting ceremony",\n  "Discuss notable historical figures who practiced hand-fasting, such as Robert Burns",\n  "Look at how hand-fasting was used to seal alliances and agreements between clans",\n  "Describe the role of the 'hand-fastening' ritual in Scottish wedding ceremonies",\n  "Investigate the influence of Christianity on the practice of hand-fasting",\n  "Explore how hand-fasting survived despite the introduction of Christian marriage rites",\n  "Analyze the significance of hand-fasting during Scotland's Jacobite risings",\n  "Discuss the romanticization of hand-fasting in Scottish literature and art",\n  "Describe the modern resurgence of interest in hand-fasting ceremonies",\n  "Look at how hand-fasting is incorporated into contemporary Scottish weddings",\n  "Examine the cultural exchange between Scottish and Norse cultures regarding hand-fasting",\n  "Investigate the connection between hand-fasting and Scotland's ancient laws",\n  "Discuss the symbolism behind the use of ribbons or cords in hand-fasting rituals",\n  "Describe the role of the 'priest' or 'officiant' in a traditional hand-fasting ceremony",\n  "Explore the regional variations of hand-fasting practices across Scotland",\n  "Analyze the impact of the Reformation on the decline of hand-fasting",\n  "Look at how hand-fasting has been used as a symbol of Scottish national identity",\n  "Discuss the modern feminist perspectives on hand-fasting and women's rights",\n  "Describe the historical significance of hand-fasting in Scotland's royal courts",\n  "Examine the influence of hand-fasting on modern wedding traditions worldwide",\n  "Investigate the connection between hand-fasting and Scotland's ancient festivals",\n  "Analyze the symbolism behind the use of specific dates or seasons for hand-fasting",\n  "Discuss the role of family and community in traditional hand-fasting ceremonies",\n  "Describe the cultural significance of hand-fasting in Scottish Highland culture",\n  "Explore the historical context of hand-fasting during Scotland's clan wars",\n  "Look at how hand-fasting has been used as a symbol of loyalty and commitment",\n  "Examine the modern relevance of hand-fasting in contemporary relationships",\n  "Discuss the connection between hand-fasting and Scotland's ancient mythology",\n  "Investigate the influence of Scottish emigration on the spread of hand-fasting practices worldwide",\n  "Analyze the cultural significance of hand-fasting in Scotland's Lowland culture",\n  "Describe the historical context of hand-fasting during Scotland's Enlightenment period",\n  "Explore the role of hand-fasting in modern Scottish pagan and druidic communities",\n  "Discuss the symbolism behind the use of specific materials or objects in hand-fasting rituals",\n  "Look at how hand-fasting has been used as a symbol of resistance against oppressive regimes"\n]	2	success	\N	2025-05-04 16:12:06.324979
29	3	[\n  "Historical Origins: Hand-fasting in ancient Celtic rituals",\n  "Pre-Christian Roots: Connection to pagan festivals and ceremonies",\n  "Medieval Era: Influence of Christianity on hand-fasting practices",\n  "18th Century: Decline of traditional hand-fasting amidst urbanization",\n  "Romanticism Revival: Victorian era's fascination with Highland culture",\n  "Folkloric Significance: Hand-fasting as a symbol of love and commitment in Scottish folklore",\n  "Social Impact: Effect on women's rights, marriage laws, and family dynamics",\n  "Royal Connections: Notable historical figures who participated in hand-fasting ceremonies",\n  "Cultural Exchange: Influence of Scottish hand-fasting traditions on other cultures",\n  "Literary References: Depictions of hand-fasting in Scottish literature, poetry, and song",\n  "Symbolism: Breaking down the symbolic elements of hand-fasting, such as ribbons and cords",\n  "Regional Variations: Diverse hand-fasting practices across different Scottish regions",\n  "Rituals and Ceremonies: Detailed descriptions of traditional hand-fasting rituals",\n  "Notable Hand-Fastings: Famous historical examples, including royal weddings and rebellions",\n  "Modern Revival: Contemporary adaptations of hand-fasting in wedding ceremonies and festivals",\n  "Neo-Pagan Resurgence: The role of hand-fasting in modern pagan and witchcraft communities",\n  "Interfaith Connections: Comparisons between Scottish hand-fasting and similar practices worldwide",\n  "Customs and Traditions: Exploring the evolution of hand-fasting customs over time",\n  "Archaeological Evidence: Uncovering physical evidence of ancient hand-fasting rituals"\n]	[\n  "Origins of hand-fasting in ancient Celtic rituals",\n  "Historical evolution from pagan to Christianized practice",\n  "Social significance as a temporary marriage contract",\n  "Differences between Highland and Lowland Scottish traditions",\n  "Role of hand-fasting in medieval Scottish law and governance",\n  "Influence on modern Western wedding ceremonies",\n  "Symbolism of the hand-fasting cord or ribbon",\n  "Folklore surrounding the breaking of the hand-fasting bond",\n  "Notable historical figures who participated in hand-fasting",\n  "Hand-fasting as a means of securing alliances between clans",\n  "The role of women in hand-fasting ceremonies and traditions",\n  "Comparison with other European pre-marital customs",\n  "Survival of hand-fasting traditions in modern Scottish weddings",\n  "Adaptation of hand-fasting into Wiccan and pagan wedding rituals",\n  "Hand-fasting as a symbol of devotion during times of war",\n  "The impact of the Reformation on hand-fasting practices",\n  "Use of hand-fasting in modern commitment ceremonies",\n  "Incorporating hand-fasting into interfaith or non-traditional weddings",\n  "Preservation of hand-fasting traditions through Scottish heritage societies",\n  "Hand-fasting as a means of strengthening family ties",\n  "Ceremonial objects used in hand-fasting rituals, such as the quaich",\n  "Regional variations in hand-fasting customs across Scotland",\n  "Historical accounts of hand-fasting ceremonies from diaries and letters",\n  "The significance of hand-fasting during times of social upheaval",\n  "Influence of Scottish hand-fasting on other cultures' pre-marital customs",\n  "Romanticization of hand-fasting in literature and art",\n  "Role of the community in hand-fasting ceremonies and celebrations",\n  "Hand-fasting as a precursor to modern engagement traditions",\n  "The spiritual significance of hand-fasting in ancient Celtic culture",\n  "Connection between hand-fasting and Scottish folklore, such as the selkies",\n  "Adaptation of hand-fasting into same-sex commitment ceremonies",\n  "Comparison with other pre-marital customs from around the world",\n  "Hand-fasting in times of war or economic hardship",\n  "Symbolism of the hand-fasting ceremony's timing and location",\n  "Notable modern couples who have incorporated hand-fasting into their wedding",\n  "Preservation of hand-fasting traditions through Scottish cultural events",\n  "The role of music and poetry in hand-fasting ceremonies",\n  "Hand-fasting as a means of securing land or property rights",\n  "Influence of Christianity on the decline of hand-fasting practices",\n  "Revival of interest in hand-fasting during the Romantic era",\n  "Cultural significance of hand-fasting in modern Scottish identity",\n  "Regional differences in hand-fasting traditions across the Highlands and Islands",\n  "Historical records of hand-fasting ceremonies from Scotland's past"\n]	2	success	\N	2025-05-04 15:02:26.295808
30	3	["test1", "test2"]	[\n  "Hand-fasting's origins in ancient Celtic rituals",\n  "The role of hand-fasting in Scottish folklore and mythology",\n  "Historical accounts of hand-fasting in medieval Scotland",\n  "Influence of Christianity on hand-fasting traditions",\n  "The significance of hand-fasting in Scottish Highland culture",\n  "Symbolism of the hand-fasting ribbon or cord",\n  "Variations of hand-fasting across different Scottish regions",\n  "Hand-fasting as a symbol of commitment and loyalty",\n  "The social impact of hand-fasting on Scottish communities",\n  "Notable historical figures who participated in hand-fasting ceremonies",\n  "Queen Victoria's influence on modernizing hand-fasting traditions",\n  "The role of hand-fasting in Scottish wedding customs",\n  "Comparison of hand-fasting to other Celtic cultures' betrothal rituals",\n  "The use of hand-fasting in Scottish literature and poetry",\n  "Hand-fasting as a motif in traditional Scottish music and art",\n  "Folkloric associations between hand-fasting and the supernatural",\n  "Historical instances of hand-fasting being used to seal alliances or treaties",\n  "Modern revival of hand-fasting in contemporary Scottish weddings",\n  "Cultural significance of hand-fasting in modern Scotland",\n  "Influence of hand-fasting on feminist and LGBTQ+ perspectives on marriage",\n  "Hand-fasting as a symbol of unity and cooperation",\n  "The role of nature and the environment in hand-fasting ceremonies",\n  "Seasonal associations with hand-fasting, such as spring or autumn equinoxes",\n  "Astronomical significance of hand-fasting, including celestial alignments",\n  "Hand-fasting's connection to Scottish clan heritage and identity",\n  "Historical records of hand-fasting among Scottish nobility and aristocracy",\n  "Romanticism and the idealization of hand-fasting in Scottish literature",\n  "Social class and the accessibility of hand-fasting ceremonies",\n  "Regional differences in hand-fasting customs across Scotland's islands",\n  "The use of specific plants, flowers, or trees in hand-fasting rituals",\n  "Folkloric associations between hand-fasting and fertility or prosperity",\n  "Hand-fasting as a symbol of protection or safeguarding",\n  "Notable examples of hand-fasting in Scottish art and sculpture",\n  "Cultural exchange and the influence of other cultures on hand-fasting traditions",\n  "Historical instances of hand-fasting being banned or suppressed",\n  "The role of hand-fasting in Scottish diaspora communities",\n  "Modern adaptations of hand-fasting for non-traditional relationships",\n  "Hand-fasting's connection to Scottish pagan and druidic practices",\n  "Rites of passage and the significance of hand-fasting in coming-of-age rituals",\n  "Hand-fasting as a symbol of spiritual growth or enlightenment",\n  "Interfaith and ecumenical perspectives on hand-fasting",\n  "Ceremonial parallels between hand-fasting and other global betrothal traditions"\n]	2	success	\N	2025-05-04 15:30:39.069335
31	3	["test1", "test2"]	[\n  "Historical origins: tracing hand-fasting back to ancient Celtic rituals",\n  "The role of Druids in hand-fasting ceremonies",\n  "Hand-fasting as a symbol of unity during times of war",\n  "Comparing Scottish hand-fasting to other European betrothal traditions",\n  "Cultural significance: hand-fasting as a rite of passage",\n  "Social impact: how hand-fasting influenced marriage laws in Scotland",\n  "The importance of hand-fasting in Highland clan culture",\n  "Key events: notable hand-fastings throughout Scottish history",\n  "Folklore and mythology surrounding hand-fasting",\n  "Notable figures: famous Scots who participated in hand-fasting ceremonies",\n  "Royal connections: hand-fasting among Scottish monarchs",\n  "The role of the Kirk in regulating hand-fasting practices",\n  "Hand-fasting during times of persecution, such as the Jacobite risings",\n  "Regional variations: differences in hand-fasting customs across Scotland",\n  "Symbolism of the hand-fasting cord or ribbon",\n  "Involvement of family and community in hand-fasting ceremonies",\n  "The significance of hand-fasting in Scottish folklore and ballads",\n  "Hand-fasting as a form of trial marriage",\n  "The consequences of breaking a hand-fasting agreement",\n  "Modern relevance: the revival of hand-fasting in contemporary weddings",\n  "Neo-Pagan and Wiccan adaptations of traditional hand-fasting practices",\n  "Interfaith and intercultural hand-fasting ceremonies in modern Scotland",\n  "Hand-fasting as a feminist symbol of partnership equality",\n  "The impact of Christianity on hand-fasting traditions",\n  "Romanticism and the idealization of hand-fasting in Scottish literature",\n  "Historical accounts: first-hand descriptions of hand-fasting ceremonies",\n  "Archaeological evidence: artifacts related to hand-fasting rituals",\n  "Comparative anthropology: similar customs in other cultures",\n  "Scottish Gaelic terminology related to hand-fasting",\n  "Hand-fasting as a symbol of national identity",\n  "Influence of Viking and Norse cultures on Scottish hand-fasting practices",\n  "The role of the clan chief or laird in overseeing hand-fasting ceremonies",\n  "Women's roles in traditional hand-fasting customs",\n  "Music and dance associated with hand-fasting celebrations",\n  "Food and drink traditions during hand-fasting ceremonies",\n  "Hand-fasting as a form of social contract",\n  "Ceremonial spaces: locations where hand-fasting took place",\n  "Rituals and superstitions surrounding hand-fasting",\n  "Divination practices used in conjunction with hand-fasting",\n  "The relationship between hand-fasting and Scottish clan heraldry",\n  "Artistic depictions of hand-fasting in Scottish art and literature"\n]	2	success	\N	2025-05-04 15:41:45.366094
33	3	["test1", "test2"]	[\n  "Explore the ancient Celtic roots of hand-fasting in Scotland",\n  "Discuss the symbolism behind the use of ribbons, cords, or fabric in hand-fasting ceremonies",\n  "Describe the role of hand-fasting in Scottish marriage traditions and its relation to modern wedding practices",\n  "Analyze the historical significance of hand-fasting during the Viking invasions of Scotland",\n  "Delve into the social impact of hand-fasting on Scottish communities throughout history",\n  "Highlight notable figures who practiced hand-fasting, such as Robert Burns or Mary Queen of Scots",\n  "Examine the cultural exchange between Scottish and Irish hand-fasting traditions",\n  "Investigate the use of hand-fasting in Scottish folklore and mythology",\n  "Discuss the connection between hand-fasting and the festival of Beltane",\n  "Describe the role of hand-fasting in Scottish Highland culture and tradition",\n  "Analyze the symbolism behind the use of different colors or patterns in hand-fasting cords",\n  "Explore the historical context of hand-fasting during times of war or conflict",\n  "Discuss the significance of hand-fasting as a symbol of commitment and loyalty",\n  "Highlight the differences between Scottish hand-fasting traditions and those found in other Celtic cultures",\n  "Investigate the use of hand-fasting in modern Scottish wedding ceremonies",\n  "Describe the role of hand-fasting in Scottish Pagan or Wiccan communities",\n  "Analyze the cultural significance of hand-fasting as a symbol of love and unity",\n  "Explore the historical records of hand-fasting ceremonies in Scotland's major cities",\n  "Discuss the use of hand-fasting as a form of symbolic marriage during times of social change",\n  "Highlight notable events or periods where hand-fasting played a significant role, such as the Jacobite risings",\n  "Examine the impact of Christianity on Scottish hand-fasting traditions",\n  "Investigate the modern revival of hand-fasting in Scotland and its connection to heritage tourism",\n  "Describe the use of hand-fasting in Scottish literature and poetry",\n  "Analyze the role of hand-fasting as a symbol of cultural identity in Scotland",\n  "Discuss the differences between hand-fasting and other forms of symbolic marriage or union",\n  "Explore the historical records of hand-fasting ceremonies in rural Scotland",\n  "Highlight notable figures who wrote about or practiced hand-fasting, such as Sir Walter Scott",\n  "Investigate the connection between hand-fasting and Scottish music or dance traditions",\n  "Examine the role of hand-fasting in modern Scottish cultural events or festivals",\n  "Describe the significance of hand-fasting as a symbol of community and social bonding",\n  "Analyze the historical context of hand-fasting during times of economic hardship",\n  "Discuss the use of hand-fasting as a form of resistance against cultural assimilation",\n  "Highlight notable examples of hand-fasting in Scottish art or iconography",\n  "Investigate the modern interpretation of hand-fasting as a feminist symbol",\n  "Explore the historical records of hand-fasting ceremonies among Scotland's traveling communities",\n  "Describe the role of hand-fasting in Scottish cultural heritage and its preservation for future generations"\n]	2	success	\N	2025-05-04 16:06:35.404204
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

COPY public.llm_prompt (id, name, description, prompt_text, system_prompt, parameters, created_at, updated_at) FROM stdin;
11	Allocate Ideas & Facts	Put them into their most relevant sections	You are an editorial assistant helping to structure a blog article on Scottish culture and heritage.\nYou are provided with:\n\t•\tA short idea or theme from a database field labeled idea\n\t•\tA list of interesting facts or points from a database field labeled interesting_facts\n\nYour task is to assign each fact to one of the following section titles, ensuring that:\n\t•\tEach section contains only one fact\n\t•\tEach fact is used once and only once\n\t•\tAll facts are distributed\n\t•\tSection headings are preserved as-is\n\nReturn your response in valid JSON format with the following structure:	\N	\N	2025-05-04 14:30:59.400632	2025-05-04 14:30:59.400642
8	Catchy title	Expand the basic idea and scope into an engaging title	You are a professional copywriter and editor specializing in digital publishing and historical blogging.\n\nYour task is to generate one catchy and engaging blog title suitable for a wide audience from the ideas provided below. This is especially those interested in Scottish culture and heritage. The title should be compelling, relevant to the content, and appropriate for web publication.\n\nReturn only the title with no explanation, commentary, or additional text. Do NOT enclose it in quote marks.\n\n\nYour topic is the following:\n\t1.\tThe basic idea of: {{basic_idea}}\n\t2.\tTheses topics and angles:\n{{idea_scope}}	\N	\N	2025-05-04 11:30:44.517966	2025-05-04 11:38:53.864178
10	Structuring section headings	Thematic section	You are an experienced editor and content strategist. Your task is to analyze the blog post title and content below intended for a blog article on Scottish culture and heritage.\nGroup and organize the content into a logical structure by identifying distinct thematic sections.\nReturn only a JSON array of paragraph titles that represent the structure of the final article.\nEach title should be concise, descriptive, and reflect a key theme from the text.\nDo not include any explanation, commentary, or full text of the paragraphs. Return only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.\n---\n\nTitle: {{provisional_title}}\n\nScope of ideas:\n{{idea_scope}}\n\nSome interesting facts: 	\N	\N	2025-05-04 12:56:29.9372	2025-05-04 13:13:33.234702
9	Interesting facts	Interesting facts	You are a researcher specialising in finding curious facts for blog articles for specialist audiences. You have been commissioned to assist with an article about {{basic_idea}} which will examine in depth these ideas {{idea_scope}}.\n\nPlease do a deep dive into this topic and provide a list of up to ten unusual and interesting facts that people might not know, to make this article worth reading. \n\nReturn only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.”	\N	\N	2025-05-04 12:36:41.74155	2025-05-04 13:15:09.283475
7	Basic Idea to Idea Scope	Expand Basic Idea to Idea Scope	You are an expert historical researcher and cultural writer specializing in Scottish history, traditions, and heritage. Your task is to expand the basic idea of {{basic_idea}} into an around 50 (fifty) ideas that outline and describe the full scope of an in-depth blog article about that topic in Scottish culture. Suggest (for example) different historical angles, cultural significance, social impact, key events or periods, folklore, notable figures, and/or modern relevance. Focus on breadth of ideas without writing the actual article — this list will as a guide for what should be covered in a full blog post. Keep each idea succinct but be imaginative, including both grand scale ideas and micro ideas. Return only a valid JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	\N	\N	2025-05-04 11:18:41.267767	2025-05-04 16:11:42.445259
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

COPY public.post_section (id, post_id, section_order, section_heading, first_draft, uk_british, highlighting, image_concepts, image_prompts, generation, optimization, watermarking, image_meta_descriptions, image_captions, ideas_to_include, facts_to_include) FROM stdin;
3	2	1	The Evolution of Hand-Fasting in Scotland's Historical Landscape	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
4	2	2	Symbolism and Significance: Unpacking the Cultural Importance of Hand-Fasting	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
5	2	3	Hand-Fasting as a Social Contract: Securing Alliances and Marriage Agreements	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
6	2	4	A Glimpse into Scotland's Past: Key Events that Shaped Hand-Fasting Traditions	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
7	2	5	Notable Scots Who Tied the Knot with Hand-Fasting Ceremonies	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
8	2	6	Mythical Ties: Exploring Hand-Fasting in Scottish Folklore and Mythology	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
9	2	7	Revival and Reinterpretation: Modern Takes on Traditional Hand-Fasting Practices	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
2	2	0	Unraveling the Ancient Celtic Roots of Hand-Fasting	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N		\N
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
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: llm_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_action_history_id_seq', 34, true);


--
-- Name: llm_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_action_id_seq', 6, true);


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

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 11, true);


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

