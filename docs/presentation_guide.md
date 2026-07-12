# แนวทางนำเสนอ ISAP Data Engineer ภายใน 15 นาที

เอกสารนี้ออกแบบจากเงื่อนไขว่า **15 นาทีรวมการพูด, live automation demo และ Q&A** ดังนั้นเป้าหมายไม่ใช่เล่าทุกไฟล์ใน repository แต่ทำให้ผู้สัมภาษณ์เห็นเหตุผลทางวิศวกรรม หลักฐานที่รันได้ และข้อจำกัดที่เรารู้ตัว

แกนของเรื่องมีประโยคเดียว:

> ผมเปลี่ยน Excel report สองแหล่งที่โครงสร้างไม่สม่ำเสมอ ให้เป็น DuckDB warehouse ที่ trace กลับไปยังไฟล์ต้นทางได้ รันซ้ำไม่สร้างข้อมูลซ้ำ และมีทางตรวจ release ใหม่รายเดือน

## แบ่งเวลา 15 นาที

| เวลา | สิ่งที่ทำ | เป้าหมาย |
|---|---|---|
| 0:00-0:30 | เปิดงานและสรุปคำตอบ | บอกปัญหาและผลลัพธ์ในประโยคเดียว |
| 0:30-1:30 | แหล่งข้อมูลและความยาก | ชี้ว่า Excel เป็น report ไม่ใช่ flat table |
| 1:30-3:00 | EDA ของ OCSC และ CGD | แสดงปัญหาที่ทำให้ต้องมี parser/cleaning เฉพาะ |
| 3:00-4:30 | Warehouse design | อธิบาย raw, staging, mart และเหตุผลที่ไม่รวม fact ทั้งสองแหล่ง |
| 4:30-6:15 | Pipeline และ idempotency | เชื่อมปัญหา EDA เข้ากับ extraction, cleaning, DQ และ loading |
| 6:15-7:30 | Automation และข้อจำกัด | monthly check, CI, source-unavailable และขอบเขตที่ทำได้จริง |
| 7:30-10:30 | Live demo | test, run ซ้ำ, query mart |
| 10:30-11:30 | ข้อเสนอแนะต่อ production | เลือก 3-4 ข้อที่มีผลสูงสุด |
| 11:30-15:00 | Q&A และเวลาสำรอง | ตอบคำถามหรือใช้แก้ปัญหา demo |

เวลา 15 นาทีนี้ไม่เหมาะกับ deck 35 หน้า ให้เตรียม deck หลักเพียง 7-8 หน้า และเก็บรายละเอียดอื่นเป็น appendix หรือเปิดจาก repository เมื่อถูกถาม

## Deck หลักที่ควรใช้

### Slide 1: งานนี้แก้ปัญหาอะไร

**หัวข้อ:** `From Excel Reports to a Reproducible Data Warehouse`

**บนสไลด์:**

`OCSC + CGD Excel -> Python pipeline -> DuckDB -> Analyst SQL`

**พูด 30 วินาที:**

> งานนี้รับ Excel report จากสำนักงาน ก.พ. และกรมบัญชีกลาง ซึ่งไม่ได้ออกแบบมาให้ query โดยตรง ผมจึงสร้าง pipeline ที่เก็บที่มาของข้อมูล แปลงเฉพาะตารางที่มีความหมายชัด และโหลดเข้า DuckDB แบบรันซ้ำได้ครับ

### Slide 2: ข้อมูลสองชุดและข้อจำกัดตั้งต้น

**บนสไลด์:**

- OCSC: 68 sheets, ปีงบประมาณ 2567
- CGD: 15 sheets, snapshot ณ 3 กรกฎาคม 2569
- รวม 125,890 non-empty cells
- ปัญหาร่วม: merged header, total/detail, formula และชื่อหน่วยงานไม่ใช่ key กลาง

**พูด 1 นาที:**

> ความยากของงานนี้อยู่ที่โครงสร้างรายงาน ไม่ใช่ขนาดข้อมูล ถ้าอ่าน Excel ด้วย header แถวแรกทันที โครงสร้างจะผิดและเสี่ยงรวม total ซ้ำกับ detail จึงต้อง profile workbook ก่อนกำหนดกฎ parser ครับ

### Slide 3: EDA ทำให้เห็นว่าต้องแก้อะไร

**บนสไลด์:** แบ่งสองคอลัมน์ `OCSC` และ `CGD` พร้อมปัญหาอย่างละ 3 ข้อและกฎที่ใช้แก้

