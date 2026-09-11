-- NYC311 Pulse: relational database schema (PostgreSQL)
-- Star schema: one fact table, four dimension tables.
-- Natural keys are used as primary keys to keep the ETL simple.

CREATE TABLE IF NOT EXISTS dim_agency (
    agency_code   TEXT PRIMARY KEY,
    agency_name   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_complaint_type (
    complaint_type TEXT PRIMARY KEY,
    descriptor      TEXT
);

CREATE TABLE IF NOT EXISTS dim_borough (
    borough TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key    DATE PRIMARY KEY,
    year        INT NOT NULL,
    month       INT NOT NULL,
    day         INT NOT NULL,
    day_of_week TEXT NOT NULL,
    is_weekend  BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_311_requests (
    unique_key        BIGINT PRIMARY KEY,
    created_date      TIMESTAMP NOT NULL,
    created_date_key  DATE NOT NULL REFERENCES dim_date(date_key),
    closed_date       TIMESTAMP,
    agency_code       TEXT REFERENCES dim_agency(agency_code),
    complaint_type    TEXT REFERENCES dim_complaint_type(complaint_type),
    borough           TEXT REFERENCES dim_borough(borough),
    status            TEXT,
    resolution_hours  NUMERIC,
    latitude          NUMERIC,
    longitude         NUMERIC
);

CREATE INDEX IF NOT EXISTS idx_fact_created_date ON fact_311_requests (created_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_agency ON fact_311_requests (agency_code);
CREATE INDEX IF NOT EXISTS idx_fact_borough ON fact_311_requests (borough);
CREATE INDEX IF NOT EXISTS idx_fact_complaint_type ON fact_311_requests (complaint_type);
