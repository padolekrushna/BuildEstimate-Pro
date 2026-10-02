from backend.services.calculation_engine.painting import calculate_painting_area, calculate_perimeter_wall_area, calculate_room_wall_area


def test_simple_wall_no_openings():
    walls = [{"length": 5.0, "height": 3.0, "openings": []}]
    res = calculate_painting_area(walls, coats=1)
    assert res["quantity"] == 15.0
    assert res["unit"] == "sqm"


def test_wall_with_openings():
    walls = [{"length": 5.0, "height": 3.0, "openings": [{"width": 0.9, "height": 2.1}, {"width": 1.5, "height": 1.2}]}]
    res = calculate_painting_area(walls, coats=1)
    # gross 15 - openings 1.89 - 1.8 = 11.31
    assert round(res["quantity"], 2) == 11.31


def test_wall_with_multiple_openings_uses_count():
    walls = [{"length": 5.0, "height": 3.0, "openings": [{"width": 1.2, "height": 1.2, "count": 2}]}]
    res = calculate_painting_area(walls, coats=1)
    assert round(res["quantity"], 2) == 12.12


def test_room_net_wall_area_deducts_all_openings_without_clamping_a_single_wall():
    result = calculate_room_wall_area(
        5, 4, 3,
        [{"width": 1, "height": 2, "count": 2}, {"width": 1.5, "height": 1.2, "count": 2}],
    )
    assert result["quantity"] == 46.4


def test_perimeter_wall_finishes_deduct_opening_area_per_face():
    result = calculate_perimeter_wall_area(70, 3, openings_area=5, faces=2)
    assert result["quantity"] == 410
