from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from dataclasses import replace
from pathlib import Path

import duckdb
import pandas as pd

from isap_pipeline.clean import fiscal_year_from_filename
from isap_pipeline.config import load_pipeline_config, load_sources
from isap_pipeline.discovery import compare_with_manifest, discover_sources, save_manifest
from isap_pipeline.dq import run_data_quality_checks
from isap_pipeline.excel_inspector import inspect_workbook
from isap_pipeline.extract_cgd import extract_cgd_workbook
from isap_pipeline.extract_ocsc import extract_ocsc_workbook
from isap_pipeline.load import load_dataframes
from isap_pipeline.logging_utils import configure_logging
from isap_pipeline.metadata import SourceFileMetadata, new_run_id, sha256_file, utc_now_iso

LOGGER = logging.getLogger(__name__)

def main(argv: list[str] | None = None) -> int:
    _configure_utf8_console()
    _configure_warnings()
    parser = argparse.ArgumentParser(description="ISAP Data Engineer pipeline")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile = subparsers.add_parser("profile", help="Profile input Excel workbooks.")
    profile.add_argument("--ocsc", required=True, help="Path to OCSC workbook.")
    profile.add_argument("--cgd", required=True, help="Path to CGD workbook.")

    run = subparsers.add_parser("run", help="Run extraction, cleaning, DQ, and DuckDB load.")
    run.add_argument("--ocsc", required=True, help="Path to OCSC workbook.")
    run.add_argument("--cgd", required=True, help="Path to CGD workbook.")
    run.add_argument("--warehouse", default="data/warehouse/isap.duckdb", help="DuckDB output path.")

    check = subparsers.add_parser("check-new", help="Check official source pages for new files.")
    check.add_argument("--save-manifest", action="store_true", help="Persist discovered metadata.")

    demo = subparsers.add_parser("demo", help="Run sample analytical queries.")
    demo.add_argument("--warehouse", default="data/warehouse/isap.duckdb", help="DuckDB path.")

    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    if args.command == "profile":
        return command_profile(Path(args.ocsc), Path(args.cgd))
    if args.command == "run":
        return command_run(Path(args.ocsc), Path(args.cgd), Path(args.warehouse))
    if args.command == "check-new":
        return command_check_new(save=args.save_manifest)
    if args.command == "demo":
        return command_demo(Path(args.warehouse))
    return 2

def _configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

def _configure_warnings() -> None:
    warnings.filterwarnings("ignore", category=UserWarning, module=r"openpyxl\..*")
    warnings.filterwarnings(
        "ignore",
        category=FutureWarning,
        message=r"The behavior of DataFrame concatenation with empty or all-NA entries.*",
    )

def command_profile(ocsc_path: Path, cgd_path: Path) -> int:
    cfg = load_pipeline_config()
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    profiles = {
        "generated_at": utc_now_iso(),
        "ocsc": inspect_workbook(ocsc_path),
        "cgd": inspect_workbook(cgd_path),
    }
    cfg.profile_output.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    write_profile_markdown(profiles, Path("docs/data_profiling_report.md"))
    LOGGER.info("Wrote profile JSON: %s", cfg.profile_output)
    LOGGER.info("Wrote profiling report: docs/data_profiling_report.md")
    return 0

def command_run(ocsc_path: Path, cgd_path: Path, warehouse_path: Path) -> int:
    run_id = new_run_id()
    LOGGER.info("Starting ingestion run %s", run_id)
    sources = {item.dataset_name: item for item in load_sources()}
    ocsc_meta = _source_metadata("ocsc_government_manpower", ocsc_path, sources)
    cgd_meta = _source_metadata("cgd_budget_execution", cgd_path, sources)

    LOGGER.info("Inspecting workbook structure")
    ocsc_profile = inspect_workbook(ocsc_path)
    cgd_profile = inspect_workbook(cgd_path)
    workbook_sheets = pd.concat(
        [
            _sheet_profile_frame(ocsc_meta, ocsc_profile),
            _sheet_profile_frame(cgd_meta, cgd_profile),
        ],
        ignore_index=True,
    )

    LOGGER.info("Extracting OCSC workbook")
    ocsc_extract = extract_ocsc_workbook(ocsc_path, ocsc_meta, run_id)
    LOGGER.info("Extracting CGD workbook")
    cgd_extract = extract_cgd_workbook(cgd_path, cgd_meta, run_id)
    if cgd_extract.as_of_date:
        cgd_meta = replace(cgd_meta, as_of_date=cgd_extract.as_of_date.isoformat())

    ocsc_frames = [df for df in [ocsc_extract.workforce_agency, ocsc_extract.workforce_profile] if not df.empty]
    ocsc_workforce = pd.concat(ocsc_frames, ignore_index=True) if ocsc_frames else pd.DataFrame()
    raw_cells = pd.concat([ocsc_extract.raw_cells, cgd_extract.raw_cells], ignore_index=True)
    source_files = pd.DataFrame([ocsc_meta.as_dict(), cgd_meta.as_dict()])

    LOGGER.info("Running data quality checks")
    dq_issues = run_data_quality_checks(cgd_extract.budget_execution, ocsc_workforce, run_id)
    processed_dir = load_pipeline_config().processed_dir
    processed_dir.mkdir(parents=True, exist_ok=True)
    dq_issues.to_json(processed_dir / "dq_issues.json", orient="records", force_ascii=False, indent=2)

    LOGGER.info("Loading DuckDB warehouse: %s", warehouse_path)
    counts = load_dataframes(
        warehouse_path,
        run_id=run_id,
        source_files=source_files,
        workbook_sheets=workbook_sheets,
        raw_cells=raw_cells,
        cgd_budget_execution=cgd_extract.budget_execution,
        ocsc_workforce=ocsc_workforce,
        dq_issues=dq_issues,
    )
    LOGGER.info("Load complete: %s", counts)
    print(json.dumps({"run_id": run_id, "warehouse": str(warehouse_path), "counts": counts}, ensure_ascii=False, indent=2))
    return 0

