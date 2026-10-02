from io import BytesIO

from openpyxl import load_workbook

from backend.services.excel_export import HEADERS, boq_to_excel_bytes


def _load(items):
    data = boq_to_excel_bytes(items, {"project_name": "Class IV formula check", "estimate_type": "Repair & Maintenance"})
    return load_workbook(BytesIO(data), data_only=False)["Class IV"]


def test_export_matches_class_iv_headers_and_long_description_section():
    long_description = "Excavation for foundation in earth, soil of all types, sand, gravel and soft murum, including removing excavated material and preparing the foundation bed."
    sheet = _load([{
        "sr_no": 1, "work_category": "Foundation", "subcategory": "Foundation excavation", "dsr_item_no": "21.02",
        "description": long_description, "quantity": 31.5, "unit": "cum", "dsr_rate": 207, "amount": 6520.5,
        "dsr_unit_matches": True,
        "calculation": {"formula": "count * length * width * depth", "inputs": {"component_count": 1, "length": 21, "width": 1.5, "depth": 1}},
    }])
    assert sheet.title == "Class IV"
    assert [sheet.cell(7, column).value for column in range(1, 12)] == HEADERS[:11]
    assert sheet["C8"].value == long_description
    assert sheet["H9"].value == "=D9*E9*F9*G9"
    assert sheet["H10"].value == "=SUM(H9:H9)"
    assert sheet["H11"].value == "=ROUNDUP(H10,0)"
    assert sheet["K11"].value == '=IF(OR(H11="",J11=""),"",H11*J11)'
    assert sheet["K13"].value == "=SUM(K11)"
    assert sheet["D9"].fill.fgColor.rgb.endswith("FFF8E1")
    assert sheet["J11"].fill.fgColor.rgb.endswith("FFF8E1")
    assert sheet.parent.sheetnames == ["Class IV"]
    assert sheet.parent.calculation.calcMode == "auto"


def test_same_dsr_item_groups_measurement_lines_then_say_and_rate():
    common = {"work_category": "Foundation", "subcategory": "Foundation excavation", "dsr_item_no": "21.02", "description": "Foundation excavation", "unit": "cum", "dsr_rate": 207, "dsr_unit_matches": True}
    items = [
        {**common, "sr_no": 1, "quantity": 31.5, "amount": 6520.5, "calculation": {"formula": "count * length * width * depth", "inputs": {"component_count": 2, "length": 21, "width": 1.5, "depth": 0.5}}},
        {**common, "sr_no": 2, "quantity": 11.25, "amount": 2328.75, "calculation": {"formula": "count * length * width * depth", "inputs": {"component_count": 2, "length": 7.5, "width": 1.5, "depth": 0.5}}},
    ]
    sheet = _load(items)
    assert sheet["C8"].value == "Foundation excavation"
    assert sheet["H9"].value == "=D9*E9*F9*G9"
    assert sheet["H10"].value == "=D10*E10*F10*G10"
    assert sheet["H11"].value == "=SUM(H9:H10)"
    assert sheet["H12"].value == "=ROUNDUP(H11,0)"
    assert sheet["J12"].value == 207
    assert sheet["K12"].value == '=IF(OR(H12="",J12=""),"",H12*J12)'


def test_slab_thickness_drives_quantity_in_measurement_line():
    sheet = _load([{
        "sr_no": 1, "work_category": "RCC", "subcategory": "Roof slab concrete", "dsr_item_no": "25.11",
        "description": "Providing and laying RCC slab concrete.", "unit": "cum", "dsr_rate": 7104, "amount": 319680,
        "calculation": {"formula": "length * width * thickness", "inputs": {"length": 20, "width": 15, "thickness": 0.15, "component_count": 1}},
    }])
    assert sheet["G9"].value == 0.15
    assert sheet["H9"].value == "=D9*E9*F9*G9"


def test_opening_count_and_area_drive_opening_quantity():
    sheet = _load([{
        "sr_no": 1, "work_category": "Doors & Windows", "subcategory": "Window openings", "dsr_item_no": "W1",
        "description": "Providing and fixing windows.", "quantity": 6, "unit": "sqm", "dsr_rate": 100, "amount": 600,
        "dsr_unit_matches": True,
        "calculation": {"formula": "sum(width * height * count)", "inputs": {"count": 2, "area": 6}},
    }])
    assert sheet["D9"].value == 2
    assert sheet["L9"].value == 3
    assert sheet["H9"].value == "=D9*L9"


def test_wall_masonry_quantity_formula_references_opening_deduction():
    sheet = _load([{
        "sr_no": 1, "work_category": "Superstructure", "subcategory": "Wall masonry", "dsr_item_no": "27.01",
        "description": "Providing burnt brick masonry.", "quantity": 22.6458, "unit": "cum", "dsr_rate": 100, "amount": 2264.58,
        "dsr_unit_matches": True,
        "calculation": {"formula": "net wall volume", "inputs": {"component_count": 2, "perimeter": 70, "thickness": 0.23, "height": 3, "openings_area": 8.4, "opening_volume": 1.932}},
    }])
    assert sheet["D9"].value == 2
    assert sheet["E9"].value == 70
    assert sheet["F9"].value == 0.23
    assert sheet["G9"].value == 3
    assert sheet["L9"].value == 8.4
    assert sheet["H9"].value == "=D9*MAX(E9*F9*G9-L9*F9,0)"


def test_staircase_formula_uses_steps_riser_tread_and_waist():
    sheet = _load([{
        "sr_no": 1, "work_category": "RCC", "subcategory": "Staircase concrete", "dsr_item_no": "25.11",
        "description": "RCC staircase concrete.", "quantity": 5.46, "unit": "cum", "dsr_rate": 100, "amount": 546,
        "dsr_unit_matches": True,
        "calculation": {"formula": "stair and waist slab", "inputs": {"component_count": 1, "horizontal_run": 4.2, "width": 1.5, "steps": 15, "riser": 0.16, "tread": 0.28, "waist_thickness": 0.15}},
    }])
    assert sheet["O9"].value == 15
    assert sheet["P9"].value == 0.16
    assert sheet["Q9"].value == 0.28
    assert sheet["R9"].value == 0.15
    assert sheet["H9"].value == "=D9*((F9*O9*P9*Q9/2)+(F9*SQRT(E9^2+(O9*P9)^2)*R9))"
