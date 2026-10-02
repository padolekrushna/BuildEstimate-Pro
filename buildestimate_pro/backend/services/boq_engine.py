import json
from typing import Any, Dict

from backend.models.dsr_item import DSRItem
from backend.models.project import Project
from backend.models.room import Room
from backend.services.calculation_engine.new_building import (
    calculate_dpc,
    calculate_floor_area,
    calculate_formwork,
    calculate_foundation_excavation,
    calculate_footings,
    calculate_reinforcement,
    calculate_service_quantity,
    calculate_slab_rcc,
    calculate_staircase,
    calculate_wall_masonry,
)
from backend.services.calculation_engine.painting import (
    calculate_perimeter_wall_area,
    calculate_room_wall_area,
)


def _rate_unit_matches(item, quantity_unit: str) -> bool:
    if not item or not item.unit:
        return False
    unit = item.unit.lower().replace(" ", "")
    aliases = {
        "sqm": ("squaremetre", "squaremeter", "sqm", "sq.m"),
        "cum": ("cubicmetre", "cubicmeter", "cum", "cu.m"),
        "kg": ("kilogram", "kg"),
        "nos": ("number", "nos", "no."),
        "points": ("point", "number", "nos", "no."),
    }
    return any(alias.replace(" ", "") in unit for alias in aliases.get(quantity_unit, (quantity_unit.lower(),)))


def _find_dsr_match(db, keyword: str) -> Dict[str, Any]:
    candidates = db.query(DSRItem).filter(
        DSRItem.description.ilike(f"%{keyword}%") | DSRItem.chapter.ilike(f"%{keyword}%")
    ).all()
    if not candidates:
        return {"item": None, "confidence": 0.0, "approval_required": True}

    def score(item):
        text = (item.description or "").lower()
        chapter = (item.chapter or "").lower()
        value = 10 if item.rate is not None else 0
        if keyword == "paint":
            value += 100 * ("painting" in text)
            value += 80 * any(term in text for term in ("internal wall", "emulsion", "distemper", "white wash"))
            value += 100 * (item.item_no or "").startswith(("35.", "36.", "51."))
        elif keyword == "floor":
            value += 100 * ("flooring" in text)
            value += 80 * any(term in text for term in ("tile", "vitrified", "kota", "marble"))
        elif keyword == "plaster":
            value += 100 * ("plaster" in text)
            value += 80 * any(term in text for term in ("internal cement plaster", "external cement plaster", "wall plaster"))
        elif keyword == "masonry":
            value += 140 * any(term in text for term in ("brick masonry", "brick work", "block masonry"))
            value += 80 * (item.item_no or "").startswith(("27.", "29."))
        elif keyword == "concrete":
            value += 140 * any(term in text for term in ("reinforcement cement concrete", "r.c.c", "rcc"))
            value += 80 * (item.item_no or "").startswith(("25.", "26."))
        elif keyword in {"door", "window"}:
            value += 80 * any(term in text for term in ("shutter", "frame", "aluminium", "wooden"))
            value += 100 * ("shutter" in text if keyword == "door" else "sliding window" in text)
        elif keyword == "reinforcement" and any(term in text for term in ("reinforcement", "steel bar", "tmt")):
            value += 100
        elif keyword == "formwork" and any(term in text for term in ("formwork", "centering", "shuttering")):
            value += 100
        elif keyword in {"electrical", "plumbing"} and keyword in text:
            value += 100
        if "antitermite" in text:
            value -= 100
        if "information pillar" in text or "road" in chapter:
            value -= 120
        return value

    ranked = sorted(candidates, key=score, reverse=True)
    best = ranked[0]
    best_score = score(best)
    runner_up = score(ranked[1]) if len(ranked) > 1 else 0
    confidence = round(min(0.99, max(0.25, 0.55 + (best_score - runner_up) / 200)), 2)
    return {"item": best, "confidence": confidence, "approval_required": confidence < 0.8}