| OCSC | CGD |
|---|---|
| หลาย layout และหัวตารางหลายชั้น | header 2 ชั้น แบ่ง current/investment/total |
| แถว `ร้อยละ` ไม่ใช่ headcount | `เบิกจ่าย` กับ `ใช้จ่าย` เป็นคนละความหมาย |
| total/subtotal และค่า `#REF!` ปะปน | total/detail ปะปน และตัวเลขมีหน่วยล้านบาท |

**พูด 1 นาที 30 วินาที:**

> OCSC กับ CGD ไม่ใช้ parser เดียวกัน เพราะความหมายของแถวไม่เหมือนกัน OCSC ต้องกันแถวร้อยละไม่ให้กลายเป็นจำนวนคน ส่วน CGD ต้องแยก report type และ expense category เพื่อไม่ให้ข้อมูลคนละนิยามถูกนำมารวมกันครับ

### Slide 4: Warehouse ที่ส่งต่อให้ Analyst ใช้ได้

**บนสไลด์:** diagram `Raw -> Staging -> Mart` และ fact สองตาราง

- Raw: source metadata, sheet profile, raw cells
- Staging: clean rows ที่ยังใกล้ต้นทาง
- Mart: `fact_government_manpower` และ `fact_budget_execution`

**พูด 1 นาที 30 วินาที:**

> Raw เก็บหลักฐานเพื่อ audit, staging แก้โครงสร้างรายงาน, mart ทำให้ analyst query ได้ง่าย ผมแยก fact กำลังพลกับ fact งบประมาณ เพราะ grain, หน่วยวัด และปีข้อมูลต่างกัน การรวมเป็น fact เดียวจะทำให้คำตอบดูเหมือนถูกแต่ความหมายผิดครับ

### Slide 5: Pipeline แก้ปัญหาอย่างไร

**บนสไลด์:**

`inspect -> raw cells -> source-specific parser -> clean -> DQ -> DuckDB -> demo SQL`

ใส่กล่องเล็ก 3 กล่อง:

- `SHA-256`: ระบุ source release และกันข้อมูลซ้ำ
- `DQ`: numeric range, duplicate grain, reconciliation
- `tests + CI`: ตรวจ logic ทุก push/PR

**พูด 1 นาที 45 วินาที:**

> ผมเก็บ raw cell ของทุก sheet เพื่อย้อนกลับไปดูต้นทางได้ แล้วใช้ parser แยกตาม source หลัง clean จะตรวจ DQ ก่อนโหลด SHA-256 ของไฟล์เป็น idempotency key ดังนั้นเมื่อได้รับ release เดิมอีกครั้ง pipeline จะลบ partition เดิมและใส่ใหม่ ไม่เกิด duplicate และยังรู้ที่มาของข้อมูลครับ

### Slide 6: Automation ที่ทำได้จริง และสิ่งที่ไม่เดาเอง

**บนสไลด์:**

`monthly-check -> no_new_data | new_data_found | source_unavailable`

- GitHub Actions ตรวจ source ทุกวันที่ 1
- เปรียบเทียบ filename, publish date และ file URL กับ manifest
- `sync-latest` ทำงานเมื่อค้นหา direct file URL ได้และทั้งสอง source พร้อม ingest

**พูด 1 นาที 15 วินาที:**

> จุดสำคัญคือ network error ไม่ได้แปลว่าไม่มีข้อมูลใหม่ จึงแยก `source_unavailable` ออกจาก `no_new_data` หากหา direct file URL ไม่ได้ ระบบหยุดและไม่อัปเดต manifest หรือทำ partial load ครับ

### Slide 7: Live Automation Demo

**บนสไลด์:** `Test -> Run -> Run Again -> Query`

**พูดก่อนสลับหน้าจอ 15 วินาที:**

> เดโมนี้จะพิสูจน์สามเรื่องครับ: กฎสำคัญมี test, pipeline รันจริงและรันซ้ำไม่เพิ่มข้อมูล, แล้ว mart ตอบคำถามของ analyst ได้จริง

ทำตาม [docs/demo_script.md](demo_script.md) หัวข้อ `Interview Automation Demo (3 นาที)` โดยอย่า live download จากเว็บภายนอก

### Slide 8: ข้อเสนอแนะและปิด

เลือกเพียง 4 ข้อ:

