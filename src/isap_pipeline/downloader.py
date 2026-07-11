from __future__ import annotations

import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from isap_pipeline.metadata import sha256_file

def download_file(url: str, output_dir: str | Path, timeout: int = 60) -> dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(urlparse(url).path).name or "downloaded_source"
    target_path = target_dir / filename
    with requests.get(url, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        with target_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return {"path": str(target_path), "sha256": sha256_file(target_path)}

def extract_first_excel_from_zip(zip_path: str | Path, output_dir: str | Path) -> Path:
    path = Path(zip_path)
    target_dir = Path(output_dir)
    with zipfile.ZipFile(path) as archive:
        excel_names = [name for name in archive.namelist() if name.lower().endswith((".xlsx", ".xls"))]
        if not excel_names:
            raise ValueError(f"No Excel file found in {zip_path}")
        selected = excel_names[0]
        archive.extract(selected, target_dir)
        return target_dir / selected