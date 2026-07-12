# พจนานุกรมข้อมูล (Data Dictionary)

เอกสารนี้อธิบาย grain, หน่วยวัด และความหมายของตารางที่ Data Analyst ใช้ โดย source field names ใน code และ database ใช้ English `snake_case` ส่วนคำอธิบายใช้ภาษาไทย

## อ่านก่อนใช้ข้อมูล

1. `grain` หมายถึงหนึ่งแถวแทนอะไร ต้องอ่านก่อนรวมยอดทุกครั้ง
2. ตัวเลขเงินของ CGD ใช้หน่วยล้านบาท และร้อยละใช้สเกล 0-100
3. ห้ามรวม `total` กับยอดย่อย หรือรวม `disbursement` กับ `expenditure` โดยยังไม่กำหนดคำถามที่ต้องการตอบ

คำอธิบายศัพท์เพิ่มเติมอยู่ที่ [docs/terms_explained.md](terms_explained.md)

## ชื่อคอลัมน์และหน่วย

| Convention | ความหมาย |
|---|---|
| `*_million_baht` | จำนวนเงินหน่วยล้านบาทตามข้อความกำกับในรายงาน CGD |
| `*_pct` หรือ `percentage` | ร้อยละในสเกล 0-100 |
| `fiscal_year_be` | ปีงบประมาณ พ.ศ. |
| `fiscal_year` | ปีเดียวกันใน ค.ศ. |
| `as_of_date` | วันที่ snapshot ในรูป `YYYY-MM-DD` |
| `source_file_hash` / `sha256` | SHA-256 ของ source file ใช้ lineage และ idempotency |
| `ingestion_run_id` | รหัสการรันหนึ่งครั้ง ใช้เชื่อม operational evidence |

## ตารางที่ Analyst ใช้

### `mart.fact_budget_execution`

Grain: หนึ่งแถวต่อ source release, sheet, entity, `report_type` และ `expense_category`

| Column | Type | Nullable | ความหมาย |
|---|---|---:|---|
| `ingestion_run_id` | VARCHAR | no | รหัส pipeline run |
| `dataset_name` | VARCHAR | no | ค่าคงที่ `cgd_budget_execution` |
| `source_file_hash` | VARCHAR | no | SHA-256 ของไฟล์ CGD |
| `sheet_name` | VARCHAR | no | ชื่อ sheet ต้นทาง |
| `row_number` | INTEGER | no | แถวใน Excel สำหรับ trace กลับ |
| `fiscal_year` | INTEGER | yes | ปีงบประมาณ ค.ศ. |
| `fiscal_year_be` | INTEGER | yes | ปีงบประมาณ พ.ศ. |
| `as_of_date` | VARCHAR | yes | วันที่ข้อมูล ณ วันนั้น |
| `report_type` | VARCHAR | no | `disbursement` หรือ `expenditure` |
| `entity_type` | VARCHAR | no | เช่น ministry, agency, province, municipality, fund, total |
| `entity_name` | VARCHAR | no | ชื่อหน่วยงาน/พื้นที่ภาษาไทย |
| `entity_code` | VARCHAR | yes | รหัสจากต้นทาง มีเฉพาะบาง sheet |
| `expense_category` | VARCHAR | no | `current`, `investment` หรือ `total` |
| `budget_after_transfer_million_baht` | DOUBLE | yes | วงเงินงบประมาณหลังโอนเปลี่ยนแปลง |
| `allocated_million_baht` | DOUBLE | yes | วงเงินจัดสรร |
| `po_reserved_debt_million_baht` | DOUBLE | yes | PO และสำรองเงินแบบมีหนี้ |
| `disbursement_million_baht` | DOUBLE | yes | จำนวนเบิกจ่าย |
| `disbursement_pct` | DOUBLE | yes | ร้อยละการเบิกจ่าย สเกล 0-100 |
| `expenditure_million_baht` | DOUBLE | yes | จำนวนการใช้จ่ายตามนิยามต้นทาง |
| `expenditure_pct` | DOUBLE | yes | ร้อยละการใช้จ่าย สเกล 0-100 |
| `monthly_target_gap_pct` | DOUBLE | yes | สูง/ต่ำกว่าเป้าหมายรายเดือน หน่วย percentage point ตามต้นทาง |
| `remaining_million_baht` | DOUBLE | yes | คงเหลือที่รายงานระบุ |
| `remaining_pct` | DOUBLE | yes | ร้อยละคงเหลือ |

ข้อควรระวัง:

- อย่ารวม `expense_category='total'` พร้อม `current` และ `investment` ใน query เดียวกัน
- อย่ารวม `report_type='disbursement'` กับ `expenditure` โดยไม่กำหนด metric ที่ต้องการ
- `entity_code` ไม่ใช่ conformed key เพราะมีค่าไม่ครบทุก sheet

### `mart.fact_government_manpower`

Grain: หนึ่งแถวต่อ source release, sheet, entity, metric และ source row

