import json
import re
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend.models.dsr_item import DSRItem
from backend.services.gemini_service import GeminiService

DEFAULT_SSR_PATH = Path(__file__).parents[2] / "knowledge_base" / "PWD Civil SSR_2022-23_Final.pdf"


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("₹", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _extract_json_payload(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\[.*\]|\{.*\})\s*```", text, re.S | re.I)
    if match:
        text = match.group(1)
    elif text.startswith("[") or text.startswith("{"):
        pass
    else:
        # Try to extract the first JSON array seen in the answer
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        else:
            raise ValueError("No JSON payload found in Gemini response")
    return json.loads(text)


def _fallback_parse_pdf_rows(pdf_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    import fitz

    doc = fitz.open(pdf_path)
    rows: List[Dict[str, Any]] = []
    unit_pattern = re.compile(
        r"^(One|Per)\s+(Square|Cubic|Running|Number|Kilogram|Litre|Metre|Meter|Set|Job)",
        re.I,
    )

    def is_integer_line(value: str) -> bool:
        return bool(re.fullmatch(r"\d{1,4}", value))

    def first_numeric_value(value: str) -> float | None:
        match = re.search(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", value)
        return _safe_float(match.group(0)) if match else None

    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for idx, line in enumerate(lines):
            # A real row starts with the serial number and is followed by a
            # chapter name, unlike the numeric rate/labour columns.
            if not is_integer_line(line) or idx + 3 >= len(lines) or is_integer_line(lines[idx + 1]):
                continue
            item_idx = next(
                (
                    pos
                    for pos in range(idx + 2, min(idx + 5, len(lines)))
                    if re.fullmatch(r"\d+\.\d+[a-z]?", lines[pos], re.I)
                ),
                None,
            )
            if item_idx is None:
                continue
            unit_idx = next(
                (
                    pos
                    for pos in range(item_idx + 2, len(lines) - 1)
                    if unit_pattern.match(lines[pos])
                    and (
                        first_numeric_value(lines[pos + 1]) is not None
                        or (
                            lines[pos + 1].lower() in {"meter", "metre", "meterr"}
                            and pos + 2 < len(lines)
                            and first_numeric_value(lines[pos + 2]) is not None
                        )
                    )
                ),
                None,
            )
            if unit_idx is None:
                continue
            rate_idx = unit_idx + 1
            if first_numeric_value(lines[rate_idx]) is None:
                rate_idx += 1
            if rate_idx is None:
                continue

            item_no = lines[item_idx]
            chapter = " ".join(lines[idx + 1:item_idx - 1]).strip()
            description = " ".join(lines[item_idx + 2:unit_idx]).strip()
            rate = first_numeric_value(lines[rate_idx])
            unit = lines[unit_idx]
            if rate_idx > unit_idx + 1:
                unit = f"{unit} {lines[unit_idx + 1]}"
            unit = unit.replace("Meterr", "Metre").replace("Metres", "Metre")
            if not description or len(description) < 12 or rate is None or rate <= 0:
                continue
            rows.append({
                "item_no": item_no,
                "chapter": chapter,
                "description": description,
                "unit": unit,
                "rate": rate,
                "source": "SSR PDF",
                "page": page_no,
            })
        if len(rows) >= limit:
            break
    return rows[:limit]


def import_ssr_pdf_to_db(db: Session, pdf_path: str | None = None, limit: int = 100) -> Dict[str, Any]:
    path = pdf_path or str(DEFAULT_SSR_PATH)
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    # Try Gemini extraction first; fallback to simple extraction if unavailable.
    try:
        service = GeminiService()
        response = service.ask(
            (
                "Extract only structured DSR/SSR rate rows from this document. "
                "Return a JSON array of objects with keys: item_no, chapter, description, unit, rate, source, page. "
                "Keep only the most important civil construction items and rate rows. "
                "Do not include explanations. "
                "If a row has no clear rate, skip it. "
                f"Return at most {limit} rows."
            ),
            str(p),
        )
        items = _extract_json_payload(response)
    except Exception:
        items = _fallback_parse_pdf_rows(str(p), limit=limit)

    # Reimporting replaces prior PDF-derived rows. This prevents an earlier
    # parser run from leaving unusable records that win keyword matching.
    db.query(DSRItem).filter(DSRItem.source == "SSR PDF").delete(synchronize_session=False)
    db.commit()

    inserted = 0
    updated = 0
    seen = set()
    for item in items:
        item_no = _clean_text(item.get("item_no"))
        description = _clean_text(item.get("description"))
        if not description and not item_no:
            continue
        # Deduplicate by item_no or description
        key = (item_no or description).lower()
        if key in seen:
            continue
        seen.add(key)

        row = db.query(DSRItem).filter((DSRItem.item_no == item_no) | (DSRItem.description == description)).first()
        if row is None:
            row = DSRItem(
                item_no=item_no or None,
                chapter=_clean_text(item.get("chapter")) or "SSR",
                description=description or "Imported SSR item",
                unit=_clean_text(item.get("unit")) or "unit",
                rate=_safe_float(item.get("rate")),
                source=_clean_text(item.get("source")) or "SSR PDF",
                page=int(item.get("page")) if item.get("page") is not None else None,
            )
            db.add(row)
            inserted += 1
        else:
            if row.rate is None and _safe_float(item.get("rate")) is not None:
                row.rate = _safe_float(item.get("rate"))
            if not row.unit and _clean_text(item.get("unit")):
                row.unit = _clean_text(item.get("unit"))
            if not row.source:
                row.source = _clean_text(item.get("source")) or row.source
            updated += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "source_pdf": str(p), "total_rows": len(items)}
