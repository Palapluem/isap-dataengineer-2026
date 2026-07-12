# คำตอบโจทย์ ISAP Data Engineer ข้อ 1-4

เอกสารนี้ตอบคำถามตามลำดับและน้ำหนักคะแนนในข้อสอบโดยตรง ส่วนรายละเอียดเชิงลึกและหลักฐานที่รันได้เชื่อมไปยัง code, SQL, notebook และเอกสารประกอบใน repository

## แผนที่คำตอบ

| ถ้าต้องการดู | เปิดไฟล์นี้ |
|---|---|
| คำตอบครบทั้ง 4 ข้อแบบเรียงตามโจทย์ | เอกสารนี้ |
| ภาพรวม deliverable และสิ่งที่ commit | `docs/submission_overview.md` |
| แผนผัง warehouse และความหมายของตาราง | `docs/warehouse_design.md`, `docs/data_dictionary.md` |
| คำศัพท์ทางเทคนิคแบบภาษาง่าย | `docs/terms_explained.md` |
| หลักฐาน EDA ของ OCSC และ CGD | `notebooks/01_eda_data_profiling.ipynb`, `docs/data_profiling_report.md` |
| คำสั่ง pipeline, ผลที่ควรเห็น และ demo | `README.md`, `docs/demo_script.md` |

## ขอบเขตข้อมูลที่ใช้

- OCSC: `thai-gov-manpower-2567.4.xlsx` ข้อมูลกำลังพลภาครัฐ ปีงบประมาณ พ.ศ. 2567 จำนวน 68 sheets
- CGD: `2026.07.03.xlsx` ผลการเบิกจ่ายและการใช้จ่ายงบประมาณ ณ วันที่ 3 กรกฎาคม พ.ศ. 2569 จำนวน 15 sheets
- ใช้ไฟล์ทั้งสองที่ได้รับเป็น submission baseline เพราะเป็นไฟล์ล่าสุดตามบริบทของโจทย์
- ระบบมีคำสั่งตรวจหน้าเว็บทางการแยกต่างหาก หากหน้าเว็บตอบ `403`, ใช้ JavaScript rendering หรือไม่พบลิงก์จาก static HTML ระบบจะรายงาน `source_unavailable` แทนการสรุปว่าไม่มีข้อมูลใหม่

## ข้อ 1: Data Warehouse Design (20 คะแนน)

### คำตอบโดยสรุป

เลือกใช้ DuckDB เป็น local analytical warehouse และแบ่งข้อมูลเป็น 3 layers คือ `raw`, `staging` และ `mart` เพราะต้นทางเป็น Excel report สำหรับมนุษย์อ่าน ไม่ใช่ตารางที่พร้อม query โดยตรง การแยก layer ทำให้เก็บหลักฐานต้นทางได้ แก้โครงสร้างที่ไม่สม่ำเสมอได้อย่างตรวจสอบย้อนกลับ และส่งมอบตารางที่ Data Analyst ใช้ SQL วิเคราะห์ได้สะดวก

### เหตุผลที่เลือก DuckDB

1. ขนาดข้อมูลอยู่ในระดับไม่กี่ MB ต่อ release จึงยังไม่ต้องใช้ database server หรือ cloud warehouse
2. DuckDB เป็น columnar analytical database รองรับ SQL, aggregation และ window function เหมาะกับงานวิเคราะห์
3. Demo ได้จากไฟล์เดียวและ rebuild ได้จาก source Excel กับ code
4. ไม่มีค่า infrastructure และลดขั้นตอน setup ในวันสัมภาษณ์
5. หาก production มีหลายผู้ใช้หรือข้อมูลโตขึ้น สามารถย้าย dimensional model เดิมไป PostgreSQL, BigQuery หรือ Snowflake ได้

DuckDB ไม่ได้ถูกเลือกเพราะเป็น query cache เป็นหลัก แต่เลือกเพราะเป็น embedded OLAP engine ที่อ่านและประมวลผลข้อมูลเชิงวิเคราะห์บนเครื่องได้โดยไม่ต้องมี server

### Layer และหน้าที่

