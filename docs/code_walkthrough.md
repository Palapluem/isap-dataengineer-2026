# โค้ดทำงานอย่างไร

เอกสารนี้ช่วยให้ตาม code ได้โดยไม่ต้องจำทีละบรรทัด ให้เริ่มจากหน้าที่ของแต่ละไฟล์, รับอะไรเข้ามา, ส่งอะไรออกไป และกรณีไหนที่ระบบหยุดพร้อมบอกเหตุผล

## เลือกอ่านตามคำถาม

| อยากรู้เรื่องไหน | เริ่มอ่านไฟล์ |
|---|---|
| คำสั่ง `profile`, `run`, `demo` เรียกอะไรบ้าง | `cli.py` |
| ทำไม OCSC กับ CGD อ่านคนละแบบ | `extract_ocsc.py`, `extract_cgd.py` |
| ข้อความ, ตัวเลข และวันที่ไทยถูกจัดการอย่างไร | `clean.py` |
| ทำไมรันไฟล์เดิมซ้ำแล้วไม่เกิดข้อมูลซ้ำ | `metadata.py`, `load.py` |
| ระบบตรวจข้อมูลใหม่รายเดือนอย่างไร | `discovery.py`, `downloader.py` |

คำศัพท์ที่พบในเอกสารอยู่ที่ [docs/terms_explained.md](terms_explained.md)

## ภาพรวมการเรียกใช้งาน

```text
python -m isap_pipeline <command>
  -> __main__.py
  -> cli.main()
  -> profile / run / check-new / sync-latest / demo
```

`cli.py` เป็นตัวจัดลำดับงาน จึงไม่ควรมีรายละเอียดการอ่าน Excel มากเกินไป กฎเฉพาะของแต่ละแหล่งอยู่ใน extractor และกฎที่ใช้ร่วมกันอยู่ใน `clean.py`

## Module Map

### `config.py`

- อ่าน `config/sources.yml` และ `config/pipeline.yml`
- คืน dataclass เพื่อให้ path และ source configuration มีโครงสร้างชัด
- เหตุผล: ไม่ hard-code URL/output path กระจายหลาย module

### `metadata.py`

- สร้าง `ingestion_run_id`, UTC timestamp และ SHA-256
- สร้าง source metadata record ที่ raw/mart ใช้ร่วมกัน
- SHA-256 ใช้ทั้ง lineage และ idempotency ไม่ได้ใช้ filename อย่างเดียว เพราะไฟล์ชื่อเดิมอาจมีเนื้อหาเปลี่ยน

### `excel_inspector.py`

- เปิด workbook จริงและ profile ทุก sheet
- นับ rows, columns, merged cells, formulas, blanks และเดา header row/sheet type
- เป็น structural EDA และใช้สร้าง `raw.workbook_sheets`
- heuristic ไม่ใช่ business truth จึงใช้คำว่า guessed header และเก็บ raw evidence ไว้

### `clean.py`

- `normalize_text`: ลบ newline/repeated whitespace
- `normalize_header`: แปลงหัวคอลัมน์ไทยที่รู้จักเป็นชื่อมาตรฐาน
- `canonical_entity_name`: ตัด running number และ normalize whitespace
- `to_number` / `to_int`: แปลง comma, percent และ Excel error token อย่างปลอดภัย
- `parse_thai_date`: แปลงวันที่ภาษาไทยและ พ.ศ. เป็น date ค.ศ.
- หลักสำคัญ: parsing rule ที่ใช้ร่วมกันต้องมีจุดเดียวและมี unit test

### `extract_ocsc.py`

- อ่าน OCSC workbook ด้วย `data_only=True`
- เก็บ raw cells ของทุก sheet
- normalize ตารางที่เลือกเพราะมี grain อธิบายได้
- รักษา ministry context ระหว่างไล่แถว
- แปลง wide metrics เป็น long rows ด้วย `metric_name` และ `metric_group`
- ไม่พยายาม scrape ตัวเลขจากรูป/กราฟ เพราะตรวจสอบย้อนกลับยากและเกินหลักฐานจาก cell

