# Notebooks

Notebook ในโฟลเดอร์นี้เป็น companion artifact สำหรับ EDA/profiling เท่านั้น ไม่ใช่ pipeline หลัก

ถ้าต้อง rebuild notebook จาก source UTF-8:

```powershell
python scripts/build_eda_notebook.py
```

รันซ้ำได้ด้วย:

```powershell
python -m nbconvert --execute --to notebook --inplace "notebooks/01_eda_data_profiling.ipynb"
```

ไฟล์หลัก:

- `01_eda_data_profiling.ipynb`: สำรวจ workbook inventory, sheet-level issues, preview source cells และสรุป cleaning strategy