| Layer | ตารางหลัก | หน้าที่ |
|---|---|---|
| Raw | `raw.source_files` | เก็บ filename, SHA-256, ปีข้อมูล, URL และเวลาโหลด |
| Raw | `raw.workbook_sheets` | เก็บ sheet inventory, row/column count, header ที่คาดการณ์, merged/formula count |
| Raw | `raw.cells` | เก็บค่าระดับ cell พร้อม sheet/row/column เพื่อ audit และ debug parser |
| Staging | `staging.ocsc_workforce` | แปลงกำลังพลเป็น long-form metric rows |
| Staging | `staging.cgd_budget_execution` | แปลงงบประจำ/ลงทุน/รวม และเบิกจ่าย/ใช้จ่ายเป็น analytical rows |
| Mart | `mart.fact_government_manpower` | fact กำลังพลตามหน่วยงานและ metric |
| Mart | `mart.fact_budget_execution` | fact งบประมาณตามหน่วยงาน หมวดรายจ่าย และมุมรายงาน |
| Mart | `mart.dim_source_file`, `mart.dim_agency`, `mart.dim_date` | dimension สำหรับ lineage, entity และเวลา |
| Mart | `mart.fact_ingestion_run`, `mart.fact_data_quality_issue` | operational facts สำหรับตรวจการรันและคุณภาพข้อมูล |

### Grain ของ fact table

`mart.fact_budget_execution` มี grain เป็น 1 แถวต่อ:

`source release × sheet × entity × report_type × expense_category`

- `report_type`: `disbursement` หรือ `expenditure`
- `expense_category`: `current`, `investment` หรือ `total`
- measure ใช้หน่วยล้านบาทและร้อยละตามต้นทาง

`mart.fact_government_manpower` มี grain เป็น 1 แถวต่อ:

`source release × sheet × entity × metric_name × source row`

- รองรับ metric หลายกลุ่ม เช่น employment type, age, gender และ education
- `headcount` กับ `percentage` แยกกันเพื่อไม่ผสมหน่วยวัด

ไม่รวมข้อมูลทั้งสองแหล่งไว้ใน fact เดียว เพราะ grain, หน่วยวัด และช่วงเวลาต่างกัน OCSC เป็น annual workforce snapshot ปี 2567 ส่วน CGD เป็น budget snapshot ปี 2569 ณ วันที่ระบุ การบังคับรวมจะทำให้เกิด row duplication และอาจทำให้ผู้ใช้เข้าใจผิดว่าเป็นข้อมูลช่วงเวลาเดียวกัน

### การใช้งานของ Data Analyst

Analyst สามารถตอบคำถาม เช่น:

- หน่วยงานใดมีกำลังพลมากที่สุดตามประเภทบุคลากร
- กระทรวงใดมีอัตราเบิกจ่ายต่ำ
- หน่วยงานใดใช้จ่ายต่ำกว่าเป้าหมายรายเดือน
- ชื่อหน่วยงานใดเป็น candidate ที่เชื่อมกันได้ระหว่าง OCSC และ CGD

ตัวอย่าง SQL อยู่ใน `sql/004_sample_queries.sql` และรันรวมได้ด้วย `python -m isap_pipeline demo`

### ข้อจำกัดที่ตั้งใจเปิดเผย

- `dim_agency` ใน demo ใช้ normalized exact Thai name ยังไม่ใช่ master data ที่ผ่าน human review
- exact normalized name จับคู่ได้ 159 ชื่อ จากชื่อ OCSC 257 ชื่อ และ CGD 569 ชื่อ ขอบเขตของสองแหล่งไม่เท่ากัน จึงไม่ควรตีความตัวเลขนี้เป็น accuracy
- time dimension ของ OCSC ยังไม่มี snapshot date ระดับวัน เพราะต้นทางระบุเป็นปี/edition
- `.duckdb` ไม่ commit เพราะเป็น generated artifact; reviewer ควร rebuild เพื่อพิสูจน์ reproducibility

หลักฐานหลัก: `docs/warehouse_design.md`, `docs/data_dictionary.md`, `sql/001_create_raw.sql`, `sql/002_create_staging.sql`, `sql/003_create_marts.sql`

## ข้อ 2: EDA & Data Profiling (20 คะแนน)

### วิธีสำรวจ

EDA แบ่งเป็น 2 ระดับ:

1. Structural profiling ใช้ `openpyxl` ตรวจ workbook จริง เช่น sheet count, dimensions, merged cells, formulas, blank rows และตำแหน่ง header
2. Content validation ตรวจผลหลัง extraction เช่น row count, duplicate grain, numeric range, percentage range, entity names และความสัมพันธ์ข้ามแหล่ง

การแยกสองระดับสำคัญเพราะปัญหาเชิง layout จะหายไปหลัง normalize หากดูเฉพาะ DataFrame ที่ clean แล้วจะอธิบายไม่ได้ว่าทำไม parser ต้องมี logic เฉพาะ

