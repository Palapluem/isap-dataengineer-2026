from pathlib import Path

from openpyxl import Workbook

from isap_pipeline.extract_ocsc import extract_ocsc_workbook
from isap_pipeline.metadata import SourceFileMetadata, sha256_file


def test_ocsc_transform_extracts_workforce_metrics(tmp_path: Path) -> None:
    path = tmp_path / "thai-gov-manpower-2567.4.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "17-29"
    ws.append(["ข้าราชการ ลูกจ้างประจำ ลูกจ้างชั่วคราว และพนักงานราชการ"])
    ws.append(["ส่วนราชการ", None, None, "ข้าราชการ", "ลูกจ้างประจำ", None, None, None, None, "พนักงานราชการ"])
    ws.append([None] * 12)
    ws.append([None] * 12)
    ws.append([None] * 12)
    ws.append(["รวม", None, None, 1000, 10, 0, 0, 0, 0, 100, 50, 0])
    ws.append(["1. สำนักนายกรัฐมนตรี", None, None, 100, 1, 0, 0, 0, 0, 10, 0, 0])
    ws.append([None, "1.1", "กรมตัวอย่าง", 20, 0, 0, 0, 0, 0, 5, 0, 0])
    wb.save(path)

    meta = SourceFileMetadata(
        dataset_name="ocsc_government_manpower",
        source_name="OCSC",
        path=path,
        sha256=sha256_file(path),
        fiscal_year=2024,
        fiscal_year_be=2567,
    )
    result = extract_ocsc_workbook(path, meta, "run-1").workforce_agency

    agency = result[(result["agency_name"] == "กรมตัวอย่าง") & (result["metric_name"] == "civil_servant")]
    assert agency.iloc[0]["headcount"] == 20
    assert agency.iloc[0]["ministry_name"] == "สำนักนายกรัฐมนตรี"


def test_ocsc_profile_skips_percentage_summary_row(tmp_path: Path) -> None:
    path = tmp_path / "thai-gov-manpower-2567.4.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "88-97"
    ws.append(["รายงาน", "ช่วงอายุ", None, "เพศ", None, "ระดับการศึกษา"])
    ws.append([None] * 20)
    ws.append([None] * 20)
    ws.append(["รวมทั้งหมด", 100, 1, 20, 30, 25, 15, 5, 3, 1, 0, 1, 40, 45, 55, 55, 20, 70, 25, 5])
    ws.append(["ร้อยละ", 100, 1, 20, 30, 25, 15, 5, 3, 1, 0, 1, 40, 45, 55, 55, 20, 70, 25, 5])
    wb.save(path)

    meta = SourceFileMetadata(
        dataset_name="ocsc_government_manpower",
        source_name="OCSC",
        path=path,
        sha256=sha256_file(path),
        fiscal_year=2024,
        fiscal_year_be=2567,
    )
    result = extract_ocsc_workbook(path, meta, "run-1").workforce_profile

    assert not (result["agency_name"] == "ร้อยละ").any()
    assert (result["agency_name"] == "รวมทั้งหมด").any()
