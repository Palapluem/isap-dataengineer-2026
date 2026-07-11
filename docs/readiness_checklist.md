# ISAP Submission Readiness Checklist

เอกสารนี้ใช้ตรวจความพร้อมก่อนส่งงานและใช้เป็น cheat sheet ตอน demo/interview สำหรับโจทย์ ISAP Data Engineer

## Overall Assessment

สถานะปัจจุบัน: พร้อมส่งแบบมี caveat

เหตุผล: pipeline รันได้จริง, มี warehouse, มี EDA notebook, มี data profiling report, มี DW design, มี tests และมี demo queries ครบตามแกนหลักของโจทย์แล้ว จุดที่ควรพูด caveat คือ official source pages อาจตอบ `403 Forbidden` ในบาง environment จึงต้องอธิบาย fallback `source_unavailable` และ local dataset assumption ให้ชัด

## Score Mapping

| เกณฑ์จากโจทย์ | สถานะ | หลักฐานใน repo |
|---|---|---|
| Visual submission overview | ครบ | `docs/submission_overview.md` |
| Data Warehouse design 20 คะแนน | ครบ | `docs/warehouse_design.md`, `sql/001_create_raw.sql`, `sql/002_create_staging.sql`, `sql/003_create_marts.sql` |
| EDA & Data Profiling 20 คะแนน | ครบ | `notebooks/01_eda_data_profiling.ipynb`, `docs/data_profiling_report.md`, `data/processed/profile_summary.json` |
| Automated pipeline 60 คะแนน | ครบ | `src/isap_pipeline/cli.py`, `extract_ocsc.py`, `extract_cgd.py`, `clean.py`, `dq.py`, `load.py` |
| Monthly new-data check | มีแล้ว มี caveat | `src/isap_pipeline/discovery.py`, `.github/workflows/monthly-check.yml`, `data/processed/source_check_latest.json` หลังรัน `check-new` |
| Junior recommendations 20 คะแนน | ครบ | `docs/junior_recommendations.md` |
| Demo readiness | ครบ | `docs/demo_script.md`, `sql/004_sample_queries.sql`, `data/warehouse/isap.duckdb` |
| Code explainability | ดี | module แยกตามหน้าที่, มี CLI commands, มี tests 9 ตัว |

## Current Validation Snapshot

รันล่าสุดในเครื่องนี้:

| Check | Result |
|---|---|
| `python -m pytest` | ผ่าน 9 tests |
| `python -m isap_pipeline demo --warehouse data/warehouse/isap.duckdb` | รัน sample queries ได้ |
| ตรวจ placeholder question marks ใน repo หลัก | ไม่พบจากไฟล์งานจริง |
| DQ output | `all_core_checks` ผ่าน, issue count = 0 |
| Warehouse tables | raw/staging/mart มีครบ |
| `check-new` | command ทำงาน แต่เว็บทางการตอบ `403 Forbidden` ใน environment นี้ |

## Visuals To Prepare

มีภาพ Mermaid ใน `docs/submission_overview.md` และ `docs/warehouse_design.md` แล้ว สำหรับ screenshot/PNG เพิ่มเติมเป็น optional ถ้าต้องการใช้เปิดระหว่าง demo:

| Visual | Source | เหตุผล |
|---|---|---|
| Pipeline architecture | Mermaid ใน `docs/warehouse_design.md` | อธิบาย flow จาก official/local Excel ไป raw/staging/mart |
| Star schema / ERD | Mermaid ใน `docs/warehouse_design.md` | แสดง fact/dimension และ grain |
| EDA workbook profile chart | `notebooks/01_eda_data_profiling.ipynb` | ช่วยให้เห็นว่า Excel เป็น report-style ไม่ใช่ flat table |
| DuckDB table list / row counts | VS Code Database Client หรือ DuckDB CLI | พิสูจน์ว่ามี warehouse จริง |
| Demo query output | `python -m isap_pipeline demo` | พิสูจน์ว่า mart query ได้และตอบ business question ได้ |

## Improvements If Time Allows

1. เพิ่ม screenshot หรือ exported PNG ลง `docs/assets/` แล้ว embed ใน README/รายงานหลัก
2. เพิ่ม `docs/code_walkthrough.md` อธิบายแต่ละ module แบบสั้น ๆ เพื่อใช้ซ้อมตอบว่า code แต่ละส่วนทำอะไร
3. เพิ่ม data dictionary ราย column สำหรับ `fact_budget_execution` และ `fact_government_manpower` ให้ละเอียดกว่า summary ปัจจุบัน
4. เพิ่ม GitHub Actions workflow สำหรับ `pytest` อีกอัน นอกเหนือจาก monthly source check
5. เพิ่ม integration test สำหรับ workbook sample ที่มี merged cells และ multi-row headers
6. เพิ่ม reconciliation DQ เช่น subtotal เท่ากับผลรวม detail ภายใน tolerance
7. เพิ่ม master agency mapping design/table stub เพื่อเล่าการ join OCSC-CGD แบบ production
8. เพิ่ม export PDF/HTML ของ notebook หรือ report สำหรับเปิดง่ายในวันสัมภาษณ์

## Interview Talking Points

พูดแกนหลักแบบนี้จะชัด:

1. Source Excel เป็น report workbook มี merged cells, multi-row header, total/subtotal และ formula จึงต้องแยก raw/staging/mart
2. Raw layer เก็บ cell-level evidence เพื่อ audit และ rebuild ได้
3. Staging แปลง workbook ให้เป็น normalized rows พร้อม standardize date, Thai text, unit และ percent
4. Mart ใช้ dimensional model เพราะ analyst ต้อง query ตาม agency, date, expense category, metric
5. DuckDB เหมาะกับ local demo เพราะไม่ต้องตั้ง server แต่ production สามารถย้าย mart ไป PostgreSQL/BigQuery/Snowflake ได้
6. Idempotency ใช้ `source_file_hash` และ delete-insert ตาม hash เพื่อรันซ้ำแล้วไม่ duplicate
7. Monthly check มีสถานะ `no_new_data`, `new_data_found`, `source_unavailable` เพื่อไม่ silently fail
8. ข้อจำกัดหลักคือ agency name mapping ระหว่าง OCSC และ CGD ยังเป็น exact normalized name ใน demo; production ควรมี master mapping