### Dataset 1: OCSC Government Workforce

ผลสำรวจหลัก:

- มี 68 sheets และเป็น digital report ที่มีทั้งปก สารบัญ ตาราง summary ตาราง detail และหน้าเชิงกราฟ
- ชื่อ sheet และตำแหน่ง header ไม่ได้เป็น schema เดียวกันทั้ง workbook
- มี merged cells และ multi-row headers หลายระดับ ทำให้ `read_excel(header=0)` ใช้ไม่ได้กับทุก sheet
- มีสูตร Excel, total/subtotal และข้อความประกอบปะปนในพื้นที่ตาราง
- หลายตารางเป็น wide format โดยประเภทบุคลากรหรือ demographic อยู่ตามคอลัมน์
- ปีเป็น พ.ศ. 2567 ต้องเก็บทั้ง `fiscal_year_be=2567` และ `fiscal_year=2024`
- ค่าอย่าง `#REF!`, `-`, ช่องว่าง และ non-breaking space ต้องจัดการอย่างชัดเจน ไม่แปลงเป็นศูนย์อัตโนมัติ
- แถว summary ชื่อ `ร้อยละ` ใช้หน่วย percent และต้องไม่ถูกตีความเป็น headcount แม้อยู่ในคอลัมน์เดียวกับจำนวนคน
- pipeline เลือก normalize sheet ที่มี grain ชัดและยังเก็บ cell-level raw ของทุก sheet เพื่อไม่ทำข้อมูลต้นทางหาย
- ผล extraction ปัจจุบันได้ 5,784 staging rows หลังตัดแถว summary `ร้อยละ` ที่ไม่ควรถูกตีความเป็น headcount

ผลกระทบหาก ingest แบบตรงไปตรงมา:

- header จะกลายเป็น `Unnamed` หรือชื่อคอลัมน์ผิด
- hierarchy กระทรวง/หน่วยงานอาจหายเพราะ merged cell มีค่าเฉพาะแถวแรก
- total อาจถูกรวมซ้ำกับ detail
- สูตรหรือ placeholder อาจกลายเป็น string ใน numeric column

### Dataset 2: CGD Budget Execution

ผลสำรวจหลัก:

- มี 15 sheets ครอบคลุม summary, กระทรวง, หน่วยงาน, อบจ., เทศบาล, จังหวัด, รัฐวิสาหกิจและกองทุน
- ตารางส่วนใหญ่มี header 2 ชั้นและใช้ merged cells แบ่งกลุ่มรายจ่ายประจำ รายจ่ายลงทุน และรวม
- มีทั้งมุม `เบิกจ่าย` และ `ใช้จ่าย` ซึ่งเป็นคนละนิยาม ต้องเก็บ `report_type` แยก
- หน่วยเงินเป็นล้านบาทจากข้อความกำกับรายงาน ไม่ได้อยู่ในทุกชื่อคอลัมน์
- percentage อยู่ในสเกล 0-100 ไม่ใช่ 0-1
- entity code มีเฉพาะบาง sheet จึงใช้เป็น universal key ไม่ได้
- total/subtotal อยู่ร่วมกับ detail และต้อง tag `entity_type`
- วันที่ภาษาไทยถูกแปลงเป็น `2026-07-03` และยังเก็บปี พ.ศ. 2569
- ผล extraction ปัจจุบันได้ 2,937 staging rows รวม total rows ที่ต้นทางวางคำว่า `รวม` ไว้ในคอลัมน์ลำดับ

ผลกระทบหาก ingest แบบตรงไปตรงมา:

- คอลัมน์ของรายจ่ายประจำ/ลงทุนจะถูกอ่านไม่ครบจาก merged header
- metric เบิกจ่ายและใช้จ่ายอาจถูกผสมกัน
- ตัวเลขล้านบาทอาจถูกตีความเป็นบาท ทำให้ผิด 1,000,000 เท่า
- query ที่รวม total กับ detail จะ double count

### ปัญหาข้าม Dataset

