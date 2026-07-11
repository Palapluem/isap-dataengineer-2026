# แนวทางทำสไลด์และนำเสนอ ISAP Data Engineer

แนวทางนี้ออกแบบสำหรับ presentation 10-12 นาที ตามด้วย live demo 3-5 นาที หากเวลาจริงสั้นกว่า ให้ลดรายละเอียด slide 4-5 และ 11 แต่คง architecture, pipeline, evidence และ limitation ไว้

## หลักการของ Deck

- เล่าเป็นเรื่องเดียว: source มีปัญหาอะไร → ออกแบบอย่างไร → pipeline แก้อย่างไร → พิสูจน์อย่างไร → ถ้า production จะทำอะไรต่อ
- หนึ่ง slide มีข้อสรุปหลักหนึ่งประโยค ไม่ใส่ข้อความจากรายงานทั้งย่อหน้า
- ใช้ภาพจากงานจริง เช่น workbook profile, architecture, schema และ query output
- ตัวเลขทุกตัวบน slide ต้องรันซ้ำได้จาก notebook, DuckDB หรือ test output
- แยก “สิ่งที่ทำแล้ว” ออกจาก “สิ่งที่เสนอสำหรับ production” ให้เห็นชัด
- อย่าเปรียบเทียบกับงานของผู้สมัครคนอื่น และไม่ต้องเล่ากระบวนการใช้ AI จนบดบัง engineering decisions

## Visual Style

- Canvas: 16:9, พื้นหลังขาวหรือเทาอ่อน ตัวอักษรเข้ม
- ใช้สีหลักไม่เกิน 3 สี: น้ำเงินสำหรับ pipeline, เขียวสำหรับ passed evidence, แดง/ส้มสำหรับ risk และ limitation
- Heading 28-32 pt, body 18-22 pt, code 16-18 pt
- diagram ใช้คำสั้นและลูกศรซ้ายไปขวา
- ตารางบน slide ไม่เกิน 5-6 rows; รายละเอียดเต็มอยู่ใน GitHub docs
- ใส่ชื่อ repository แบบสั้นที่ footer เฉพาะ slide แรก/สุดท้ายก็พอ

## Slide-by-Slide Story

### Slide 1: ชื่อโครงการและคำตอบหนึ่งประโยค

เวลา: 30 วินาที

หัวข้อแนะนำ:

`Government Workforce & Budget Data Pipeline`

ข้อความรอง:

`เปลี่ยน Excel report 83 sheets เป็น DuckDB warehouse ที่ตรวจสอบย้อนหลังและรันซ้ำได้`

ภาพ:

- flow สั้น `OCSC + CGD Excel → Python Pipeline → DuckDB → Analyst`

พูด:

> งานนี้รับข้อมูล Excel จากสำนักงาน ก.พ. และกรมบัญชีกลาง ซึ่งออกแบบมาเพื่ออ่านเป็นรายงาน ผมจึงสร้าง pipeline ที่เก็บหลักฐานต้นทาง แปลงข้อมูลให้ query ได้ และโหลดเข้า DuckDB แบบรันซ้ำไม่เกิดข้อมูลซ้ำครับ

ไม่ควรใส่:

- รายชื่อ library ยาว ๆ
- คำอธิบายตัวเองหลายบรรทัด

### Slide 2: โจทย์และขอบเขต 120 คะแนน

เวลา: 45 วินาที

เนื้อหา:

| Deliverable | สิ่งที่ส่ง |
|---|---|
| Warehouse design | raw/staging/mart + facts/dimensions |
| EDA 2 datasets | notebook + profiling report |
| Automated pipeline | CLI, monthly check, sync latest, DQ, tests |
| Junior recommendation | prioritized production roadmap |

ภาพ:

- ใช้ Mermaid `4 Core Deliverables` จาก `docs/submission_overview.md`

พูด:

> ผมจัด repository ตามข้อ 1 ถึง 4 และทำให้แต่ละคำตอบมี implementation หรือหลักฐานที่เปิดดูได้ ไม่ได้มีเฉพาะ design document ครับ

### Slide 3: Source ไม่ใช่ Flat Table

เวลา: 60 วินาที

ข้อความหลัก:

`ความยากอยู่ที่โครงสร้างรายงาน ไม่ใช่ขนาดข้อมูล`

ตัวเลข:

