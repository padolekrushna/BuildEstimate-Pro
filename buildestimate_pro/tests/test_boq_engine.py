from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.base import Base
from backend.models.dsr_item import DSRItem
from backend.models.dsr_labour import DSRLabour
from backend.models.dsr_material import DSRMaterial
from backend.models.estimate_run import EstimateRun
from backend.models.opening import Opening
from backend.models.project import Project
from backend.models.room import Room
from backend.services.boq_engine import generate_boq_for_project


def test_new_building_boq_deducts_openings_and_scales_room_count():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        project = Project(name="Measured new building", estimate_type="New Building", project_type="New Building")
        session.add(project)
        session.flush()
        foundation = Room(project_id=project.id, name="Foundation", length=5, width=4, height=1, count=1)
        wall = Room(project_id=project.id, name="Wall masonry", length=18, width=0.23, height=3, count=2)
        session.add_all([foundation, wall])
        session.flush()
        session.add_all([
            Opening(room_id=wall.id, type="door", width=0.9, height=2.1, count=1),
            Opening(room_id=wall.id, type="window", width=1.2, height=1.2, count=2),
        ])
        session.add_all([
            DSRItem(item_no="27.01", chapter="Brick Masonry", description="Second class burnt brick masonry", unit="One Cubic Metre", rate=100, source="test"),
            DSRItem(item_no="36.01", chapter="Painting", description="Internal wall painting", unit="One Square Metre", rate=5, source="test"),
            DSRItem(item_no="32.01", chapter="Plaster", description="Internal cement plaster", unit="One Square Metre", rate=10, source="test"),
            DSRItem(item_no="33.01", chapter="Flooring", description="Vitrified tile flooring", unit="One Square Metre", rate=50, source="test"),
        ])
        session.commit()

        result = generate_boq_for_project(session, project.id)["boq"]
        by_label = {item["subcategory"]: item for item in result}
        assert by_label["Wall masonry"]["quantity"] == 22.6458
        assert by_label["Wall masonry"]["dsr_unit_matches"] is True
        assert by_label["Plaster"]["quantity"] == 196.92
        assert by_label["Internal wall painting"]["quantity"] == 98.46
        assert by_label["Flooring"]["quantity"] == 20.0
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_repair_boq_scales_room_count_and_filters_selected_work():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        project = Project(name="Measured repair", estimate_type="Repair & Maintenance", context_json='{"works":["Internal wall painting"]}')
        session.add(project)
        session.flush()
        room = Room(project_id=project.id, name="Hall", length=5, width=4, height=3, count=2)
        session.add(room)
        session.flush()
        session.add(Opening(room_id=room.id, type="door", width=0.9, height=2.1, count=1))
        session.add(DSRItem(item_no="36.01", chapter="Painting", description="Internal wall painting", unit="One Square Metre", rate=50, source="test"))
        session.commit()

        boq = generate_boq_for_project(session, project.id)["boq"]
        assert [item["work_category"] for item in boq] == ["Painting"]
        assert boq[0]["quantity"] == 104.22
        assert boq[0]["amount"] == 5211.0
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
