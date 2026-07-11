CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.fact_budget_execution (
    ingestion_run_id VARCHAR,
    dataset_name VARCHAR,
    source_file_hash VARCHAR,
    sheet_name VARCHAR,
    row_number INTEGER,
    fiscal_year INTEGER,
    fiscal_year_be INTEGER,
    as_of_date VARCHAR,
    report_type VARCHAR,
    entity_type VARCHAR,
    entity_name VARCHAR,
    entity_code VARCHAR,
    expense_category VARCHAR,
    budget_after_transfer_million_baht DOUBLE,
    allocated_million_baht DOUBLE,
    po_reserved_debt_million_baht DOUBLE,
    disbursement_million_baht DOUBLE,
    disbursement_pct DOUBLE,
    expenditure_million_baht DOUBLE,
    expenditure_pct DOUBLE,
    monthly_target_gap_pct DOUBLE,
    remaining_million_baht DOUBLE,
    remaining_pct DOUBLE
);

CREATE TABLE IF NOT EXISTS mart.fact_government_manpower (
    ingestion_run_id VARCHAR,
    dataset_name VARCHAR,
    source_file_hash VARCHAR,
    sheet_name VARCHAR,
    row_number INTEGER,
    fiscal_year INTEGER,
    fiscal_year_be INTEGER,
    entity_type VARCHAR,
    ministry_name VARCHAR,
    agency_name VARCHAR,
    metric_name VARCHAR,
    metric_group VARCHAR,
    headcount DOUBLE,
    percentage DOUBLE,
    source_value VARCHAR,
    source_unit VARCHAR
);

CREATE TABLE IF NOT EXISTS mart.fact_ingestion_run (
    ingestion_run_id VARCHAR,
    loaded_at VARCHAR,
    raw_cell_count INTEGER,
    cgd_row_count INTEGER,
    ocsc_row_count INTEGER,
    dq_failed_check_count INTEGER,
    status VARCHAR
);

CREATE TABLE IF NOT EXISTS mart.fact_data_quality_issue (
    ingestion_run_id VARCHAR,
    check_name VARCHAR,
    severity VARCHAR,
    dataset_name VARCHAR,
    table_name VARCHAR,
    issue_count INTEGER,
    sample VARCHAR,
    status VARCHAR,
    source_file_hash VARCHAR
);

CREATE TABLE IF NOT EXISTS mart.dim_source_file (
    source_file_key INTEGER,
    dataset_name VARCHAR,
    source_name VARCHAR,
    filename VARCHAR,
    sha256 VARCHAR,
    source_page_url VARCHAR,
    file_url VARCHAR,
    fiscal_year INTEGER,
    fiscal_year_be INTEGER,
    as_of_date VARCHAR,
    loaded_at VARCHAR
);

CREATE TABLE IF NOT EXISTS mart.dim_agency (
    agency_key INTEGER,
    entity_name VARCHAR,
    normalized_entity_name VARCHAR,
    entity_type VARCHAR,
    ministry_name VARCHAR,
    source_systems VARCHAR
);

CREATE TABLE IF NOT EXISTS mart.dim_date (
    date_key INTEGER,
    date_value DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER
);
