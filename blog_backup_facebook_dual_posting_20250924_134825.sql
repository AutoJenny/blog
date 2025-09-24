-- Database backup created on 2025-09-24 13:48:25
-- Facebook dual-page posting functionality fix


-- Table: active_credentials
CREATE TABLE IF NOT EXISTS active_credentials (
    id integer,
    name character varying,
    description text,
    credential_type USER-DEFINED,
    status USER-DEFINED,
    last_used_at timestamp without time zone,
    last_verified_at timestamp without time zone,
    error_message text,
    channel_name character varying,
    channel_icon character varying,
    channel_color character varying,
    service_name character varying,
    service_description text,
    service_url character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

-- Data for table active_credentials