1. ทำ data contract และ schema versioning กับเจ้าของข้อมูล
2. สร้าง master agency mapping ที่มีคน review
3. ขยาย reconciliation หลังยืนยัน semantic grain ของแต่ละ measure
4. เพิ่ม monitoring, alert และ immutable raw storage เมื่อขึ้น production

**พูด 1 นาที:**

> สิ่งที่งานนี้ตั้งใจพิสูจน์ไม่ใช่แค่ว่าอ่าน Excel ได้ แต่คือทุกแถวมาจากไหน รันซ้ำอย่างไร และข้อจำกัดตรงไหนที่ต้องแก้ก่อนนำไปใช้จริงครับ

## วิธีตัด Deck ปัจจุบัน

PDF ปัจจุบันมี 35 หน้า จึงเหมาะเป็น **appendix** มากกว่า deck ที่พูดต่อเนื่อง ให้แก้จาก Canva source แล้ว export PDF ใหม่เป็น deck หลัก 7-8 หน้า ตามตารางด้านบน

| หน้าใน PDF ปัจจุบัน | การตัดสินใจ | เหตุผล |
|---|---|---|
| 1 | เก็บและย่อชื่อให้ชัด | เป็น opening ที่ดี แต่ตัดวันที่ได้ถ้าไม่จำเป็น |
| 2, 6 | ตัด | เป็น section divider ที่ไม่เพิ่มเนื้อหา |
| 3-4 | รวมเป็น Slide 2 | แสดงแหล่งข้อมูล แต่ไม่ต้องโชว์ URL ยาว |
| 5 | ตัด | ข้อความโจทย์แน่นเกินไป ใช้พูดสรุปแทน |
| 7-8 | เลือกใช้ diagram เดียวใน Slide 4 หรือ 5 | architecture กับ lineage ซ้ำกันบางส่วน |
| 9-11 | เก็บเป็น appendix | star schema และตารางมีรายละเอียดมากเกินเวลาหลัก |
| 12 | ย่อเป็นส่วนหนึ่งของ Slide 4 | เหตุผลเลือก DuckDB สำคัญ แต่ไม่ต้องเป็นหน้าที่ยาว |
| 13, 16, 18 | รวมเป็น Slide 3 | มีหลักฐาน EDA และปัญหาสอง source ครบ |
| 14, 15, 17, 19 | ย้ายเป็น appendix | ตาราง raw ยาว อ่านไม่ทันและไม่ใช่ conclusion |
| 20-21 | เลือกกราฟเดียวเป็น supporting evidence | อย่าใส่กราฟสองหน้า ถ้าไม่ได้อธิบาย insight เพิ่ม |
| 22-25 | ย่อเป็น notes/appendix | เนื้อหาถูกต้อง แต่จำนวน bullet มากเกินเวลาหลัก |
| 26, 28-31 | รวมเป็น Slide 5 และ 6 | แก่นคือ pipeline, tests/CI และ monthly check |
| 27 | แก้หรือเอาออก | มีข้อความแดงแสดงผิดตำแหน่งด้านบน จึงไม่ควรใช้ในวันสัมภาษณ์ |
| 32-33 | ลบหนึ่งหน้า | เนื้อหาซ้ำกันทั้งหมด |
| 34 | ย่อเหลือ 4 recommendations และลบอักขระ `T` มุมซ้ายบน | 12 ข้อยาวเกินไปและมีองค์ประกอบหลงเหลือ |
| 35 | เก็บเป็น closing หรือข้ามเพื่อเข้า Q&A | ไม่ต้องใช้เวลานาน |

## Live Demo ที่ควรซ้อม

เปิด terminal ที่ repository root แล้วรันตามลำดับนี้:

```powershell
$warehouse = "data/warehouse/interview_demo.duckdb"
Remove-Item -LiteralPath $warehouse -ErrorAction SilentlyContinue
python -m pytest
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse $warehouse
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse $warehouse
python -m isap_pipeline demo --warehouse $warehouse
```

สิ่งที่ต้องพูดระหว่างรัน:

- ตอน test: `16 tests` ครอบคลุม parser, cleaning, reconciliation, idempotency และ source monitoring
- ตอน run ครั้งแรก: ชี้ row counts `2,937` CGD และ `5,784` OCSC
- ตอน run ครั้งที่สอง: จำนวนแถวเท่าเดิม เพราะใช้ file hash คุม release
- ตอน query: ก่อนอ่านผล ระบุ filter ที่คุม grain เช่น `metric_name`, `report_type`, `expense_category` และการตัด total/detail

