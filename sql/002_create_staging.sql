CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.cgd_budget_execution (
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

CREATE TABLE IF NOT EXISTS staging.ocsc_workforce (
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
