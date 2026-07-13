# Automated Pipeline: อธิบาย code ทีละขั้น

เอกสารนี้อธิบาย implementation ของข้อ 3 ในโจทย์: ดึงข้อมูล, จัดข้อมูล, ตรวจคุณภาพ, โหลดเข้า warehouse, ตรวจ release ใหม่รายเดือน และ ingest release ใหม่ได้ภายใต้สมมติฐานว่าโครงสร้างข้อมูลยังมีความหมายเดิม

เนื้อหานี้เน้น Python code ที่อยู่ใน `src/isap_pipeline/` ไม่ใช่ PowerShell demo script

## ภาพรวมการทำงาน

```text
config -> inspect Excel -> extract raw cells -> parse by source
       -> clean values -> data-quality checks -> idempotent DuckDB load
       -> demo SQL

official source page -> discovery -> compare manifest -> download -> run pipeline
```

## 1. CLI เป็นจุดสั่งงานเดียว

ไฟล์: [`src/isap_pipeline/cli.py`](../src/isap_pipeline/cli.py)

ผู้ใช้ไม่ต้องเรียกแต่ละ module เอง เพราะ `main()` แปลงคำสั่งให้เป็น function ที่ถูกต้อง:

```python
if args.command == "profile":
    return command_profile(Path(args.ocsc), Path(args.cgd))
if args.command == "run":
    return command_run(Path(args.ocsc), Path(args.cgd), Path(args.warehouse))
if args.command == "check-new":
    return command_check_new(save=args.save_manifest)
if args.command == "sync-latest":
    return command_sync_latest(Path(args.download_dir), Path(args.warehouse))
if args.command == "demo":
    return command_demo(Path(args.warehouse))
```

ความหมายแบบง่าย: `cli.py` เป็นตัวจัดลำดับงาน ส่วนกฎอ่าน Excel อยู่ใน module ที่รับผิดชอบ source นั้นโดยตรง

## 2. Profile โครงสร้าง Excel ก่อนอ่านข้อมูล

ไฟล์: [`excel_inspector.py`](../src/isap_pipeline/excel_inspector.py)

คำสั่ง `profile` เปิด workbook จริงและสร้าง profile ต่อ sheet เช่น จำนวนแถว, จำนวนคอลัมน์, merged cells, formula cells, blank rows และตำแหน่ง header ที่คาดไว้

```python
profiles = {
    "generated_at": utc_now_iso(),
    "ocsc": inspect_workbook(ocsc_path),
    "cgd": inspect_workbook(cgd_path),
}
cfg.profile_output.write_text(
    json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8"
)
write_profile_markdown(profiles, Path("docs/data_profiling_report.md"))
```

ผลลัพธ์คือ JSON สำหรับตรวจด้วยโปรแกรม และ Markdown สำหรับคนอ่าน จุดนี้ตอบโจทย์ EDA เชิงโครงสร้างก่อนเริ่ม parse ตัวเลข

## 3. สร้าง metadata ของไฟล์เพื่อ trace กลับได้

ไฟล์: [`metadata.py`](../src/isap_pipeline/metadata.py), [`cli.py`](../src/isap_pipeline/cli.py)

ทุก run สร้าง `run_id` ใหม่ และทุก source file มี SHA-256 ของเนื้อหาไฟล์:

```python
run_id = new_run_id()
ocsc_meta = _source_metadata("ocsc_government_manpower", ocsc_path, sources)
cgd_meta = _source_metadata("cgd_budget_execution", cgd_path, sources)

return SourceFileMetadata(
    dataset_name=dataset_name,
    source_name=getattr(source_cfg, "name", dataset_name),
    path=path,
    sha256=sha256_file(path),
    fiscal_year=fiscal_year,
    fiscal_year_be=fiscal_year_be,
)
```

จึงตอบได้ว่า row นี้มาจาก run ไหน, ไฟล์ใด, sheet ใด และ release ใด โดยไม่พึ่งชื่อไฟล์อย่างเดียว

## 4. Extract raw cells ของทุก sheet

