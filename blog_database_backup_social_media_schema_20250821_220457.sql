--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

-- Started on 2025-08-21 22:04:57 BST

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

DROP DATABASE IF EXISTS blog;
--
-- TOC entry 3981 (class 1262 OID 3786014)
-- Name: blog; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE blog WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'C';


\connect blog

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
-- TOC entry 321 (class 1259 OID 4602141)
-- Name: social_media_content_processes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_media_content_processes (
    id integer NOT NULL,
    process_name character varying(100) NOT NULL,
    display_name character varying(150) NOT NULL,
    platform_id integer,
    content_type character varying(50) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    priority integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- TOC entry 3982 (class 0 OID 0)
-- Dependencies: 321
-- Name: TABLE social_media_content_processes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.social_media_content_processes IS 'Stores LLM-based content conversion processes for social media platforms';


--
-- TOC entry 3983 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN social_media_content_processes.process_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_content_processes.process_name IS 'Unique identifier for the process (e.g., facebook_feed_post)';


--
-- TOC entry 3984 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN social_media_content_processes.content_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_content_processes.content_type IS 'Type of content this process generates (e.g., feed_post, story_post, reels_caption)';


--
-- TOC entry 3985 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN social_media_content_processes.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_content_processes.is_active IS 'Whether this process is currently available for use';


--
-- TOC entry 3986 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN social_media_content_processes.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_content_processes.priority IS 'Priority level for process selection (1=highest)';


--
-- TOC entry 320 (class 1259 OID 4602140)
-- Name: social_media_content_processes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_media_content_processes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3987 (class 0 OID 0)
-- Dependencies: 320
-- Name: social_media_content_processes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_media_content_processes_id_seq OWNED BY public.social_media_content_processes.id;


--
-- TOC entry 319 (class 1259 OID 4585772)
-- Name: social_media_platform_specs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_media_platform_specs (
    id integer NOT NULL,
    platform_id integer,
    spec_category character varying(50) NOT NULL,
    spec_key character varying(100) NOT NULL,
    spec_value text NOT NULL,
    spec_type character varying(20) DEFAULT 'text'::character varying,
    is_required boolean DEFAULT false,
    display_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- TOC entry 318 (class 1259 OID 4585771)
-- Name: social_media_platform_specs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_media_platform_specs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3988 (class 0 OID 0)
-- Dependencies: 318
-- Name: social_media_platform_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_media_platform_specs_id_seq OWNED BY public.social_media_platform_specs.id;


--
-- TOC entry 317 (class 1259 OID 4585757)
-- Name: social_media_platforms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_media_platforms (
    id integer NOT NULL,
    platform_name character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    status character varying(20) DEFAULT 'undeveloped'::character varying NOT NULL,
    priority integer DEFAULT 0,
    icon_url text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- TOC entry 316 (class 1259 OID 4585756)
-- Name: social_media_platforms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_media_platforms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3989 (class 0 OID 0)
-- Dependencies: 316
-- Name: social_media_platforms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_media_platforms_id_seq OWNED BY public.social_media_platforms.id;


--
-- TOC entry 323 (class 1259 OID 4602161)
-- Name: social_media_process_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_media_process_configs (
    id integer NOT NULL,
    process_id integer,
    config_category character varying(50) NOT NULL,
    config_key character varying(100) NOT NULL,
    config_value text NOT NULL,
    config_type character varying(20) DEFAULT 'text'::character varying,
    is_required boolean DEFAULT false,
    display_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT social_media_process_configs_config_type_check CHECK (((config_type)::text = ANY ((ARRAY['text'::character varying, 'integer'::character varying, 'json'::character varying, 'boolean'::character varying])::text[])))
);


--
-- TOC entry 3990 (class 0 OID 0)
-- Dependencies: 323
-- Name: TABLE social_media_process_configs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.social_media_process_configs IS 'Stores configuration settings for each content conversion process';


--
-- TOC entry 3991 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN social_media_process_configs.config_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_configs.config_category IS 'Category of configuration: llm_prompt, constraints, style_guide, etc.';


--
-- TOC entry 3992 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN social_media_process_configs.config_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_configs.config_key IS 'Unique key for the configuration within its category';


--
-- TOC entry 3993 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN social_media_process_configs.config_value; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_configs.config_value IS 'The actual configuration value';


--
-- TOC entry 3994 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN social_media_process_configs.config_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_configs.config_type IS 'Data type of the configuration value';


--
-- TOC entry 322 (class 1259 OID 4602160)
-- Name: social_media_process_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_media_process_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3995 (class 0 OID 0)
-- Dependencies: 322
-- Name: social_media_process_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_media_process_configs_id_seq OWNED BY public.social_media_process_configs.id;


--
-- TOC entry 325 (class 1259 OID 4602183)
-- Name: social_media_process_executions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_media_process_executions (
    id integer NOT NULL,
    process_id integer,
    post_id integer,
    section_id integer,
    input_content text,
    output_content text,
    execution_status character varying(20) DEFAULT 'pending'::character varying,
    error_message text,
    processing_time_ms integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT social_media_process_executions_execution_status_check CHECK (((execution_status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


--
-- TOC entry 3996 (class 0 OID 0)
-- Dependencies: 325
-- Name: TABLE social_media_process_executions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.social_media_process_executions IS 'Stores execution history and results of content conversion processes';


--
-- TOC entry 3997 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN social_media_process_executions.execution_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_executions.execution_status IS 'Current status of the process execution';


--
-- TOC entry 3998 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN social_media_process_executions.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_executions.error_message IS 'Error details if execution failed';


--
-- TOC entry 3999 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN social_media_process_executions.processing_time_ms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.social_media_process_executions.processing_time_ms IS 'Time taken to process the content in milliseconds';


--
-- TOC entry 324 (class 1259 OID 4602182)
-- Name: social_media_process_executions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_media_process_executions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4000 (class 0 OID 0)
-- Dependencies: 324
-- Name: social_media_process_executions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_media_process_executions_id_seq OWNED BY public.social_media_process_executions.id;


--
-- TOC entry 3779 (class 2604 OID 4602144)
-- Name: social_media_content_processes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_content_processes ALTER COLUMN id SET DEFAULT nextval('public.social_media_content_processes_id_seq'::regclass);


--
-- TOC entry 3773 (class 2604 OID 4585775)
-- Name: social_media_platform_specs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platform_specs ALTER COLUMN id SET DEFAULT nextval('public.social_media_platform_specs_id_seq'::regclass);


--
-- TOC entry 3768 (class 2604 OID 4585760)
-- Name: social_media_platforms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platforms ALTER COLUMN id SET DEFAULT nextval('public.social_media_platforms_id_seq'::regclass);


--
-- TOC entry 3784 (class 2604 OID 4602164)
-- Name: social_media_process_configs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_configs ALTER COLUMN id SET DEFAULT nextval('public.social_media_process_configs_id_seq'::regclass);


--
-- TOC entry 3791 (class 2604 OID 4602186)
-- Name: social_media_process_executions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_executions ALTER COLUMN id SET DEFAULT nextval('public.social_media_process_executions_id_seq'::regclass);


--
-- TOC entry 3812 (class 2606 OID 4602152)
-- Name: social_media_content_processes social_media_content_processes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_content_processes
    ADD CONSTRAINT social_media_content_processes_pkey PRIMARY KEY (id);


--
-- TOC entry 3814 (class 2606 OID 4602154)
-- Name: social_media_content_processes social_media_content_processes_process_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_content_processes
    ADD CONSTRAINT social_media_content_processes_process_name_key UNIQUE (process_name);


--
-- TOC entry 3804 (class 2606 OID 4585784)
-- Name: social_media_platform_specs social_media_platform_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platform_specs
    ADD CONSTRAINT social_media_platform_specs_pkey PRIMARY KEY (id);


--
-- TOC entry 3806 (class 2606 OID 4585786)
-- Name: social_media_platform_specs social_media_platform_specs_platform_id_spec_category_spec__key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platform_specs
    ADD CONSTRAINT social_media_platform_specs_platform_id_spec_category_spec__key UNIQUE (platform_id, spec_category, spec_key);


--
-- TOC entry 3797 (class 2606 OID 4585768)
-- Name: social_media_platforms social_media_platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platforms
    ADD CONSTRAINT social_media_platforms_pkey PRIMARY KEY (id);


--
-- TOC entry 3799 (class 2606 OID 4585770)
-- Name: social_media_platforms social_media_platforms_platform_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platforms
    ADD CONSTRAINT social_media_platforms_platform_name_key UNIQUE (platform_name);


--
-- TOC entry 3819 (class 2606 OID 4602174)
-- Name: social_media_process_configs social_media_process_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_configs
    ADD CONSTRAINT social_media_process_configs_pkey PRIMARY KEY (id);


--
-- TOC entry 3821 (class 2606 OID 4602176)
-- Name: social_media_process_configs social_media_process_configs_process_id_config_category_con_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_configs
    ADD CONSTRAINT social_media_process_configs_process_id_config_category_con_key UNIQUE (process_id, config_category, config_key);


--
-- TOC entry 3826 (class 2606 OID 4602194)
-- Name: social_media_process_executions social_media_process_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_executions
    ADD CONSTRAINT social_media_process_executions_pkey PRIMARY KEY (id);


--
-- TOC entry 3807 (class 1259 OID 4602202)
-- Name: idx_content_processes_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_processes_active ON public.social_media_content_processes USING btree (is_active);


--
-- TOC entry 3808 (class 1259 OID 4602201)
-- Name: idx_content_processes_content_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_processes_content_type ON public.social_media_content_processes USING btree (content_type);


--
-- TOC entry 3809 (class 1259 OID 4602200)
-- Name: idx_content_processes_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_processes_platform_id ON public.social_media_content_processes USING btree (platform_id);


--
-- TOC entry 3810 (class 1259 OID 4602203)
-- Name: idx_content_processes_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_processes_priority ON public.social_media_content_processes USING btree (priority);


--
-- TOC entry 3815 (class 1259 OID 4602205)
-- Name: idx_process_configs_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_configs_category ON public.social_media_process_configs USING btree (config_category);


--
-- TOC entry 3816 (class 1259 OID 4602206)
-- Name: idx_process_configs_process_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_configs_process_category ON public.social_media_process_configs USING btree (process_id, config_category);


--
-- TOC entry 3817 (class 1259 OID 4602204)
-- Name: idx_process_configs_process_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_configs_process_id ON public.social_media_process_configs USING btree (process_id);


--
-- TOC entry 3822 (class 1259 OID 4602209)
-- Name: idx_process_executions_post_section; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_executions_post_section ON public.social_media_process_executions USING btree (post_id, section_id);


--
-- TOC entry 3823 (class 1259 OID 4602207)
-- Name: idx_process_executions_process_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_executions_process_id ON public.social_media_process_executions USING btree (process_id);


--
-- TOC entry 3824 (class 1259 OID 4602208)
-- Name: idx_process_executions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_executions_status ON public.social_media_process_executions USING btree (execution_status);


--
-- TOC entry 3800 (class 1259 OID 4585793)
-- Name: idx_specs_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_specs_category ON public.social_media_platform_specs USING btree (spec_category);


--
-- TOC entry 3801 (class 1259 OID 4585794)
-- Name: idx_specs_platform_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_specs_platform_category ON public.social_media_platform_specs USING btree (platform_id, spec_category);


--
-- TOC entry 3802 (class 1259 OID 4585792)
-- Name: idx_specs_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_specs_platform_id ON public.social_media_platform_specs USING btree (platform_id);


--
-- TOC entry 3833 (class 2620 OID 4602210)
-- Name: social_media_content_processes update_social_media_content_processes_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_social_media_content_processes_updated_at BEFORE UPDATE ON public.social_media_content_processes FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 3832 (class 2620 OID 4585796)
-- Name: social_media_platform_specs update_social_media_platform_specs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_social_media_platform_specs_updated_at BEFORE UPDATE ON public.social_media_platform_specs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 3831 (class 2620 OID 4585795)
-- Name: social_media_platforms update_social_media_platforms_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_social_media_platforms_updated_at BEFORE UPDATE ON public.social_media_platforms FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 3834 (class 2620 OID 4602211)
-- Name: social_media_process_configs update_social_media_process_configs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_social_media_process_configs_updated_at BEFORE UPDATE ON public.social_media_process_configs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 3835 (class 2620 OID 4602212)
-- Name: social_media_process_executions update_social_media_process_executions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_social_media_process_executions_updated_at BEFORE UPDATE ON public.social_media_process_executions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 3828 (class 2606 OID 4602155)
-- Name: social_media_content_processes social_media_content_processes_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_content_processes
    ADD CONSTRAINT social_media_content_processes_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.social_media_platforms(id) ON DELETE CASCADE;


--
-- TOC entry 3827 (class 2606 OID 4585787)
-- Name: social_media_platform_specs social_media_platform_specs_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_platform_specs
    ADD CONSTRAINT social_media_platform_specs_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.social_media_platforms(id) ON DELETE CASCADE;


--
-- TOC entry 3829 (class 2606 OID 4602177)
-- Name: social_media_process_configs social_media_process_configs_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_configs
    ADD CONSTRAINT social_media_process_configs_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.social_media_content_processes(id) ON DELETE CASCADE;


--
-- TOC entry 3830 (class 2606 OID 4602195)
-- Name: social_media_process_executions social_media_process_executions_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_media_process_executions
    ADD CONSTRAINT social_media_process_executions_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.social_media_content_processes(id);


-- Completed on 2025-08-21 22:04:57 BST

--
-- PostgreSQL database dump complete
--

