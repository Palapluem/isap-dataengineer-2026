from __future__ import annotations

from pathlib import Path
import duckdb
import pandas as pd
from isap_pipeline.metadata import utc_now_iso

DDL_FILES = [
    "sql/001_create_raw.sql",
    "sql/002_create_staging.sql",
    "sql/003_create_marts.sql",
]

def create_database(warehouse_path: str | Path) -> duckdb.DuckDBPyConnection:
    warehouse = Path(warehouse_path)
    warehouse.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(warehouse))
    for sql_file in DDL_FILES:
        con.execute(Path(sql_file).read_text(encoding="utf-8"))
    return con

def load_dataframes(
    warehouse_path: str | Path,
    *,
    run_id: str,
    source_files: pd.DataFrame,
    workbook_sheets: pd.DataFrame,
    raw_cells: pd.DataFrame,
    cgd_budget_execution: pd.DataFrame,
    ocsc_workforce: pd.DataFrame,
    dq_issues: pd.DataFrame,
) -> dict[str, int]:
    con = create_database(warehouse_path)
    try:
        hashes = sorted(set(source_files["sha256"].dropna().astype(str).tolist()))
        _delete_existing(con, hashes)
        loaded_at = utc_now_iso()
        source_files = source_files.copy()
        source_files["loaded_at"] = loaded_at
        dq_issues = dq_issues.copy()
        if "source_file_hash" not in dq_issues.columns or dq_issues["source_file_hash"].isna().all():
            dq_issues["source_file_hash"] = "|".join(hashes) if hashes else None

        counts = {
            "raw_source_files": _insert(con, "raw.source_files", source_files),
            "raw_workbook_sheets": _insert(con, "raw.workbook_sheets", workbook_sheets),
            "raw_cells": _insert(con, "raw.cells", raw_cells),
            "staging_cgd_budget_execution": _insert(
                con, "staging.cgd_budget_execution", cgd_budget_execution
            ),
            "staging_ocsc_workforce": _insert(con, "staging.ocsc_workforce", ocsc_workforce),
            "mart_fact_budget_execution": _insert(
                con, "mart.fact_budget_execution", cgd_budget_execution
            ),
            "mart_fact_government_manpower": _insert(
                con, "mart.fact_government_manpower", ocsc_workforce
            ),
            "mart_fact_data_quality_issue": _insert(
                con, "mart.fact_data_quality_issue", dq_issues
            ),
        }
        con.execute(
            """
            INSERT INTO mart.fact_ingestion_run
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                loaded_at,
                int(counts["raw_cells"]),
                int(counts["staging_cgd_budget_execution"]),
                int(counts["staging_ocsc_workforce"]),
                int(dq_issues[dq_issues["status"] == "failed"].shape[0])
                if "status" in dq_issues.columns
                else 0,
                "completed",
            ],
        )
        rebuild_dimensions(con)
        return counts
    finally:
        con.close()

def _delete_existing(con: duckdb.DuckDBPyConnection, hashes: list[str]) -> None:
    if not hashes:
        return
    tables = [
        "raw.source_files",
        "raw.workbook_sheets",
        "raw.cells",
        "staging.cgd_budget_execution",
        "staging.ocsc_workforce",
        "mart.fact_budget_execution",
        "mart.fact_government_manpower",
        "mart.fact_data_quality_issue",
    ]
    for table in tables:
        for file_hash in hashes:
            if table == "raw.source_files":
                con.execute(f"DELETE FROM {table} WHERE sha256 = ?", [file_hash])
            elif table == "mart.fact_data_quality_issue":
                con.execute(f"DELETE FROM {table} WHERE source_file_hash LIKE '%' || ? || '%'", [file_hash])
            else:
                con.execute(f"DELETE FROM {table} WHERE source_file_hash = ?", [file_hash])

def _insert(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    cols = _table_columns(con, table)
    prepared = df.copy()
    for col in cols:
        if col not in prepared.columns:
            prepared[col] = None
    prepared = prepared[cols]
    view_name = "df_to_insert"
    con.register(view_name, prepared)
    quoted_cols = ", ".join(cols)
    con.execute(f"INSERT INTO {table} ({quoted_cols}) SELECT {quoted_cols} FROM {view_name}")
    con.unregister(view_name)
    return len(prepared)

def _table_columns(con: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    schema, table_name = table.split(".", 1)
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        ORDER BY ordinal_position
        """,
        [schema, table_name],
    ).fetchall()
    return [row[0] for row in rows]

def rebuild_dimensions(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE mart.dim_source_file AS
        SELECT
            row_number() OVER () AS source_file_key,
            dataset_name,
            source_name,
            filename,
            sha256,
            source_page_url,
            file_url,
            fiscal_year,
            fiscal_year_be,
            as_of_date,
            loaded_at
        FROM raw.source_files
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE mart.dim_agency AS
        WITH names AS (
            SELECT
                agency_name AS entity_name,
                entity_type,
                ministry_name,
                'ocsc' AS source_system
            FROM staging.ocsc_workforce
            WHERE agency_name IS NOT NULL
            UNION ALL
            SELECT
                entity_name,
                entity_type,
                NULL AS ministry_name,
                'cgd' AS source_system
            FROM staging.cgd_budget_execution
            WHERE entity_name IS NOT NULL
        )
        SELECT
            row_number() OVER (ORDER BY entity_name, entity_type) AS agency_key,
            entity_name,
            lower(regexp_replace(entity_name, '\\s+', '', 'g')) AS normalized_entity_name,
            max(entity_type) AS entity_type,
            max(ministry_name) AS ministry_name,
            string_agg(DISTINCT source_system, ',') AS source_systems
        FROM names
        GROUP BY entity_name, entity_type
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE mart.dim_date AS
        WITH dates AS (
            SELECT DISTINCT as_of_date::DATE AS date_value
            FROM staging.cgd_budget_execution
            WHERE as_of_date IS NOT NULL
        )
        SELECT
            row_number() OVER (ORDER BY date_value) AS date_key,
            date_value,
            year(date_value) AS year,
            month(date_value) AS month,
            day(date_value) AS day
        FROM dates
        """
    )