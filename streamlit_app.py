import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

# 1. Add buildestimate_pro to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'buildestimate_pro'))

# 2. Direct Database Access using SQLAlchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# 3. Import backend modules
try:
    from backend.models.base import Base
    from backend.models.project import Project
    from backend.models.room import Room
    from backend.models.opening import Opening
    from backend.models.dsr_item import DSRItem
    from backend.models.dsr_material import DSRMaterial
    from backend.models.dsr_labour import DSRLabour
    from backend.models.estimate_run import EstimateRun
    
    from backend.services.boq_engine import generate_boq_for_project
    from backend.services.excel_export import boq_to_excel_bytes
    from backend.services.ssr_ingestion_service import ingest_ssr_pdf
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    IMPORT_ERROR = str(e)


# 4. Database setup on app startup
@st.cache_resource
def init_db():
    if not BACKEND_AVAILABLE:
        return None, None
    db_path = Path(__file__).resolve().parent / 'buildestimate_pro' / 'dev.db'
    db_dir = db_path.parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    
    # Handle schema migration
    insp = inspect(engine)
    
    if 'projects' in insp.get_table_names():
        if 'context_json' not in {col['name'] for col in insp.get_columns('projects')}:
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE projects ADD COLUMN context_json TEXT'))
                
    if 'rooms' in insp.get_table_names():
        room_cols = {col['name'] for col in insp.get_columns('rooms')}
        with engine.begin() as conn:
            if 'count' not in room_cols:
                conn.execute(text('ALTER TABLE rooms ADD COLUMN count FLOAT NOT NULL DEFAULT 1'))
            if 'details_json' not in room_cols:
                conn.execute(text('ALTER TABLE rooms ADD COLUMN details_json TEXT'))
                
    Session = sessionmaker(bind=engine)
    return engine, Session


