from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

@dataclass(frozen=True)
class SourceConfig:
    name: str
    dataset_name: str
    page_url: str
    local_filename: str

@dataclass(frozen=True)
class PipelineConfig:
    raw_dir: Path
    processed_dir: Path
    warehouse_dir: Path
    profile_output: Path
    manifest_path: Path
    source_check_output: Path

def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}

def load_sources(path: str | Path = "config/sources.yml") -> list[SourceConfig]:
    payload = load_yaml(path)
    sources = []
    for item in payload.get("sources", []):
        sources.append(
            SourceConfig(
                name=item["name"],
                dataset_name=item["dataset_name"],
                page_url=item["page_url"],
                local_filename=item["local_filename"],
            )
        )
    return sources

def load_pipeline_config(path: str | Path = "config/pipeline.yml") -> PipelineConfig:
    payload = load_yaml(path)
    dirs = payload.get("directories", {})
    outputs = payload.get("outputs", {})
    processed_dir = Path(dirs.get("processed", "data/processed"))
    return PipelineConfig(
        raw_dir=Path(dirs.get("raw", "data/raw")),
        processed_dir=processed_dir,
        warehouse_dir=Path(dirs.get("warehouse", "data/warehouse")),
        profile_output=Path(outputs.get("profile_json", processed_dir / "profile_summary.json")),
        manifest_path=Path(outputs.get("manifest_json", processed_dir / "source_manifest.json")),
        source_check_output=Path(
            outputs.get("source_check_json", processed_dir / "source_check_latest.json")
        ),
    )