- OCSC: 68 sheets, FY 2567
- CGD: 15 sheets, as of 2026-07-03
- รวม 125,890 non-empty raw cells

ภาพ:

- screenshot workbook OCSC หนึ่งหน้าและ CGD หนึ่งหน้า
- crop ให้เห็น merged header, title rows และ total row

พูด:

> ถ้าใช้ read_excel header แถวแรกทันที จะได้ schema ผิด เพราะมีปก สารบัญ merged cells และหัวหลายชั้น ผมจึง profile workbook ก่อนเลือก extraction rule และยังเก็บ cell-level evidence ไว้ครับ

### Slide 4: EDA Findings - OCSC

เวลา: 60 วินาที

ข้อความหลัก:

`OCSC เป็น digital report หลาย layout จึงต้องเลือก normalize ตาม grain`

ใช้ 4 findings:

- 68 sheets มี cover/index/table/chart-style pages
- header position และ merged hierarchy ต่างกัน
- formulas, totals และ placeholders ปะปน
- fiscal year เป็น พ.ศ. และบาง metric เป็น wide format

ภาพ:

- bar chart หรือ table จาก notebook แสดง merged/formula counts ตาม sheet
- ใส่กล่อง `ผลลัพธ์: 5,801 normalized rows`

พูด:

> ผมไม่บังคับทุกหน้าให้เป็น fact เดียว เพราะแต่ละหน้ามี grain ต่างกัน แนวทางคือเก็บ raw ครบ และ normalize เฉพาะตารางที่นิยาม row ได้ชัดเจนเป็น metric-driven fact ครับ

### Slide 5: EDA Findings - CGD

เวลา: 60 วินาที

ข้อความหลัก:

`CGD layout ซ้ำมากกว่า แต่ต้องแยกความหมายของกลุ่มคอลัมน์`

ใช้ 4 findings:

- 15 sheets และ header 2 ชั้น
- current/investment/total ต้อง unpivot
- disbursement กับ expenditure เป็นคนละ report type
- หน่วยล้านบาท, percent 0-100, entity code ไม่ครบทุก sheet

ภาพ:

- diagram ก่อน/หลัง: wide Excel columns → long rows
- ใส่กล่อง `ผลลัพธ์: 2,913 normalized rows`

พูด:

> จุดที่ต้องระวังคือถ้ารวม total กับ current และ investment จะ double count และถ้าผสมเบิกจ่ายกับใช้จ่ายจะเป็นคนละนิยาม ผมจึงทำสองคอลัมน์ควบคุมคือ report_type และ expense_category ครับ

### Slide 6: Architecture และ Data Flow

เวลา: 75 วินาที

ข้อความหลัก:

`Raw รักษาหลักฐาน, Staging แก้โครงสร้าง, Mart ทำให้ Analyst ใช้งานง่าย`

ภาพ:

- ใช้ architecture Mermaid จาก `docs/warehouse_design.md`
- highlight ทีละ layer ระหว่างพูด

พูด:

> Raw เก็บ source metadata, sheet profile และ cell หลักฐาน Staging เป็น clean source-aligned tables ส่วน Mart แยก fact กำลังพลกับ fact งบประมาณ เพราะหน่วยวัดและช่วงเวลาต่างกันครับ

ตอบเผื่อถูกถาม:

- DuckDB เหมาะเพราะเป็น embedded OLAP และข้อมูลระดับ MB ไม่ต้องมี server
- `.duckdb` ไม่ commit เพราะต้อง rebuild ได้จาก source และ code

### Slide 7: Warehouse Grain และ Analyst Safety

เวลา: 75 วินาที

ข้อความหลัก:

`แยก fact เพราะการรวมคนละ grain จะสร้างคำตอบที่ดูถูกแต่ผิดความหมาย`

ภาพ:

- ใช้ star schema จาก `docs/warehouse_design.md`
- ใต้ fact ใส่ grain สั้น ๆ

เนื้อหาที่ควรพูด:

- Budget grain: release × sheet × entity × report type × expense category
- Manpower grain: release × sheet × entity × metric × source row
- OCSC FY2567 และ CGD FY2569 ไม่ใช่ same-period comparison
- normalized exact name join เป็น candidate เท่านั้น

ตัวเลขเสริม:

- exact normalized match 158 ชื่อ
- เทียบกับ OCSC distinct 258 และ CGD distinct 568

พูด caveat ทันที:

