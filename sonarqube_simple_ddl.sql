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