def _append_item(boq, match, calculation, category, subcategory, sr):
    calculation = dict(calculation)
    calculation["inputs"] = {**calculation.get("inputs", {}), "component_name": calculation.get("inputs", {}).get("component_name", subcategory)}
    item = match.get("item") if isinstance(match, dict) else match
    confidence = match.get("confidence", 0.5) if isinstance(match, dict) else 0.5
    approval_required = match.get("approval_required", True) if isinstance(match, dict) else True
    compatible = _rate_unit_matches(item, calculation["unit"])
    rate = float(item.rate) if item and item.rate is not None and compatible else None
    quantity = calculation["quantity"]
    boq.append({
        "sr_no": sr,
        "work_category": category,
        "subcategory": subcategory,
        "dsr_item_no": item.item_no if item else None,
        "description": item.description if item else f"{subcategory} (rate unavailable)",
        "calculation": calculation,
        "quantity": quantity,
        "unit": calculation["unit"],
        "dsr_rate": rate,
        "amount": quantity * rate if rate is not None else None,
        "source": item.source if item else "DSR unavailable",
        "dsr_unit": item.unit if item else None,
        "dsr_unit_matches": compatible,
        "dsr_confidence": confidence if compatible else 0.0,
        "dsr_approval_required": approval_required or not compatible,
        "dsr_approved": False,
    })


def _scale_calculation(calculation, count):
    count = float(count or 1)
    result = dict(calculation)
    result["quantity"] = round(float(result["quantity"]) * count, 4)
    result["inputs"] = {**result.get("inputs", {}), "component_count": count}
    result["formula"] = f"{count:g} * ({result['formula']})"
    return result


def _openings(room):
    return [
        {"type": opening.type.lower(), "width": opening.width, "height": opening.height, "count": opening.count}
        for opening in getattr(room, "openings", [])
    ]


def generate_new_building_boq(db, rooms):
    boq = []
    rates = {key: _find_dsr_match(db, key) for key in (
        "excavation", "concrete", "masonry", "floor", "plaster", "paint",
        "reinforcement", "formwork", "electrical", "plumbing", "door", "window",
    )}
    sequence = 1
    formwork_area = 0.0
    rcc_volume = 0.0
    measured_openings = []
    wall_room = None
    foundation = None

    def add(match, calculation, category, label):
        nonlocal sequence
        _append_item(boq, match, calculation, category, label, sequence)
        sequence += 1

    for room in rooms:
        name = (room.name or "").lower()
        count = float(room.count or 1)
        openings = _openings(room)
        measured_openings.extend(openings)
        opening_area = sum(item["width"] * item["height"] * item["count"] for item in openings)

        if "foundation" in name:
            foundation = room
            add(rates["excavation"], _scale_calculation(calculate_foundation_excavation(room.length, room.width, room.height), count), "Foundation", "Foundation excavation")
        elif "footing" in name:
            calculation = calculate_footings(count, room.length, room.width, room.height)
            add(rates["concrete"], calculation, "Foundation", "RCC isolated footings")
            rcc_volume += calculation["quantity"]
            formwork_area += 2 * (room.length + room.width) * room.height * count
        elif "column" in name:
            calculation = _scale_calculation(calculate_slab_rcc(room.length, room.width, room.height), count)
            add(rates["concrete"], calculation, "RCC", "RCC columns")
            rcc_volume += calculation["quantity"]
            formwork_area += 2 * (room.length + room.width) * room.height * count
        elif "beam" in name:
            calculation = _scale_calculation(calculate_slab_rcc(room.length, room.width, room.height), count)
            add(rates["concrete"], calculation, "RCC", "RCC beams")
            rcc_volume += calculation["quantity"]
            formwork_area += (2 * room.width + room.height) * room.length * count
        elif "dpc" in name:
            add(rates["concrete"], _scale_calculation(calculate_dpc(room.length, room.width, room.height), count), "Plinth", "Damp proof course")
        elif "wall" in name:
            wall_room = room
            calculation = _scale_calculation(calculate_wall_masonry(room.length, room.width, room.height, opening_area), count)
            add(rates["masonry"], calculation, "Superstructure", "Wall masonry")
        elif "slab" in name:
            calculation = _scale_calculation(calculate_slab_rcc(room.length, room.width, room.height), count)
            add(rates["concrete"], calculation, "RCC", "Roof slab concrete")
            rcc_volume += calculation["quantity"]
            formwork_area += room.length * room.width * count
        elif "stair" in name:
            details = json.loads(room.details_json or "{}")
            steps = float(details.get("steps", 0))
            if steps > 0:
                calculation = calculate_staircase(
                    room.length, room.width, steps,
                    float(details.get("riser", 0.16)),
                    float(details.get("tread", 0.28)),
                    float(details.get("waist_thickness", 0.15)),
                )
                calculation = _scale_calculation(calculation, count)
                add(rates["concrete"], calculation, "RCC", "Staircase concrete")
                rcc_volume += calculation["quantity"]
                formwork_area += room.width * calculation["inputs"]["slope_length"] * count
        elif "electrical point" in name:
            add(rates["electrical"], calculate_service_quantity(count, "points", "measured electrical point count"), "Services", "Electrical points")
        elif "plumbing point" in name:
            add(rates["plumbing"], calculate_service_quantity(count, "points", "measured plumbing point count"), "Services", "Plumbing points")

    if foundation:
        add(rates["floor"], _scale_calculation(calculate_floor_area(foundation.length, foundation.width), foundation.count or 1), "Finishes", "Flooring")
    if wall_room:
        openings = _openings(wall_room)
        opening_area = sum(item["width"] * item["height"] * item["count"] for item in openings)
        wall_count = float(wall_room.count or 1)
        for faces, label, matcher in ((2, "Plaster", rates["plaster"]), (1, "Internal wall painting", rates["paint"])):
            calculation = calculate_perimeter_wall_area(wall_room.length, wall_room.height, opening_area, faces=faces)
            calculation["quantity"] = round(calculation["quantity"] * wall_count, 4)
            calculation["inputs"]["component_count"] = wall_count
            add(matcher, calculation, "Finishes", label)

    if rcc_volume > 0:
        calculation = calculate_reinforcement(rcc_volume)
        calculation["assumptions"] = ["Indicative 80 kg/cum allowance only; verify against approved structural reinforcement schedules."]
        add(rates["reinforcement"], calculation, "RCC", "Reinforcement steel")
    if formwork_area > 0:
        add(rates["formwork"], calculate_formwork(formwork_area), "Formwork", "Total formwork")

    for kind in ("door", "window"):
        matching = [item for item in measured_openings if item["type"] == kind]
        count = sum(item["count"] for item in matching)
        area = sum(item["width"] * item["height"] * item["count"] for item in matching)
        if count:
            calculation = {"quantity": round(area, 4), "unit": "sqm", "formula": "sum(width * height * count)", "inputs": {"count": count, "area": round(area, 4)}}
            add(rates[kind], calculation, "Openings", kind.title())

    return {"boq": boq, "materials": [], "labour": []}


