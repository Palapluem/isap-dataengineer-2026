# Demo Script

## 1. Setup

```powershell
python -m pip install -e ".[dev]"
```

Expected: package `isap-data-eng-pipeline` ติดตั้งแบบ editable

## 2. Profile Workbooks

```powershell
python -m isap_pipeline profile --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx"
```

Expected:

- สร้าง `data/processed/profile_summary.json`
- สร้าง/อัปเดต `docs/data_profiling_report.md`
- OCSC มี 68 sheets, CGD มี 15 sheets

## 3. Run Pipeline

```powershell
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
```

Expected output โดยประมาณ:

```text
raw_source_files: 2
raw_workbook_sheets: 83
raw_cells: 125890
staging_cgd_budget_execution: 2937
staging_ocsc_workforce: 5784
mart_fact_budget_execution: 2937
mart_fact_government_manpower: 5784
```

## 4. Run Demo Queries

```powershell
python -m isap_pipeline demo --warehouse "data/warehouse/isap.duckdb"
```

Expected:

- Query 1: top entities by manpower
- Query 2: low CGD disbursement performance by ministry
- Query 3: low expenditure against monthly target
- Query 4: exact-name join candidates between OCSC and CGD

## 5. Check New Data

```powershell
python -m isap_pipeline check-new
```

Expected status:

- `no_new_data` ถ้า metadata ตรง manifest
- `new_data_found` ถ้า URL/filename/date เปลี่ยน
- `source_unavailable` ถ้า network หรือ source page ใช้งานไม่ได้

## 6. Tests

```powershell
python -m pytest
```

Expected: 16 tests passed

## 7. Optional Sync Latest

ใช้เมื่อ official pages เปิดเผย direct file URL จาก environment ที่รัน:

```powershell
python -m isap_pipeline sync-latest --warehouse "data/warehouse/isap.duckdb"
```

Expected:

- discover และ download OCSC/CGD ให้ครบก่อน load
- รองรับ `.xlsx`, `.xls` และ ZIP ที่มี Excel
- update `config/source_manifest.json` หลัง load สำเร็จ
- คืน exit code 1 และไม่ partial load หาก source ใด source หนึ่ง unavailable

ไม่แนะนำให้ใช้คำสั่งนี้เป็นเส้นทางหลักของ live demo เพราะขึ้นกับเว็บไซต์ภายนอก

## 8. Optional EDA Notebook

```powershell
python -m nbconvert --execute --to notebook --inplace "notebooks/01_eda_data_profiling.ipynb"
```

Expected: notebook executes top-to-bottom and shows workbook profiling tables/charts.
