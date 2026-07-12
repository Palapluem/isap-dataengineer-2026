# ISAP Data Engineer Take-Home Test

โปรเจกต์นี้เป็นคำตอบสำหรับโจทย์ Innosoft Student Associate Program สาย Data Engineer งานมีเป้าหมายชัดเจน: เปลี่ยน Excel report จากสำนักงาน ก.พ. และกรมบัญชีกลางให้เป็นข้อมูลที่ตรวจสอบที่มาได้ รันซ้ำได้ และส่งต่อให้ Data Analyst ใช้ SQL วิเคราะห์ได้สะดวก

ผลลัพธ์หลักเป็น local data pipeline ที่ใช้ Python และ DuckDB จึงเปิดดูและสาธิตได้บนเครื่องเดียว โดยไม่ต้องติดตั้ง database server

คำอย่าง `raw`, `staging`, `mart`, `grain` และ `idempotency` มีคำอธิบายแบบภาษาง่ายที่ [docs/terms_explained.md](docs/terms_explained.md)

## Project Overview

repository นี้ตอบโจทย์ครบทั้ง 4 ส่วนของข้อสอบ:

- **ข้อ 1: Data Warehouse Design** - ออกแบบ `raw`, `staging` และ `mart` พร้อมกำหนด grain ของ fact table และเหตุผลในการเลือก DuckDB
- **ข้อ 2: EDA & Data Profiling** - สำรวจโครงสร้างและปัญหาของ OCSC กับ CGD แยกกันก่อนออกแบบ parser
- **ข้อ 3: Automated Data Pipeline** - มี CLI สำหรับ profile, extract, clean, validate, load, demo query, ตรวจ source รายเดือน และ ingest release ใหม่
- **ข้อ 4: Junior Data Engineer Recommendations** - เสนอสิ่งที่ควรทำต่อหากนำงานไปใช้จริง

อ่านคำตอบโดยตรงได้ที่ [docs/assignment_answers.md](docs/assignment_answers.md) และดูแผนที่ของหลักฐานทั้งหมดได้ที่ [docs/submission_overview.md](docs/submission_overview.md)

## Data Provided

งานนี้ใช้ Excel 2 ชุดที่อยู่ใน repository เพื่อให้ reviewer clone แล้วรันซ้ำได้ทันที:

- **OCSC** - `datasets/ocsc/thai-gov-manpower-2567.4.xlsx`: ข้อมูลกำลังพลภาครัฐ ปีงบประมาณ พ.ศ. 2567 จำนวน 68 sheets
- **CGD** - `datasets/cgd/2026.07.03.xlsx`: ข้อมูลผลการเบิกจ่ายและการใช้จ่ายงบประมาณ ณ วันที่ 3 กรกฎาคม พ.ศ. 2569 จำนวน 15 sheets

ทั้งสองไฟล์เป็นรายงาน Excel สำหรับมนุษย์อ่าน ไม่ใช่ตารางที่พร้อม query โดยตรง จึงมี merged cells, หัวตารางหลายชั้น, total/subtotal, formula และ layout ที่ต่างกันตาม sheet

## Key Result

```text
OCSC Excel (68 sheets) + CGD Excel (15 sheets)
        -> profile และเก็บ raw evidence ระดับ cell
        -> parser แยกตาม source และ clean ตามกฎที่ทดสอบได้
        -> data quality checks
        -> DuckDB warehouse: raw / staging / mart
        -> SQL สำหรับ Data Analyst
```

เมื่อรันกับไฟล์ baseline ปัจจุบัน pipeline สร้าง:

```text
2 source files
83 workbook sheets
125,890 non-empty raw cells
5,784 OCSC normalized rows
2,937 CGD normalized rows
```

การโหลดใช้ SHA-256 ของ source file เป็นตัวระบุ release เดิม จึงรันซ้ำแล้วไม่สร้างข้อมูลซ้ำ และยังตรวจสอบย้อนกลับได้ว่าแต่ละแถวมาจากไฟล์ใด

## Project Structure

```text
isap-data-eng-take-home-test/
├── assignment/                 # PDF โจทย์ที่เผยแพร่ได้
├── config/                     # source URLs และ baseline manifest
├── datasets/                   # Excel baseline สำหรับรัน demo
│   ├── cgd/
│   └── ocsc/
├── docs/                       # คำตอบ, design, demo และแนวทางนำเสนอ
├── notebooks/                  # EDA notebook ที่รันซ้ำได้
├── sql/                        # DDL และ analytical SQL
├── src/isap_pipeline/          # production-style pipeline package
├── tests/                      # unit และ integration-focused tests
├── .github/workflows/          # CI และ monthly source check
├── data/                       # โฟลเดอร์ผลลัพธ์ที่สร้างตอนรัน (ไม่ commit)
└── README.md                   # เอกสารเริ่มต้นของโครงการ
```

