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
    "order" integer
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
-- Name: llm_action id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action ALTER COLUMN id SET DEFAULT nextval('public.llm_action_id_seq'::regclass);


--
-- Name: llm_prompt id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_prompt ALTER COLUMN id SET DEFAULT nextval('public.llm_prompt_id_seq'::regclass);


--
-- Data for Name: llm_action; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_action (id, prompt_template, llm_model, temperature, created_at, updated_at, field_name, max_tokens, prompt_template_id) FROM stdin;
6	You are an experienced editor and content strategist. Your task is to analyze the blog post title and content below intended for a blog article on Scottish culture and heritage.\nGroup and organize the content into a logical structure by identifying distinct thematic sections.\nReturn only a JSON array of paragraph titles that represent the structure of the final article.\nEach title should be concise, descriptive, and reflect a key theme from the text.\nDo not include any explanation, commentary, or full text of the paragraphs. Return only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.\n---\n\nTitle: {{provisional_title}}\n\nScope of ideas:\n{{idea_scope}}\n\nSome interesting facts: 	llama3.1:70b	0.7	2025-05-04 12:57:21.257811	2025-05-04 13:15:38.601902	Outlining section headings	1000	10
3	You are an expert historical researcher and cultural writer specializing in Scottish history, traditions, and heritage. Your task is to expand the basic idea of {{basic_idea}} into an around 50 (fifty) ideas that outline and describe the full scope of an in-depth blog article about that topic in Scottish culture. Suggest (for example) different historical angles, cultural significance, social impact, key events or periods, folklore, notable figures, and/or modern relevance. Focus on breadth of ideas without writing the actual article — this list will as a guide for what should be covered in a full blog post. Keep each idea succinct but be imaginative, including both grand scale ideas and micro ideas. Return only a JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	llama3.1:70b	0.7	2025-05-03 15:34:47.074891	2025-05-04 14:40:15.628692	Idea Scope from Basic Idea	3000	7
4	You are a professional copywriter and editor specializing in digital publishing and historical blogging.\n\nYour task is to generate one catchy and engaging blog title suitable for a wide audience from the ideas provided below. This is especially those interested in Scottish culture and heritage. The title should be compelling, relevant to the content, and appropriate for web publication.\n\nReturn only the title with no explanation, commentary, or additional text. Do NOT enclose it in quote marks.\n\n\nYour topic is the following:\n\t1.\tThe basic idea of: {{basic_idea}}\n\t2.\tTheses topics and angles:\n{{idea_scope}}	llama3.1:70b	0.7	2025-05-04 11:31:21.820742	2025-05-04 11:39:17.573338	Generate blog title	1000	8
5	You are a researcher specialising in finding curious facts for blog articles for specialist audiences. You have been commissioned to assist with an article about {{basic_idea}} which will examine in depth these ideas {{idea_scope}}.\n\nPlease do a deep dive into this topic and provide a list of up to ten unusual and interesting facts that people might not know, to make this article worth reading. \n\nReturn only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.”	llama3.1:70b	0.9	2025-05-04 12:37:27.007623	2025-05-04 13:15:28.400889	Interesting facts	1000	9
7	You are a professional historical writer specializing in Scottish culture and heritage.\nYour task is to write 2–3 well-written paragraphs for a blog article based on a specific section.\n\nYou are given:\n\t•\tThe overall subject of the blog post, which is: {{basic_idea}}\n\n\t•\tGeneral background context about the topic, describing the range of content the full blog will cover, which is: {{idea_scope}}\n\n\t•\tThe current section title to write under, which is: {{section_heading}}\n\n\t•\tConcepts and angles that should guide this section (but that you may also add to and expand) which are: {{ideas_to_include}}\n\n\t•\tSome interesting factual points that must be included in this section, which are: {{facts_to_include}}\n\nWrite clear, informative, and engaging text that suits a public-facing blog while respecting historical accuracy. Use only UK-British spellings and idioms, avoiding Americanisms (eg colour not color, and 's' not 'z' in words like authorise). \nEnsure that all the <SECTION IDEAS> and <SECTION FACTS> are incorporated meaningfully into the text.\nDo not include any commentary, headings, titles, or formatting — return only the body paragraphs in plain text.	llama3.1:70b	0.7	2025-05-05 10:02:43.403787	2025-05-05 10:14:09.733123	Write Section first draft	1000	12
\.


