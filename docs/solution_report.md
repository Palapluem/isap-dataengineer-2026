# Solution Report

## Executive Summary

โซลูชันนี้สร้าง data pipeline ที่รันได้จริงสำหรับข้อมูลกำลังพลภาครัฐของสำนักงาน ก.พ. และข้อมูลผลการเบิกจ่าย/ใช้จ่ายงบประมาณของกรมบัญชีกลาง โดยออกแบบเป็น 3 layer คือ raw, staging และ mart บน DuckDB เพื่อให้ demo ได้ง่ายในวันสัมภาษณ์

ผลการรันล่าสุด:

- raw cells: 125,890 rows
- workbook sheet inventory: 83 sheets
- CGD budget execution fact: 2,913 rows
- OCSC government manpower fact: 5,801 rows
- warehouse output: `data/warehouse/isap.duckdb`
- EDA notebook: `notebooks/01_eda_data_profiling.ipynb`
- tests: `python -m pytest` ผ่าน 9 tests

## Mapping ต่อเกณฑ์ 120 คะแนน

| เกณฑ์ | สิ่งที่ทำ |
|---|---|
| DW design 20 คะแนน | ออกแบบ raw/staging/mart, star schema, fact/dimension, grain และเหตุผลใน `docs/warehouse_design.md` |
| EDA & Data Profiling 20 คะแนน | inspect workbook จริงทั้ง 2 ไฟล์และเขียน report ใน `docs/data_profiling_report.md` |
| Automated Pipeline 60 คะแนน | CLI `profile`, `run`, `check-new`, `demo`; มี extractor, cleaning, DQ, DuckDB loading และ SQL sample |
| Junior Recommendation 20 คะแนน | ข้อเสนอแนะ 12 ข้อใน `docs/junior_recommendations.md` |
| GitHub/Demo | repo มี source code, tests, SQL, config, README และ demo script |
| ใช้ AI ได้แต่อธิบาย code ได้ | module แยกชัดเจน อ่านง่าย มี type hints และเอกสารอธิบาย flow |

## Data Source Overview

| Dataset | Local file | Official page | Hash |
|---|---|---|---|
| OCSC government workforce | `datasets/ocsc/thai-gov-manpower-2567.4.xlsx` | https://www.ocsc.go.th/strategy-policy-work-plan/reports-statistics/government-workforce-statistics-report/2021-present-workforce-statistics/ | `fcb9ee5644ee235031a0e363e42dc8a207b72248e8d8ac770e6b4de9afad7f9b` |
| CGD budget execution | `datasets/cgd/2026.07.03.xlsx` | https://www.cgd.go.th/cs/internet/internet/%E0%B8%82%E0%B9%88%E0%B8%B2%E0%B8%A7%E0%B8%AA%E0%B8%96%E0%B8%B4%E0%B8%95%E0%B8%B4.html | `309ad096e8e1372968346f994d2912faa5e89e96a3d389552ea9f9e3b2c58e95` |

Assumption: ใน runtime นี้ network ของ shell ถูก block จึงใช้ local files ที่โจทย์ให้เป็น latest dataset สำหรับ demo และบันทึกข้อจำกัดไว้ใน README/DQ flow

## DW Design Summary

ใช้ dimensional model เพราะ analyst ต้องการ query ด้วยมุมมอง agency, ministry, geography, date, metric และ expense category มากกว่าการอ่าน cell report ตามรูป Excel เดิม

- Raw layer: เก็บ source file metadata, sheet inventory และ raw cell ทุก cell พร้อม `source_file_hash`
- Staging layer: แปลง report table เป็น normalized rows เช่น CGD จาก wide current/investment/total เป็น long rows
- Mart layer: fact tables สำหรับ manpower และ budget execution พร้อม dimensions สำหรับ source file, date และ agency

## Pipeline Implementation Summary

CLI หลักอยู่ที่ `src/isap_pipeline/cli.py`

- `excel_inspector.py`: profile sheet count, rows, columns, merged cells, formulas, blank rows และ guessed header
- `extract_ocsc.py`: extract raw cells และ manpower facts จาก sheet สำคัญของ OCSC
- `extract_cgd.py`: extract summary/detail budget rows และ unpivot expense categories
- `clean.py`: normalize Thai text/header, date พ.ศ. เป็น ค.ศ., numeric conversion
- `dq.py`: ตรวจ non-negative, percent range และ duplicate grain
- `load.py`: create DuckDB schemas และ load แบบ delete-insert ตาม file hash
- `discovery.py`: ตรวจหน้าเว็บ source รายเดือนและคืน status `no_new_data`, `new_data_found`, `source_unavailable`

## How To Run Demo

```powershell
python -m isap_pipeline profile --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx"
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
python -m isap_pipeline demo --warehouse "data/warehouse/isap.duckdb"
python -m pytest
```

## Assumptions and Limitations

- OCSC มี 68 sheets และหลาย sheet เป็น chart/report decoration จึงไม่ได้ force ทุก sheet เข้าหนึ่ง schema เดียว แต่เก็บ raw cells ทั้งหมดไว้ audit
- CGD มี 15 sheets ที่โครงสร้างใกล้กัน แต่มี variant ระหว่างเบิกจ่ายและใช้จ่าย จึง normalize ด้วย `report_type`
- การเทียบ OCSC-CGD ยังใช้ normalized Thai name เป็น demo join ควรทำ master agency mapping ก่อน production
- DuckDB เหมาะกับ take-home demo; production สามารถย้าย mart layer ไป PostgreSQL, ClickHouse, BigQuery หรือ Snowflake ได้