> สัดส่วนนี้ไม่ใช่ accuracy เพราะ entity scope สองแหล่งไม่เท่ากัน และ exact match ไม่ได้ยืนยันว่าเป็นหน่วยงานเดียวกันทั้งหมด Production ต้องมี agency master ที่คน review ครับ

### Slide 8: Automated Pipeline และ Idempotency

เวลา: 75 วินาที

ข้อความหลัก:

`หนึ่ง CLI ครอบคลุม profile, run, monitor, sync และ demo`

ภาพ:

```text
profile → run → DQ → load → demo
          ↑
check-new → sync-latest
```

เนื้อหา:

- extraction แยก source-specific parser
- shared cleaning rules สำหรับ text, number, Thai date
- SHA-256 partition ทำให้โหลดซ้ำไม่ duplicate
- `sync-latest` update manifest หลัง load สำเร็จเท่านั้น

พูด:

> Idempotency ในงานนี้ไม่ใช่แค่ distinct หลังโหลด แต่ใช้ content hash ระบุ release ลบ partition เดิมและ insert ใหม่ จึงตรวจ lineage ได้ด้วยครับ

### Slide 9: Data Quality, Tests และ CI

เวลา: 60 วินาที

ข้อความหลัก:

`หลักฐานความน่าเชื่อถืออยู่ใน checks ที่รันซ้ำได้`

ตัวเลข:

- 13 tests passed
- core DQ issue count = 0
- lint passed
- 2 GitHub Actions workflows: CI และ monthly source check

ภาพ:

- screenshot GitHub Actions สีเขียว หรือ terminal test summary
- แสดง check groups: presence, non-negative, 0-100 percent, duplicate grain, idempotency

พูด caveat:

> DQ ผ่านไม่ได้แปลว่าพิสูจน์ business truth ทุกตัว ปัจจุบันยังขาด reconciliation total เทียบ detail ที่ต้องกำหนด scope และ tolerance ร่วมกับเจ้าของข้อมูลครับ

### Slide 10: Monthly Check และ New Release

เวลา: 60 วินาที

ข้อความหลัก:

`Network failure ต้องไม่ถูกตีความว่าไม่มีข้อมูลใหม่`

ภาพ:

- state flow 3 สถานะ: `no_new_data`, `new_data_found`, `source_unavailable`
- ลูกศรจาก `new_data_found` ไป `sync-latest`

พูด:

> Workflow รันวันที่ 1 ของทุกเดือน เทียบกับ committed baseline manifest และอัปโหลด JSON result เป็น artifact หากพบ direct file URL คำสั่ง sync-latest จะดาวน์โหลด แตก ZIP และ ingest ได้ แต่ถ้าหน้าเว็บใช้ JavaScript หรือ block request ระบบจะหยุดและรายงาน source_unavailable โดยไม่ทำ partial load ครับ

### Slide 11: Live Demo

เวลา: 30 วินาทีก่อนสลับหน้าจอ

ข้อความบน slide:

1. Run tests
2. Rebuild warehouse
3. Show row counts and DQ
4. Run analytical queries
5. Show monthly-check status

พูด:

> ใน demo ผมจะพิสูจน์สามเรื่อง คือ pipeline รันจริง, รันซ้ำไม่เพิ่มข้อมูล และ mart ตอบคำถามวิเคราะห์ได้ครับ

อย่า live download เป็นเส้นทางหลัก เพราะเว็บภายนอกควบคุมไม่ได้ ให้ใช้ local baseline สำหรับ deterministic demo แล้วเปิด `source_check_latest.json` แสดง monitoring behavior

### Slide 12: Recommendations และ Closing

เวลา: 60 วินาที

ข้อความหลัก:

`จาก take-home ที่รันได้ ไป production ที่เชื่อถือได้`

เลือก 4 recommendation:

1. Data contract + schema versioning
2. Human-reviewed agency master
3. Total/detail reconciliation
4. Immutable raw storage + observability

ปิดด้วย:

> สิ่งที่ผมให้ความสำคัญที่สุดในงานนี้คือไม่ทำให้ Excel ดูสะอาดอย่างเดียว แต่ต้องอธิบายได้ว่าทุกแถวมาจากไหน รันซ้ำอย่างไร และมีข้อจำกัดอะไร ก่อนส่งต่อให้ Analyst ใช้ครับ

## Live Demo Script แบบกระชับ

เปิด terminal ที่ repository root และเตรียม environment ไว้ก่อนเริ่ม

