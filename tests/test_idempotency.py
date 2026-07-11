from pathlib import Path

import pandas as pd

from isap_pipeline.dq import run_data_quality_checks
from isap_pipeline.load import load_dataframes


def test_load_is_idempotent_by_source_hash(tmp_path: Path) -> None:
    warehouse = tmp_path / "isap.duckdb"
    source_files = pd.DataFrame(
        [
            {
                "dataset_name": "test",
                "source_name": "test",
                "filename": "test.xlsx",
                "path": "test.xlsx",
                "sha256": "hash-1",
                "source_page_url": None,
                "file_url": None,
                "fiscal_year": 2026,
                "fiscal_year_be": 2569,
                "as_of_date": "2026-07-03",
            }
        ]
    )
    workbook_sheets = pd.DataFrame(
        [
            {
                "dataset_name": "test",
                "source_file_hash": "hash-1",
                "sheet_index": 1,
                "sheet_name": "sheet",
                "max_row": 1,
                "max_column": 1,
                "non_empty_cells": 1,
                "merged_cell_count": 0,
                "formula_cell_count": 0,
                "blank_row_count": 0,
                "blank_column_count": 0,
                "guessed_header_row": 1,
                "sheet_type": "test",
            }
        ]
    )
    raw_cells = pd.DataFrame(
        [
            {
                "ingestion_run_id": "run-1",
                "dataset_name": "test",
                "source_file_hash": "hash-1",
                "sheet_index": 1,
                "sheet_name": "sheet",
                "row_number": 1,
                "column_number": 1,
                "cell_value": "x",
            }
        ]
    )
    cgd = pd.DataFrame(
        [
            {
                "ingestion_run_id": "run-1",
                "dataset_name": "cgd_budget_execution",
                "source_file_hash": "hash-1",
                "sheet_name": "sheet",
                "row_number": 1,
                "fiscal_year": 2026,
                "fiscal_year_be": 2569,
                "as_of_date": "2026-07-03",
                "report_type": "disbursement",
                "entity_type": "agency",
                "entity_name": "กรมตัวอย่าง",
                "entity_code": "001",
                "expense_category": "total",
                "budget_after_transfer_million_baht": 100.0,
                "allocated_million_baht": 100.0,
                "po_reserved_debt_million_baht": 0.0,
                "disbursement_million_baht": 70.0,
                "disbursement_pct": 70.0,
                "expenditure_million_baht": None,
                "expenditure_pct": None,
                "monthly_target_gap_pct": None,
                "remaining_million_baht": None,
                "remaining_pct": None,
            }
        ]
    )
    ocsc = pd.DataFrame(
        [
            {
                "ingestion_run_id": "run-1",
                "dataset_name": "ocsc_government_manpower",
                "source_file_hash": "hash-1",
                "sheet_name": "sheet",
                "row_number": 1,
                "fiscal_year": 2024,
                "fiscal_year_be": 2567,
                "entity_type": "agency",
                "ministry_name": "กระทรวงตัวอย่าง",
                "agency_name": "กรมตัวอย่าง",
                "metric_name": "civil_servant",
                "metric_group": "employment_type",
                "headcount": 10,
                "percentage": None,
                "source_value": "10",
                "source_unit": "person",
            }
        ]
    )
    dq = run_data_quality_checks(cgd, ocsc, "run-1")

    for run_id in ["run-1", "run-2"]:
        load_dataframes(
            warehouse,
            run_id=run_id,
            source_files=source_files,
            workbook_sheets=workbook_sheets,
            raw_cells=raw_cells.assign(ingestion_run_id=run_id),
            cgd_budget_execution=cgd.assign(ingestion_run_id=run_id),
            ocsc_workforce=ocsc.assign(ingestion_run_id=run_id),
            dq_issues=dq.assign(ingestion_run_id=run_id),
        )

    import duckdb

    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        assert con.execute("select count(*) from mart.fact_budget_execution").fetchone()[0] == 1
        assert con.execute("select count(*) from mart.fact_government_manpower").fetchone()[0] == 1
    finally:
        con.close()
