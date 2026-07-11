from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "01_eda_data_profiling.ipynb"


def md(source: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(dedent(source).strip() + "\n")


def code(source: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(dedent(source).strip() + "\n")


def build_notebook() -> nbf.NotebookNode:
    cells = [
        md(
            """
            # ISAP EDA & Data Profiling Notebook

            Notebook นี้เป็นหลักฐานการสำรวจข้อมูลจริงของทั้ง 2 datasets คือ OCSC และ CGD ก่อนนำไปออกแบบ data warehouse และ pipeline

            หลักการใช้งาน:

            - ใช้ notebook เพื่ออธิบาย EDA/profiling ให้อ่านตามง่าย
            - ใช้ production-style code ใน `src/isap_pipeline/` สำหรับ pipeline จริง
            - ใช้รายงานใน `docs/` เป็น final answer สำหรับส่งผู้ตรวจ
            """
        ),
        md(
            """
            ## tl;dr

            - OCSC workbook มี 68 sheets และเป็น Excel แบบรายงาน มี cover/index, merged cells, formula cells, multi-row headers, subtotal/total rows และ wide tables หลายรูปแบบ
            - CGD workbook มี 15 sheets โครงสร้างสม่ำเสมอกว่า แต่ยังมีหัวตาราง 2 ชั้น และต้องแยกความหมายระหว่าง `เบิกจ่าย` กับ `ใช้จ่าย`
            - แนวทางที่เหมาะคือเก็บ raw cells ทุก sheet ก่อน แล้ว normalize เฉพาะ sheet/table ที่มี grain ชัดเจนเข้าสู่ staging/mart
            - การเชื่อม OCSC กับ CGD ทำได้ระดับ demo ด้วย normalized Thai entity name แต่ production ควรมี master agency mapping
            """
        ),
        md(
            """
            ## 1. Setup

            ส่วนนี้โหลด dependency และ helper function จาก package จริง เพื่อให้ notebook ไม่แยก logic ออกจาก pipeline
            """
        ),
        code(
            r"""
            from pathlib import Path
            import sys
            import warnings

            import matplotlib.pyplot as plt
            import pandas as pd
            from IPython.display import display
            from openpyxl import load_workbook

            PROJECT_ROOT = Path.cwd()
            if PROJECT_ROOT.name == "notebooks":
                PROJECT_ROOT = PROJECT_ROOT.parent

            sys.path.insert(0, str(PROJECT_ROOT / "src"))

            from isap_pipeline.dq import run_data_quality_checks
            from isap_pipeline.excel_inspector import inspect_workbook
            from isap_pipeline.extract_cgd import extract_cgd_workbook
            from isap_pipeline.extract_ocsc import extract_ocsc_workbook
            from isap_pipeline.metadata import SourceFileMetadata, sha256_file

            warnings.filterwarnings("ignore", category=UserWarning, module=r"openpyxl\..*")
            pd.set_option("display.max_columns", 40)
            pd.set_option("display.max_colwidth", 90)

            OCSC_PATH = PROJECT_ROOT / "datasets" / "ocsc" / "thai-gov-manpower-2567.4.xlsx"
            CGD_PATH = PROJECT_ROOT / "datasets" / "cgd" / "2026.07.03.xlsx"

            assert OCSC_PATH.exists(), OCSC_PATH
            assert CGD_PATH.exists(), CGD_PATH
            """
        ),
        md(
            """
            ## 2. Source Metadata

            ตารางนี้ยืนยันตำแหน่งไฟล์, ขนาดไฟล์ และ SHA-256 hash สำหรับ lineage/idempotency
            """
        ),
        code(
            r"""
            source_files = pd.DataFrame(
                [
                    {
                        "dataset": "ocsc_government_manpower",
                        "path": str(OCSC_PATH.relative_to(PROJECT_ROOT)),
                        "sha256": sha256_file(OCSC_PATH),
                        "size_mb": round(OCSC_PATH.stat().st_size / 1024 / 1024, 2),
                    },
                    {
                        "dataset": "cgd_budget_execution",
                        "path": str(CGD_PATH.relative_to(PROJECT_ROOT)),
                        "sha256": sha256_file(CGD_PATH),
                        "size_mb": round(CGD_PATH.stat().st_size / 1024 / 1024, 2),
                    },
                ]
            )
            source_files
            """
        ),
        md(
            """
            ## 3. Workbook Inventory

            ใช้ `inspect_workbook()` เพื่อสรุป sheet count, cell count, merged cells, formula cells, blank rows และ guessed header row จากไฟล์จริง
            """
        ),
        code(
            r"""
            ocsc_profile = inspect_workbook(OCSC_PATH)
            cgd_profile = inspect_workbook(CGD_PATH)

            ocsc_sheets = pd.DataFrame(ocsc_profile["sheets"])
            cgd_sheets = pd.DataFrame(cgd_profile["sheets"])

            workbook_summary = pd.DataFrame(
                [
                    {
                        "dataset": "OCSC",
                        "sheet_count": ocsc_profile["sheet_count"],
                        "total_non_empty_cells": int(ocsc_sheets["non_empty_cells"].sum()),
                        "merged_cells": int(ocsc_sheets["merged_cell_count"].sum()),
                        "formula_cells": int(ocsc_sheets["formula_cell_count"].sum()),
                        "blank_rows": int(ocsc_sheets["blank_row_count"].sum()),
                    },
                    {
                        "dataset": "CGD",
                        "sheet_count": cgd_profile["sheet_count"],
                        "total_non_empty_cells": int(cgd_sheets["non_empty_cells"].sum()),
                        "merged_cells": int(cgd_sheets["merged_cell_count"].sum()),
                        "formula_cells": int(cgd_sheets["formula_cell_count"].sum()),
                        "blank_rows": int(cgd_sheets["blank_row_count"].sum()),
                    },
                ]
            )
            workbook_summary
            """
        ),
        code(
            r"""
            fig, axes = plt.subplots(1, 2, figsize=(11, 4))
            for ax, frame, title in [
                (axes[0], ocsc_sheets, "OCSC sheet types"),
                (axes[1], cgd_sheets, "CGD sheet types"),
            ]:
                counts = frame["sheet_type"].value_counts().sort_values(ascending=True)
                counts.plot(kind="barh", ax=ax)
                ax.set_title(title)
                ax.set_xlabel("sheet count")
                ax.set_ylabel("")
            plt.tight_layout()
            plt.show()
            """
        ),
        md(
            """
            ## 4. OCSC EDA

            OCSC เป็น workbook ที่ซับซ้อนกว่า เพราะมีหลาย report sections ในไฟล์เดียว ตารางด้านล่างแสดง sheet ที่ใหญ่ที่สุดและ sheet ที่มี merged/formula cells สูง
            """
        ),
        code(
            r"""
            profile_cols = [
                "sheet_name",
                "max_row",
                "max_column",
                "non_empty_cells",
                "merged_cell_count",
                "formula_cell_count",
                "blank_row_count",
                "guessed_header_row",
                "sheet_type",
            ]

            print("OCSC: top 12 sheets by non-empty cells")
            display(ocsc_sheets.sort_values("non_empty_cells", ascending=False)[profile_cols].head(12))

            print("OCSC: top 12 sheets by merged cells")
            display(ocsc_sheets.sort_values("merged_cell_count", ascending=False)[profile_cols].head(12))
            """
        ),
        code(
            r"""
            ocsc_issues = pd.DataFrame(
                [
                    {
                        "observed_issue": "มี cover/index/report decoration",
                        "why_it_matters": "ไม่ควร ingest ทุก sheet เป็น fact table เดียว",
                        "cleaning_strategy": "เก็บ raw cells ทุก sheet แล้วเลือก normalize เฉพาะ sheet ที่ grain ชัดเจน",
                    },
                    {
                        "observed_issue": "merged cells และ multi-row headers",
                        "why_it_matters": "header ไม่อยู่ใน row เดียวและชื่อ metric กระจายหลาย column",
                        "cleaning_strategy": "flatten header และ map metric เป็น long format",
                    },
                    {
                        "observed_issue": "subtotal/total ปะปนกับ detail rows",
                        "why_it_matters": "ถ้านับรวมกับ detail จะ double count",
                        "cleaning_strategy": "tag `entity_type` เป็น total/ministry/agency",
                    },
                    {
                        "observed_issue": "บาง cell เป็น formula/error token เช่น #REF!",
                        "why_it_matters": "numeric conversion ต้องไม่ crash และต้อง audit ได้",
                        "cleaning_strategy": "convert แบบ safe, เก็บ `source_value`, และใช้ DQ checks",
                    },
                ]
            )
            ocsc_issues
            """
        ),
        code(
            r"""
            def preview_sheet_by_name(path: Path, name_contains: str, rows: int = 12, cols: int = 12) -> pd.DataFrame:
                wb = load_workbook(path, data_only=True, read_only=True)
                ws = next(sheet for sheet in wb.worksheets if name_contains in sheet.title)
                values = []
                for row_idx in range(1, min(ws.max_row, rows) + 1):
                    values.append(
                        [
                            str(ws.cell(row_idx, col_idx).value or "").replace("\n", " ")[:80]
                            for col_idx in range(1, min(ws.max_column, cols) + 1)
                        ]
                    )
                wb.close()
                columns = [f"c{i}" for i in range(1, len(values[0]) + 1)]
                return pd.DataFrame(values, index=range(1, len(values) + 1), columns=columns)

            print("OCSC preview: sheet '17-29' workforce by agency")
            display(preview_sheet_by_name(OCSC_PATH, "17-29", rows=14, cols=12))

            print("OCSC preview: sheet '88-97' workforce profile")
            display(preview_sheet_by_name(OCSC_PATH, "88-97", rows=10, cols=20))
            """
        ),
        md(
            """
            ## 5. CGD EDA

            CGD โครงสร้างค่อนข้างสม่ำเสมอ แต่ต้องอ่านความหมายทางธุรกิจให้ถูก: `เบิกจ่าย` และ `ใช้จ่าย` ไม่ใช่ metric เดียวกัน
            """
        ),
        code(
            r"""
            print("CGD: all sheets")
            display(cgd_sheets[profile_cols].sort_values("sheet_name"))

            cgd_issues = pd.DataFrame(
                [
                    {
                        "observed_issue": "หัวตาราง 2 ชั้น",
                        "why_it_matters": "ชื่อ measure เช่น budget/disbursement/pct อยู่คนละ row กับ current/investment/total",
                        "cleaning_strategy": "หา group span จาก header row แล้ว unpivot เป็น long rows",
                    },
                    {
                        "observed_issue": "มีทั้ง sheet เบิกจ่ายและใช้จ่าย",
                        "why_it_matters": "เบิกจ่ายคือเงินจ่ายจริง ส่วนใช้จ่ายรวมมุมมอง commitment/PO บางส่วน",
                        "cleaning_strategy": "เก็บ `report_type` เป็น disbursement/expenditure",
                    },
                    {
                        "observed_issue": "หน่วยเงินเป็นล้านบาท",
                        "why_it_matters": "ต้องระบุ unit ชัดเจนเพื่อไม่ให้ analyst ตีความผิด",
                        "cleaning_strategy": "ใช้ column suffix `_million_baht`",
                    },
                    {
                        "observed_issue": "ชื่อหน่วยงานอาจซ้ำ แต่มี entity_code ต่างกัน",
                        "why_it_matters": "duplicate check ต้องใช้ grain ที่รวม code ไม่ใช่ใช้ชื่ออย่างเดียว",
                        "cleaning_strategy": "grain ของ CGD ใช้ source/sheet/entity/entity_code/report_type/expense_category",
                    },
                ]
            )
            cgd_issues
            """
        ),
        code(
            r"""
            print("CGD preview: summary sheet")
            display(preview_sheet_by_name(CGD_PATH, "สรุปภาพรวม", rows=12, cols=10))

            print("CGD preview: disbursement by agency")
            display(preview_sheet_by_name(CGD_PATH, "3.", rows=12, cols=15))

            print("CGD preview: expenditure by agency")
            display(preview_sheet_by_name(CGD_PATH, "4.", rows=12, cols=18))
            """
        ),
        md(
            """
            ## 6. Extracted Rows and Transform Validation

            ส่วนนี้เรียก extractor จริงจาก pipeline เพื่อให้เห็นว่า EDA เชื่อมกับ implementation ไม่ใช่แค่การดู Excel ด้วยตา
            """
        ),
        code(
            r"""
            run_id = "notebook-eda"
            ocsc_meta = SourceFileMetadata(
                dataset_name="ocsc_government_manpower",
                source_name="OCSC government workforce statistics",
                path=OCSC_PATH,
                sha256=sha256_file(OCSC_PATH),
                fiscal_year=2024,
                fiscal_year_be=2567,
            )
            cgd_meta = SourceFileMetadata(
                dataset_name="cgd_budget_execution",
                source_name="CGD budget disbursement statistics",
                path=CGD_PATH,
                sha256=sha256_file(CGD_PATH),
                fiscal_year=2026,
                fiscal_year_be=2569,
            )

            ocsc_extract = extract_ocsc_workbook(OCSC_PATH, ocsc_meta, run_id)
            cgd_extract = extract_cgd_workbook(CGD_PATH, cgd_meta, run_id)
            ocsc_workforce = pd.concat(
                [ocsc_extract.workforce_agency, ocsc_extract.workforce_profile],
                ignore_index=True,
            )

            extracted_summary = pd.DataFrame(
                [
                    {
                        "dataset": "OCSC",
                        "raw_cell_rows": len(ocsc_extract.raw_cells),
                        "normalized_rows": len(ocsc_workforce),
                        "target_table": "staging.ocsc_workforce",
                    },
                    {
                        "dataset": "CGD",
                        "raw_cell_rows": len(cgd_extract.raw_cells),
                        "normalized_rows": len(cgd_extract.budget_execution),
                        "target_table": "staging.cgd_budget_execution",
                    },
                ]
            )
            extracted_summary
            """
        ),
        code(
            r"""
            print("OCSC extracted rows by metric group")
            display(
                ocsc_workforce.groupby(["entity_type", "metric_group"], dropna=False)
                .size()
                .reset_index(name="rows")
                .sort_values("rows", ascending=False)
                .head(20)
            )

            print("CGD extracted rows by report type, entity type, and expense category")
            display(
                cgd_extract.budget_execution.groupby(
                    ["report_type", "entity_type", "expense_category"], dropna=False
                )
                .size()
                .reset_index(name="rows")
                .sort_values(["report_type", "entity_type", "expense_category"])
            )
            """
        ),
        code(
            r"""
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))

            ocsc_workforce["metric_group"].value_counts().sort_values().plot(kind="barh", ax=axes[0])
            axes[0].set_title("OCSC normalized rows by metric group")
            axes[0].set_xlabel("rows")
            axes[0].set_ylabel("")

            cgd_extract.budget_execution["report_type"].value_counts().sort_values().plot(kind="barh", ax=axes[1])
            axes[1].set_title("CGD normalized rows by report type")
            axes[1].set_xlabel("rows")
            axes[1].set_ylabel("")

            plt.tight_layout()
            plt.show()
            """
        ),
        md(
            """
            ## 7. Data Quality Checks

            DQ checks ใช้กฎที่ตรงกับ business grain เช่น CGD ต้องรวม `entity_code` ใน duplicate key เพราะบางหน่วยงานชื่อซ้ำได้
            """
        ),
        code(
            r"""
            dq_result = run_data_quality_checks(cgd_extract.budget_execution, ocsc_workforce, run_id)
            dq_result
            """
        ),
        md(
            """
            ## 8. Takeaways

            - ทั้ง 2 datasets ถูกแยก source, extractor, staging และ mart ชัดเจน
            - OCSC ต้องระวัง report workbook structure จึงใช้แนว raw-first และ normalize เฉพาะ grain ที่ชัดเจนก่อน
            - CGD เหมาะกับการ flatten/unpivot เพราะ header structure ค่อนข้างซ้ำกันหลาย sheet
            - การ join ระหว่าง OCSC และ CGD ยังควรถือเป็น demo จนกว่าจะมี master agency mapping
            - Notebook นี้ควรใช้เป็น EDA evidence ส่วนการ demo pipeline ให้ใช้ CLI ใน README
            """
        ),
    ]

    return nbf.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
    )


def main() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(build_notebook(), NOTEBOOK_PATH)
    print(f"Wrote {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
