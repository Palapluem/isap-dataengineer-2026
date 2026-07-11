from pathlib import Path

from openpyxl import Workbook

from isap_pipeline.extract_cgd import _report_type_from_sheet, extract_cgd_workbook
from isap_pipeline.metadata import SourceFileMetadata, sha256_file


def test_cgd_transform_unpivots_expense_groups(tmp_path: Path) -> None:
    path = tmp_path / "2026.07.03.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "3.หน่วยงาน"
    ws.append(["รายงานผลการเบิกจ่ายเงินงบประมาณประจำปี พ.ศ. 2569"])
    ws.append(["ตั้งแต่ต้นปีงบประมาณ จนถึงวันที่ 3 กรกฎาคม 2569"])
    ws.append(["หน่วย: ล้านบาท"])
    ws.append(
        [
            "ลำดับ ที่",
            "หน่วยงาน",
            "รายจ่ายประจำ",
            None,
            None,
            None,
            "รายจ่ายลงทุน",
            None,
            None,
            None,
            "รวม",
            None,
            None,
            None,
            "รหัสกรม",
        ]
    )
    ws.append(
        [
            None,
            None,
            "วงเงิน งบประมาณ หลังโอน เปลี่ยนแปลง",
            "PO+สำรอง เงินมีหนี้",
            "เบิกจ่าย",
            "ร้อยละเบิกจ่าย ต่องบประมาณ หลังโอน เปลี่ยนแปลง",
            "วงเงิน งบประมาณ หลังโอน เปลี่ยนแปลง",
            "PO+สำรอง เงินมีหนี้",
            "เบิกจ่าย",
            "ร้อยละเบิกจ่าย ต่องบประมาณ หลังโอน เปลี่ยนแปลง",
            "วงเงิน งบประมาณ หลังโอน เปลี่ยนแปลง",
            "PO+สำรอง เงินมีหนี้",
            "เบิกจ่าย",
            "ร้อยละเบิกจ่าย ต่องบประมาณ หลังโอน เปลี่ยนแปลง",
            None,
        ]
    )
    ws.append([1, "กรมบัญชีกลาง", 100, 10, 70, 70, 50, 5, 20, 40, 150, 15, 90, 60, "03003"])
    ws.append(["รวม", None, 100, 10, 70, 70, 50, 5, 20, 40, 150, 15, 90, 60, None])
    wb.save(path)

    meta = SourceFileMetadata(
        dataset_name="cgd_budget_execution",
        source_name="CGD",
        path=path,
        sha256=sha256_file(path),
        fiscal_year=2026,
        fiscal_year_be=2569,
    )
    result = extract_cgd_workbook(path, meta, "run-1").budget_execution

    assert len(result) == 6
    agency_total = result[
        (result["entity_name"] == "กรมบัญชีกลาง")
        & (result["expense_category"] == "total")
    ].iloc[0]
    assert agency_total["disbursement_million_baht"] == 90
    assert agency_total["disbursement_pct"] == 60

    published_total = result[
        (result["entity_type"] == "total") & (result["expense_category"] == "total")
    ].iloc[0]
    assert published_total["entity_name"] == "รวม"
    assert published_total["disbursement_million_baht"] == 90


def test_cgd_truncated_expenditure_sheet_name_is_classified() -> None:
    assert _report_type_from_sheet("14.ส่วนกลางจัดสรรให้จังหวัด(ใช้") == "expenditure"
    assert _report_type_from_sheet("3.หน่วยงาน") == "disbursement"
