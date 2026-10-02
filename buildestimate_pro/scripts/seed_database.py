"""Seed the database with demo DSR items and a sample project."""
from backend.database import engine, SessionLocal
from backend.models.base import Base
from backend.models.dsr_item import DSRItem
from backend.models.project import Project
from backend.models.room import Room
from backend.models.opening import Opening


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Add demo DSR items
        existing = db.query(DSRItem).count()
        if existing == 0:
            demo = [
                DSRItem(item_no="PA-001", chapter="Painting", description="Internal wall painting with emulsion (per sqm)", unit="sqm", rate=25.0, source="DEMO DSR", page=1),
                DSRItem(item_no="PL-010", chapter="Plaster", description="12 mm cement plaster (per sqm)", unit="sqm", rate=150.0, source="DEMO DSR", page=2),
                DSRItem(item_no="FL-001", chapter="Flooring", description="Tile flooring 600x600 (per sqm)", unit="sqm", rate=450.0, source="DEMO DSR", page=3),
            ]
            db.add_all(demo)
            db.commit()

        # Add sample project
        if db.query(Project).count() == 0:
            p = Project(name="Demo Project", client="Client Demo", location="Demoville")
            db.add(p)
            db.commit()
            # add sample rooms
            r1 = Room(project_id=p.id, name="Hall", length=5.0, width=4.0, height=3.0)
            r2 = Room(project_id=p.id, name="Kitchen", length=4.0, width=3.0, height=3.0)
            r3 = Room(project_id=p.id, name="Bedroom 1", length=4.0, width=4.0, height=3.0)
            db.add_all([r1, r2, r3])
            db.commit()
            # add openings: doors and windows
            db.add_all([
                Opening(room_id=r1.id, type="door", width=0.9, height=2.1, count=1),
                Opening(room_id=r1.id, type="window", width=1.5, height=1.2, count=2),
                Opening(room_id=r2.id, type="door", width=0.9, height=2.1, count=1),
                Opening(room_id=r2.id, type="window", width=1.2, height=1.0, count=1),
                Opening(room_id=r3.id, type="door", width=0.9, height=2.1, count=1),
                Opening(room_id=r3.id, type="window", width=1.5, height=1.2, count=1),
            ])
            db.commit()
            # Add demo material & labour decomposition for FL-001 (tile flooring)
            fl_item = db.query(DSRItem).filter(DSRItem.item_no == 'FL-001').first()
            if fl_item:
                from backend.models.dsr_material import DSRMaterial
                from backend.models.dsr_labour import DSRLabour
                # Example: per sqm tile flooring requires 0.01 cum cement, 0.03 cum sand
                m1 = DSRMaterial(dsr_item_id=fl_item.id, material="Cement", quantity=0.01, unit="cum")
                m2 = DSRMaterial(dsr_item_id=fl_item.id, material="Sand", quantity=0.03, unit="cum")
                db.add_all([m1, m2])
                # Labour: mason hours per sqm
                l1 = DSRLabour(dsr_item_id=fl_item.id, labour_type="Mason", quantity=0.2, unit="man-hr")
                db.add(l1)
                db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seeding complete. Run the backend and frontend as in README.")