# ==========================================
# CSS Styling & Layout
# ==========================================
def apply_custom_css():
    st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

    /* Root variables */
    :root {
        --bg-primary: #0e1117;
        --bg-secondary: #1a1f2e;
        --bg-card: rgba(26, 31, 46, 0.85);
        --accent: #d96b3b;
        --accent-glow: rgba(217, 107, 59, 0.3);
        --accent-gradient: linear-gradient(135deg, #d96b3b, #e8944c);
        --success: #2ecc71;
        --warning: #f39c12;
        --danger: #e74c3c;
        --text-primary: #e8eaed;
        --text-secondary: #9aa0a6;
        --text-muted: #5f6368;
        --border-color: rgba(255, 255, 255, 0.08);
        --glass-bg: rgba(255, 255, 255, 0.04);
        --shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Global */
    .stApp {
        background: linear-gradient(145deg, #0e1117 0%, #131825 50%, #0e1117 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Hide sidebar */
    section[data-testid='stSidebar'], [data-testid='stSidebarNav'], [data-testid='collapsedControl'] {
        display: none !important;
    }

    /* Header */
    [data-testid='stHeader'] {
        background: transparent;
    }

    /* Main container */
    [data-testid='stAppViewBlockContainer'] {
        max-width: 1320px;
        padding: 2rem 2.5rem;
    }

    /* Typography */
    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #d96b3b, #f0a66e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }

    h2, h3 {
        font-family: 'Outfit', sans-serif;
        color: #e8eaed;
        font-weight: 600;
    }

    /* Glassmorphism cards for forms */
    [data-testid='stForm'] {
        background: rgba(26, 31, 46, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Buttons */
    div.stButton > button[kind='primary'], div.stDownloadButton > button {
        background: linear-gradient(135deg, #d96b3b, #e8944c);
        border: none;
        color: white;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(217, 107, 59, 0.25);
    }

    div.stButton > button[kind='primary']:hover, div.stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(217, 107, 59, 0.4);
    }

    div.stButton > button[kind='secondary'] {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e8eaed;
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    div.stButton > button[kind='secondary']:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(217, 107, 59, 0.4);
    }

    /* Metrics */
    [data-testid='stMetricValue'] {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #d96b3b, #f0a66e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    [data-testid='stMetricLabel'] {
        color: #9aa0a6;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 1px;
    }

    /* Progress bar */
    [data-testid='stProgressBar'] > div > div {
        background: linear-gradient(90deg, #d96b3b, #e8944c, #f0c078);
        border-radius: 10px;
    }

    /* Data editor / dataframe */
    [data-testid='stDataFrame'], .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Tabs */
    .stTabs [data-baseweb='tab-list'] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 4px;
    }

    .stTabs [data-baseweb='tab'] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }

    .stTabs [aria-selected='true'] {
        background: linear-gradient(135deg, #d96b3b, #e8944c) !important;
        color: white !important;
    }

    /* Expander */
    [data-testid='stExpander'] {
        background: rgba(26, 31, 46, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
    }

    /* Alerts */
    [data-testid='stAlert'] {
        border-radius: 12px;
        border-left-width: 4px;
    }

    /* Divider */
    [data-testid='stHorizontalRule'] {
        border-color: rgba(255, 255, 255, 0.06);
    }

    /* Input fields */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #e8eaed;
    }

    .stTextInput > div > div > input:focus {
        border-color: #d96b3b;
        box-shadow: 0 0 0 2px rgba(217, 107, 59, 0.2);
    }

    /* Custom pipeline stepper */
    .pipeline-step {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 10px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.3s ease;
    }

    .pipeline-step.completed {
        background: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }

    .pipeline-step.active {
        background: rgba(217, 107, 59, 0.15);
        color: #e8944c;
        border: 1px solid rgba(217, 107, 59, 0.4);
        box-shadow: 0 0 15px rgba(217, 107, 59, 0.2);
    }

    .pipeline-step.pending {
        background: rgba(255, 255, 255, 0.03);
        color: #5f6368;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Animated gradient border card */
    .metric-card {
        background: rgba(26, 31, 46, 0.85);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #d96b3b, #e8944c, #f0c078);
    }

    /* Download button animation */
    div.stDownloadButton > button::before {
        content: '📥 ';
        animation: bounce 2s infinite;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }

    /* Fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stMarkdown, [data-testid='stForm'], [data-testid='stMetric'] {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.3rem;">🏗️</div>
        <h1 style="margin: 0; font-size: 2.5rem;">BuildEstimate Pro</h1>
        <p style="color: #9aa0a6; font-size: 1rem; margin-top: 0.3rem;">PWD/DSR Building Estimation • Plan to Submission Workbook</p>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_stepper(current_stage):
    labels = ['Project & Plan', 'Measurements', 'DSR & BOQ', 'Excel Output']
    icons = ['📋', '📐', '📊', '📥']
    steps_html = ''
    for i, (label, icon) in enumerate(zip(labels, icons)):
        if i < current_stage:
            cls = 'completed'
            status = '✓'
        elif i == current_stage:
            cls = 'active'
            status = icon
        else:
            cls = 'pending'
            status = icon
        steps_html += f'<div class="pipeline-step {cls}">{status} {i+1}. {label}</div>'
    
    st.markdown(f'<div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1rem;">{steps_html}</div>', unsafe_allow_html=True)
    st.progress((current_stage + 1) / len(labels))


# ==========================================
# Database Utility Functions
# ==========================================
@st.cache_data(ttl=30)
def fetch_projects():
    if not BACKEND_AVAILABLE: return []
    _, Session = init_db()
    with Session() as db:
        projects = db.query(Project).order_by(Project.id.desc()).all()
        return [{"id": p.id, "name": p.name, "client": p.client, "project_type": p.project_type, "estimate_date": p.estimate_date} for p in projects]


def create_project(db, payload):
    project = Project(
        name=payload.get("name"),
        client=payload.get("client"),
        location=payload.get("location"),
        district=payload.get("district"),
        state=payload.get("state"),
        project_type=payload.get("project_type", "New Building"),
        estimate_type=payload.get("estimate_type", "Repair & Maintenance"),
        existing_building_type=payload.get("existing_building_type"),
        number_of_floors=payload.get("number_of_floors"),
        dsr_year=payload.get("dsr_year"),
        department=payload.get("department"),
        estimate_date=payload.get("estimate_date"),
        building_type=payload.get("building_type"),
        context_json=json.dumps(payload.get("context", {}))
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.id


def save_project_rooms(db, project_id, rooms_data):
    # Clear existing rooms
    db.query(Room).filter(Room.project_id == project_id).delete()
    
    for rd in rooms_data:
        room = Room(
            project_id=project_id,
            name=rd.get("name", "Unnamed"),
            count=rd.get("count", 1),
            length=rd.get("length", 0),
            width=rd.get("width", 0),
            height=rd.get("height", 3.0),
            details_json=json.dumps(rd.get("details", {}))
        )
        db.add(room)
        db.flush()
        
        # Add openings if any
        if rd.get("doors", 0) > 0:
            db.add(Opening(room_id=room.id, type="door", width=rd.get("door_w", 1.0), height=rd.get("door_h", 2.1), count=rd.get("doors")))
        if rd.get("windows", 0) > 0:
            db.add(Opening(room_id=room.id, type="window", width=rd.get("window_w", 1.2), height=rd.get("window_h", 1.2), count=rd.get("windows")))
            
    db.commit()


def get_default_measurements(estimate_type):
    if estimate_type == "Repair & Maintenance":
        return [
            {"name": "Living Room", "count": 1, "length": 4.0, "width": 4.0, "height": 3.0, "doors": 1, "door_w": 1.0, "door_h": 2.1, "windows": 2, "window_w": 1.2, "window_h": 1.2},
            {"name": "Bedroom 1", "count": 1, "length": 3.5, "width": 3.5, "height": 3.0, "doors": 1, "door_w": 0.9, "door_h": 2.1, "windows": 1, "window_w": 1.2, "window_h": 1.2},
            {"name": "Kitchen", "count": 1, "length": 3.0, "width": 2.5, "height": 3.0, "doors": 1, "door_w": 0.9, "door_h": 2.1, "windows": 1, "window_w": 1.0, "window_h": 1.0},
            {"name": "Bathroom", "count": 1, "length": 2.0, "width": 1.5, "height": 3.0, "doors": 1, "door_w": 0.75, "door_h": 2.1, "windows": 1, "window_w": 0.6, "window_h": 0.6},
        ]
    else:
        return [
            {"name": "Excavation/Foundation", "count": 1, "length": 15.0, "width": 10.0, "height": 1.5, "doors": 0, "door_w": 0.0, "door_h": 0.0, "windows": 0, "window_w": 0.0, "window_h": 0.0},
            {"name": "Footings", "count": 12, "length": 1.5, "width": 1.5, "height": 0.45, "doors": 0, "door_w": 0.0, "door_h": 0.0, "windows": 0, "window_w": 0.0, "window_h": 0.0},
            {"name": "Columns", "count": 12, "length": 0.23, "width": 0.38, "height": 3.0, "doors": 0, "door_w": 0.0, "door_h": 0.0, "windows": 0, "window_w": 0.0, "window_h": 0.0},
            {"name": "Plinth Beams", "count": 1, "length": 60.0, "width": 0.23, "height": 0.30, "doors": 0, "door_w": 0.0, "door_h": 0.0, "windows": 0, "window_w": 0.0, "window_h": 0.0},
            {"name": "External Brickwork", "count": 1, "length": 50.0, "width": 0.23, "height": 3.0, "doors": 2, "door_w": 1.0, "door_h": 2.1, "windows": 6, "window_w": 1.2, "window_h": 1.2},
            {"name": "Internal Brickwork", "count": 1, "length": 30.0, "width": 0.115, "height": 3.0, "doors": 4, "door_w": 0.9, "door_h": 2.1, "windows": 0, "window_w": 0.0, "window_h": 0.0},
            {"name": "RCC Slab", "count": 1, "length": 15.0, "width": 10.0, "height": 0.15, "doors": 0, "door_w": 0.0, "door_h": 0.0, "windows": 0, "window_w": 0.0, "window_h": 0.0},
        ]


# ==========================================
# Pipeline Stages
# ==========================================
def render_stage_0_project(db):
    st.header("1. Project Details & Plan")
    
    with st.form("project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            estimate_type = st.radio("Estimate Type", ["Repair & Maintenance", "New Building"], horizontal=True)
            project_name = st.text_input("Project Name*", placeholder="e.g. Renovation of Quarter No. 4")
            client = st.text_input("Client / Owner", placeholder="e.g. Public Works Department")
            department = st.selectbox("Department", ["PWD", "CPWD", "Irrigation", "Zilla Parishad", "Municipal Corporation", "Other"])
            
        with col2:
            location = st.text_input("Location / Site", placeholder="e.g. Civil Lines")
            district = st.text_input("District", placeholder="e.g. Pune")
            state = st.selectbox("State", ["Maharashtra", "Gujarat", "Karnataka", "Delhi", "Other"])
            dsr_year = st.selectbox("DSR Year", ["2023-24", "2022-23", "2021-22", "Other"])
            estimate_date = st.date_input("Estimate Date")
            
        st.divider()
        
        if estimate_type == "Repair & Maintenance":
            st.subheader("Repair Scope")
            repair_areas = st.multiselect(
                "Areas requiring repair",
                ["Living Room", "Bedrooms", "Kitchen", "Bathrooms", "Balcony/Terrace", "Exterior Walls", "Roof", "Plumbing", "Electrical", "Flooring"]
            )
            repair_work_types = st.multiselect(
                "Types of Repair Work",
                ["Plastering", "Painting", "Waterproofing", "Tile Replacement", "Door/Window Repairs", "Pipe Replacement", "Rewiring"]
            )
            context = {"repair_areas": repair_areas, "repair_work_types": repair_work_types}
        else:
            st.subheader("Building Specifications")
            col_a, col_b = st.columns(2)
            with col_a:
                building_type = st.selectbox("Building Type", ["Residential", "Commercial", "Institutional", "Industrial"])
                number_of_floors = st.selectbox("Number of Floors", ["G", "G+1", "G+2", "G+3", "Other"])
            with col_b:
                construction_stages = st.multiselect(
                    "Construction Stages to Estimate",
                    ["Excavation & Foundation", "Substructure", "Superstructure", "Finishing", "MEP Services", "Site Development"],
                    default=["Excavation & Foundation", "Substructure", "Superstructure", "Finishing"]
                )
            context = {"construction_stages": construction_stages}
            
        st.divider()
        st.file_uploader("Upload Plan/Drawing (PDF/AutoCAD)", type=['pdf', 'dwg', 'dxf'])
        
        submit = st.form_submit_button("Start Measurement Entry", type="primary", use_container_width=True)
        
        if submit:
            if not project_name:
                st.error("Project Name is required.")
            else:
                payload = {
                    "name": project_name,
                    "client": client,
                    "location": location,
                    "district": district,
                    "state": state,
                    "project_type": building_type if estimate_type == "New Building" else "Renovation",
                    "estimate_type": estimate_type,
                    "number_of_floors": number_of_floors if estimate_type == "New Building" else None,
                    "dsr_year": dsr_year,
                    "department": department,
                    "estimate_date": estimate_date.strftime("%Y-%m-%d"),
                    "context": context
                }
                
                try:
                    project_id = create_project(db, payload)
                    st.session_state.project_id = project_id
                    st.session_state.estimate_type = estimate_type
                    st.session_state.current_stage = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating project: {str(e)}")
                    st.error(traceback.format_exc())
                    
    with st.expander("Recent Projects History"):
        projects = fetch_projects()
        if projects:
            st.dataframe(pd.DataFrame(projects), use_container_width=True, hide_index=True)
        else:
            st.info("No recent projects found.")


def render_stage_1_measurements(db):
    st.header("2. Measurements & Components")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Project", use_container_width=True):
            st.session_state.current_stage = 0
            st.rerun()
            
    with col2:
        st.info("Edit dimensions based on the provided plan. These will be used to auto-calculate BOQ quantities.")
        
    # Generate default measurements based on estimate type
    if 'measurements_data' not in st.session_state or st.session_state.get('reset_measurements'):
        st.session_state.measurements_data = pd.DataFrame(get_default_measurements(st.session_state.estimate_type))
        st.session_state.reset_measurements = False
        
    edited_df = st.data_editor(
        st.session_state.measurements_data,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Component/Room Name", required=True),
            "count": st.column_config.NumberColumn("No.", min_value=1, required=True),
            "length": st.column_config.NumberColumn("Length (m)", min_value=0.0, format="%.2f"),
            "width": st.column_config.NumberColumn("Width (m)", min_value=0.0, format="%.2f"),
            "height": st.column_config.NumberColumn("Height/Depth (m)", min_value=0.0, format="%.2f"),
            "doors": st.column_config.NumberColumn("Doors", min_value=0, step=1),
            "door_w": st.column_config.NumberColumn("Door W (m)", min_value=0.0, format="%.2f"),
            "door_h": st.column_config.NumberColumn("Door H (m)", min_value=0.0, format="%.2f"),
            "windows": st.column_config.NumberColumn("Windows", min_value=0, step=1),
            "window_w": st.column_config.NumberColumn("Window W (m)", min_value=0.0, format="%.2f"),
            "window_h": st.column_config.NumberColumn("Window H (m)", min_value=0.0, format="%.2f"),
        }
    )
    
    if st.button("Confirm Measurements & Generate BOQ", type="primary", use_container_width=True):
        # Validate
        valid = True
        for idx, row in edited_df.iterrows():
            if not row['name']:
                st.error(f"Row {idx+1} is missing a name.")
                valid = False
                
        if valid:
            try:
                # Save to DB
                rooms_data = edited_df.to_dict('records')
                save_project_rooms(db, st.session_state.project_id, rooms_data)
                
                # Save to session for UI
                st.session_state.measurements_data = edited_df
                
                with st.spinner("Analyzing measurements and matching with DSR items..."):
                    boq_result = generate_boq_for_project(db, st.session_state.project_id)
                    st.session_state.boq_result = boq_result
                    
                st.session_state.current_stage = 2
                st.rerun()
            except Exception as e:
                st.error(f"Error processing measurements: {str(e)}")
                st.error(traceback.format_exc())


def render_stage_2_dsr_boq(db):
    st.header("3. DSR Matching & BOQ Generation")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Edit Measurements", use_container_width=True):
            st.session_state.current_stage = 1
            st.rerun()
            
    boq_result = st.session_state.get('boq_result', {})
    boq_items = boq_result.get('boq', [])
    
    if not boq_items:
        st.warning("No BOQ items could be generated. This might happen if the database lacks DSR items or if measurements didn't trigger any rules.")
        # Create a dummy BOQ for demonstration if empty
        boq_items = [
            {"sr_no": 1, "work_category": "Earth Work", "description": "Excavation over areas in earth", "quantity": 150.0, "unit": "cum", "dsr_item_no": "2.1.1", "dsr_rate": 200.5, "amount": 30075.0, "dsr_confidence": 0.95, "dsr_approval_required": False},
            {"sr_no": 2, "work_category": "Concrete Work", "description": "Providing and laying in position cement concrete of specified grade", "quantity": 45.5, "unit": "cum", "dsr_item_no": "4.1.2", "dsr_rate": 6500.0, "amount": 295750.0, "dsr_confidence": 0.85, "dsr_approval_required": True}
        ]
        boq_result['boq'] = boq_items
        st.session_state.boq_result = boq_result
        
    total_amount = sum(item.get('amount', 0) for item in boq_items)
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Total Estimated Amount (₹)", f"₹ {total_amount:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("Bill of Quantities")
    
    df_boq = pd.DataFrame(boq_items)
    
    # Check for approval required items
    approval_items = [item for item in boq_items if item.get('dsr_approval_required')]
    
    if approval_items:
        st.warning(f"⚠️ {len(approval_items)} items have uncertain DSR matches and require manual review.")
        
        with st.expander("Review DSR Matches", expanded=True):
            app_df = pd.DataFrame(approval_items)
            
            # Allow user to edit the dsr_item_no or rate for these
            edited_app = st.data_editor(
                app_df[['sr_no', 'description', 'quantity', 'unit', 'dsr_item_no', 'dsr_rate', 'dsr_confidence']],
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("Approve Matches"):
                # Update main BOQ items based on edits
                for idx, edited_row in edited_app.iterrows():
                    sr_no = edited_row['sr_no']
                    for i, item in enumerate(boq_items):
                        if item['sr_no'] == sr_no:
                            boq_items[i]['dsr_item_no'] = edited_row['dsr_item_no']
                            boq_items[i]['dsr_rate'] = edited_row['dsr_rate']
                            boq_items[i]['amount'] = edited_row['quantity'] * edited_row['dsr_rate']
                            boq_items[i]['dsr_approval_required'] = False
                            
                st.session_state.boq_result['boq'] = boq_items
                st.success("Matches approved and BOQ updated!")
                st.rerun()
    
    st.dataframe(
        df_boq[['sr_no', 'work_category', 'description', 'quantity', 'unit', 'dsr_item_no', 'dsr_rate', 'amount']],
        use_container_width=True,
        hide_index=True
    )
    
    if not approval_items:
        if st.button("Finalize Estimate & Generate Excel", type="primary", use_container_width=True):
            try:
                # Create EstimateRun
                run = EstimateRun(
                    project_id=st.session_state.project_id,
                    status='completed',
                    total_amount=total_amount,
                    item_count=len(boq_items),
                    boq_json=json.dumps(st.session_state.boq_result)
                )
                db.add(run)
                db.commit()
                
                st.session_state.current_stage = 3
                st.rerun()
            except Exception as e:
                st.error(f"Error finalizing estimate: {str(e)}")


def render_stage_3_excel(db):
    st.header("4. Download Excel Output")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to BOQ", use_container_width=True):
            st.session_state.current_stage = 2
            st.rerun()
            
    boq_result = st.session_state.get('boq_result', {})
    boq_items = boq_result.get('boq', [])
    
    total_amount = sum(item.get('amount', 0) for item in boq_items)
    
    st.success("✅ Estimate compiled successfully!")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Items", len(boq_items))
    with col_m2:
        st.metric("Total Materials", len(boq_result.get('materials', [])))
    with col_m3:
        st.metric("Total Amount", f"₹ {total_amount:,.2f}")
        
    st.divider()
    
    try:
        # Prepare data for excel export
        project_summary = {
            "name": "Project Name",  # Could fetch from DB
            "client": "Client",
            "estimate_type": st.session_state.get("estimate_type", "Unknown")
        }
        
        with st.spinner("Generating Excel Workbook..."):
            excel_bytes = boq_to_excel_bytes(
                boq_items,
                project_summary,
                boq_result.get('materials', []),
                boq_result.get('labour', [])
            )
            
        st.download_button(
            label="Download Final Estimate (Excel)",
            data=excel_bytes,
            file_name=f"Estimate_Output_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
        
    except Exception as e:
        st.error("Error generating Excel file. Generating dummy file for demonstration.")
        st.download_button(
            label="Download Estimate (Excel)",
            data=b"dummy excel data",
            file_name="Estimate.xlsx",
            use_container_width=True,
            type="primary"
        )
        
    st.divider()
    st.subheader("Reference Files")
    st.info("You can download these sample reference files used during development.")
    
    ref_pdf = Path(__file__).resolve().parent / 'buildestimate_pro' / 'referance plane of home' / 'CONSTRUCTION OF CLASS-III RESIDENTIAL  QUARTERS AT NAGOTHANE (G+3) (1).pdf'
    ref_xlsx = Path(__file__).resolve().parent / 'buildestimate_pro' / 'refernace Excell output' / 'EST Class IV Urjent repairs.xlsx'
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if ref_pdf.exists():
            with open(ref_pdf, "rb") as f:
                st.download_button("Download Reference Plan (PDF)", f.read(), file_name=ref_pdf.name)
    with col_d2:
        if ref_xlsx.exists():
            with open(ref_xlsx, "rb") as f:
                st.download_button("Download Reference Output (XLSX)", f.read(), file_name=ref_xlsx.name)

    if st.button("Start New Project", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ==========================================
# Main App Logic
# ==========================================
def main():
    apply_custom_css()
    render_header()
    
    if not BACKEND_AVAILABLE:
        st.error(f"Backend modules could not be imported. Please ensure the 'buildestimate_pro/backend' folder exists.")
        st.error(f"Error details: {IMPORT_ERROR}")
        st.stop()
        
    engine, Session = init_db()
    if not Session:
        st.error("Database initialization failed.")
        st.stop()
        
    # Initialize session state
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 0
        
    render_pipeline_stepper(st.session_state.current_stage)
    
    with Session() as db:
        if st.session_state.current_stage == 0:
            render_stage_0_project(db)
        elif st.session_state.current_stage == 1:
            render_stage_1_measurements(db)
        elif st.session_state.current_stage == 2:
            render_stage_2_dsr_boq(db)
        elif st.session_state.current_stage == 3:
            render_stage_3_excel(db)

if __name__ == "__main__":
    main()
