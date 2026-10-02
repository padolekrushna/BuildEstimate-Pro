from backend.services.measurement_workflow import build_default_measurements


def test_default_measurements_include_repair_rooms():
    rows = build_default_measurements("Demo Repair", "Repair & Maintenance")
    room_names = {row["Room"] for row in rows}
    assert "Hall" in room_names
    assert any(float(row["Area_m2"]) > 0 for row in rows)


def test_default_measurements_include_new_building_components():
    rows = build_default_measurements("Demo New Building", "New Building")
    component_names = {row["Component"] for row in rows}
    assert "Foundation" in component_names
    assert "Slab" in component_names