### `extract_cgd.py`

- อ่านทั้ง 15 sheets และเก็บ raw cells
- หา snapshot date จากข้อความวันที่ภาษาไทย
- แยก summary กับ detail parser
- หา entity/code columns และ group spans จาก header
- unpivot รายจ่ายประจำ รายจ่ายลงทุน และรวม
- แยก `report_type` จากชื่อ sheet และรองรับชื่อ sheet ใช้จ่ายที่ถูก Excel ตัดเหลือท้าย `(ใช้`
- เก็บแถว `รวม` ที่อยู่ในคอลัมน์ลำดับเพื่อใช้ reconciliation

### `dq.py`

- ตรวจ rows present, non-negative numeric fields, percentage range, duplicate grain และยอดเบิกจ่ายรวมเทียบ detail ในกลุ่มที่มี published total
- คืนผลเป็น DataFrame เพื่อเขียน JSON และโหลดเข้า warehouse ได้
- check ที่ไม่ผ่านมี severity, issue count และ sample
- reconciliation ปัจจุบันใช้กับ `disbursement_million_baht` ที่พิสูจน์ grain ได้แล้ว ส่วน measure อื่นยังต้องนิยาม semantic scope และ tolerance ต่อ sheet ก่อน

### `load.py`

- สร้าง DuckDB และ execute DDL ตามลำดับ raw → staging → mart
- `_delete_existing` ลบ partition ของ source hash เดิมก่อน insert
- `_insert` align DataFrame columns กับ table schema
- รองรับ fallback parameterized insert เมื่อ DuckDB 0.10.2 ไม่รู้จัก pandas string dtype บางเวอร์ชัน
- rebuild dimensions จาก staging หลัง load facts
- ปิด connection ใน `finally` เพื่อไม่ทิ้ง file lock

### `discovery.py`

- request source pages ด้วย browser-like headers
- หา `.xlsx`, `.xls` หรือ `.zip` links จาก static HTML
- parse date จากชื่อ/ข้อความลิงก์
- เทียบ field ที่ baseline รู้จริงกับ `config/source_manifest.json`
- แยก `source_unavailable` จาก `no_new_data`
- ข้อจำกัด: เว็บที่ render download link ด้วย JavaScript หรือมี bot protection อาจต้องใช้ API/browser integration ใน production

### `downloader.py`

- stream download เพื่อลด memory usage
- คำนวณ SHA-256 หลัง download
- รองรับ ZIP และ extract Excel แรกด้วย safe basename เพื่อไม่ใช้ path ภายใน archive โดยตรง

### `cli.py`

| Command | หน้าที่ |
|---|---|
| `profile` | inspect workbook และสร้าง JSON/Markdown report |
| `run` | inspect, extract, clean, DQ และ load จาก path ที่ระบุ |
| `check-new` | ตรวจ source pages และเทียบ manifest |
| `sync-latest` | discover, download, extract ZIP, run pipeline และ update manifest เมื่อสำเร็จ |
| `demo` | รัน SQL samples แบบ read-only |

`sync-latest` ต้องพบไฟล์ทั้งสองแหล่งก่อนจึงเริ่ม load เพื่อหลีกเลี่ยง partial snapshot ที่มีแหล่งเดียว

## SQL Walkthrough

### `001_create_raw.sql`

เก็บ source identity, workbook profile และ cell-level evidence จุดสำคัญคือ raw layer ไม่พยายามเป็น analyst table

### `002_create_staging.sql`

กำหนด normalized source-aligned schema สำหรับ CGD และ OCSC เป็น contract ระหว่าง parser กับ warehouse

### `003_create_marts.sql`

กำหนด facts, dimensions และ operational tables สำหรับ analyst/demo ในงาน production facts ควรอ้าง surrogate dimension keys มากขึ้น แต่ text fields ยังช่วยให้ take-home inspect ได้ง่าย

### `004_sample_queries.sql`

แสดง business questions 4 แบบและบังคับ filter สำคัญ เช่น metric, report type และ expense category เพื่อไม่รวมคนละ grain ปะปน