--
-- Data for Name: llm_prompt; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_prompt (id, name, description, prompt_text, system_prompt, parameters, created_at, updated_at, "order") FROM stdin;
11	Allocate Ideas & Facts	Put them into their most relevant sections	You are an editorial assistant helping to structure a blog article on Scottish culture and heritage.\nYou are provided with:\n\t•\tA short idea or theme from a database field labeled idea\n\t•\tA list of interesting facts or points from a database field labeled interesting_facts\n\nYour task is to assign each fact to one of the following section titles, ensuring that:\n\t•\tEach section contains only one fact\n\t•\tEach fact is used once and only once\n\t•\tAll facts are distributed\n\t•\tSection headings are preserved as-is\n\nReturn your response in valid JSON format with the following structure:	\N	\N	2025-05-04 14:30:59.400632	2025-05-05 11:15:17.689584	4
8	Catchy title	Expand the basic idea and scope into an engaging title	You are a professional copywriter and editor specializing in digital publishing and historical blogging.\n\nYour task is to generate one catchy and engaging blog title suitable for a wide audience from the ideas provided below. This is especially those interested in Scottish culture and heritage. The title should be compelling, relevant to the content, and appropriate for web publication.\n\nReturn only the title with no explanation, commentary, or additional text. Do NOT enclose it in quote marks.\n\n\nYour topic is the following:\n\t1.\tThe basic idea of: {{basic_idea}}\n\t2.\tTheses topics and angles:\n{{idea_scope}}	\N	\N	2025-05-04 11:30:44.517966	2025-05-05 11:17:31.453734	2
10	Structuring section headings	Thematic section	You are an experienced editor and content strategist. Your task is to analyze the blog post title and content below intended for a blog article on Scottish culture and heritage.\nGroup and organize the content into a logical structure by identifying distinct thematic sections.\nReturn only a JSON array of paragraph titles that represent the structure of the final article.\nEach title should be concise, descriptive, and reflect a key theme from the text.\nDo not include any explanation, commentary, or full text of the paragraphs. Return only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.\n---\n\nTitle: {{provisional_title}}\n\nScope of ideas:\n{{idea_scope}}\n\nSome interesting facts: 	\N	\N	2025-05-04 12:56:29.9372	2025-05-05 11:15:17.688546	3
7	Basic Idea to Idea Scope	Expand Basic Idea to Idea Scope	You are an expert historical researcher and cultural writer specializing in Scottish history, traditions, and heritage. Your task is to expand the basic idea of {{basic_idea}} into an around 50 (fifty) ideas that outline and describe the full scope of an in-depth blog article about that topic in Scottish culture. Suggest (for example) different historical angles, cultural significance, social impact, key events or periods, folklore, notable figures, and/or modern relevance. Focus on breadth of ideas without writing the actual article — this list will as a guide for what should be covered in a full blog post. Keep each idea succinct but be imaginative, including both grand scale ideas and micro ideas. Return only a valid JSON array of ideas, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.	\N	\N	2025-05-04 11:18:41.267767	2025-05-05 11:14:59.670628	0
12	Author Section first draft		You are a professional historical writer specializing in Scottish culture and heritage.\nYour task is to write 2–3 well-written paragraphs for a blog article based on a specific section.\n\nYou are given:\n\t•\tThe overall subject of the blog post, which is: {{basic_idea}}\n\n\t•\tGeneral background context about the topic, describing the range of content the full blog will cover, which is: {{idea_scope}}\n\n\t•\tThe current section title to write under, which is: {{section_heading}}\n\n\t•\tConcepts and angles that should guide this section (but that you may also add to and expand) which are: {{ideas_to_include}}\n\n\t•\tSome interesting factual points that must be included in this section, which are: {{facts_to_include}}\n\nWrite clear, informative, and engaging text that suits a public-facing blog while respecting historical accuracy. Use only UK-British spellings and idioms, avoiding Americanisms (eg colour not color, and 's' not 'z' in words like authorise). \nEnsure that all the <SECTION IDEAS> and <SECTION FACTS> are incorporated meaningfully into the text.\nDo not include any commentary, headings, titles, or formatting — return only the body paragraphs in plain text.	\N	\N	2025-05-05 10:01:54.864346	2025-05-05 11:15:11.69681	5
9	Interesting facts	Interesting facts	You are a researcher specialising in finding curious facts for blog articles for specialist audiences. You have been commissioned to assist with an article about {{basic_idea}} which will examine in depth these ideas {{idea_scope}}.\n\nPlease do a deep dive into this topic and provide a list of up to ten unusual and interesting facts that people might not know, to make this article worth reading. \n\nReturn only a JSON array of paragraph titles, with no preamble, commentary, or formatting. Output must begin with [ and end with ] — no code blocks or text outside the array.”	\N	\N	2025-05-04 12:36:41.74155	2025-05-05 11:17:31.452701	1
\.


--
-- Name: llm_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_action_id_seq', 7, true);


--
-- Name: llm_prompt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_prompt_id_seq', 12, true);


--
-- Name: llm_action llm_action_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_pkey PRIMARY KEY (id);


--
-- Name: llm_prompt llm_prompt_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_prompt
    ADD CONSTRAINT llm_prompt_pkey PRIMARY KEY (id);


--
-- Name: llm_action llm_action_prompt_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_action
    ADD CONSTRAINT llm_action_prompt_template_id_fkey FOREIGN KEY (prompt_template_id) REFERENCES public.llm_prompt(id);


--
-- PostgreSQL database dump complete
--

