from isap_pipeline.clean import parse_thai_date, thai_be_year_to_ce


def test_thai_be_year_to_ce() -> None:
    assert thai_be_year_to_ce(2569) == 2026
    assert thai_be_year_to_ce(2026) == 2026


def test_parse_thai_date() -> None:
    assert parse_thai_date("ข้อมูล ณ วันที่ 3 กรกฎาคม 2569").isoformat() == "2026-07-03"