ไฟล์: [`extract_ocsc.py`](../src/isap_pipeline/extract_ocsc.py), [`extract_cgd.py`](../src/isap_pipeline/extract_cgd.py)

ทั้งสอง source เก็บ raw cells ของทุก sheet ก่อน parse ตารางสำคัญ เพื่อให้ยังมีหลักฐานต้นทางเมื่อ parser ต้องแก้ในอนาคต

```python
for row in ws.iter_rows():
    for cell in row:
        if cell.value is None:
            continue
        rows.append(
            {
                "ingestion_run_id": run_id,
                "dataset_name": meta.dataset_name,
                "source_file_hash": meta.sha256,
                "sheet_index": sheet_index,
                "sheet_name": ws.title,
                "row_number": cell.row,
                "column_number": cell.column,
                "cell_value": str(cell.value),
            }
        )
```

raw layer ไม่ได้มีไว้ให้ Analyst query ทุกวัน แต่มีไว้ตอบคำถามว่า “ตัวเลขนี้มาจากไหน” และช่วย debug layout ที่เปลี่ยน

## 5. Parse OCSC และ CGD คนละแบบ

### OCSC: เก็บบริบทกระทรวงและแยก metric

ไฟล์: [`extract_ocsc.py`](../src/isap_pipeline/extract_ocsc.py)

OCSC มีหลาย metric อยู่ตามคอลัมน์ จึงเปลี่ยนจาก wide table เป็น long rows และเก็บกระทรวงที่เป็น parent ของหน่วยงานไว้

```python
for col_idx, metric_name in WORKFORCE_METRIC_COLUMNS.items():
    value = to_int(ws.cell(row_idx, col_idx).value)
    if value is None:
        continue
    rows.append(
        {
            "entity_type": entity_type,
            "ministry_name": ministry_name,
            "agency_name": entity_name,
            "metric_name": metric_name,
            "metric_group": "employment_type",
            "headcount": value,
            "source_unit": "person",
        }
    )
```

แถว `ร้อยละ` ถูกตัดออกจาก profile parser เพื่อไม่ให้ตัวเลข percent ถูกเก็บเป็นจำนวนคน:

```python
entity_name = canonical_entity_name(ws.cell(row_idx, 1).value)
if not entity_name:
    continue
if entity_name == "ร้อยละ":
    continue
```

### CGD: อ่าน header 2 ชั้นและแยกหมวดรายจ่าย

ไฟล์: [`extract_cgd.py`](../src/isap_pipeline/extract_cgd.py)

CGD มี header group `รายจ่ายประจำ`, `รายจ่ายลงทุน`, `รวม` จึงหา span ของแต่ละกลุ่ม แล้วสร้างหนึ่ง row ต่อ `expense_category`:

```python
if label in {"รายจ่ายประจำ", "รายจ่ายลงทุน", "รวม"}:
    starts.append((_expense_category(label), col_idx))

for expense_category, start_col, end_col in group_spans:
    measures = _measure_values(ws, row_idx, subheader_row, start_col, end_col)
    rows.append(
        _base_row(
            meta, run_id, ws.title, row_idx, entity_type_current,
            entity_name, entity_code, expense_category, as_of_date,
        )
        | measures
    )
```

ชื่อ sheet บอกมุมรายงาน `เบิกจ่าย` หรือ `ใช้จ่าย`:

```python
def _report_type_from_sheet(sheet_name: str) -> str:
    normalized = sheet_name.strip()
    if "ใช้จ่าย" in normalized or normalized.endswith("(ใช้"):
        return "expenditure"
    return "disbursement"
```

## 6. Clean ข้อความ ตัวเลข และวันที่ไทยด้วยกฎกลาง

ไฟล์: [`clean.py`](../src/isap_pipeline/clean.py)

กฎที่ใช้ทั้งสอง source อยู่ในที่เดียว เพื่อลดการเขียน logic ซ้ำและทำ unit test ได้ง่าย

```python
def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def to_number(value: Any) -> float | None:
    text = normalize_text(value)
    if not text or text in {"-", "#REF!", "#DIV/0!", "#VALUE!"}:
        return None
    text = text.replace(",", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None
```