หน้าที่ของ code หลัก:

- `extract_ocsc.py` และ `extract_cgd.py` อ่าน Excel คนละแบบ เพราะ layout และ grain ของสองแหล่งต่างกัน
- `clean.py` รวมกฎทำความสะอาดข้อความ ตัวเลข และวันที่ไทยที่ใช้ร่วมกัน
- `dq.py` ตรวจความครบถ้วน, ค่า numeric, percent range, duplicate grain และ reconciliation ที่เปรียบเทียบได้
- `load.py` สร้าง DuckDB schemas และโหลดข้อมูลแบบ idempotent
- `discovery.py` และ `downloader.py` ใช้ตรวจ release ใหม่และ ingest source ที่เผยแพร่เป็น direct file URL
- `cli.py` เป็นจุดสั่งงานเดียวผ่าน `python -m isap_pipeline ...`

ดูคำอธิบาย module และ data flow แบบละเอียดได้ที่ [docs/code_walkthrough.md](docs/code_walkthrough.md)

## Git Tracking Policy

repository นี้ตั้งใจเก็บเฉพาะสิ่งที่ reviewer ต้องใช้ตรวจงานและรันซ้ำได้:

| เก็บใน GitHub | ไม่เก็บใน GitHub |
|---|---|
| code, SQL, tests, docs, notebook และ workflow | `data/warehouse/*.duckdb` และ generated JSON |
| Excel baseline ขนาดเล็กสำหรับ demo | `references/` ซึ่งเป็นข้อมูลภายใน |
| PDF โจทย์ต้นฉบับที่อนุญาตให้เผยแพร่ | agent prompt, editor state, local environment และ local helper files |

ไฟล์ `.duckdb` ไม่ใช่ source of truth แต่เป็นผลลัพธ์จาก pipeline จึงควรสร้างใหม่จาก Excel กับ code ทุกครั้ง วิธีนี้ทำให้ reviewer ตรวจ reproducibility ได้ และลดความเสี่ยงที่ไฟล์ warehouse เก่าจะไม่ตรงกับ code เวอร์ชันล่าสุด

## Getting Started

### Prerequisites

- Python 3.11 หรือใหม่กว่า
- Windows PowerShell หรือ terminal ที่รัน Python ได้
- Internet ใช้เฉพาะคำสั่งตรวจ source ใหม่หรือ `sync-latest`; การ demo หลักใช้ไฟล์ local ได้ทั้งหมด

### Install

```powershell
python -m pip install -e ".[dev]"
```

คำสั่งนี้ติดตั้ง pipeline, notebook dependencies, `pytest` และ `ruff` สำหรับตรวจคุณภาพ code

## Workflow

### 1. ดู EDA และ profiling

เปิด [notebooks/01_eda_data_profiling.ipynb](notebooks/01_eda_data_profiling.ipynb) เพื่อดูการสำรวจข้อมูลทั้งสองชุดแบบมีตารางและกราฟ หรือรัน notebook ใหม่ทั้งหมดด้วย:

```powershell
python -m nbconvert --execute --to notebook --inplace "notebooks/01_eda_data_profiling.ipynb"
```

notebook เป็นหลักฐานการสำรวจข้อมูล ส่วน pipeline ที่ใช้จริงอยู่ใน `src/isap_pipeline/`

### 2. Profile Excel workbooks

```powershell
python -m isap_pipeline profile --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx"
```

ผลลัพธ์ที่สร้าง:

- `data/processed/profile_summary.json`
- `docs/data_profiling_report.md`

ค่าที่ควรเห็นคือ OCSC 68 sheets และ CGD 15 sheets

### 3. Run the pipeline

```powershell
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
```

ลำดับการทำงานคือ:

1. inspect workbook structure
2. extract raw cells ของทุก sheet
3. parse และ normalize ตารางที่มี grain ชัดเจน
4. run data-quality checks
5. load ข้อมูลเข้า DuckDB แบบ idempotent
6. rebuild dimensions สำหรับ query ฝั่ง analyst

### 4. Run analytical demo queries

```powershell
python -m isap_pipeline demo --warehouse "data/warehouse/isap.duckdb"
```

คำสั่งนี้ตอบตัวอย่างคำถามของ Data Analyst เช่น หน่วยงานที่มีกำลังพลสูง, หน่วยงานที่มีการเบิกจ่ายต่ำ และรายชื่อหน่วยงานที่เป็น join candidate ระหว่าง OCSC กับ CGD

