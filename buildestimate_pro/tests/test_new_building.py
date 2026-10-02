from backend.services.calculation_engine.new_building import (
    calculate_dpc,
    calculate_formwork,
    calculate_foundation_excavation,
    calculate_footings,
    calculate_reinforcement,
    calculate_slab_rcc,
    calculate_staircase,
    calculate_wall_masonry,
)


def test_foundation_excavation_quantity():
    result = calculate_foundation_excavation(20, 15, 1.2)
    assert result["quantity"] == 360.0
    assert result["unit"] == "cum"


def test_wall_masonry_quantity():
    result = calculate_wall_masonry(70, 0.23, 3)
    assert result["quantity"] == 48.3


def test_slab_rcc_quantity():
    result = calculate_slab_rcc(20, 15, 0.15)
    assert result["quantity"] == 45.0


def test_reinforcement_and_formwork_quantities():
    assert calculate_reinforcement(45, 80)["quantity"] == 3600.0
    assert calculate_formwork(120)["quantity"] == 120.0


def test_detailed_staircase_quantity():
    result = calculate_staircase(4, 1.5, 10)
    assert result["quantity"] == 5.4612
    assert result["inputs"]["slope_length"] == 4.272


def test_footing_and_dpc_quantities():
    assert calculate_footings(4, 1.5, 1.5, 0.3)["quantity"] == 2.7
    assert calculate_dpc(70, 0.23, 0.05)["quantity"] == 0.805


def test_masonry_deducts_door_and_window_opening_volume():
    result = calculate_wall_masonry(70, 0.23, 3, openings_area=8.4)
    assert result["quantity"] == 46.368