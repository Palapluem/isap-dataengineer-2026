# Notebooks

Notebook ในโฟลเดอร์นี้เป็นหลักฐาน EDA และ data profiling ของทั้ง 2 datasets ไม่ใช่ pipeline หลัก โค้ดที่ใช้ ingest และสร้าง warehouse อยู่ใน `src/isap_pipeline/`

เปิดไฟล์ใน VS Code หรือ Jupyter แล้วอ่าน output ที่บันทึกไว้ได้ทันที หากต้องการตรวจว่ารันได้ตั้งแต่ต้นจนจบ ให้ execute notebook ใหม่:

```powershell
python -m nbconvert --execute --to notebook --inplace "notebooks/01_eda_data_profiling.ipynb"
```

ไฟล์หลัก:

- `01_eda_data_profiling.ipynb`: สำรวจ workbook inventory, ปัญหาแยกตาม OCSC/CGD, preview source cells, ผลหลัง normalize, กราฟประกอบ และ data-quality checks