การแปลงวันที่ภาษาไทยเปลี่ยน พ.ศ. เป็น ค.ศ. ก่อนสร้าง `date` object:

```python
def parse_thai_date(text: str) -> date | None:
    value = normalize_text(text)
    match = re.search(r"(\d{1,2})\s+([ก-๙]+)\s+(\d{4})", value)
    if not match:
        return None
    day = int(match.group(1))
    month = THAI_MONTHS.get(match.group(2))
    year = thai_be_year_to_ce(int(match.group(3)))
    return date(year, month, day)
```

ช่องว่างหรือ Excel error token กลายเป็น `None` ไม่ใช่ศูนย์ เพราะไม่มีหลักฐานว่า “ไม่มีค่า” หมายถึง “0” เสมอไป

## 7. ตรวจคุณภาพข้อมูลก่อนโหลด

ไฟล์: [`dq.py`](../src/isap_pipeline/dq.py)

`run_data_quality_checks()` รวมผล check ของ CGD และ OCSC เป็น DataFrame เดียว เพื่อบันทึกทั้ง JSON และ table ใน warehouse:

```python
issues: list[DQIssue] = []
issues.extend(_check_cgd(cgd_budget_execution))
issues.extend(_check_ocsc(ocsc_workforce))
if not issues:
    issues.append(
        DQIssue(
            check_name="all_core_checks",
            severity="info",
            dataset_name="all",
            table_name="all",
            issue_count=0,
            sample="All configured core data-quality checks passed.",
            status="passed",
        )
    )
```

ตัวอย่าง rule ที่ตรวจจริง:

```python
bad = df[df[col].notna() & ((df[col] < 0) | (df[col] > 100))]

keys = [
    "source_file_hash", "sheet_name", "entity_name", "entity_code",
    "expense_category", "report_type",
]
duplicated = df[df.duplicated(keys, keep=False)]
```

สำหรับ CGD ยังเทียบยอด `total` ที่ต้นทางเผยแพร่กับผลรวม detail ในกลุ่มที่มี grain เปรียบเทียบได้ โดยมี tolerance สำหรับ floating-point rounding

## 8. โหลด DuckDB แบบรันซ้ำไม่เกิดข้อมูลซ้ำ

ไฟล์: [`load.py`](../src/isap_pipeline/load.py)

ก่อน insert ระบบหา hashes ของ source files ในรอบนั้น แล้วลบข้อมูลของ hash เดิมจากทุก layer ที่เกี่ยวข้อง:

```python
hashes = sorted(set(source_files["sha256"].dropna().astype(str).tolist()))
_delete_existing(con, hashes)
```

```python
for table in tables:
    for file_hash in hashes:
        if table == "raw.source_files":
            con.execute(f"DELETE FROM {table} WHERE sha256 = ?", [file_hash])
        elif table == "mart.fact_data_quality_issue":
            con.execute(
                f"DELETE FROM {table} WHERE source_file_hash LIKE '%' || ? || '%'",
                [file_hash],
            )
        else:
            con.execute(f"DELETE FROM {table} WHERE source_file_hash = ?", [file_hash])
```

จากนั้น insert raw, staging และ mart ใหม่จากผล parse ล่าสุด แล้ว rebuild dimensions ความหมายคือ file เดิมมาอีกครั้งได้โดย row count ไม่เพิ่ม แต่ถ้าเนื้อหาเปลี่ยน SHA-256 จะเปลี่ยนและถูกถือเป็น release ใหม่

## 9. ตรวจ release ใหม่รายเดือน

ไฟล์: [`discovery.py`](../src/isap_pipeline/discovery.py), [`config/sources.yml`](../config/sources.yml)

`discover_source()` เปิดหน้าเว็บ, หา link ที่ลงท้ายด้วย `.xlsx`, `.xls` หรือ `.zip`, แล้วคืน `source_unavailable` หาก request ล้มเหลวหรือ static HTML ไม่มี link ที่ใช้ได้:

