--
-- PostgreSQL database dump
--

-- Dumped from database version 17.3
-- Dumped by pg_dump version 17.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: commit_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.commit_details (
    id integer NOT NULL,
    repo_name character varying(255),
    start_date date,
    end_date date,
    commit_date date,
    commit_hash character varying(255),
    commit_user character varying(255),
    commit_message text,
    files_changed integer,
    additions integer,
    deletions integer
);


ALTER TABLE public.commit_details OWNER TO postgres;

--
-- Name: commit_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.commit_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.commit_details_id_seq OWNER TO postgres;

--
-- Name: commit_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.commit_details_id_seq OWNED BY public.commit_details.id;


--
-- Name: ghcommitdetails; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ghcommitdetails (
    id integer NOT NULL,
    username text,
    total integer,
    type character(1)
);


ALTER TABLE public.ghcommitdetails OWNER TO postgres;

--
-- Name: ghcommittotal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ghcommittotal (
    id integer NOT NULL,
    total integer,
    type character(1),
    reponame text
);


ALTER TABLE public.ghcommittotal OWNER TO postgres;

--
-- Name: leads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.leads (
    id integer NOT NULL,
    name character varying
);


ALTER TABLE public.leads OWNER TO postgres;

--
-- Name: pr_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pr_details (
    id integer NOT NULL,
    repo_name character varying(255),
    start_date date,
    end_date date,
    pr_number integer,
    state character varying(50),
    author character varying(255),
    merged boolean,
    merge_time interval,
    review_time interval,
    review_count integer,
    comment_count integer,
    additions integer,
    deletions integer,
    changed_files integer
);


ALTER TABLE public.pr_details OWNER TO postgres;

--
-- Name: pr_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pr_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pr_details_id_seq OWNER TO postgres;

--
-- Name: pr_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pr_details_id_seq OWNED BY public.pr_details.id;


--
-- Name: commit_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commit_details ALTER COLUMN id SET DEFAULT nextval('public.commit_details_id_seq'::regclass);


--
-- Name: pr_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pr_details ALTER COLUMN id SET DEFAULT nextval('public.pr_details_id_seq'::regclass);


--
-- Name: commit_details commit_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commit_details
    ADD CONSTRAINT commit_details_pkey PRIMARY KEY (id);


--
-- Name: ghcommitdetails ghcommitdetails_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ghcommitdetails
    ADD CONSTRAINT ghcommitdetails_pkey PRIMARY KEY (id);


--
-- Name: ghcommittotal ghcommittotal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ghcommittotal
    ADD CONSTRAINT ghcommittotal_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (id);


--
-- Name: pr_details pr_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pr_details
    ADD CONSTRAINT pr_details_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--
--
-- Name: sonarqube_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sonarqube_results (
    id integer NOT NULL,
    repo_name character varying(255),
    project_key character varying(255),
    analysis_date timestamp with time zone,
    branch character varying(100) DEFAULT 'main'::character varying,
    quality_gate_status character varying(20),
    coverage numeric(5,2),
    bugs integer DEFAULT 0,
    vulnerabilities integer DEFAULT 0,
    code_smells integer DEFAULT 0,
    technical_debt_minutes integer DEFAULT 0,
    lines_of_code integer DEFAULT 0,
    duplicated_lines numeric(5,2),
    maintainability_rating integer,
    reliability_rating integer,
    security_rating integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.sonarqube_results OWNER TO postgres;

--
-- Name: sonarqube_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sonarqube_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sonarqube_results_id_seq OWNER TO postgres;

--
-- Name: sonarqube_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sonarqube_results_id_seq OWNED BY public.sonarqube_results.id;


--
-- Name: sonarqube_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sonarqube_results ALTER COLUMN id SET DEFAULT nextval('public.sonarqube_results_id_seq'::regclass);


--
-- Name: sonarqube_results sonarqube_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sonarqube_results
    ADD CONSTRAINT sonarqube_results_pkey PRIMARY KEY (id);

--- sonarqube_results; Type: TABLE; Schema: public; Owner: postgres


CREATE TABLE IF NOT EXISTS public.change_failure_rate_runs
(
    id integer NOT NULL DEFAULT nextval('change_failure_rate_runs_id_seq'::regclass),
    repo_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    run_id bigint NOT NULL,
    conclusion character varying(50) COLLATE pg_catalog."default",
    completed_at timestamp with time zone,
    failure_reason character varying(255) COLLATE pg_catalog."default",
    CONSTRAINT change_failure_rate_runs_pkey PRIMARY KEY (id),
    CONSTRAINT change_failure_rate_runs_repo_name_run_id_key UNIQUE (repo_name, run_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.change_failure_rate_runs
    OWNER to postgres;