def _generate_repair_boq(db, rooms, project):
    boq = []
    rates = {key: _find_dsr_match(db, key) for key in ("paint", "floor", "plaster", "door", "window")}
    sequence = 1
    for room in rooms:
        count = float(room.count or 1)
        openings = _openings(room)
        paint = _scale_calculation(calculate_room_wall_area(room.length, room.width, room.height, openings, faces=1), count)
        paint["inputs"]["location"] = room.name
        _append_item(boq, rates["paint"], paint, "Painting", "Internal wall painting", sequence)
        sequence += 1
        floor = _scale_calculation(calculate_floor_area(room.length, room.width), count)
        floor["inputs"]["location"] = room.name
        _append_item(boq, rates["floor"], floor, "Flooring", "Flooring", sequence)
        sequence += 1
        plaster = _scale_calculation(calculate_room_wall_area(room.length, room.width, room.height, openings, faces=1), count)
        plaster["inputs"]["location"] = room.name
        _append_item(boq, rates["plaster"], plaster, "Plaster", "Internal plaster", sequence)
        sequence += 1

        for kind in ("door", "window"):
            matching = [opening for opening in openings if opening["type"] == kind]
            opening_count = sum(opening["count"] for opening in matching) * count
            opening_area = sum(opening["width"] * opening["height"] * opening["count"] for opening in matching) * count
            if opening_count:
                calculation = {"quantity": round(opening_area, 4), "unit": "sqm", "formula": "sum(width * height * count) * room_count", "inputs": {"count": opening_count, "area": round(opening_area, 4), "room_count": count}}
                calculation["inputs"]["location"] = room.name
                _append_item(boq, rates[kind], calculation, "Doors & Windows", kind.title() + " openings", sequence)
                sequence += 1

    if project and project.context_json:
        selected_works = {str(work).lower() for work in json.loads(project.context_json).get("works", [])}
        if selected_works:
            category_terms = {
                "Painting": ("paint",),
                "Plaster": ("plaster",),
                "Flooring": ("floor", "tile", "marble", "granite", "kota"),
                "Doors & Windows": ("door", "window", "ventilator", "grill"),
            }
            boq = [row for row in boq if any(any(term in work for term in category_terms[row["work_category"]]) for work in selected_works)]
    return {"boq": boq, "materials": [], "labour": []}


def generate_boq_for_project(db, project_id: int) -> Dict[str, Any]:
    rooms = db.query(Room).filter(Room.project_id == project_id).all()
    project = db.query(Project).filter(Project.id == project_id).first()
    if project and project.estimate_type == "New Building":
        return generate_new_building_boq(db, rooms)
    return _generate_repair_boq(db, rooms, project)
