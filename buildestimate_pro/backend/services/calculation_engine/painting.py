from typing import List, Dict, Any


def calculate_painting_area(walls: List[Dict[str, Any]], coats: int = 1) -> Dict[str, Any]:
    """Calculate net paintable area for a list of walls.

    Each wall: {"length": float, "height": float, "openings": [{"width":..., "height":...}, ...]}
    Returns structured result with quantity, unit, formula and breakdown.
    """
    total = 0.0
    breakdown = []
    for w in walls:
        L = float(w.get("length", 0.0))
        H = float(w.get("height", 0.0))
        gross = L * H
        openings = 0.0
        for o in w.get("openings", []):
            openings += (
                float(o.get("width", 0.0))
                * float(o.get("height", 0.0))
                * int(o.get("count", 1) or 1)
            )
        net = max(gross - openings, 0.0)
        total += net
        breakdown.append({"length": L, "height": H, "gross": gross, "openings": openings, "net": net})

    quantity = total * max(1, coats)
    return {
        "quantity": round(quantity, 4),
        "unit": "sqm",
        "formula": "sum(wall_length*wall_height) - sum(openings)",
        "breakdown": breakdown,
        "coats": coats,
        "assumptions": [],
    }


def calculate_room_wall_area(length: float, width: float, height: float, openings: List[Dict[str, Any]], faces: int = 1, coats: int = 1) -> Dict[str, Any]:
    """Calculate net wall area without assigning openings to an arbitrary wall."""
    perimeter = 2 * (float(length) + float(width))
    gross_one_face = perimeter * float(height)
    opening_area = sum(
        float(item.get("width", 0.0))
        * float(item.get("height", 0.0))
        * int(item.get("count", 1) or 1)
        for item in openings
    )
    faces = max(int(faces), 1)
    net = max(gross_one_face - opening_area, 0.0) * faces
    coats = max(int(coats), 1)
    return {
        "quantity": round(net * coats, 4),
        "unit": "sqm",
        "formula": "max(2*(length+width)*height - opening_area, 0) * faces * coats",
        "inputs": {"length": length, "width": width, "height": height, "opening_area": round(opening_area, 4), "faces": faces, "coats": coats},
        "gross_area": round(gross_one_face * faces, 4),
        "deducted_openings_area": round(opening_area * faces, 4),
    }

def calculate_perimeter_wall_area(perimeter: float, height: float, openings_area: float = 0.0, faces: int = 1, coats: int = 1) -> Dict[str, Any]:
    gross_one_face = max(float(perimeter), 0.0) * max(float(height), 0.0)
    opening_area = max(float(openings_area), 0.0)
    faces = max(int(faces), 1)
    coats = max(int(coats), 1)
    net_one_face = max(gross_one_face - opening_area, 0.0)
    quantity = net_one_face * faces * coats
    return {
        "quantity": round(quantity, 4),
        "unit": "sqm",
        "formula": "max(perimeter * height - openings_area, 0) * faces * coats",
        "inputs": {"perimeter": perimeter, "height": height, "openings_area": opening_area, "faces": faces, "coats": coats},
        "gross_area": round(gross_one_face * faces, 4),
        "deducted_openings_area": round(opening_area * faces, 4),
    }
