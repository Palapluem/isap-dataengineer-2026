from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import pandas as pd

@dataclass(frozen=True)
class DQIssue:
    check_name: str
    severity: str
    dataset_name: str
    table_name: str
    issue_count: int
    sample: str
    status: str = "failed"

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "severity": self.severity,
            "dataset_name": self.dataset_name,
            "table_name": self.table_name,
            "issue_count": self.issue_count,
            "sample": self.sample,
            "status": self.status,
        }

def run_data_quality_checks(
    cgd_budget_execution: pd.DataFrame,
    ocsc_workforce: pd.DataFrame,
    run_id: str,
) -> pd.DataFrame:
    issues: list[DQIssue] = []
    issues.extend(_check_cgd(cgd_budget_execution))
    issues.extend(_check_ocsc(ocsc_workforce))
    if not issues:
        issues.append(
            DQIssue(
                check_name="all_core_checks",
                severity="info",
                dataset_name="all",
                table_name="all",
                issue_count=0,
                sample="All configured core data-quality checks passed.",
                status="passed",
            )
        )
    frame = pd.DataFrame([issue.as_dict() for issue in issues])
    frame.insert(0, "ingestion_run_id", run_id)
    return frame

def _check_cgd(df: pd.DataFrame) -> list[DQIssue]:
    if df.empty:
        return [
            DQIssue(
                check_name="cgd_rows_present",
                severity="error",
                dataset_name="cgd_budget_execution",
                table_name="staging.cgd_budget_execution",
                issue_count=1,
                sample="No CGD budget rows were extracted.",
            )
        ]
    issues: list[DQIssue] = []
    non_negative_cols = [
        "budget_after_transfer_million_baht",
        "allocated_million_baht",
        "po_reserved_debt_million_baht",
        "disbursement_million_baht",
        "expenditure_million_baht",
    ]
    for col in non_negative_cols:
        if col in df.columns:
            bad = df[df[col].notna() & (df[col] < 0)]
            if not bad.empty:
                issues.append(_issue("cgd_non_negative_" + col, "error", df, bad, col))

    pct_cols = ["disbursement_pct", "expenditure_pct"]
    for col in pct_cols:
        if col in df.columns:
            bad = df[df[col].notna() & ((df[col] < 0) | (df[col] > 100))]
            if not bad.empty:
                issues.append(_issue("cgd_pct_between_0_100_" + col, "warning", df, bad, col))

    keys = [
        "source_file_hash",
        "sheet_name",
        "entity_name",
        "entity_code",
        "expense_category",
        "report_type",
    ]
    duplicated = df[df.duplicated(keys, keep=False)] if all(col in df.columns for col in keys) else pd.DataFrame()
    if not duplicated.empty:
        issues.append(
            DQIssue(
                check_name="cgd_duplicate_grain",
                severity="error",
                dataset_name="cgd_budget_execution",
                table_name="staging.cgd_budget_execution",
                issue_count=len(duplicated),
                sample=duplicated[keys].head(3).to_dict("records").__repr__(),
            )
        )
    issues.extend(_check_cgd_total_reconciliation(df))
    return issues


def _check_cgd_total_reconciliation(df: pd.DataFrame) -> list[DQIssue]:
    issues: list[DQIssue] = []
    measures = ["disbursement_million_baht"]
    group_cols = ["source_file_hash", "sheet_name", "report_type", "expense_category"]
    if not all(col in df.columns for col in [*group_cols, "entity_type"]):
        return issues

    for group_key, group in df.groupby(group_cols, dropna=False):
        total_rows = group[group["entity_type"] == "total"]
        detail_rows = group[group["entity_type"] != "total"]
        if len(total_rows) != 1 or detail_rows.empty:
            continue
        for measure in measures:
            if measure not in group.columns:
                continue
            published = total_rows[measure].dropna()
            detail = detail_rows[measure].dropna()
            if len(published) != 1 or detail.empty:
                continue
            published_value = float(published.iloc[0])
            detail_value = float(detail.sum())
            difference = detail_value - published_value
            tolerance = max(0.01, abs(published_value) * 1e-6)
            if abs(difference) <= tolerance:
                continue
            sheet_name = str(group_key[1])
            issues.append(
                DQIssue(
                    check_name=f"cgd_total_reconciliation_{measure}",
                    severity="warning",
                    dataset_name="cgd_budget_execution",
                    table_name="staging.cgd_budget_execution",
                    issue_count=1,
                    sample=(
                        f"sheet={sheet_name!r}, published={published_value:.6f}, "
                        f"detail_sum={detail_value:.6f}, difference={difference:.6f}"
                    ),
                )
            )
    return issues

def _check_ocsc(df: pd.DataFrame) -> list[DQIssue]:
    if df.empty:
        return [
            DQIssue(
                check_name="ocsc_rows_present",
                severity="error",
                dataset_name="ocsc_government_manpower",
                table_name="staging.ocsc_workforce",
                issue_count=1,
                sample="No OCSC workforce rows were extracted.",
            )
        ]
    issues: list[DQIssue] = []
    if "headcount" in df.columns:
        bad = df[df["headcount"].notna() & (df["headcount"] < 0)]
        if not bad.empty:
            issues.append(_issue("ocsc_headcount_non_negative", "error", df, bad, "headcount"))
    if "percentage" in df.columns:
        bad = df[df["percentage"].notna() & ((df["percentage"] < 0) | (df["percentage"] > 100))]
        if not bad.empty:
            issues.append(_issue("ocsc_pct_between_0_100", "warning", df, bad, "percentage"))
    keys = ["source_file_hash", "sheet_name", "agency_name", "metric_name", "row_number"]
    duplicated = df[df.duplicated(keys, keep=False)] if all(col in df.columns for col in keys) else pd.DataFrame()
    if not duplicated.empty:
        issues.append(
            DQIssue(
                check_name="ocsc_duplicate_grain",
                severity="error",
                dataset_name="ocsc_government_manpower",
                table_name="staging.ocsc_workforce",
                issue_count=len(duplicated),
                sample=duplicated[keys].head(3).to_dict("records").__repr__(),
            )
        )
    return issues

def _issue(check_name: str, severity: str, df: pd.DataFrame, bad: pd.DataFrame, col: str) -> DQIssue:
    dataset = str(df["dataset_name"].iloc[0]) if "dataset_name" in df.columns and not df.empty else "unknown"
    return DQIssue(
        check_name=check_name,
        severity=severity,
        dataset_name=dataset,
        table_name="staging",
        issue_count=len(bad),
        sample=bad[["sheet_name", "entity_name", col]].head(3).to_dict("records").__repr__()
        if "entity_name" in bad.columns
        else bad.head(3).to_dict("records").__repr__(),
    )
