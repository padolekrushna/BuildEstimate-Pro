from typing import Dict, Any


def calculate_foundation_excavation(length: float, width: float, depth: float) -> Dict[str, Any]:
    quantity = max(float(length), 0.0) * max(float(width), 0.0) * max(float(depth), 0.0)
    return {"quantity": round(quantity, 4), "unit": "cum", "formula": "length * width * depth", "inputs": {"length": length, "width": width, "depth": depth}}


def calculate_wall_masonry(perimeter: float, thickness: float, height: float, openings_area: float = 0.0) -> Dict[str, Any]:
    gross = max(float(perimeter), 0.0) * max(float(thickness), 0.0) * max(float(height), 0.0)
    opening_volume = max(float(openings_area), 0.0) * max(float(thickness), 0.0)
    quantity = max(gross - opening_volume, 0.0)
    return {"quantity": round(quantity, 4), "unit": "cum", "formula": "max(perimeter * wall_thickness * wall_height - openings_area * wall_thickness, 0)", "inputs": {"perimeter": perimeter, "thickness": thickness, "height": height, "openings_area": openings_area, "opening_volume": round(opening_volume, 4)}}

def calculate_footings(count: float, length: float, width: float, depth: float) -> Dict[str, Any]:
    quantity = max(float(count), 0.0) * max(float(length), 0.0) * max(float(width), 0.0) * max(float(depth), 0.0)
    return {"quantity": round(quantity, 4), "unit": "cum", "formula": "count * footing_length * footing_width * footing_depth", "inputs": {"count": count, "length": length, "width": width, "depth": depth}, "assumptions": ["Footing count and sizes must be confirmed against structural drawings."]}


def calculate_dpc(perimeter: float, width: float, thickness: float = 0.05) -> Dict[str, Any]:
    quantity = max(float(perimeter), 0.0) * max(float(width), 0.0) * max(float(thickness), 0.0)
    return {"quantity": round(quantity, 4), "unit": "cum", "formula": "perimeter * dpc_width * dpc_thickness", "inputs": {"perimeter": perimeter, "width": width, "thickness": thickness}}


def calculate_slab_rcc(length: float, width: float, thickness: float) -> Dict[str, Any]:
    quantity = max(float(length), 0.0) * max(float(width), 0.0) * max(float(thickness), 0.0)
    return {"quantity": round(quantity, 4), "unit": "cum", "formula": "length * width * thickness", "inputs": {"length": length, "width": width, "thickness": thickness}}


def calculate_floor_area(length: float, width: float) -> Dict[str, Any]:
    quantity = max(float(length), 0.0) * max(float(width), 0.0)
    return {"quantity": round(quantity, 4), "unit": "sqm", "formula": "length * width", "inputs": {"length": length, "width": width}}


def calculate_reinforcement(concrete_volume: float, steel_per_cum: float = 80.0) -> Dict[str, Any]:
    quantity = max(float(concrete_volume), 0.0) * max(float(steel_per_cum), 0.0)
    return {"quantity": round(quantity, 2), "unit": "kg", "formula": "concrete_volume * steel_per_cum", "inputs": {"concrete_volume": concrete_volume, "steel_per_cum": steel_per_cum}}


def calculate_formwork(area: float) -> Dict[str, Any]:
    return {"quantity": round(max(float(area), 0.0), 4), "unit": "sqm", "formula": "formwork_area", "inputs": {"formwork_area": area}}


def calculate_staircase(length: float, width: float, steps: float, riser: float = 0.15, tread: float = 0.30, waist_thickness: float = 0.15) -> Dict[str, Any]:
    implied_run = max(float(steps), 0.0) * max(float(tread), 0.0)
    horizontal = max(float(length), 0.0) or implied_run
    stair_width = max(float(width), 0.0)
    total_rise = max(float(steps), 0.0) * max(float(riser), 0.0)
    step_volume = stair_width * horizontal * total_rise / 2
    waist_slope_length = (horizontal**2 + total_rise**2) ** 0.5
    waist_volume = stair_width * waist_slope_length * max(float(waist_thickness), 0.0)
    concrete = step_volume + waist_volume
    assumptions = []
    if length > 0 and implied_run > 0 and abs(horizontal - implied_run) / max(horizontal, implied_run) > 0.05:
        assumptions.append("Measured stair run differs from steps multiplied by tread; verify staircase geometry.")
    return {"quantity": round(concrete, 4), "unit": "cum", "formula": "(width * horizontal_run * total_rise / 2) + (width * slope_length * waist_thickness)", "inputs": {"width": width, "steps": steps, "riser": riser, "tread": tread, "waist_thickness": waist_thickness, "horizontal_run": round(horizontal, 4), "implied_run_from_treads": round(implied_run, 4), "total_rise": round(total_rise, 4), "slope_length": round(waist_slope_length, 4)}, "assumptions": assumptions}


def calculate_service_quantity(count: float, unit: str, formula: str) -> Dict[str, Any]:
    return {"quantity": round(max(float(count), 0.0), 4), "unit": unit, "formula": formula, "inputs": {"count": count}, "assumptions": ["Confirm this point count against approved electrical/plumbing drawings."]}