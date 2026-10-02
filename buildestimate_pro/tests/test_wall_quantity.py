from backend.services.calculation_engine.wall import calculate_wall_volume


def test_wall_volume_no_openings():
    res = calculate_wall_volume(2.0, 3.0, 0.2, openings_volume=0.0)
    # 2*3*0.2 = 1.2
    assert round(res["quantity"], 6) == 1.2


def test_wall_with_openings_volume():
    res = calculate_wall_volume(5.0, 3.0, 0.23, openings_volume=0.5)
    gross = 5.0 * 3.0 * 0.23
    expected = round(gross - 0.5, 6)
    assert round(res["quantity"], 6) == expected
