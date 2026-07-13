import json
from pathlib import Path

from isap_pipeline import cli
from isap_pipeline.config import PipelineConfig
from isap_pipeline.discovery import DiscoveredFile


def _config(tmp_path: Path) -> PipelineConfig:
    processed = tmp_path / "processed"
    return PipelineConfig(
        raw_dir=tmp_path / "raw",
        processed_dir=processed,
        warehouse_dir=tmp_path / "warehouse",
        profile_output=processed / "profile.json",
        manifest_path=tmp_path / "manifest.json",
        source_check_output=processed / "source_check.json",
    )


def test_check_new_returns_nonzero_when_a_source_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    unavailable = DiscoveredFile(
        source_name="OCSC",
        dataset_name="ocsc_government_manpower",
        status="source_unavailable",
        source_page_url="https://example.com/ocsc",
        title=None,
        file_url=None,
        filename=None,
        publish_date=None,
        checked_at="2026-07-13T00:00:00Z",
        message="403 Forbidden",
    )
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli, "discover_sources", lambda: [unavailable])
    monkeypatch.setattr(cli, "load_pipeline_config", lambda: cfg)

    assert cli.command_check_new() == 1
    payload = json.loads(cfg.source_check_output.read_text(encoding="utf-8"))
    assert payload["sources"][0]["status"] == "source_unavailable"