| Column | Type | Nullable | ความหมาย |
|---|---|---:|---|
| `ingestion_run_id` | VARCHAR | no | รหัส pipeline run |
| `dataset_name` | VARCHAR | no | ค่าคงที่ `ocsc_government_manpower` |
| `source_file_hash` | VARCHAR | no | SHA-256 ของไฟล์ OCSC |
| `sheet_name` | VARCHAR | no | ชื่อ sheet ต้นทาง |
| `row_number` | INTEGER | no | แถวใน Excel สำหรับ trace กลับ |
| `fiscal_year` | INTEGER | yes | ปีข้อมูล ค.ศ. |
| `fiscal_year_be` | INTEGER | yes | ปีข้อมูล พ.ศ. |
| `entity_type` | VARCHAR | no | ministry, agency หรือ total |
| `ministry_name` | VARCHAR | yes | กระทรวง parent ที่ parser รักษาบริบทไว้ |
| `agency_name` | VARCHAR | no | ชื่อ entity ภาษาไทย |
| `metric_name` | VARCHAR | no | ชื่อ metric มาตรฐาน เช่น `civil_servant`, `female_pct`, `age_20_29` |
| `metric_group` | VARCHAR | no | กลุ่ม metric เช่น employment_type, age, gender, education_level |
| `headcount` | DOUBLE | yes | จำนวนคน ใช้เมื่อ metric เป็น count |
| `percentage` | DOUBLE | yes | ร้อยละสเกล 0-100 ใช้เมื่อ metric เป็น ratio |
| `source_value` | VARCHAR | yes | ค่าเดิมจาก source เพื่อช่วยตรวจ parser |
| `source_unit` | VARCHAR | no | `person`, `pct` หรือ `year` |

ข้อควรระวัง:

- filter `metric_name` ก่อน aggregate เพราะแต่ละ entity มีหลาย metric และบาง metric ซ้อนความหมายกัน
- อย่ารวม `headcount` ข้าม employment type กับ total โดยไม่ตรวจนิยาม
- `average_age` เก็บ unit เป็น `year` และไม่ได้อยู่ใน `headcount`

### `mart.dim_source_file`

Grain: หนึ่งแถวต่อ source file release

| Column | ความหมาย |
|---|---|
| `source_file_key` | surrogate key ที่สร้างใหม่เมื่อ rebuild dimension |
| `dataset_name`, `source_name` | รหัสและชื่อแหล่งข้อมูล |
| `filename`, `sha256` | file identity และ content identity |
| `source_page_url`, `file_url` | lineage ไปหน้าประกาศและไฟล์ ถ้าค้นพบได้ |
| `fiscal_year`, `fiscal_year_be`, `as_of_date` | ช่วงเวลาของ release |
| `loaded_at` | เวลาโหลดเข้า warehouse |

### `mart.dim_agency`

Grain: หนึ่งแถวต่อ `entity_name × entity_type` ที่พบใน staging

| Column | ความหมาย |
|---|---|
| `agency_key` | surrogate key สำหรับ demo |
| `entity_name` | ชื่อ entity ตาม source |
| `normalized_entity_name` | ชื่อ lowercase ที่ตัด whitespace ใช้ exact-match candidate |
| `entity_type` | ระดับ/ประเภท entity |
| `ministry_name` | parent ministry เมื่อหาได้จาก OCSC |
| `source_systems` | source ที่พบชื่อดังกล่าว เช่น `ocsc,cgd` |

ข้อจำกัด: dimension นี้ยังไม่ใช่ master agency ที่ผ่านการรับรอง ไม่ควรใช้ fuzzy match อัตโนมัติเป็น production key

### `mart.dim_date`

Grain: หนึ่งแถวต่อ `as_of_date` ที่พบใน CGD

| Column | ความหมาย |
|---|---|
| `date_key` | surrogate key |
| `date_value` | วันที่ snapshot |
| `year`, `month`, `day` | ส่วนประกอบวันที่สำหรับ filter/group |

### Operational Facts

| Table | Grain | ใช้งาน |
|---|---|---|
| `mart.fact_ingestion_run` | หนึ่งแถวต่อ run | row counts, DQ failure count, status และเวลาโหลด |
| `mart.fact_data_quality_issue` | หนึ่งแถวต่อ check/result ใน run | ชื่อ check, severity, issue count, sample และ status |

## Staging Tables

`staging.cgd_budget_execution` และ `staging.ocsc_workforce` ใช้ schema เดียวกับ fact ที่เกี่ยวข้องใน mart จุดประสงค์คือเป็น clean source-aligned boundary ก่อนสร้าง business-facing model ในระบบที่ใหญ่ขึ้น staging อาจเพิ่ม schema validation และ mart อาจใช้ surrogate foreign keys แทน natural text fields

## Raw Tables

### `raw.source_files`

เก็บ manifest ของไฟล์ที่ ingest รวม source name, filename, path, SHA-256, URL, fiscal year, as-of date และ loaded time

### `raw.workbook_sheets`

เก็บ profile ต่อ sheet ได้แก่ sheet index/name, row/column count, non-empty/formula/merged/blank counts, guessed header row และ sheet type

### `raw.cells`

Grain: หนึ่งแถวต่อ non-empty Excel cell

คอลัมน์สำคัญคือ dataset, file hash, sheet index/name, row/column และ `cell_value` ตารางนี้มีขนาดใหญ่กว่าตาราง analytical แต่ช่วย audit, debug layout change และ rebuild parser ได้

## Recommended Analyst Filters

ตัวอย่าง CGD ที่ไม่ double count:

```sql
SELECT entity_name, disbursement_pct
FROM mart.fact_budget_execution
WHERE report_type = 'disbursement'
  AND expense_category = 'total'
  AND entity_type = 'ministry';
```

ตัวอย่าง OCSC ที่ไม่รวมหลาย metric ปะปน:

```sql
SELECT agency_name, sum(headcount) AS civil_servant_headcount
FROM mart.fact_government_manpower
WHERE metric_name = 'civil_servant'
  AND entity_type <> 'total'
GROUP BY agency_name;
```
