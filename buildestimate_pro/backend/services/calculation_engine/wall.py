from typing import Dict, Any


def calculate_wall_volume(length: float, height: float, thickness: float, openings_volume: float = 0.0) -> Dict[str, Any]:
    """Calculate wall masonry volume: L x H x T - openings_volume

    thickness in meters; length/height in meters; openings_volume in cubic meters
    """
    gross = length * height * thickness
    net = max(gross - float(openings_volume or 0.0), 0.0)
    return {
        "quantity": round(net, 6),
        "unit": "cum",
        "formula": "length * height * thickness - openings_volume",
        "inputs": {"length": length, "height": height, "thickness": thickness, "openings_volume": openings_volume},
        "assumptions": [],
    }