### 1. Tests

```powershell
python -m pytest
```

พูด: tests ครอบคลุม cleaning, source parsers, idempotency, source discovery และ sync orchestration

### 2. Pipeline

```powershell
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
```

ชี้ row counts 2,913 และ 5,801 ไม่ต้องอ่านทุกบรรทัด

### 3. Idempotency

รันคำสั่งเดิมอีกครั้ง แล้ว query count หรืออ้าง test idempotency หากเวลาน้อย จำนวน rows ต้องเท่าเดิม

### 4. Analytical Queries

```powershell
python -m isap_pipeline demo --warehouse "data/warehouse/isap.duckdb"
```

ก่อนอ่านผลทุก query ให้พูด filter/grain ที่ใช้ โดยเฉพาะ `metric_name`, `report_type` และ `expense_category`

### 5. Monthly Monitoring

```powershell
python -m isap_pipeline check-new
```

ถ้าได้ `source_unavailable` ให้พูดว่าเป็น expected failure mode ที่แยกจาก no-new-data และ output ถูกเก็บเพื่อ audit

## แผนสำรองเมื่อ Demo มีปัญหา

- Warehouse ถูก lock: ปิด Database Client connection แล้วรันใหม่
- เว็บ official เข้าไม่ได้: ใช้ local files และเปิด JSON ผล check ล่าสุด
- notebook เปิดช้า: ใช้ executed notebook ที่บันทึก output ไว้หรือเปิด Markdown profiling report
- terminal ภาษาไทยเพี้ยน: เน้น JSON keys/row counts และเปิดเอกสารบน GitHub แทน
- เวลาเหลือน้อย: ข้าม profiling command แต่ห้ามข้าม tests, pipeline row counts และ demo query

## Q&A ที่ควรซ้อม

### ถ้ามีเวลาเพิ่มจะทำอะไรเป็นอันดับแรก

ตอบ: เพิ่ม agency master แบบ human-reviewed และ reconciliation total/detail เพราะสองเรื่องนี้ลดความเสี่ยงของตัวเลขผิดเชิงธุรกิจมากกว่าการเพิ่ม dashboard

### ทำไมไม่ใช้ Airflow หรือ dbt

ตอบ: take-home นี้เป็น two-source MB-scale local demo การเพิ่ม orchestration server จะเพิ่ม setup มากกว่าคุณค่า แต่ boundaries ถูกแยกไว้แล้ว จึงย้าย orchestration หรือ transformation framework ได้เมื่อมีหลาย pipeline, dependency และ SLA จริง

### DuckDB รองรับ production ไหม

ตอบ: รองรับงาน embedded/single-writer analytics ได้ดี แต่ถ้าต้อง concurrent access, centralized security และ high availability ควรย้าย model ไป managed warehouse โดยคง contract และ tests

### ทำไมไม่ fuzzy join ชื่อหน่วยงานเลย

ตอบ: fuzzy score เป็น candidate ไม่ใช่ identity proof การ auto-join อาจสร้างตัวเลขที่น่าเชื่อแต่ผิดหน่วยงาน จึงเสนอ mapping table พร้อม confidence และ human review

### AI ช่วยงานนี้อย่างไร

ตอบให้เป็นธรรมชาติ:

> ผมใช้ AI ช่วยเร่งการวางโครงและ review แต่ผมตรวจ workbook จริง รัน pipeline และ tests และสามารถอธิบาย decision กับ failure mode ได้ทุก module จุดที่ผมไม่มั่นใจ เช่น agency matching และ reconciliation ผมระบุเป็น limitation แทนการอ้างว่าเสร็จแล้วครับ

## Checklist ก่อนวันนำเสนอ

- GitHub Actions ล่าสุดเป็นสีเขียว
- `git status` สะอาดและ commit ล่าสุดอยู่บน remote
- ทดสอบคำสั่งใน `docs/demo_script.md` จาก environment ใหม่อย่างน้อยหนึ่งรอบ
- เปิด slide, repository, notebook และ Database Client ไว้ล่วงหน้า
- ปิด connection DuckDB ก่อน live pipeline run
- เตรียม screenshot 4 ภาพ: source workbook, architecture, star schema, CI/test result
- ซ้อม presentation จับเวลา 2 รอบและ demo 1 รอบ
- จำ limitation 3 ข้อ: website access, agency mapping, period mismatch
