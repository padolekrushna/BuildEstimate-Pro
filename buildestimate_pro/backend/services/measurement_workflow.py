from typing import List, Dict, Any


def build_default_measurements(project_name: str, estimate_type: str) -> List[Dict[str, Any]]:
    if estimate_type == "New Building":
        return [
            {"Component": "Foundation", "Length_m": 20.0, "Width_m": 15.0, "Depth_m": 1.2, "Qty": 360.0, "Unit": "m³", "Source": "Plan"},
            {"Component": "Wall masonry", "Length_m": 70.0, "Width_m": 0.23, "Depth_m": 3.0, "Qty": 48.30, "Unit": "m³", "Source": "Plan"},
            {"Component": "Slab", "Length_m": 20.0, "Width_m": 15.0, "Depth_m": 0.15, "Qty": 45.0, "Unit": "m³", "Source": "Plan"},
            {"Component": "Staircase", "Length_m": 4.0, "Width_m": 1.5, "Depth_m": 2.8, "Qty": 16.8, "Unit": "m³", "Source": "Plan"},
        ]

    return [
        {"Room": "Hall", "Length_m": 5.4, "Width_m": 4.2, "Height_m": 3.0, "Area_m2": 22.68, "Source": "Plan"},
        {"Room": "Kitchen", "Length_m": 4.2, "Width_m": 3.1, "Height_m": 3.0, "Area_m2": 13.02, "Source": "Plan"},
        {"Room": "Bedroom 1", "Length_m": 4.0, "Width_m": 3.6, "Height_m": 3.0, "Area_m2": 14.4, "Source": "Plan"},
        {"Room": "Bathroom", "Length_m": 2.4, "Width_m": 1.8, "Height_m": 3.0, "Area_m2": 4.32, "Source": "Plan"},
        {"Room": "Exterior Wall", "Length_m": 24.0, "Width_m": 0.23, "Height_m": 3.0, "Area_m2": 16.56, "Source": "Plan"},
    ]