```python
try:
    response = requests.get(config.page_url, headers=REQUEST_HEADERS, timeout=timeout)
    response.raise_for_status()
except requests.RequestException as exc:
    return DiscoveredFile(
        source_name=config.name,
        dataset_name=config.dataset_name,
        status="source_unavailable",
        source_page_url=config.page_url,
        file_url=None,
        message=str(exc),
    )
```

ผลล่าสุดถูกเทียบกับ manifest จาก `file_url`, `filename` และ `publish_date`:

```python
comparable_fields = [
    field
    for field in ("file_url", "filename", "publish_date")
    if prior.get(field) is not None
]
changed = any(prior.get(field) != current.get(field) for field in comparable_fields)
status = "new_data_found" if changed or not comparable_fields else "no_new_data"
```

จุดสำคัญคือ `source_unavailable` ไม่ถูกเปลี่ยนเป็น `no_new_data` เพราะ network failure ไม่ใช่หลักฐานว่าไม่มี release ใหม่

## 10. Download และ ingest release ใหม่แบบไม่ partial load

ไฟล์: [`downloader.py`](../src/isap_pipeline/downloader.py), [`cli.py`](../src/isap_pipeline/cli.py)

download ใช้ streaming เพื่อไม่ต้องเก็บไฟล์ทั้งหมดใน memory:

```python
with requests.get(url, headers=DOWNLOAD_HEADERS, timeout=timeout, stream=True) as response:
    response.raise_for_status()
    with target_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)
return {"path": str(target_path), "sha256": sha256_file(target_path)}
```

`sync-latest` ตรวจทั้งสอง source ให้พร้อมก่อน download และจะ update manifest หลัง `command_run()` สำเร็จเท่านั้น:

```python
unavailable = [item for item in discovered if item.status != "discovered" or not item.file_url]
if unavailable:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    LOGGER.error("Cannot sync latest files because one or more source pages are unavailable.")
    return 1

exit_code = command_run(
    downloaded["ocsc_government_manpower"],
    downloaded["cgd_budget_execution"],
    warehouse_path,
)
if exit_code == 0:
    save_manifest(discovered, cfg.manifest_path)
```

นี่คือเหตุผลที่ระบบไม่ทำ partial load: ถ้า source ใด source หนึ่งไม่พร้อม ระบบหยุดก่อน run pipeline

## 11. CI และการทดสอบ

ไฟล์: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), [`.github/workflows/monthly-check.yml`](../.github/workflows/monthly-check.yml), [`tests/`](../tests)

CI รันทุก push และ pull request:

```yaml
- name: Lint
  run: python -m ruff check .
- name: Test
  run: python -m pytest
```

monthly workflow ตั้งใจรันวันที่ 1 ของทุกเดือน เวลา 02:00 ตามเวลาไทย (`Asia/Bangkok`) และอัปโหลด JSON หลักฐานของผลตรวจ แม้ command จะล้มเหลว GitHub Actions ใช้ cron แบบ UTC จึงเปิด window ที่ 19:00 UTC ของวันที่ 28-31 แล้ว gate ด้วยวันที่ Bangkok เพื่อเลือกเฉพาะ 02:00 ของวันที่ 1; การกด manual dispatch รันได้ทุกวัน ถ้า source ใด unavailable, `check-new` คืน exit code 1 เพื่อให้ run เป็น failure/alert แทนการเป็นสีเขียวโดยไม่มีข้อมูล:

```yaml
on:
  schedule:
    - cron: "0 19 28-31 * *"

- name: Check Bangkok schedule
  id: bangkok_schedule
  run: |
    if [ "${{ github.event_name }}" = "workflow_dispatch" ] || [ "$(TZ=Asia/Bangkok date +%d)" = "01" ]; then
      echo "should_run=true" >> "$GITHUB_OUTPUT"
    fi

- name: Upload source-check evidence
  if: always() && steps.bangkok_schedule.outputs.should_run == 'true'
  uses: actions/upload-artifact@v4
```

tests ปัจจุบันครอบคลุม date conversion, header normalization, OCSC/CGD transforms, DQ, idempotency, manifest comparison, ZIP extraction และ sync orchestration

