from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from isap_pipeline.config import SourceConfig, load_sources
from isap_pipeline.metadata import utc_now_iso

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}

@dataclass(frozen=True)
class DiscoveredFile:
    source_name: str
    dataset_name: str
    status: str
    source_page_url: str
    title: str | None
    file_url: str | None
    filename: str | None
    publish_date: str | None
    checked_at: str
    message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "dataset_name": self.dataset_name,
            "status": self.status,
            "source_page_url": self.source_page_url,
            "title": self.title,
            "file_url": self.file_url,
            "filename": self.filename,
            "publish_date": self.publish_date,
            "checked_at": self.checked_at,
            "message": self.message,
        }

def discover_sources(sources: list[SourceConfig] | None = None, timeout: int = 20) -> list[DiscoveredFile]:
    configs = sources or load_sources()
    return [discover_source(config, timeout=timeout) for config in configs]

def discover_source(config: SourceConfig, timeout: int = 20) -> DiscoveredFile:
    checked_at = utc_now_iso()
    try:
        response = requests.get(config.page_url, headers=REQUEST_HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        return DiscoveredFile(
            source_name=config.name,
            dataset_name=config.dataset_name,
            status="source_unavailable",
            source_page_url=config.page_url,
            title=None,
            file_url=None,
            filename=None,
            publish_date=None,
            checked_at=checked_at,
            message=str(exc),
        )

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = _extract_file_candidates(soup, config.page_url, config.dataset_name)
    if not candidates:
        return DiscoveredFile(
            source_name=config.name,
            dataset_name=config.dataset_name,
            status="source_unavailable",
            source_page_url=config.page_url,
            title=soup.title.string.strip() if soup.title and soup.title.string else None,
            file_url=None,
            filename=None,
            publish_date=None,
            checked_at=checked_at,
            message="No xlsx/zip candidate link found in static HTML.",
        )
    latest = candidates[0]
    return DiscoveredFile(
        source_name=config.name,
        dataset_name=config.dataset_name,
        status="discovered",
        source_page_url=config.page_url,
        title=latest["title"],
        file_url=latest["file_url"],
        filename=latest["filename"],
        publish_date=latest["publish_date"],
        checked_at=checked_at,
    )

def compare_with_manifest(discovered: list[DiscoveredFile], manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path)
    previous: dict[str, Any] = {}
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))

    results = []
    for item in discovered:
        current = item.as_dict()
        prior = previous.get(item.dataset_name)
        status = item.status
        if item.status == "discovered":
            if not prior:
                status = "new_data_found"
            elif (
                prior.get("file_url") == item.file_url
                and prior.get("filename") == item.filename
                and prior.get("publish_date") == item.publish_date
            ):
                status = "no_new_data"
            else:
                status = "new_data_found"
        current["status"] = status
        results.append(current)
    return {"checked_at": utc_now_iso(), "sources": results}

def save_manifest(discovered: list[DiscoveredFile], manifest_path: str | Path) -> None:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {item.dataset_name: item.as_dict() for item in discovered if item.status == "discovered"}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def _extract_file_candidates(soup: BeautifulSoup, page_url: str, dataset_name: str) -> list[dict[str, str | None]]:
    candidates = []
    file_pattern = re.compile(r"\.(xlsx|xls|zip)(\?|$)", re.IGNORECASE)
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not file_pattern.search(href):
            continue
        file_url = urljoin(page_url, href)
        title = " ".join(link.get_text(" ", strip=True).split()) or link.get("title")
        filename = Path(file_url.split("?")[0]).name
        publish_date = _extract_date(title or filename)
        candidates.append(
            {
                "title": title or filename,
                "file_url": file_url,
                "filename": filename,
                "publish_date": publish_date,
            }
        )
    candidates.sort(key=lambda item: item["publish_date"] or item["filename"] or "", reverse=True)
    if dataset_name == "cgd_budget_execution":
        candidates.sort(key=lambda item: _sortable_cgd_date(item), reverse=True)
    return candidates

def _extract_date(text: str) -> str | None:
    match = re.search(r"(20\d{2})[.\-/](\d{2})[.\-/](\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"(\d{1,2})/(\d{1,2})/(25\d{2}|20\d{2})", text)
    if match:
        year = int(match.group(3))
        if year >= 2500:
            year -= 543
        return f"{year:04d}-{int(match.group(2)):02d}-{int(match.group(1)):02d}"
    return None

def _sortable_cgd_date(item: dict[str, str | None]) -> str:
    return item.get("publish_date") or item.get("filename") or ""