| ปัญหา | ผลกระทบ | วิธีที่ใช้ในงานนี้ |
|---|---|---|
| ชื่อหน่วยงานไม่ตรงกันทั้งหมด | join หลุดหรือจับคู่ผิด | normalize whitespace สำหรับ demo และเปิดเผย match limitation |
| ไม่มีรหัสกลางร่วมกัน | สร้าง conformed dimension อัตโนมัติได้ไม่สมบูรณ์ | เก็บ `dim_agency` เป็นจุดเริ่มต้นและเสนอ human-reviewed mapping ใน production |
| ปีข้อมูลต่างกัน | อาจสรุปความสัมพันธ์เชิงเวลาเกินหลักฐาน | แยก fiscal year และไม่อ้างว่าเป็น same-period comparison |
| หน่วยวัดต่างกัน | headcount กับล้านบาทรวมกันไม่ได้ | แยก fact table และกำหนด semantic ratio ก่อนใช้ |
| total ปะปน detail | double count | tag entity/expense/report type และกำหนด filter ใน analytical query |

หลักฐานหลัก: `notebooks/01_eda_data_profiling.ipynb`, `docs/data_profiling_report.md`, `data/processed/profile_summary.json` หลังรัน profiling

## ข้อ 3: Automated Data Pipeline (60 คะแนน)

### 3a Extraction, Cleaning, Loading และ Code Quality (40 คะแนน)

Pipeline ทำงานตามลำดับ:

```text
source discovery/local files
  -> workbook inspection
  -> raw cell extraction
  -> source-specific parsing
  -> normalization and type conversion
  -> data quality checks
  -> idempotent DuckDB load
  -> dimensions and analytical marts
```

Extraction:

- `extract_ocsc.py` และ `extract_cgd.py` แยกกัน เพราะ layout และ business grain ต่างกัน
- เก็บ raw cells ของทุก sheet พร้อม file hash, sheet, row และ column
- อ่านสูตรในโหมด `data_only=True` และเก็บค่าที่แสดงใน workbook
- CGD parser ตรวจ header group และ unpivot รายจ่ายประจำ/ลงทุน/รวม
- OCSC parser รักษา ministry context และแปลง metric wide columns เป็น long rows

Cleaning/Data Preparation:

- normalize newline, repeated whitespace และ non-breaking space
- ตัด running number หน้าชื่อหน่วยงานโดยไม่แก้ข้อความต้นฉบับใน raw layer
- แปลง comma, percent sign และ Excel error token เป็น numeric/null ตามกฎ
- แปลงปี พ.ศ. เป็น ค.ศ. ด้วยฟังก์ชันเดียวที่มี unit test
- แยก `report_type`, `expense_category`, `metric_name`, `metric_group` และ `source_unit`
- รักษา null แยกจาก zero เพราะไม่มีหลักฐานว่าช่องว่างหมายถึงศูนย์ทุกกรณี

Loading:

- สร้าง schema จาก SQL versioned files
- โหลด raw/staging/mart ใน DuckDB
- ใช้ SHA-256 ของ source file เป็น idempotency key
- ก่อน insert release เดิม จะ delete rows ของ hash เดิมแล้ว insert ใหม่ จึงรันซ้ำแล้วไม่เพิ่ม duplicate
- บันทึก ingestion run และ DQ result เพื่อ audit

Code quality:

- module แยกตามหน้าที่และมี CLI entry point
- `ruff` ตรวจ style/static issues
- `pytest` ปัจจุบันมี 16 tests ครอบคลุม date conversion, header normalization, source transforms, total-row handling, reconciliation, idempotency, manifest comparison, ZIP extraction และ sync orchestration
- GitHub Actions รัน lint และ tests ทุก push/PR

### 3b ตรวจข้อมูลใหม่ทุกเดือน (10 คะแนน)

- `.github/workflows/monthly-check.yml` รันวันที่ 1 ของทุกเดือน เวลา 02:00 UTC และสั่งรันเองได้
- `check-new` อ่าน URL จาก `config/sources.yml`
- เทียบ filename, publish date และ file URL กับ `config/source_manifest.json`
- คืนสถานะ `no_new_data`, `new_data_found` หรือ `source_unavailable`
- เก็บ `source_check_latest.json` เป็น GitHub Actions artifact เพื่อให้มีหลักฐานจากแต่ละรอบ
- การแยก `source_unavailable` สำคัญ เพราะ network failure ไม่ควรถูกตีความเป็น no new data

### 3c Ingest Dataset ใหม่ที่โครงสร้างเดิม (10 คะแนน)

มี 2 วิธี:

1. รัน `python -m isap_pipeline run --ocsc <new_ocsc.xlsx> --cgd <new_cgd.xlsx> --warehouse <path>` เมื่อต้องการควบคุมไฟล์เอง
2. รัน `python -m isap_pipeline sync-latest` เพื่อ discover, download, แตก ZIP หากจำเป็น, ingest ทั้งสองแหล่ง และอัปเดต manifest หลัง load สำเร็จ