## 12. Tests: ทดสอบอะไรโดยไม่ใช้ PowerShell

คำสั่งทดสอบหลักคือ:

```powershell
python -m pytest
```

หากต้องการตรวจเฉพาะ behavior สำคัญโดยไม่รันทั้งชุด:

```powershell
python -m pytest tests/test_cgd_transform.py -q
python -m pytest tests/test_idempotency.py -q
python -m pytest tests/test_sync_latest.py tests/test_sync_latest_end_to_end.py -q
```

ชุดทดสอบเป็น Python `pytest` โดยตรง ไม่เรียก `.ps1`, ไม่เปิด terminal แบบ interactive และไม่ต้องเข้าถึงเว็บไซต์จริง แต่ละ test สร้างไฟล์ Excel/ZIP/warehouse ชั่วคราวของตัวเองใน `tmp_path` แล้วลบทิ้งเมื่อจบ จึงรันซ้ำได้เหมือนกันบนเครื่อง developer และ GitHub Actions

| กลุ่มที่ทดสอบ | ไฟล์ | จำนวน | สิ่งที่พิสูจน์ |
|---|---:|---:|---|
| Clean และ header | `test_header_normalization.py` | 4 | newline/ช่องว่าง, synonym, error token และเลขลำดับหน้าชื่อหน่วยงานถูกจัดการตามกฎเดียวกัน |
| วันที่ไทย | `test_date_conversion.py` | 2 | พ.ศ. 2569 กลายเป็น ค.ศ. 2026 และ parse วันที่ไทยได้ |
| OCSC parser | `test_ocsc_transform.py` | 2 | เก็บ context กระทรวง, แปลง metric และไม่เอาแถว `ร้อยละ` ไปเป็น headcount |
| CGD parser | `test_cgd_transform.py` | 2 | unpivot `ประจำ/ลงทุน/รวม`, เก็บ total row และแยกชื่อ sheet ใช้จ่ายที่ถูกตัด |
| Data quality | `test_data_quality.py` | 1 | เมื่อ published total ไม่เท่าผลรวม detail ต้องมี reconciliation issue |
| Idempotent load | `test_idempotency.py` | 1 | โหลด file hash เดิมสองครั้งแล้ว mart row count ไม่เพิ่ม |
| Release discovery | `test_discovery.py` | 2 | manifest เดิมเป็น `no_new_data`; filename ใหม่เป็น `new_data_found` |
| Download safety | `test_downloader.py` | 1 | แตก ZIP โดยเก็บเฉพาะ basename ของ Excel file |
| Source availability | `test_source_check.py` | 1 | `source_unavailable` เขียนหลักฐานและคืน exit code 1 เพื่อ alert |
| Sync orchestration | `test_sync_latest.py` | 1 | download ทั้งสอง source ก่อนเรียก load และส่ง path ที่ถูกต้องเข้า pipeline |
| End-to-end sync | `test_sync_latest_end_to_end.py` | 1 | ดาวน์โหลดผ่าน local HTTP, parse OCSC/CGD, DQ, load DuckDB และ save manifest ครบเส้น |

รวม 18 tests ใน 11 ไฟล์

### ตัวอย่าง 1: ตรวจ conversion ก่อนให้ parser ใช้

ไฟล์: [`tests/test_header_normalization.py`](../tests/test_header_normalization.py)

```python
def test_to_number_handles_report_tokens() -> None:
    assert to_number("1,234.50") == 1234.5
    assert to_number("#REF!") is None

def test_canonical_entity_name_strips_order_prefix() -> None:
    assert canonical_entity_name("1. สำนักนายกรัฐมนตรี") == "สำนักนายกรัฐมนตรี"
```

สิ่งที่พิสูจน์: Excel error ไม่กลายเป็นศูนย์แบบเงียบ ๆ และชื่อหน่วยงานที่มีเลขนำหน้าจะ join/query ได้สม่ำเสมอ

### ตัวอย่าง 2: ตรวจ OCSC ไม่เอาร้อยละเป็นจำนวนคน

ไฟล์: [`tests/test_ocsc_transform.py`](../tests/test_ocsc_transform.py)