ตัวอย่าง SQL ฉบับเต็มอยู่ที่ [sql/004_sample_queries.sql](sql/004_sample_queries.sql) โดยทุก query ระบุ filter ที่กันการรวม total/detail หรือ metric คนละความหมายเข้าด้วยกัน

### 5. Inspect DuckDB without a database server

DuckDB เป็น embedded analytical database: warehouse อยู่ในไฟล์เดียวและ Python เปิดไฟล์นั้นโดยตรงได้

```powershell
python -c "import duckdb; con = duckdb.connect('data/warehouse/isap.duckdb'); print(con.execute('SHOW TABLES').fetchall())"
```

หากเปิดด้วย GUI ให้ปิด connection ก่อนสั่ง pipeline เขียนไฟล์เดิม เพื่อหลีกเลี่ยง file lock บน Windows

### 6. Run tests and lint

```powershell
python -m ruff check .
python -m pytest
```

ปัจจุบันมี 16 tests ครอบคลุมการแปลงวันที่, header/text cleaning, parser ของแต่ละ source, total-row handling, reconciliation, idempotency, manifest comparison, ZIP extraction และ sync orchestration GitHub Actions จะรัน lint และ tests ทุก push/PR

## Monitoring New Releases

ทุกเดือน GitHub Actions จะเรียก `check-new` เพื่อเปรียบเทียบ source page กับ baseline ที่ [config/source_manifest.json](config/source_manifest.json)

```powershell
python -m isap_pipeline check-new
```

สถานะที่เป็นไปได้:

- `no_new_data` - metadata ที่ตรวจพบยังเหมือน baseline
- `new_data_found` - filename, publish date หรือ file URL เปลี่ยน
- `source_unavailable` - หน้าเว็บหรือ network ใช้ไม่ได้ จึงต้องไม่ตีความว่าไม่มีข้อมูลใหม่

หาก source page เปิด direct file URL และโครงสร้างใหม่ยังเหมือน baseline ตามสมมติฐานในโจทย์ สามารถสั่ง ingest ทั้งสองแหล่งได้ด้วย:

```powershell
python -m isap_pipeline sync-latest --warehouse "data/warehouse/isap.duckdb"
```

ระบบจะอัปเดต manifest หลังดาวน์โหลดและ load ครบทั้งสองแหล่งเท่านั้น เพื่อหลีกเลี่ยง partial load

## Review Guide

| ถ้าต้องการตรวจเรื่องนี้ | เริ่มที่ |
|---|---|
| คำตอบข้อ 1-4 ตามโจทย์ | [docs/assignment_answers.md](docs/assignment_answers.md) |
| ภาพรวมสิ่งที่ส่งและหลักฐาน | [docs/submission_overview.md](docs/submission_overview.md) |
| Warehouse, grain และ schema | [docs/warehouse_design.md](docs/warehouse_design.md) |
| Data dictionary | [docs/data_dictionary.md](docs/data_dictionary.md) |
| คำศัพท์เทคนิคแบบภาษาง่าย | [docs/terms_explained.md](docs/terms_explained.md) |
| EDA และปัญหาของแต่ละ dataset | [notebooks/01_eda_data_profiling.ipynb](notebooks/01_eda_data_profiling.ipynb), [docs/data_profiling_report.md](docs/data_profiling_report.md) |
| คำสั่งและผลที่ควรเห็น | [docs/demo_script.md](docs/demo_script.md) |
| ข้อเสนอแนะต่อ Senior Data Engineer | [docs/junior_recommendations.md](docs/junior_recommendations.md) |

## Limitations and Next Steps

- OCSC ปี 2567 และ CGD ปี 2569 เป็นคนละช่วงเวลา จึงไม่ควรสรุปความสัมพันธ์เชิงเวลาโดยตรง
- การจับคู่ชื่อหน่วยงานใช้ normalized exact Thai name เพื่อ demo เท่านั้น Production ควรมี master agency mapping ที่ผ่านการ review โดยคน
- Data-quality checks ยืนยันกฎที่กำหนดไว้ ไม่ได้พิสูจน์ business truth ทุก measure โดยอัตโนมัติ
- `sync-latest` ต้องพึ่งรูปแบบของหน้าเว็บทางการ หาก web page เปลี่ยนเป็น client-side rendering หรือปิดกั้น request ระบบจะหยุดและรายงานอย่างชัดเจน

ข้อเสนอแนะที่มีผลสูงสุดสำหรับ production คือทำ data contract กับเจ้าของข้อมูล, สร้าง agency master, ขยาย reconciliation ตาม semantic grain และเพิ่ม monitoring/alerting สำหรับ pipeline runs

## Author

- Wisit Suwannao