สมมติฐานคือ workbook release ใหม่มีโครงสร้าง semantic เดิมตามโจทย์ ถ้า official page ใช้ client-side rendering หรือป้องกัน bot จนหา direct file URL ไม่ได้ `sync-latest` จะหยุดด้วย exit code 1 และเก็บผล `source_unavailable` โดยไม่อัปเดต manifest และไม่ทำ partial load

คำสั่งหลักและ expected output อยู่ใน `docs/demo_script.md`

## ข้อ 4: ข้อเสนอแนะจาก Junior ต่อ Senior Data Engineer (20 คะแนน)

ข้อเสนอแนะเรียงตามความเสี่ยงและผลกระทบ ไม่ได้เสนอเครื่องมือเพิ่มเพียงเพราะเป็น best practice

### Priority 1: ทำ Data Contract และ Schema Versioning

กำหนด expected sheets, header pattern, required fields, data types, units และ release cadence ของแต่ละแหล่ง ถ้าโครงสร้างเปลี่ยนให้จำแนก compatible กับ breaking change ก่อน ingest วิธีนี้ลดความเสี่ยงที่ pipeline รันผ่านแต่ได้ข้อมูลผิดความหมาย

### Priority 2: สร้าง Government Agency Master

กำหนด agency code กลาง, ministry hierarchy, aliases, effective date และสถานะการจับคู่ การใช้ fuzzy matching ควรสร้าง candidate เพื่อให้คน review ไม่ควร auto-join ลง production เพราะชื่อคล้ายกันอาจเป็นคนละหน่วยงาน

### Priority 3: เพิ่ม Reconciliation กับยอดในรายงาน

ตรวจผลรวม detail เทียบ total/subtotal ที่ต้นทางเผยแพร่ด้วย tolerance ที่กำหนด แยก warning จาก blocking error เพราะข้อมูลจริงอาจมี rounding หรือ business exception การเช็กนี้ให้ความมั่นใจมากกว่าตรวจเพียง non-negative และ duplicate

### Priority 4: ทำ Immutable Raw Zone และ Lineage

เก็บไฟล์ต้นฉบับใน object storage แบบ write-once พร้อม SHA-256, source URL, checked time และ retention policy เพื่อ replay/rebuild ได้ และทำให้ตอบได้ว่าตัวเลขใน mart มาจาก release ใด

### Priority 5: เพิ่ม Observability และ Alerting

ติดตาม run duration, downloaded bytes, row count trend, schema fingerprint, DQ failures และ source availability พร้อม alert เมื่อผิดจาก baseline การมี schedule อย่างเดียวไม่เพียงพอถ้าไม่มีคนรู้ว่า job ล้ม

### Priority 6: กำหนด Backfill และ Release Policy

แยก latest snapshot, historical releases และ correction/revision ให้ชัด กำหนดว่าจะ replace release เดิมหรือเก็บ revision เพื่อให้ analyst เปรียบเทียบย้อนหลังได้โดยไม่สับสน

### Priority 7: ทำ Semantic Layer ร่วมกับ Data Analyst

ตกลงนิยามคำว่า เบิกจ่าย, ใช้จ่าย, จัดสรร, PO, กำลังพล และ ratio ข้ามแหล่งก่อนสร้าง dashboard หลีกเลี่ยง metric ที่ดูคำนวณได้แต่เปรียบเทียบคนละช่วงเวลา หรือคนละ entity scope

### Priority 8: วาง Production Migration ตามการใช้งานจริง

DuckDB เหมาะกับ take-home และ single-user local analysis หากมี concurrent users, SLA, access control หรือข้อมูลหลายปีจำนวนมาก ค่อยย้าย storage/compute ไป platform ที่รองรับ โดยคง raw/staging/mart contract และ automated tests เดิม

รายการเต็มอยู่ใน `docs/junior_recommendations.md`

## หลักฐานการรันล่าสุด

| รายการ | ผล |
|---|---:|
| Raw source files | 2 |
| Workbook sheets | 83 |
| Raw non-empty cells | 125,890 |
| CGD staging/mart rows | 2,937 |
| OCSC staging/mart rows | 5,784 |
| Core DQ issues | 0 |
| Automated tests | 13 passed |

ตัวเลขนี้เป็น snapshot จากไฟล์ submission baseline และสามารถสร้างใหม่ได้ด้วยคำสั่งใน `README.md`
