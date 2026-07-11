# ISAP Data Engineer Take-home Pipeline

โปรเจกต์นี้เป็นคำตอบสำหรับโจทย์ Innosoft Student Associate Program สาย Data Engineer โดยสร้าง local automated data pipeline สำหรับข้อมูล 2 แหล่ง:

- OCSC government workforce statistics: `datasets/ocsc/thai-gov-manpower-2567.4.xlsx`
- CGD budget disbursement/expenditure statistics: `datasets/cgd/2026.07.03.xlsx`

ระบบใช้ Python, pandas, openpyxl และ DuckDB เพื่อ demo ได้บนเครื่อง local โดยไม่ต้องติดตั้ง database server

หมายเหตุ: warehouse file นี้ตั้งใจสร้างด้วย DuckDB `0.10.2` เพื่อให้เปิดกับ VS Code Database Client extension ที่ bundle `duckdb.exe v0.10.2` ได้ตรงกัน

## Repository Layout

```text
.
├── assignment/              # PDF โจทย์ต้นฉบับและนโยบายไฟล์ภายใน
├── datasets/                # source Excel files ที่ใช้รัน demo
│   ├── ocsc/
│   └── cgd/
├── notebooks/               # EDA notebook แบบ reproducible
├── src/isap_pipeline/       # production-style pipeline code
├── sql/                     # DDL และ sample analytical queries
├── docs/                    # รายงานคำตอบภาษาไทย
└── data/                    # generated outputs เช่น profile JSON และ DuckDB
```

หมายเหตุ: PDF โจทย์ต้นฉบับเผยแพร่ใน repository ได้ ส่วน `references/` และ agent prompt เป็นข้อมูลภายในที่ถูกเก็บเฉพาะ local และ exclude จาก GitHub

## Setup

```powershell
python -m pip install -e ".[dev]"
```

ถ้าใช้เฉพาะ pipeline ไม่รัน lint สามารถใช้:

```powershell
python -m pip install -e .
```

## Run Profiling

```powershell
python -m isap_pipeline profile --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx"
```

ผลลัพธ์:

- `data/processed/profile_summary.json`
- `docs/data_profiling_report.md`

## Run Pipeline

```powershell
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
```

pipeline จะทำงานตามลำดับ:

1. inspect workbook structure
2. extract raw cells ทุก sheet
3. clean/normalize sheet สำคัญของ OCSC และ CGD
4. run data quality checks
5. load raw/staging/mart เข้า DuckDB แบบ idempotent ด้วย `source_file_hash`

## Demo Queries

```powershell
python -m isap_pipeline demo --warehouse "data/warehouse/isap.duckdb"
```

ตัวอย่าง query อยู่ใน `sql/004_sample_queries.sql`

## EDA Notebook

```powershell
python -m nbconvert --execute --to notebook --inplace "notebooks/01_eda_data_profiling.ipynb"
```

notebook นี้เป็นหลักฐานการสำรวจข้อมูลแบบอ่านตามได้ ส่วน pipeline จริงยังอยู่ใน `src/isap_pipeline/`

ถ้าต้อง rebuild notebook จาก script:

```powershell
python scripts/build_eda_notebook.py
```

## Check New Data

```powershell
python -m isap_pipeline check-new
```

คำสั่งนี้ตรวจหน้าเว็บทางการตาม `config/sources.yml` และเทียบกับ baseline ที่ `config/source_manifest.json` ถ้า network ใช้ไม่ได้จะคืน `source_unavailable` พร้อม error ที่ตรวจสอบได้
ผลการตรวจล่าสุดจะถูกบันทึกไว้ที่ `data/processed/source_check_latest.json` เพื่อใช้เป็นหลักฐานประกอบ demo

หากหน้าเว็บเปิดเผย direct file URL และต้องการดาวน์โหลดพร้อม ingest release ล่าสุด:

```powershell
python -m isap_pipeline sync-latest --warehouse "data/warehouse/isap.duckdb"
```

คำสั่งนี้จะอัปเดต manifest หลังจากดาวน์โหลดทั้งสอง source และ load สำเร็จเท่านั้น

## Inspect DuckDB

```powershell
python - <<'PY'
import duckdb
con = duckdb.connect("data/warehouse/isap.duckdb")
print(con.execute("show tables").fetchall())
print(con.execute("select count(*) from mart.fact_budget_execution").fetchone())
PY
```

หรือใช้ DuckDB CLI แล้วเปิดไฟล์ `data/warehouse/isap.duckdb`

## Run Tests

```powershell
python -m pytest
```

## Scoring Checklist

- Original assignment: ดู `assignment/ISAP_DATA_ENG.pdf`
- Direct answers for Tasks 1-4: ดู `docs/assignment_answers.md`
- Submission overview with visuals: ดู `docs/submission_overview.md`
- Data Warehouse design: ดู `docs/warehouse_design.md`
- Data dictionary: ดู `docs/data_dictionary.md`
- EDA & Data Profiling: ดู `docs/data_profiling_report.md`
- Automated Data Pipeline: ดู `src/isap_pipeline/`, `sql/`, และ demo commands ด้านบน
- Monthly new-data check: ดู `src/isap_pipeline/discovery.py` และ `.github/workflows/monthly-check.yml`
- Junior recommendation: ดู `docs/junior_recommendations.md`
- Demo script: ดู `docs/demo_script.md`
- Code walkthrough: ดู `docs/code_walkthrough.md`
- Presentation guide: ดู `docs/presentation_guide.md`
- Submission readiness: ดู `docs/readiness_checklist.md`

## Artifact Policy

- Commit: source code, SQL, tests, docs, notebooks และ source Excel datasets ที่ใช้รัน demo
- Do not commit: `data/warehouse/*.duckdb`, `data/processed/*.json`, `references/`, agent prompt และ local editor/agent folders
- เหตุผลที่ ignore `.duckdb`: warehouse เป็น generated output ที่ควร rebuild ได้จาก source data และ pipeline เพื่อพิสูจน์ reproducibility

## Limitations

- OCSC workbook มี report-style sheets หลายรูปแบบมาก จึงเก็บ raw ทุก cell และทำ mart จาก sheet ที่มี grain ชัดเจนก่อน
- การ join ระหว่าง OCSC และ CGD ใช้ exact normalized Thai entity name เป็น demo เท่านั้น production ควรมี master agency mapping และ agency code กลาง
- ใน shell sandbox นี้ outbound network ถูก block ทำให้ `check-new` คืน `source_unavailable`; pipeline จึงถือ local files เป็น latest dataset สำหรับ demo