def command_check_new(save: bool = False) -> int:
    cfg = load_pipeline_config()
    discovered = discover_sources()
    result = compare_with_manifest(discovered, cfg.manifest_path)
    if save:
        save_manifest(discovered, cfg.manifest_path)
    cfg.source_check_output.parent.mkdir(parents=True, exist_ok=True)
    cfg.source_check_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

def command_demo(warehouse_path: Path) -> int:
    if not warehouse_path.exists():
        raise FileNotFoundError(f"Warehouse not found: {warehouse_path}")
    con = duckdb.connect(str(warehouse_path), read_only=True)
    try:
        queries = _sample_queries()
        for idx, query in enumerate(queries, start=1):
            print(f"\n--- Query {idx} ---")
            frame = con.execute(query).df()
            if frame.empty:
                print("(no rows)")
            else:
                print(frame.to_string(index=False, max_rows=12))
    finally:
        con.close()
    return 0

def _source_metadata(
    dataset_name: str, path: Path, sources: dict[str, object]
) -> SourceFileMetadata:
    source_cfg = sources.get(dataset_name)
    fiscal_year, fiscal_year_be = fiscal_year_from_filename(path.name)
    return SourceFileMetadata(
        dataset_name=dataset_name,
        source_name=getattr(source_cfg, "name", dataset_name),
        path=path,
        sha256=sha256_file(path),
        source_page_url=getattr(source_cfg, "page_url", None),
        file_url=None,
        fiscal_year=fiscal_year,
        fiscal_year_be=fiscal_year_be,
    )

def _sheet_profile_frame(meta: SourceFileMetadata, profile: dict[str, object]) -> pd.DataFrame:
    rows = []
    for idx, sheet in enumerate(profile["sheets"], start=1):  # type: ignore[index]
        rows.append(
            {
                "dataset_name": meta.dataset_name,
                "source_file_hash": meta.sha256,
                "sheet_index": idx,
                **sheet,
            }
        )
    return pd.DataFrame(rows)

def write_profile_markdown(profiles: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ocsc = profiles["ocsc"]  # type: ignore[index]
    cgd = profiles["cgd"]  # type: ignore[index]
    lines = [
        "# Data Profiling Report",
        "",
        "รายงานนี้สร้างจากการ inspect workbook จริงด้วย `openpyxl` ผ่านคำสั่ง `python -m isap_pipeline profile`.",
        "",
        "## สรุปภาพรวม",
        "",
        f"- OCSC: `{ocsc['path']}` มี {ocsc['sheet_count']} sheets",  # type: ignore[index]
        f"- CGD: `{cgd['path']}` มี {cgd['sheet_count']} sheets",  # type: ignore[index]
        "",
        "## OCSC government workforce statistics",
        "",
        _sheet_table(ocsc["sheets"]),  # type: ignore[index]
        "",
        "ปัญหาสำคัญที่พบ: workbook เป็นรายงานสำหรับอ่าน ไม่ใช่ flat data; มี cover/index, merged cells, multi-row headers, formula cells, wide tables และ subtotal/total ปะปนกับ detail rows จึงต้องเก็บ raw cell ก่อน แล้วค่อย normalize เฉพาะ sheet ที่มี grain ชัดเจน",
        "",
        "## CGD budget execution statistics",
        "",
        _sheet_table(cgd["sheets"]),  # type: ignore[index]
        "",
        "ปัญหาสำคัญที่พบ: ตารางมีหัว 2 ชั้น, มีทั้งมุมมองเบิกจ่ายและใช้จ่าย, ค่าเงินเป็นล้านบาท, percent อยู่ในรูป 0-100, มีรหัสหน่วยงานเฉพาะบาง sheet และมีช่องว่างจาก merged cells ต้อง flatten header และ unpivot current/investment/total เป็น long rows",
        "",
        "## Cleaning Strategy",
        "",
        "- เก็บ raw cell พร้อม sheet, row, column, file hash และ ingestion_run_id เพื่อ audit ย้อนกลับได้",
        "- normalize header โดยลบ newline/ช่องว่างซ้ำและ map synonym สำคัญ เช่น เบิกจ่าย/การใช้จ่าย/วงเงินงบประมาณหลังโอนเปลี่ยนแปลง",
        "- unpivot wide tables ให้หนึ่ง row ต่อ entity/report_type/expense_category",
        "- แยก total/subtotal ด้วย `entity_type` แทนการทิ้งทันที เพื่อให้ตรวจ reconciliation ได้",
        "- แปลงวันที่ พ.ศ. เป็น ค.ศ. และเก็บ fiscal_year_be ควบคู่ fiscal_year",
        "- เก็บ `source_file_hash` เพื่อให้โหลดซ้ำแบบ idempotent และตรวจไฟล์ใหม่รายเดือนได้",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _sheet_table(sheets: object) -> str:
    rows = [
        "| sheet | rows | cols | merged | formulas | blank rows | guessed header | type |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for sheet in sheets:  # type: ignore[assignment]
        rows.append(
            "| {sheet_name} | {max_row} | {max_column} | {merged_cell_count} | {formula_cell_count} | {blank_row_count} | {guessed_header_row} | {sheet_type} |".format(
                **sheet
            )
        )
    return "\n".join(rows)

def _sample_queries() -> list[str]:
    sql = Path("sql/004_sample_queries.sql").read_text(encoding="utf-8")
    return [part.strip() for part in sql.split(";") if part.strip()]