## Pre-flight ก่อนสัมภาษณ์

ทำก่อนเวลานัด ไม่ใช่ระหว่างนำเสนอ:

1. รัน `python -m ruff check .` และ `python -m pytest` ให้ผ่าน
2. ปิด DuckDB GUI connection ที่เปิดไฟล์เดียวกับ demo หรือใช้ `interview_demo.duckdb` ตามคำสั่งข้างบน
3. เปิด README, executed notebook และ repository URL ไว้ใน tab แยก
4. เตรียม terminal 2 หน้าต่าง: หน้าหนึ่งไว้รันคำสั่ง อีกหน้าหนึ่งไว้ดู output โดยไม่ต้อง scroll ย้อน
5. อย่าใช้ `sync-latest` เป็น live demo เพราะเว็บภายนอกเปลี่ยนได้ ให้เก็บเป็น capability ที่อธิบายพร้อมหลักฐาน workflow แทน
6. Export PDF ใหม่หลังแก้ และเปิดดูทุกหน้าอีกครั้ง โดยเฉพาะข้อความที่ยาว ตาราง และ slide 27/32/33/34 ที่พบปัญหาใน PDF ปัจจุบัน

## Q&A ที่ควรซ้อม

### ทำไมเลือก DuckDB ไม่ใช้ PostgreSQL หรือ cloud warehouse

> ข้อมูลต่อ release มีขนาดเล็กและ demo ต้องรันบนเครื่องเดียว DuckDB เป็น analytical database ที่ใช้ SQL ได้โดยไม่ต้องดูแล server แต่ model ที่ออกแบบแยก layer และ fact/dimension ยังย้ายไป warehouse ที่ใหญ่กว่าได้เมื่อมีผู้ใช้หรือข้อมูลมากขึ้นครับ

### ทำไมไม่รวม OCSC กับ CGD เป็นตารางเดียว

> ทั้งสอง source มี grain, หน่วยวัด และเวลาคนละแบบ OCSC เป็นกำลังพลรายปี ส่วน CGD เป็นงบประมาณ ณ วันหนึ่ง การรวมโดยไม่มี semantic ratio ที่ยืนยันแล้วเสี่ยงสร้างตัวเลขที่ตีความผิด จึงแยก fact และให้ `dim_agency` เป็นจุดเชื่อมสำหรับ analysis ที่ระวังข้อจำกัดครับ

### idempotency ทำงานอย่างไร

> ใช้ SHA-256 ของ source file ระบุ release ก่อน insert จะลบข้อมูลของ hash เดิม แล้ว insert ผลที่คำนวณใหม่ ทำให้รันไฟล์เดิมซ้ำได้โดยไม่เพิ่ม duplicate และตรวจ lineage ได้ครับ

### ถ้าเว็บต้นทางเปิดไม่ได้ ระบบทำอย่างไร

> ระบบคืน `source_unavailable` และเก็บหลักฐานการตรวจไว้ แยกจาก `no_new_data` เพราะ network failure ไม่ควรถูกตีความว่าไม่มี release ใหม่ และจะไม่อัปเดต manifest หรือทำ partial load ครับ

### ถ้า layout ของ Excel เปลี่ยน

> โจทย์สมมติ semantic structure เดิมไว้ แต่ใน production จะเพิ่ม data contract, schema versioning และ integration test จาก workbook ตัวอย่าง ถ้าเป็น breaking change pipeline ควรหยุดพร้อมแจ้งเตือนแทนการเดาข้อมูลครับ

### DQ ผ่านแล้วเชื่อถือได้ทั้งหมดหรือไม่

> ไม่ทั้งหมด DQ ยืนยันกฎที่เขียนไว้ เช่น range, duplicate grain และ reconciliation ที่เปรียบเทียบได้ ส่วน business definition ของ measure ต้องยืนยันกับเจ้าของข้อมูล และควรขยาย checks ต่อเมื่อ grain กับ tolerance ชัดเจนครับ

### การ join ชื่อหน่วยงานแม่นแค่ไหน

> ตอนนี้เป็น exact normalized Thai name เพื่อ demo ไม่ใช่ master data และไม่ควรเรียกตัวเลข match ว่า accuracy เพราะสอง source มี scope ต่างกัน Production ต้องมี agency master mapping ที่คน review ครับ
