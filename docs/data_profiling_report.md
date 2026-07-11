# Data Profiling Report

รายงานนี้สร้างจากการ inspect workbook จริงด้วย `openpyxl` ผ่านคำสั่ง `python -m isap_pipeline profile`.

## สรุปภาพรวม

- OCSC: `datasets\ocsc\thai-gov-manpower-2567.4.xlsx` มี 68 sheets
- CGD: `datasets\cgd\2026.07.03.xlsx` มี 15 sheets

## OCSC government workforce statistics

| sheet | rows | cols | merged | formulas | blank rows | guessed header | type |
|---|---:|---:|---:|---:|---:|---:|---|
| ปกหน้า | 1 | 1 | 0 | 0 | 1 | None | cover_or_blank |
| แนวโน้ม 10 ปี | 45 | 17 | 2 | 0 | 39 | 1 | agency |
| สารบัญ | 98 | 16 | 5 | 0 | 6 | 11 | index |
| 11 | 32 | 20 | 1 | 0 | 30 | 1 | cover_or_blank |
| 12 | 32 | 16 | 1 | 0 | 4 | 4 | summary |
| 13 | 34 | 16 | 6 | 1 | 14 | 2 | agency |
| 14 | 39 | 16 | 2 | 0 | 19 | 1 | summary |
| 15 | 25 | 15 | 1 | 0 | 24 | 1 | cover_or_blank |
| 16 | 36 | 16 | 1 | 0 | 35 | 1 | cover_or_blank |
| 17-29 | 648 | 15 | 9 | 23 | 353 | 6 | agency |
| 30 | 40 | 16 | 7 | 0 | 18 | 2 | geography |
| 31-32 | 138 | 16 | 7 | 75 | 76 | 4 | agency |
| 33 | 51 | 16 | 4 | 0 | 31 | 2 | geography |
| 34-35 | 129 | 16 | 6 | 0 | 69 | 2 | agency |
| 36 | 57 | 18 | 6 | 0 | 45 | 2 | budget_execution |
| 37 | 76 | 19 | 27 | 5 | 50 | 2 | budget_execution |
| 38-39 | 123 | 32 | 8 | 0 | 62 | 2 | agency |
| 40 | 44 | 16 | 4 | 0 | 23 | 2 | geography |
| 41-42 | 135 | 22 | 6 | 0 | 75 | 2 | agency |
| 43-44 | 83 | 40 | 16 | 7 | 38 | 2 | agency |
| 45-49 | 197 | 46 | 20 | 0 | 95 | 9 | geography |
| 50-53 | 135 | 25 | 5 | 0 | 2 | 4 | geography |
| 54 | 40 | 16 | 4 | 0 | 0 | 11 | geography |
| 55-64 | 203 | 18 | 8 | 0 | 4 | 2 | agency |
| 65  | 25 | 24 | 17 | 0 | 8 | 3 | agency |
| 66-69 | 88 | 29 | 12 | 0 | 8 | 2 | agency |
| 70 | 33 | 30 | 79 | 0 | 4 | 8 | wide_report |
| 71 | 32 | 25 | 5 | 0 | 19 | 1 | agency |
| 72 | 25 | 21 | 15 | 0 | 13 | 6 | geography |
| 73 | 37 | 16 | 1 | 0 | 36 | 1 | cover_or_blank |
| 74 | 25 | 16 | 1 | 0 | 24 | 1 | cover_or_blank |
| 75 | 34 | 16 | 4 | 42 | 10 | 12 | agency |
| 76-77 | 64 | 16 | 4 | 0 | 39 | 2 | agency |
| 78-79 | 67 | 16 | 3 | 27 | 42 | 1 | agency |
| 80 | 39 | 11 | 10 | 0 | 31 | 1 | budget_execution |
| 81 | 33 | 12 | 6 | 1 | 12 | 2 | budget_execution |
| 82 | 25 | 16 | 1 | 0 | 24 | 1 | cover_or_blank |
| 83 | 48 | 40 | 9 | 0 | 22 | 4 | agency |
| 84 | 26 | 19 | 8 | 0 | 2 | 4 | agency |
| 85 | 25 | 16 | 4 | 0 | 4 | 4 | budget_execution |
| 86 | 38 | 16 | 2 | 0 | 36 | 1 | cover_or_blank |
| 87 | 29 | 26 | 7 | 0 | 4 | 3 | agency |
| 88-97 | 199 | 39 | 11 | 33 | 0 | 2 | agency |
| 98 | 26 | 16 | 4 | 0 | 14 | 1 | budget_execution |
| 99-113 | 312 | 30 | 10 | 16 | 0 | 10 | budget_execution |
| 114 | 29 | 14 | 1 | 0 | 1 | 12 | report |
| 115-116 | 68 | 12 | 3 | 0 | 42 | 2 | agency |
| 117-122 | 203 | 17 | 5 | 0 | 5 | 5 | agency |
| 123 | 39 | 19 | 3 | 0 | 13 | 1 | agency |
| 124-127 | 103 | 44 | 3 | 0 | 1 | 8 | agency |
| 128-133 | 104 | 38 | 10 | 0 | 0 | 4 | budget_execution |
| 134 | 25 | 16 | 21 | 0 | 2 | 10 | budget_execution |
| 135 | 26 | 16 | 6 | 0 | 15 | 12 | agency |
| 136 | 28 | 16 | 6 | 0 | 2 | 3 | agency |
| 137 | 26 | 16 | 7 | 0 | 12 | 7 | budget_execution |
| 138-143 | 199 | 16 | 4 | 0 | 1 | 3 | agency |
| 144 | 32 | 16 | 6 | 0 | 11 | 2 | budget_execution |
| 145 | 36 | 14 | 2 | 0 | 23 | 2 | budget_execution |
| 146 | 26 | 16 | 1 | 0 | 21 | 1 | budget_execution |
| 147 | 27 | 16 | 5 | 0 | 2 | 4 | agency |
| 148 | 32 | 16 | 5 | 10 | 16 | 2 | budget_execution |
| 149 | 34 | 12 | 2 | 0 | 11 | 1 | agency |
| 150-151 | 58 | 16 | 4 | 0 | 43 | 1 | agency |
| 152-153 | 58 | 22 | 5 | 20 | 29 | 1 | agency |
| 154 | 37 | 15 | 1 | 0 | 13 | 1 | agency |
| 155 | 37 | 23 | 5 | 1 | 25 | 1 | budget_execution |
| 156-157 | 46 | 7 | 1 | 0 | 34 | 1 | report |
| ปกหลัง | 1 | 1 | 0 | 0 | 1 | None | cover_or_blank |

