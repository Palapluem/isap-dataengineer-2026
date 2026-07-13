from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import duckdb
from openpyxl import Workbook

from isap_pipeline import cli
from isap_pipeline.config import PipelineConfig
from isap_pipeline.discovery import DiscoveredFile


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return None


@contextmanager
def _static_server(directory: Path):
    handler = partial(_QuietStaticHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()


def _write_ocsc_workbook(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "17-29"
    worksheet.append(["ข้าราชการ ลูกจ้างประจำ ลูกจ้างชั่วคราว และพนักงานราชการ"])
    worksheet.append(
        [
            "ส่วนราชการ",
            None,
            None,
            "ข้าราชการ",
            "ลูกจ้างประจำ",
            None,
            None,
            None,
            None,
            "พนักงานราชการ",
        ]
    )
    for _ in range(3):
        worksheet.append([None] * 12)
    worksheet.append(["รวม", None, None, 1000, 10, 0, 0, 0, 0, 100, 50, 0])
    worksheet.append(["1. สำนักนายกรัฐมนตรี", None, None, 100, 1, 0, 0, 0, 0, 10, 0, 0])
    worksheet.append([None, "1.1", "กรมตัวอย่าง", 20, 0, 0, 0, 0, 0, 5, 0, 0])
    workbook.save(path)


def _write_cgd_workbook(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "3.หน่วยงาน"
    worksheet.append(["รายงานผลการเบิกจ่ายเงินงบประมาณประจำปี พ.ศ. 2569"])
    worksheet.append(["ตั้งแต่ต้นปีงบประมาณ จนถึงวันที่ 3 กรกฎาคม 2569"])
    worksheet.append(["หน่วย: ล้านบาท"])
    worksheet.append(
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
    worksheet.append(
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
    worksheet.append([1, "กรมตัวอย่าง", 100, 10, 70, 70, 50, 5, 20, 40, 150, 15, 90, 60, "03003"])
    worksheet.append(["รวม", None, 100, 10, 70, 70, 50, 5, 20, 40, 150, 15, 90, 60, None])
    workbook.save(path)


def _source(dataset_name: str, filename: str, base_url: str) -> DiscoveredFile:
    return DiscoveredFile(
        source_name=dataset_name,
        dataset_name=dataset_name,
        status="discovered",
        source_page_url=f"{base_url}/listing",
        title=filename,
        file_url=f"{base_url}/{filename}",
        filename=filename,
        publish_date="2026-07-03",
        checked_at="2026-07-13T00:00:00Z",
    )


def test_sync_latest_downloads_parses_and_loads_real_http_files(tmp_path: Path, monkeypatch) -> None:
    served = tmp_path / "served"
    served.mkdir()
    _write_ocsc_workbook(served / "ocsc.xlsx")
    _write_cgd_workbook(served / "cgd.xlsx")

    processed = tmp_path / "processed"
    cfg = PipelineConfig(
        raw_dir=tmp_path / "raw",
        processed_dir=processed,
        warehouse_dir=tmp_path / "warehouse",
        profile_output=processed / "profile.json",
        manifest_path=tmp_path / "manifest.json",
        source_check_output=processed / "source_check.json",
    )
    monkeypatch.setattr(cli, "load_pipeline_config", lambda: cfg)

    with _static_server(served) as base_url:
        sources = [
            _source("ocsc_government_manpower", "ocsc.xlsx", base_url),
            _source("cgd_budget_execution", "cgd.xlsx", base_url),
        ]
        monkeypatch.setattr(cli, "discover_sources", lambda: sources)
        warehouse = tmp_path / "warehouse" / "isap.duckdb"

        assert cli.command_sync_latest(cfg.raw_dir, warehouse) == 0

    assert (cfg.raw_dir / "ocsc_government_manpower" / "ocsc.xlsx").exists()
    assert (cfg.raw_dir / "cgd_budget_execution" / "cgd.xlsx").exists()
    assert cfg.manifest_path.exists()

    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM mart.fact_budget_execution").fetchone()[0] > 0
        assert con.execute("SELECT count(*) FROM mart.fact_government_manpower").fetchone()[0] > 0
    finally:
        con.close()