```python
result = extract_ocsc_workbook(path, meta, "run-1").workforce_profile

assert not (result["agency_name"] == "ร้อยละ").any()
assert (result["agency_name"] == "รวมทั้งหมด").any()
```

สิ่งที่พิสูจน์: parser ตัด summary percentage ที่ตีความเป็น headcount ไม่ได้ แต่ยังรักษา total row ไว้สำหรับตรวจสอบยอด

### ตัวอย่าง 3: ตรวจ CGD unpivot และ total row

ไฟล์: [`tests/test_cgd_transform.py`](../tests/test_cgd_transform.py)

```python
result = extract_cgd_workbook(path, meta, "run-1").budget_execution

agency_total = result[
    (result["entity_name"] == "กรมบัญชีกลาง")
    & (result["expense_category"] == "total")
].iloc[0]
published_total = result[
    (result["entity_type"] == "total")
    & (result["expense_category"] == "total")
].iloc[0]

assert len(result) == 6
assert agency_total["disbursement_million_baht"] == 90
assert published_total["entity_type"] == "total"
```

สิ่งที่พิสูจน์: ตาราง wide ที่มี 3 expense groups ถูกแปลงเป็น long rows ตามที่คาด และ row `รวม` ยังถูกระบุว่าเป็น total ไม่ใช่ agency detail

### ตัวอย่าง 4: ตรวจรันซ้ำแล้วไม่มีข้อมูลซ้ำ

ไฟล์: [`tests/test_idempotency.py`](../tests/test_idempotency.py)

```python
for run_id in ["run-1", "run-2"]:
    load_dataframes(
        warehouse,
        run_id=run_id,
        source_files=source_files,
        workbook_sheets=workbook_sheets,
        raw_cells=raw_cells.assign(ingestion_run_id=run_id),
        cgd_budget_execution=cgd.assign(ingestion_run_id=run_id),
        ocsc_workforce=ocsc.assign(ingestion_run_id=run_id),
        dq_issues=dq.assign(ingestion_run_id=run_id),
    )

assert con.execute(
    "select count(*) from mart.fact_budget_execution"
).fetchone()[0] == 1
```

สิ่งที่พิสูจน์: ต่อให้ pipeline ถูกเรียกสองครั้ง แต่ source file hash เดิมจะถูก replace ก่อน insert จึงไม่เกิด duplicate ใน mart

### ตัวอย่าง 5: ตรวจ decision ของ monthly sync โดยไม่เรียกเว็บจริง

ไฟล์: [`tests/test_discovery.py`](../tests/test_discovery.py), [`tests/test_sync_latest.py`](../tests/test_sync_latest.py)

```python
result = compare_with_manifest(
    [_discovered("2026.08.01.xlsx", "2026-08-01")], manifest
)
assert result["sources"][0]["status"] == "new_data_found"
```

```python
monkeypatch.setattr(cli, "download_file", fake_download)
monkeypatch.setattr(cli, "command_run", fake_run)

result = cli.command_sync_latest(tmp_path / "raw", warehouse)
assert result == 0
```

สิ่งที่พิสูจน์: กฎเปรียบเทียบ manifest และลำดับ download -> load ถูกตรวจได้แบบ deterministic โดยไม่รอ network หรือหน้าเว็บต้นทาง ส่วน `test_sync_latest_end_to_end.py` พิสูจน์เส้น download -> parse -> DQ -> DuckDB ด้วย HTTP server ในเครื่อง

## สรุปสำหรับการตอบในห้องสัมภาษณ์

> Automation ของงานนี้ไม่ใช่แค่ตั้งเวลา run ครับ แต่เริ่มจากตรวจว่ามีไฟล์ใหม่จริงหรือไม่, หยุดอย่างปลอดภัยเมื่อเว็บเข้าถึงไม่ได้, อ่าน source-specific layout, ตรวจคุณภาพข้อมูล, โหลดด้วย file hash เพื่อไม่ให้ข้อมูลซ้ำ และมี tests/CI คอยตรวจ logic ทุกครั้งที่ code เปลี่ยน
