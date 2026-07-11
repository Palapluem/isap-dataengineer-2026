from __future__ import annotations

import re
from datetime import date
from typing import Any

THAI_MONTHS = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
}

def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_header(value: Any) -> str:
    text = normalize_text(value).lower()
    text = text.replace("%", "percent")
    text = re.sub(r"[()/+.,:;]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    replacements = {
        "วงเงิน งบประมาณ หลังโอน เปลี่ยนแปลง": "budget_after_transfer",
        "วงเงินงบประมาณ หลังโอนเปลี่ยนแปลง": "budget_after_transfer",
        "po สำรอง เงินมีหนี้": "po_reserved_debt",
        "po สำรองเงิน มีหนี้": "po_reserved_debt",
        "po": "po_reserved_debt",
        "จัดสรร": "allocated",
        "แผนการ ใช้จ่าย": "planned_expenditure",
        "แผนการใช้จ่าย": "planned_expenditure",
        "เบิกจ่าย": "disbursement",
        "การใช้จ่าย": "expenditure",
        "สูง ต่ำกว่า เป้าหมายการ ใช้จ่าย รายเดือน": "monthly_target_gap",
        "สูง ต่ำกว่า เป้าหมายการใช้จ่าย รายเดือน": "monthly_target_gap",
        "ร้อยละ": "pct",
        "คงเหลือยังไม่เบิกจ่าย": "remaining_not_disbursed",
        "ลำดับ ที่": "rank",
        "ลำดับ": "rank",
        "หน่วยงาน": "agency_name",
        "กระทรวง": "ministry_name",
        "จังหวัด": "province_name",
        "รายการ": "item_name",
        "รหัสกรมจังหวัด": "entity_code",
        "รหัสกรม": "entity_code",
    }
    return replacements.get(text, slugify(text))

def slugify(text: str) -> str:
    text = normalize_text(text).lower()
    text = text.replace("%", "pct")
    text = re.sub(r"[^\wก-๙]+", "_", text, flags=re.UNICODE)
    text = re.sub(r"_+", "_", text).strip("_")
    return text

def canonical_entity_name(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", text)
    text = text.replace("\u00a0", " ")
    return normalize_text(text)

def to_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    text = normalize_text(value)
    if not text or text in {"-", "#REF!", "#DIV/0!", "#VALUE!"}:
        return None
    text = text.replace(",", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None

def to_int(value: Any) -> int | None:
    number = to_number(value)
    if number is None:
        return None
    return int(round(number))

def thai_be_year_to_ce(year: int) -> int:
    return year - 543 if year >= 2400 else year

def parse_thai_date(text: str) -> date | None:
    value = normalize_text(text)
    match = re.search(r"(\d{1,2})\s+([ก-๙]+)\s+(\d{4})", value)
    if not match:
        return None
    day = int(match.group(1))
    month = THAI_MONTHS.get(match.group(2))
    if month is None:
        return None
    year = thai_be_year_to_ce(int(match.group(3)))
    return date(year, month, day)

def extract_first_thai_date(text: str) -> date | None:
    for line in normalize_text(text).split(" "):
        _ = line
    return parse_thai_date(text)

def is_total_label(value: Any) -> bool:
    text = canonical_entity_name(value)
    return text in {"รวม", "รวมทั้งสิ้น", "รวมทั้งหมด", "ร้อยละ"} or text.startswith("รวม")

def fiscal_year_from_filename(filename: str) -> tuple[int | None, int | None]:
    match = re.search(r"(25\d{2}|20\d{2})", filename)
    if not match:
        return None, None
    raw = int(match.group(1))
    if raw >= 2500:
        return thai_be_year_to_ce(raw), raw
    return raw, raw + 543