ปัญหาสำคัญที่พบ: workbook เป็นรายงานสำหรับอ่าน ไม่ใช่ flat data; มี cover/index, merged cells, multi-row headers, formula cells, wide tables และ subtotal/total ปะปนกับ detail rows จึงต้องเก็บ raw cell ก่อน แล้วค่อย normalize เฉพาะ sheet ที่มี grain ชัดเจน

## CGD budget execution statistics

| sheet | rows | cols | merged | formulas | blank rows | guessed header | type |
|---|---:|---:|---:|---:|---:|---:|---|
| 1.สรุปภาพรวม | 21 | 16 | 10 | 19 | 0 | 9 | summary |
| 2.กระทรวง | 37 | 22 | 41 | 0 | 1 | 4 | agency |
| 3.หน่วยงาน | 323 | 15 | 14 | 0 | 1 | 4 | agency |
| 4.หน่วยงาน(ใช้จ่าย) | 327 | 18 | 330 | 0 | 1 | 4 | agency |
| 5.อบจ. | 88 | 15 | 14 | 0 | 2 | 5 | geography |
| 6.อบจ.(ใช้จ่าย) | 92 | 18 | 94 | 0 | 2 | 5 | geography |
| 7.เทศบาล | 2484 | 15 | 14 | 0 | 2 | 5 | agency |
| 8.เทศบาล(ใช้จ่าย) | 2488 | 19 | 2490 | 0 | 2 | 5 | agency |
| 9.ลงทุน 1,000 ล้าน | 72 | 12 | 51 | 0 | 1 | 4 | agency |
| 10.รัฐวิสาหกิจ | 33 | 12 | 14 | 0 | 1 | 4 | agency |
| 11.จังหวัดได้รับจัดสรร | 105 | 15 | 14 | 0 | 1 | 4 | geography |
| 12.จังหวัดได้รับจัดสรร(ใช้จ่าย) | 109 | 18 | 112 | 0 | 1 | 4 | geography |
| 13.ส่วนกลางจัดสรรให้จังหวัด | 88 | 15 | 14 | 0 | 2 | 6 | geography |
| 14.ส่วนกลางจัดสรรให้จังหวัด(ใช้ | 91 | 18 | 94 | 0 | 1 | 5 | geography |
| 15.กองทุนฯ | 46 | 12 | 14 | 0 | 1 | 4 | budget_execution |

ปัญหาสำคัญที่พบ: ตารางมีหัว 2 ชั้น, มีทั้งมุมมองเบิกจ่ายและใช้จ่าย, ค่าเงินเป็นล้านบาท, percent อยู่ในรูป 0-100, มีรหัสหน่วยงานเฉพาะบาง sheet และมีช่องว่างจาก merged cells ต้อง flatten header และ unpivot current/investment/total เป็น long rows

## Cleaning Strategy

- เก็บ raw cell พร้อม sheet, row, column, file hash และ ingestion_run_id เพื่อ audit ย้อนกลับได้
- normalize header โดยลบ newline/ช่องว่างซ้ำและ map synonym สำคัญ เช่น เบิกจ่าย/การใช้จ่าย/วงเงินงบประมาณหลังโอนเปลี่ยนแปลง
- unpivot wide tables ให้หนึ่ง row ต่อ entity/report_type/expense_category
- แยก total/subtotal ด้วย `entity_type` แทนการทิ้งทันที เพื่อให้ตรวจ reconciliation ได้
- แปลงวันที่ พ.ศ. เป็น ค.ศ. และเก็บ fiscal_year_be ควบคู่ fiscal_year
- เก็บ `source_file_hash` เพื่อให้โหลดซ้ำแบบ idempotent และตรวจไฟล์ใหม่รายเดือนได้
