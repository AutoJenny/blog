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

SET default_tablespace = '';

SET default_table_access_method = heap;

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
    CONSTRAINT workflow_field_mapping_field_type_check CHECK (((field_type)::text = ANY ((ARRAY['input'::character varying, 'output'::character varying])::text[])))
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
    config jsonb DEFAULT '{}'::jsonb,
    field_name text,
    order_index integer,
    default_input_format_id integer,
    default_output_format_id integer
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
-- Name: workflow_field_mapping id; Type: DEFAULT; Schema: public; Owner: nickfiddes
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
-- Name: workflow_sub_stage_entity id; Type: DEFAULT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity ALTER COLUMN id SET DEFAULT nextval('public.workflow_sub_stage_entity_id_seq'::regclass);


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
-- Data for Name: workflow_stage_entity; Type: TABLE DATA; Schema: public; Owner: nickfiddes
--

COPY public.workflow_stage_entity (id, name, description, stage_order) FROM stdin;
8	publishing	Publishing	3
10	planning	Planning phase	1
54	writing	Content writing and development	2
58	authoring	Content creation and editing phase	2
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
44	22	IMAGES section concept	\N	2	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "image_concepts", "table": "post_section"}}}, "llm_available_tables": ["post_section"]}	\N	\N	39	38
18	21	Main	Meta info step	1	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "basic_metadata", "table": "post_development"}}}, "field_mapping": [], "llm_available_tables": ["post_development", "post_section"]}	\N	\N	\N	\N
45	22	IMAGES section LLM prompt	\N	3	{"settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "image_prompts", "table": "post_section"}}}, "llm_available_tables": ["post_section"]}	\N	\N	\N	\N
30	9	Engagement Tracking	Track post engagement metrics	4	{"title": "Engagement Tracking", "inputs": {"engagement_tracking": {"type": "textarea", "label": "Engagement Metrics", "db_field": "engagement_tracking", "db_table": "post_development", "required": true, "placeholder": "Enter engagement metrics..."}}, "outputs": {"engagement_tracking": {"type": "textarea", "label": "Tracking Results", "db_field": "engagement_tracking", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "engagement_tracking", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
32	2	Topics To Cover	List topics to cover	3	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "topics_to_cover", "table": "post_development"}}}, "field_mapping": [{"field_name": "research_notes", "order_index": 0}, {"field_name": "topics_to_cover", "order_index": 1}, {"field_name": "interesting_facts", "order_index": 2}]}	topics_to_cover	1	\N	\N
7	7	Final Check	Perform final checks	1	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "seo_optimization", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
28	8	Deployment	Deploy the post to production	1	{"title": "Deployment", "inputs": {"deployment": {"type": "textarea", "label": "Deployment Notes", "db_field": "deployment", "db_table": "post_development", "required": true, "placeholder": "Enter deployment details..."}}, "outputs": {"deployment": {"type": "textarea", "label": "Deployment Status", "db_field": "deployment", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "basic_metadata", "table": "post_development"}}}, "field_mapping": [{"field_name": "scheduling", "order_index": 1}, {"field_name": "deployment", "order_index": 2}, {"field_name": "verification", "order_index": 3}]}	scheduling	1	\N	\N
34	7	Tartans Products	Add relevant tartan products	5	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "tartans_products", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
43	19	Ideas to include	\N	1	{"inputs": {}, "outputs": {"output1": {"type": "textarea", "label": "Ideas to Include", "db_field": "ideas_to_include", "db_table": "post_section"}}, "settings": {"ui": {"llm_config": {"timeout": 30, "temperature": 0.7}, "field_selections": {"inputs": "basic_idea", "outputs": "ideas_to_include"}, "section_checkboxes": [710, 711]}, "llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_input_mappings": {"input1": {"field": "section_heading", "table": "post_section"}, "input2": {"field": "section_description", "table": "post_section"}}, "user_output_mapping": {"field": "ideas_to_include", "table": "post_section"}, "user_context_mappings": {"basic_idea": {"field": "basic_idea", "table": "post_development"}, "idea_scope": {"field": "section_heading", "table": "post_section"}, "section_headings": {"field": "section_headings", "table": "post_development"}}}}, "llm_available_tables": ["post_development", "post_section"]}	\N	\N	39	28
9	9	Content Adaptation	Adapt content for platforms	1	{"settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "content_updates", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
29	9	Content Distribution	Manage content distribution across platforms	2	{"title": "Content Distribution", "inputs": {"distribution": {"type": "textarea", "label": "Distribution Plan", "db_field": "distribution", "db_table": "post_development", "required": true, "placeholder": "Enter distribution plan..."}}, "outputs": {"distribution": {"type": "textarea", "label": "Distribution Status", "db_field": "distribution", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "content_updates", "table": "post_development"}}}, "field_mapping": [{"field_name": "feedback_collection", "order_index": 1}, {"field_name": "content_updates", "order_index": 2}, {"field_name": "version_control", "order_index": 3}, {"field_name": "platform_selection", "order_index": 4}, {"field_name": "content_adaptation", "order_index": 5}, {"field_name": "distribution", "order_index": 6}, {"field_name": "engagement_tracking", "order_index": 7}]}	feedback_collection	1	\N	\N
26	7	SEO Optimization	Optimize the post for search engines	3	{"title": "SEO Optimization", "inputs": {"seo_optimization": {"type": "textarea", "label": "SEO Notes", "db_field": "seo_optimization", "db_table": "post_development", "required": true, "placeholder": "Enter SEO optimization notes..."}}, "outputs": {"seo_optimization": {"type": "textarea", "label": "SEO Results", "db_field": "seo_optimization", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:70b", "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "user_output_mapping": {"field": "seo_optimization", "table": "post_development"}}}, "field_mapping": [{"field_name": "self_review", "order_index": 1}, {"field_name": "peer_review", "order_index": 2}, {"field_name": "final_check", "order_index": 3}, {"field_name": "seo_optimization", "order_index": 4}, {"field_name": "tartans_products", "order_index": 8}]}	self_review	1	\N	\N
21	1	Provisional Title	Generate a title for your post	3	{"title": "Title", "inputs": {"expanded_idea": {"type": "textarea", "label": "Expanded Idea", "db_field": "expanded_idea", "db_table": "post_development", "required": true, "placeholder": "The expanded idea from the previous step..."}}, "outputs": {"provisional_title": {"type": "textarea", "label": "Title", "db_field": "provisional_title", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:8b", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1092, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "[system] You are an expert in Scottish history and culture. Generate five alternative, arresting, and informative blog post titles for a post based on the following expanded idea. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.\\n\\nExpanded Idea:\\n[data:expanded_idea]", "input_mapping": {"expanded_idea": {"field": "expanded_idea", "table": "post_development", "description": "The expanded idea to base the title on"}}, "system_prompt": "[system] You are an expert in Scottish history and culture.", "output_mapping": {"field": "provisional_title", "table": "post_development"}, "user_input_mappings": {"expanded_idea": {"field": "basic_idea", "table": "post_development"}}, "user_output_mapping": {"field": "provisional_title", "table": "post_development"}, "user_context_mappings": {"basic_idea": {"field": "basic_idea", "table": "post_development"}}}}, "description": "Generate a title for your post based on the expanded idea.", "field_mapping": [{"field_name": "idea_seed", "order_index": 0}, {"field_name": "basic_idea", "order_index": 1}, {"field_name": "provisional_title", "order_index": 2}, {"field_name": "idea_scope", "order_index": 3}]}	provisional_title	1	39	28
41	1	Initial Concept	Initial concept for the post	2	{"title": "Initial Concept", "inputs": {"input1": {"type": "textarea", "label": "Input Field", "db_field": "idea_seed", "db_table": "post_development"}}, "outputs": {"output1": {"type": "textarea", "label": "Expanded Idea", "db_field": "", "db_table": "post_development"}}, "settings": {"llm": {"model": "llama3.1:8b", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 1000, "temperature": 0.7, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "task_prompt": "Generate five alternative, arresting, and informative blog post titles for a post based on the following input. Return your response as a strict JSON array of strings, with no commentary or formatting—just the list of titles.", "input_mapping": {"input1": {"field": "idea_seed", "table": "post_development"}}, "system_prompt": "You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.", "output_mapping": {"field": "basic_idea", "table": "post_development"}, "user_input_mappings": {"input1": {"field": "idea_seed", "table": "post_development"}}, "user_output_mapping": {"field": "basic_idea", "table": "post_development"}}}, "field_mapping": [{"field_name": "idea_seed", "order_index": 0}, {"field_name": "basic_idea", "order_index": 1}, {"field_name": "provisional_title", "order_index": 2}, {"field_name": "idea_scope", "order_index": 3}]}	\N	\N	39	38
24	3	Section Headings	Define the headings for each section	1	{"title": "Section Headings", "inputs": {"basic_idea": {"type": "textarea", "label": "Basic Idea", "db_field": "basic_idea", "db_table": "post_development", "required": true}, "idea_scope": {"type": "textarea", "label": "Idea Scope", "db_field": "idea_scope", "db_table": "post_development", "required": true}}, "outputs": {"section_headings": {"type": "textarea", "label": "Section Headings", "db_field": "section_headings", "db_table": "post_development", "required": true}}, "settings": {"llm": {"model": "llama3.2:latest", "timeout": 360, "provider": "ollama", "parameters": {"top_p": 0.9, "max_tokens": 100, "temperature": 0.1, "presence_penalty": 0.0, "frequency_penalty": 0.0}, "input_mapping": {"idea": {"field": "basic_idea", "table": "post_development", "description": "The basic idea"}, "facts": {"field": "idea_scope", "table": "post_development", "description": "The idea scope"}, "title": {"field": "basic_idea", "table": "post_development", "description": "The basic idea (used as title)"}}, "system_prompt": "You are an expert in Scottish history, culture, and traditions. You have deep knowledge of clan history, tartans, kilts, quaichs, and other aspects of Scottish heritage. You write in a clear, engaging style that balances historical accuracy with accessibility for a general audience.", "user_input_mappings": {"input3": {"field": "provisional_title", "table": "post_development"}, "basic_idea": {"field": "basic_idea", "table": "post_development"}}, "user_output_mapping": {"field": "section_headings", "table": "post_development"}}}, "field_mapping": [{"field_name": "structure", "order_index": 0}, {"field_name": "section_planning", "order_index": 1}, {"field_name": "section_headings", "order_index": 2}, {"field_name": "section_order", "order_index": 3}]}	section_planning	1	39	28
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
19	54	content	Content writing and development	1
22	54	images	Add images	3
21	54	meta	Add meta information	2
\.


--
-- Name: workflow_field_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_field_mapping_id_seq', 1158, true);


--
-- Name: workflow_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_stage_entity_id_seq', 59, true);


--
-- Name: workflow_step_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_step_entity_id_seq', 49, true);


--
-- Name: workflow_sub_stage_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nickfiddes
--

SELECT pg_catalog.setval('public.workflow_sub_stage_entity_id_seq', 22, true);


--
-- Name: workflow_field_mapping workflow_field_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_field_mapping
    ADD CONSTRAINT workflow_field_mapping_pkey PRIMARY KEY (id);


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
-- Name: workflow_field_mapping trigger_update_workflow_field_mapping_updated_at; Type: TRIGGER; Schema: public; Owner: nickfiddes
--

CREATE TRIGGER trigger_update_workflow_field_mapping_updated_at BEFORE UPDATE ON public.workflow_field_mapping FOR EACH ROW EXECUTE FUNCTION public.update_workflow_field_mapping_updated_at();


--
-- Name: workflow_sub_stage_entity fk_stage_id; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT fk_stage_id FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


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
-- Name: workflow_sub_stage_entity workflow_sub_stage_entity_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nickfiddes
--

ALTER TABLE ONLY public.workflow_sub_stage_entity
    ADD CONSTRAINT workflow_sub_stage_entity_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.workflow_stage_entity(id) ON DELETE CASCADE;


--
-- Name: TABLE workflow_field_mapping; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_field_mapping TO postgres;


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
-- Name: TABLE workflow_sub_stage_entity; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT ALL ON TABLE public.workflow_sub_stage_entity TO postgres;


--
-- Name: SEQUENCE workflow_sub_stage_entity_id_seq; Type: ACL; Schema: public; Owner: nickfiddes
--

GRANT SELECT,USAGE ON SEQUENCE public.workflow_sub_stage_entity_id_seq TO postgres;


--
-- PostgreSQL database dump complete
--

