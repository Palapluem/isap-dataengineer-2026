from isap_pipeline.clean import canonical_entity_name, normalize_header, normalize_text, to_number


def test_normalize_text_removes_newline_and_extra_spaces() -> None:
    assert normalize_text("วงเงิน\n งบประมาณ   หลังโอน") == "วงเงิน งบประมาณ หลังโอน"


def test_normalize_header_maps_budget_synonym() -> None:
    assert normalize_header("วงเงิน งบประมาณ หลังโอน เปลี่ยนแปลง") == "budget_after_transfer"


def test_to_number_handles_report_tokens() -> None:
    assert to_number("1,234.50") == 1234.5
    assert to_number("#REF!") is None


def test_canonical_entity_name_strips_order_prefix() -> None:
    assert canonical_entity_name("1. สำนักนายกรัฐมนตรี") == "สำนักนายกรัฐมนตรี"
