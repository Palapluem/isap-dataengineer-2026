import pandas as pd

from isap_pipeline.dq import run_data_quality_checks


def test_cgd_reconciliation_flags_mismatched_published_total() -> None:
    base = {
        "ingestion_run_id": "run-1",
        "dataset_name": "cgd_budget_execution",
        "source_file_hash": "hash",
        "sheet_name": "2.ministry",
        "report_type": "disbursement",
        "expense_category": "total",
        "entity_code": None,
        "disbursement_pct": 50.0,
    }
    cgd = pd.DataFrame(
        [
            base
            | {
                "entity_type": "ministry",
                "entity_name": "Ministry A",
                "disbursement_million_baht": 40.0,
            },
            base
            | {
                "entity_type": "ministry",
                "entity_name": "Ministry B",
                "disbursement_million_baht": 50.0,
            },
            base
            | {
                "entity_type": "total",
                "entity_name": "Total",
                "disbursement_million_baht": 100.0,
            },
        ]
    )
    ocsc = pd.DataFrame(
        [
            {
                "dataset_name": "ocsc_government_manpower",
                "source_file_hash": "ocsc-hash",
                "sheet_name": "workforce",
                "row_number": 1,
                "agency_name": "Agency A",
                "metric_name": "civil_servant",
                "headcount": 1,
                "percentage": None,
            }
        ]
    )

    result = run_data_quality_checks(cgd, ocsc, "run-1")

    assert "cgd_total_reconciliation_disbursement_million_baht" in set(
        result["check_name"]
    )
