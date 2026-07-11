# Datasets

โฟลเดอร์นี้เก็บ source Excel files ที่ใช้สำหรับ local demo

```text
datasets/
├── ocsc/
│   └── thai-gov-manpower-2567.4.xlsx
└── cgd/
    └── 2026.07.03.xlsx
```

ไฟล์เหล่านี้เป็น input ของคำสั่ง:

```powershell
python -m isap_pipeline profile --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx"
python -m isap_pipeline run --ocsc "datasets/ocsc/thai-gov-manpower-2567.4.xlsx" --cgd "datasets/cgd/2026.07.03.xlsx" --warehouse "data/warehouse/isap.duckdb"
```
