from pathlib import Path

from isap_pipeline import cli
from isap_pipeline.discovery import DiscoveredFile


def _source(dataset_name: str, filename: str) -> DiscoveredFile:
    return DiscoveredFile(
        source_name=dataset_name,
        dataset_name=dataset_name,
        status="discovered",
        source_page_url="https://example.com/source",
        title=filename,
        file_url=f"https://example.com/{filename}",
        filename=filename,
        publish_date=None,
        checked_at="2026-07-11T00:00:00Z",
    )


def test_sync_latest_downloads_both_sources_before_loading(tmp_path, monkeypatch):
    discovered = [
        _source("ocsc_government_manpower", "ocsc.xlsx"),
        _source("cgd_budget_execution", "cgd.xlsx"),
    ]
    monkeypatch.setattr(cli, "discover_sources", lambda: discovered)

    def fake_download(url: str, output_dir: Path):
        path = output_dir / Path(url).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return {"path": str(path), "sha256": "test"}

    monkeypatch.setattr(cli, "download_file", fake_download)
    loaded: dict[str, Path] = {}

    def fake_run(ocsc_path: Path, cgd_path: Path, warehouse_path: Path) -> int:
        loaded.update(ocsc=ocsc_path, cgd=cgd_path, warehouse=warehouse_path)
        return 0

    monkeypatch.setattr(cli, "command_run", fake_run)
    monkeypatch.setattr(cli, "save_manifest", lambda items, path: None)

    warehouse = tmp_path / "warehouse.duckdb"
    result = cli.command_sync_latest(tmp_path / "raw", warehouse)

    assert result == 0
    assert loaded["ocsc"].name == "ocsc.xlsx"
    assert loaded["cgd"].name == "cgd.xlsx"
    assert loaded["warehouse"] == warehouse
