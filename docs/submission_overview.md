# ภาพรวมสิ่งที่ส่ง (Submission Overview)

เริ่มอ่านคำตอบตามข้อสอบได้ที่ `docs/assignment_answers.md` และใช้เอกสารนี้เป็นแผนที่ภาพรวมของ artifacts

หน้านี้เป็นหน้าเปิดอ่านเร็วสำหรับ reviewer/interviewer เพื่อเห็นภาพว่า repo นี้ตอบโจทย์หลักครบอย่างไร และไฟล์ไหนควรเป็น source artifact หรือ generated artifact

ถ้ายังไม่คุ้นคำทาง Data Engineering ให้เปิด [docs/terms_explained.md](terms_explained.md) ก่อน แล้วค่อยตามแผนภาพด้านล่าง

## 4 สิ่งที่งานนี้ตอบ

```mermaid
flowchart TD
    A[งาน ISAP Data Engineer] --> B[1. ออกแบบที่เก็บข้อมูล]
    A --> C[2. สำรวจข้อมูล 2 ชุด]
    A --> D[3. ทำ pipeline อัตโนมัติ]
    A --> E[4. ข้อเสนอแนะสำหรับงานจริง]

    B --> B1[raw / staging / mart]
    B --> B2[กำหนดว่าหนึ่งแถวแทนอะไร]
    B --> B3[DuckDB สำหรับ demo บนเครื่องเดียว]

    C --> C1[ดูโครงสร้าง OCSC]
    C --> C2[ดูโครงสร้าง CGD]
    C --> C3[พบปัญหาและกำหนดวิธีจัดการ]

    D --> D1[profile workbook]
    D --> D2[extract clean load]
    D --> D3[ตรวจข้อมูลใหม่รายเดือน]
    D --> D4[demo query และ tests]

    E --> E1[ตกลงรูปแบบไฟล์กับต้นทาง]
    E --> E2[ทำรายชื่อหน่วยงานกลาง]
    E --> E3[เพิ่มการตรวจและแจ้งเตือน]
```

## Pipeline แบบย่อ

```mermaid
flowchart LR
    O[OCSC Excel] --> P[สำรวจโครงสร้างไฟล์]
    C[CGD Excel] --> P
    O --> X[อ่านและจัดข้อมูล]
    C --> X
    X --> R[(raw: หลักฐานไฟล์ sheet cell)]
    X --> S[(staging: ตารางที่จัดรูปแบบแล้ว)]
    S --> Q[ตรวจคุณภาพข้อมูล]
    Q --> M[(mart: ตารางสำหรับวิเคราะห์)]
    M --> D[SQL ตัวอย่างสำหรับ analyst]
    W[หน้าเว็บต้นทาง] --> N[ตรวจข้อมูลใหม่รายเดือน]
```

## Evidence Map

| Deliverable | Main Evidence | Notes |
|---|---|---|
| Data Warehouse design | `docs/warehouse_design.md`, `sql/001_create_raw.sql`, `sql/002_create_staging.sql`, `sql/003_create_marts.sql` | มี architecture, ERD, table inventory, fact grain และ design tradeoffs |
| EDA and Data Profiling | `notebooks/01_eda_data_profiling.ipynb`, `docs/data_profiling_report.md` | แยก OCSC และ CGD ชัดเจน พร้อม workbook/sheet-level profiling |
| Automated Data Pipeline | `src/isap_pipeline/`, `sql/`, `.github/workflows/ci.yml`, `.github/workflows/monthly-check.yml` | มี extraction, cleaning, loading, DQ, idempotency, source monitoring และ tests |
| Junior Recommendations | `docs/junior_recommendations.md` | ข้อเสนอ production readiness จากมุม Junior Data Engineer |
| Demo Readiness | `README.md`, `docs/demo_script.md`, `sql/004_sample_queries.sql` | มีคำสั่ง setup/profile/run/demo/test ที่รันตามได้ |

## Artifact Policy

| Type | Commit to GitHub? | Reason |
|---|---|---|
| Source code, SQL, tests, docs, notebooks | Yes | เป็น deliverable และต้อง review ได้ |
| Small source Excel datasets used for demo | Yes | ทำให้ reviewer clone แล้วรัน pipeline ได้ทันที |
| `data/warehouse/*.duckdb` | No | เป็น generated warehouse output; ควร rebuild จาก code + source data เพื่อพิสูจน์ reproducibility |
| `data/processed/*.json` | No | เป็น generated profiling/DQ/source-check output; command สามารถสร้างใหม่ได้ |
| `references/` | No | เป็น internal/private reference material |
| agent prompt / working brief | No | เป็น local working artifact ไม่ใช่ deliverable |
| original assignment PDF | Yes | เจ้าของงานยืนยันว่าเผยแพร่ได้และช่วยให้ผู้ตรวจเทียบคำตอบกับโจทย์ต้นฉบับ |

## Why Ignore `.duckdb`

ไฟล์ `.duckdb` ในงานนี้เป็นผลลัพธ์จาก pipeline ไม่ใช่ source of truth จึงควร ignore ไว้ เพื่อให้ reviewer เห็นว่า warehouse สร้างซ้ำได้ด้วยคำสั่ง:

```powershell
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
```

ถ้าต้องการส่ง demo แบบ offline มาก ๆ สามารถแนบ `.duckdb` แยกเป็น release artifact หรือไฟล์ zip ส่วนตัวได้ แต่ไม่ควร commit ลง repo หลัก เพราะจะทำให้ repo หนักขึ้นและเสี่ยงมี stale output ที่ไม่ตรงกับ code ล่าสุด
