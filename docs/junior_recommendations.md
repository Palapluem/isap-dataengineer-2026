# Junior Recommendations

ข้อเสนอแนะต่อ Senior Data Engineer เพื่อให้โครงการนี้ production-ready:

1. ทำ data contract กับ OCSC และ CGD ระบุ expected workbook structure, sheet naming, header rows และ release cadence
2. สร้าง master agency mapping กลางที่มี agency code, ministry code, alias name และ effective date
3. เพิ่ม schema versioning สำหรับแต่ละ source file เพื่อแยก compatible change กับ breaking change
4. ทำ automated source monitoring รายเดือนผ่าน GitHub Actions หรือ scheduler พร้อม alert เมื่อ `source_unavailable`
5. ขยาย DQ reconciliation จากยอดเบิกจ่ายไปยัง measure อื่นหลังยืนยัน grain และ tolerance ของแต่ละ sheet
6. แยก secrets/config ออกจาก code หาก production ต้องใช้ proxy, credential หรือ storage account
7. เพิ่ม observability เช่น run duration, row count trend, DQ failed count และ file hash history
8. เก็บ raw files ใน object storage แบบ immutable เช่น S3/Blob Storage พร้อม retention policy
9. ทำ data dictionary และ business glossary ร่วมกับ analyst เพื่อกำหนดนิยามคำว่าเบิกจ่าย, ใช้จ่าย, จัดสรร และ PO
10. ทำ backfill strategy สำหรับไฟล์ย้อนหลัง เพื่อให้ mart มีหลาย fiscal years ไม่ใช่แค่ latest snapshot
11. เพิ่ม integration tests ด้วย sample workbook ที่เลียนแบบ merged cells และ multi-row headers จริง
12. เตรียม dashboard/semantic layer เช่น OBT view สำหรับคำถามยอดนิยม: top manpower, low disbursement, workforce vs budget
