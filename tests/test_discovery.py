import json

from isap_pipeline.discovery import DiscoveredFile, compare_with_manifest


def _discovered(filename: str, publish_date: str | None = None) -> DiscoveredFile:
    return DiscoveredFile(
        source_name="CGD",
        dataset_name="cgd_budget_execution",
        status="discovered",
        source_page_url="https://example.com/source",
        title=filename,
        file_url=f"https://example.com/{filename}",
        filename=filename,
        publish_date=publish_date,
        checked_at="2026-07-11T00:00:00Z",
    )


def test_compare_manifest_uses_known_baseline_fields(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cgd_budget_execution": {
                    "file_url": None,
                    "filename": "2026.07.03.xlsx",
                    "publish_date": "2026-07-03",
                }
            }
        ),
        encoding="utf-8",
    )

    result = compare_with_manifest(
        [_discovered("2026.07.03.xlsx", "2026-07-03")], manifest
    )

    assert result["sources"][0]["status"] == "no_new_data"


def test_compare_manifest_flags_changed_filename(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cgd_budget_execution": {
                    "file_url": None,
                    "filename": "2026.07.03.xlsx",
                    "publish_date": "2026-07-03",
                }
            }
        ),
        encoding="utf-8",
    )

    result = compare_with_manifest(
        [_discovered("2026.08.01.xlsx", "2026-08-01")], manifest
    )

    assert result["sources"][0]["status"] == "new_data_found"
