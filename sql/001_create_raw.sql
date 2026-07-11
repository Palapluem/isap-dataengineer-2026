CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.source_files (
    dataset_name VARCHAR,
    source_name VARCHAR,
    filename VARCHAR,
    path VARCHAR,
    sha256 VARCHAR,
    source_page_url VARCHAR,
    file_url VARCHAR,
    fiscal_year INTEGER,
    fiscal_year_be INTEGER,
    as_of_date VARCHAR,
    loaded_at VARCHAR
);

CREATE TABLE IF NOT EXISTS raw.workbook_sheets (
    dataset_name VARCHAR,
    source_file_hash VARCHAR,
    sheet_index INTEGER,
    sheet_name VARCHAR,
    max_row INTEGER,
    max_column INTEGER,
    non_empty_cells INTEGER,
    merged_cell_count INTEGER,
    formula_cell_count INTEGER,
    blank_row_count INTEGER,
    blank_column_count INTEGER,
    guessed_header_row INTEGER,
    sheet_type VARCHAR
);

CREATE TABLE IF NOT EXISTS raw.cells (
    ingestion_run_id VARCHAR,
    dataset_name VARCHAR,
    source_file_hash VARCHAR,
    sheet_index INTEGER,
    sheet_name VARCHAR,
    row_number INTEGER,
    column_number INTEGER,
    cell_value VARCHAR
);