## Test Walkthrough

| Test file | สิ่งที่พิสูจน์ |
|---|---|
| `test_date_conversion.py` | พ.ศ. และวันที่ภาษาไทยแปลงถูก |
| `test_header_normalization.py` | text/header/number cleaning คงที่ |
| `test_ocsc_transform.py` | parser สร้าง OCSC long rows จาก workbook structure |
| `test_cgd_transform.py` | parser แยก expense groups และ measures |
| `test_data_quality.py` | reconciliation แจ้งเตือนเมื่อ published total ไม่ตรงผลรวม detail |
| `test_idempotency.py` | โหลด source hash เดิมซ้ำแล้ว row count ไม่เพิ่ม |
| `test_discovery.py` | manifest baseline แยก same/new release ถูก |
| `test_downloader.py` | ZIP extraction ใช้ safe output path |
| `test_sync_latest.py` | sync ต้อง download สองแหล่งก่อนเรียก load |

## คำถามที่มีโอกาสถูกถาม

### ทำไมไม่ใช้ pandas `read_excel` ครั้งเดียว

เพราะ workbook มี multi-row headers, merged cells, cover/index, formulas และหลาย grain การใช้ header row เดียวจะทำให้ schema ผิดตั้งแต่ต้น จึง inspect ด้วย openpyxl และใช้ parser แยกตาม source

### ทำไมเก็บ raw cell ทั้งหมด

เพื่อ audit และ debug เมื่อ layout เปลี่ยน ถ้าเก็บเฉพาะ cleaned DataFrame จะพิสูจน์ไม่ได้ว่าค่าเดิมอยู่ cell ไหนหรือ parser ทำค่าหายตรงไหน

### รันซ้ำแล้วไม่ duplicate ได้อย่างไร

คำนวณ SHA-256 ต่อไฟล์ ใช้ hash เป็น release partition และ delete rows ของ hash เดิมก่อน insert จากนั้น test idempotency ตรวจ row count หลังโหลดซ้ำ

### ถ้าไฟล์ใหม่เพิ่ม column จะเกิดอะไร

ภายใต้สมมติฐานโจทย์ว่าโครงสร้างเหมือนเดิม parser ทำงานได้ ถ้าเป็น compatible extra column ที่ไม่ได้ใช้จะถูกเก็บใน raw แต่ไม่กระทบ staging หาก header/grain เปลี่ยนควรให้ schema fingerprint/DQ หยุด pipeline และสร้าง parser version ใหม่

### ทำไม DQ ผ่านไม่ได้แปลว่าข้อมูลถูกทั้งหมด

DQ ปัจจุบันพิสูจน์ core invariants และ reconciliation ของยอดเบิกจ่ายในกลุ่มที่มี published total แต่ยังไม่ครอบคลุมทุก measure และทุก sheet จึงไม่ควรสรุปว่า DQ ผ่านแล้วเท่ากับ business truth ถูกทุกมิติ

### ใช้ AI ส่วนไหน

ตอบอย่างตรงไปตรงมา: AI ช่วยวางโครง ตรวจ code และเขียนเอกสาร แต่การตัดสินใจเรื่อง grain, parser, idempotency, DQ และ limitations ต้องอธิบายจาก source กับ code ที่รันได้ การพิสูจน์ความเข้าใจคือสามารถไล่ data flow และแก้ failure scenario ได้ ไม่ใช่บอกว่า AI สร้างให้

## วิธีซ้อมก่อนสัมภาษณ์

1. ปิดเอกสารแล้วอธิบาย data flow ภายใน 90 วินาที
2. เปิด extractor อย่างละหนึ่งไฟล์และชี้ให้ได้ว่า entity, header และ measure ถูกหาอย่างไร
3. อธิบาย idempotency จาก test ไม่ใช่จากคำว่า deduplicate
4. รัน demo และอธิบาย grain/filter ของทุก query
5. เตรียมตอบ limitation 3 ข้อ: source website access, agency mapping และ period mismatch
