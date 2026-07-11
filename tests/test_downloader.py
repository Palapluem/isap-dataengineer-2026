import zipfile

from isap_pipeline.downloader import extract_first_excel_from_zip


def test_extract_excel_from_zip_uses_safe_basename(tmp_path):
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/report.xlsx", b"excel-placeholder")

    output_path = extract_first_excel_from_zip(archive_path, tmp_path / "output")

    assert output_path == tmp_path / "output" / "report.xlsx"
    assert output_path.read_bytes() == b"excel-placeholder"
