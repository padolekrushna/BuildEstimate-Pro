import os
import re
import sys
import requests
import streamlit as st
from pathlib import Path
import pandas as pd

MAX_UPLOAD_SIZE_MB = 200
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
PROJECT_TYPES = ["New Building", "Repair & Maintenance", "Renovation", "Existing Structure", "Industrial / Utility"]
REFERENCE_PDF = Path(__file__).resolve().parent.parent / "referance plane of home" / "CONSTRUCTION OF CLASS-III RESIDENTIAL  QUARTERS AT NAGOTHANE (G+3) (1).pdf"
REFERENCE_XLSX = Path(__file__).resolve().parent.parent / "refernace Excell output" / "EST Class IV Urjent repairs.xlsx"

st.set_page_config(page_title="BuildEstimate Pro", page_icon="🏗️", layout="wide")
st.markdown(
    """
    <style>
    :root { --ink: #18323a; --muted: #60747a; --accent: #d96b3b; --soft: #f4eee7; --line: #dfd8cf; }
    .stApp { background: linear-gradient(135deg, #fbfaf7 0%, #f2f6f2 100%); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    section[data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stAppViewBlockContainer"] { max-width: 1280px; padding-left: 2rem; padding-right: 2rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    h1 { font-weight: 750; }
    [data-testid="stProgressBar"] > div > div { background: var(--accent); }
    [data-testid="stForm"] { border: 1px solid var(--line); border-radius: 10px; padding: 1.25rem 1.5rem; background: rgba(255,255,255,.72); }
    [data-testid="stMetricValue"] { color: var(--accent); }
    div.stButton > button[kind="primary"], div.stDownloadButton > button { background: var(--accent); border-color: var(--accent); color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)


def validate_uploaded_file(file_obj):
    if file_obj is None:
        return True, ""

    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if getattr(file_obj, "size", 0) > max_bytes:
        return False, f"File '{file_obj.name}' is too large. Maximum allowed is {MAX_UPLOAD_SIZE_MB} MB per file."
    return True, ""


def build_default_measurements(project_name: str, estimate_type: str):
    """Generate default measurement templates based on estimation type"""
    if estimate_type == "New Building":
        return [
            {"Component": "Foundation", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
            {"Component": "Plinth", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
            {"Component": "Columns", "Length_m": 0, "Width_m": 0, "Height_m": 3.0, "Area_m2": 0, "Qty": 0},
            {"Component": "Beams", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
            {"Component": "Walls", "Length_m": 0, "Width_m": 0, "Height_m": 3.0, "Area_m2": 0, "Qty": 0},
            {"Component": "Slab", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
            {"Component": "Staircase", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
            {"Component": "Doors", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
            {"Component": "Windows", "Length_m": 0, "Width_m": 0, "Height_m": 0, "Area_m2": 0, "Qty": 0},
        ]
    else:  # Repair & Maintenance
        return [
            {"Room": "Hall", "Length_m": 5.0, "Width_m": 4.0, "Height_m": 3.0, "Area_m2": 20.0},
            {"Room": "Kitchen", "Length_m": 3.0, "Width_m": 2.5, "Height_m": 3.0, "Area_m2": 7.5},
            {"Room": "Bedroom 1", "Length_m": 4.0, "Width_m": 3.5, "Height_m": 3.0, "Area_m2": 14.0},
            {"Room": "Bedroom 2", "Length_m": 3.5, "Width_m": 3.0, "Height_m": 3.0, "Area_m2": 10.5},
            {"Room": "Bathroom", "Length_m": 2.5, "Width_m": 2.0, "Height_m": 3.0, "Area_m2": 5.0},
        ]

@st.cache_data(ttl=30)
def fetch_projects():
    try:
        r = requests.get(f"{API_URL}/projects/", timeout=20)
        if r.ok:
            return r.json()
    except Exception:
        return []
    return []


@st.cache_data(ttl=30)
def fetch_dsr_items(q: str = ""):
    try:
        url = f"{API_URL}/dsr/items"
        if q:
            url += f"?q={requests.utils.quote(q)}"
        r = requests.get(url, timeout=20)
        if r.ok:
            return r.json()
    except Exception:
        return []
    return []


def create_project(payload):
    try:
        return requests.post(f"{API_URL}/projects/", json=payload, timeout=20)
    except requests.RequestException as exc:
        st.error(f"Could not connect to the backend at {API_URL}. Start FastAPI and try again. Details: {exc}")
        return None


def import_ssr(limit=20):
    r = requests.post(f"{API_URL}/dsr/import-ssr?limit={limit}", timeout=120)
    return r


def export_boq(project_id):
    return requests.get(f"{API_URL}/projects/{project_id}/export-excel", timeout=120)


def save_project_rooms(project_id: int, rooms_data: list):
    try:
        r = requests.post(f"{API_URL}/projects/{project_id}/rooms", json=rooms_data, timeout=30)
        return r
    except Exception as e:
        st.error(f"Failed to save rooms: {str(e)}")
        return None


def fetch_project_rooms(project_id: int):
    try:
        r = requests.get(f"{API_URL}/projects/{project_id}/rooms", timeout=30)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return []


def fetch_boq_summary(project_id: int):
    try:
        r = requests.get(f"{API_URL}/projects/{project_id}/summary", timeout=30)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


def fetch_boq_items(project_id: int):
    try:
        r = requests.get(f"{API_URL}/projects/{project_id}/boq", timeout=30)
        if r.ok:
            return r.json()
    except requests.RequestException:
        pass
    return []


def fetch_project_history():
    try:
        response = requests.get(f"{API_URL}/projects/history/all", timeout=30)
        if response.ok:
            return response.json()
    except requests.RequestException:
        pass
    return []


def create_estimate_run(project_id: int):
    try:
        return requests.post(f"{API_URL}/projects/{project_id}/runs", timeout=60)
    except requests.RequestException as exc:
        st.error(f"Could not save estimate history: {exc}")
        return None


def save_dsr_approvals(project_id: int, approvals: dict):
    try:
        return requests.post(f"{API_URL}/projects/{project_id}/dsr-approvals", json={"approvals": approvals}, timeout=30)
    except requests.RequestException as exc:
        st.error(f"Could not save DSR approvals: {exc}")
        return None


def sample_measurements():
    estimate_type = st.session_state.get("estimation_type", "Repair & Maintenance")
    return build_default_measurements("Current Project", estimate_type)


def ensure_dataframe(data):
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, dict):
        return pd.DataFrame([data])
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame(data)


def render_repair_workflow():
    st.header("Repair & Maintenance Estimation")
    with st.form("repair_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project name")
            client_name = st.text_input("Client name")
            location = st.text_input("Location")
            district = st.text_input("District")
            state = st.text_input("State")
        with col2:
            existing_building_type = st.text_input("Existing building type")
            number_of_floors = st.text_input("Number of floors")
            dsr_year = st.text_input("Applicable PWD/DSR year", value="PWD SSR 2022-23")
            department = st.text_input("Applicable PWD department/circle")
            estimate_date = st.date_input("Estimate date")

        st.subheader("Upload existing building plan")
        uploaded_plan = st.file_uploader(
            "Upload PDF / JPG / PNG plan",
            type=["pdf", "png", "jpg", "jpeg"],
            help=f"Maximum file size: {MAX_UPLOAD_SIZE_MB} MB per file.",
        )
        if uploaded_plan is not None:
            is_valid, msg = validate_uploaded_file(uploaded_plan)
            if not is_valid:
                st.error(msg)
                uploaded_plan = None

        if REFERENCE_PDF.exists():
            st.caption(f"Reference plan available: {REFERENCE_PDF.name}")

        st.subheader("Select Areas for Repair")
        areas = st.multiselect(
            "Areas",
            ["Hall", "Kitchen", "Bedroom 1", "Bedroom 2", "Bathroom", "Balcony", "Terrace", "External Walls", "Store room", "Office", "Veranda", "Staircase", "Custom area"],
            default=["Kitchen", "Hall"],
        )

        st.subheader("Repair / Maintenance work selection")
        repair_work = {
            "Surface / Painting": [
                "Internal wall painting",
                "External wall painting",
                "Ceiling painting",
                "Primer",
                "Putty",
                "Distemper",
                "Emulsion",
                "Cement paint",
            ],
            "Plaster": [
                "Internal plaster repair",
                "External plaster repair",
                "Ceiling plaster",
                "Complete plaster replacement",
                "Crack repair",
            ],
            "Flooring": [
                "Floor tile replacement",
                "Wall tile replacement",
                "Marble",
                "Granite",
                "Kota",
                "Skirting",
                "Dado",
            ],
            "Doors / Windows": [
                "Door repair",
                "Door replacement",
                "Window repair",
                "Window replacement",
                "Ventilator",
                "Grill",
            ],
            "Plumbing": [
                "Pipe replacement",
                "Sanitary fixture",
                "Tap/fitting",
                "Drainage",
                "Waterproofing",
            ],
            "Electrical": [
                "Wiring",
                "Switch/socket",
                "Light point",
                "Fan point",
                "Fixture",
                "DB/MCB",
            ],
        }
        selected_works = []
        for section_name, options in repair_work.items():
            section_selected = st.multiselect(section_name, options)
            selected_works.extend(section_selected)

        st.subheader("BOQ review")
        review_rows = []
        for item in selected_works:
            review_rows.append({
                "Item": item,
                "Location": ", ".join(areas) if areas else "General",
                "Qty": 1,
                "Unit": "Job",
                "Rate": "DSR",
                "Amount": "Computed from DSR",
            })
        st.dataframe(review_rows, use_container_width=True)

        submitted = st.form_submit_button("Generate repair BOQ")
        if submitted:
            payload = {
                "name": project_name,
                "client": client_name,
                "location": location,
                "district": district,
                "state": state,
                "project_type": "Repair & Maintenance",
                "estimate_type": "Repair & Maintenance",
                "existing_building_type": existing_building_type,
                "number_of_floors": number_of_floors,
                "dsr_year": dsr_year,
                "department": department,
                "estimate_date": str(estimate_date),
                "plan_file_name": uploaded_plan.name if uploaded_plan else (st.session_state.get("ref_plan_name") or "reference_plan.pdf"),
            }
            if project_name:
                result = create_project(payload)
                if result.ok:
                    st.success(f"Repair estimate project '{project_name}' created.")
                    st.session_state["created_project_id"] = result.json().get("id")
                else:
                    st.error(result.text)
            else:
                st.warning("Project name is required.")

        st.subheader("Editable measurement sheet")
        df = st.data_editor(sample_measurements(), use_container_width=True, num_rows="dynamic")
        st.dataframe(df, use_container_width=True)

        if df is not None:
            st.subheader("Repair estimate summary")
            rows = ensure_dataframe(df).to_dict("records")
            for row in rows:
                room = row.get("Room")
                a = float(row.get("Area_m2", 0) or 0)
                if room:
                    st.write(f"- {room}: area {a:.2f} m²")

        if selected_works:
            st.subheader("Selected repair items")
            for item in selected_works:
                st.write(f"• {item}")


def render_new_building_workflow():
    st.header("New Building Construction Estimation")
    with st.form("new_building_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project name", key="nb_project_name")
            client_name = st.text_input("Client", key="nb_client")
            location = st.text_input("Location", key="nb_location")
            district = st.text_input("District", key="nb_district")
            state = st.text_input("State", key="nb_state")
        with col2:
            building_type = st.text_input("Building type")
            floors = st.text_input("Number of floors")
            dsr_year = st.text_input("Applicable DSR year", value="PWD SSR 2022-23")
            department = st.text_input("PWD department/circle")

        st.subheader("Upload building plans")
        uploaded_files = st.file_uploader(
            "Architectural / structural / elevation / section plan files",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help=f"Maximum file size: {MAX_UPLOAD_SIZE_MB} MB per file.",
        )
        if uploaded_files:
            invalid_files = []
            valid_files = []
            for f in uploaded_files:
                is_valid, msg = validate_uploaded_file(f)
                if is_valid:
                    valid_files.append(f)
                else:
                    invalid_files.append(msg)
            uploaded_files = valid_files
            if invalid_files:
                for msg in invalid_files:
                    st.error(msg)
            st.write("Uploaded files:")
            for f in uploaded_files:
                st.write(f"- {f.name}")

        st.subheader("General building information")
        overall_length = st.number_input("Overall building length (m)", value=20.0)
        overall_width = st.number_input("Overall building width (m)", value=15.0)
        floor_height = st.number_input("Floor height (m)", value=3.0)
        wall_thickness = st.number_input("Wall thickness (m)", value=0.23)

        st.subheader("Stage-wise construction breakdown")
        stages = {
            "Site Preparation": ["Site clearance", "Excavation", "Filling", "Disposal", "Compaction"],
            "Foundation": ["Excavation", "PCC", "Footings", "RCC", "Reinforcement", "Formwork", "Foundation masonry", "Waterproofing", "Backfilling"],
            "Plinth": ["Plinth filling", "Plinth beam", "DPC", "PCC", "Waterproofing"],
            "Columns": ["RCC columns", "Reinforcement", "Formwork"],
            "Beams": ["RCC beams", "Reinforcement", "Formwork"],
            "Walls": ["Brick/block masonry", "Internal walls", "External walls"],
            "Lintels / Chajjas": ["RCC lintels", "Chajjas/sunshades"],
            "Slab": ["RCC slab", "Reinforcement", "Formwork"],
            "Staircase": ["RCC staircase", "Reinforcement", "Formwork", "Steps", "Flooring"],
            "Plaster": ["Internal plaster", "External plaster", "Ceiling plaster"],
            "Doors": ["Frames", "Shutters", "Hardware"],
            "Windows": ["Frames", "Shutters", "Glass", "Grills"],
            "Ventilators": ["Frames", "Shutters", "Glass/grill"],
            "Flooring": ["Tiles", "Stone", "Marble", "Granite", "Skirting", "Dado"],
            "Painting": ["Putty", "Primer", "Internal paint", "External paint", "Ceiling paint", "Door/window painting"],
            "Electrical": ["Wiring", "Points", "Switches", "Sockets", "Fixtures", "DB", "MCB", "Earthing"],
            "Plumbing & Sanitary": ["Water supply", "Drainage", "Sanitary fittings", "Pipes", "Fixtures"],
            "External Works": ["Compound wall", "Gate", "Paving", "Drainage"],
        }

        selected_stages = []
        for title, options in stages.items():
            chosen = st.multiselect(title, options)
            selected_stages.extend(chosen)

        calculation_method = st.selectbox("Calculation Method", ["Auto", "Centre Line", "Long Wall–Short Wall", "Manual"])
        submitted = st.form_submit_button("Generate new building BOQ")
        if submitted:
            payload = {
                "name": project_name,
                "client": client_name,
                "location": location,
                "district": district,
                "state": state,
                "project_type": "New Building",
                "estimate_type": "New Building",
                "building_type": building_type,
                "number_of_floors": floors,
                "dsr_year": dsr_year,
                "department": department,
                "plan_file_name": ", ".join(f.name for f in uploaded_files) if uploaded_files else "sample_plan_set.pdf",
            }
            if project_name:
                result = create_project(payload)
                if result.ok:
                    st.success(f"New building project '{project_name}' created with {calculation_method} method.")
                else:
                    st.error(result.text)
            else:
                st.warning("Project name is required.")

        st.subheader("Plan-derived measurements (editable)")
        nb_measurements = build_default_measurements(project_name or "New Building", "New Building")
        edited_nb_measurements = st.data_editor(nb_measurements, use_container_width=True, num_rows="dynamic")
        st.dataframe(edited_nb_measurements, use_container_width=True)

        if selected_stages:
            st.subheader("Selected new building stages")
            for item in selected_stages:
                st.write(f"• {item}")

        st.subheader("New building BOQ review")
        review_rows = []
        for stage in selected_stages:
            review_rows.append({
                "Stage": stage,
                "Component": "Work item",
                "Qty": 1,
                "Unit": "Job",
                "Rate": "DSR",
                "Amount": "Computed from DSR",
            })
        st.dataframe(review_rows, use_container_width=True)

        st.caption("Structural information such as reinforcement schedules and slab detailing may need user confirmation if not available from the plan.")


def render_project_wizard():
    st.header("Select estimation type")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Repair & Maintenance", use_container_width=True):
            st.session_state["estimation_type"] = "Repair & Maintenance"
    with col2:
        if st.button("New Building Construction", use_container_width=True):
            st.session_state["estimation_type"] = "New Building"

    if REFERENCE_PDF.exists():
        if st.button("Use reference plan sample", key="use_reference_plan"):
            st.session_state["ref_plan_name"] = REFERENCE_PDF.name
            st.success(f"Selected reference plan: {REFERENCE_PDF.name}")

    estimation_type = st.session_state.get("estimation_type", "Repair & Maintenance")
    st.write(f"Current selection: **{estimation_type}**")

    if estimation_type == "Repair & Maintenance":
        render_repair_workflow()
    else:
        render_new_building_workflow()


def render_measurement_review():
    st.header("Measurement Review & Room Storage")
    projects = fetch_projects()
    if not projects:
        st.info("Create a project first.")
        return
    
    project_id = st.selectbox("Select project", [p["id"] for p in projects], format_func=lambda pid: next(p["name"] for p in projects if p["id"] == pid))
    project = next((p for p in projects if p["id"] == project_id), None)
    
    st.subheader(f"Project: {project['name']}")
    st.write(f"Type: {project.get('project_type')} | Estimate: {project.get('estimate_type')}")
    
    stored_rooms = fetch_project_rooms(project_id)
    
    if not stored_rooms:
        st.info("No rooms saved yet. Add measurements below.")
        estimate_type = project.get("estimate_type", "Repair & Maintenance")
        default_measurements = build_default_measurements(project["name"], estimate_type)
    else:
        default_measurements = stored_rooms
    
    st.subheader("Edit measurements")
    edited_data = st.data_editor(default_measurements, use_container_width=True, num_rows="dynamic")
    edited_df = ensure_dataframe(edited_data)
    
    if st.button("Save measurements to database"):
        rooms_to_save = [
            {
                "name": row.get("Room") or row.get("Component"),
                "length": float(row.get("Length_m", 0) or 0),
                "width": float(row.get("Width_m", 0) or 0),
                "height": float(row.get("Height_m", 3.0) or 3.0),
            }
            for row in edited_df.to_dict("records")
        ]
        result = save_project_rooms(project_id, rooms_to_save)
        if result and result.ok:
            st.success(result.json().get("message", "Rooms saved successfully!"))
            st.rerun()
        else:
            st.error("Failed to save measurements.")
    
    st.subheader("Measurement summary")
    if edited_data is not None:
        total_area = 0
        for row in ensure_dataframe(edited_data).to_dict("records"):
            area = float(row.get("Area_m2") or row.get("Qty") or 0)
            if area > 0:
                total_area += area
        st.metric("Total area/quantity", f"{total_area:.2f} m²/m³")


def render_boq_summary():
    st.header("BOQ Summary & Cost Sheet")
    projects = fetch_projects()
    if not projects:
        st.info("Create a project first.")
        return
    
    project_id = st.selectbox("Select project", [p["id"] for p in projects], format_func=lambda pid: next(p["name"] for p in projects if p["id"] == pid))
    project = next((p for p in projects if p["id"] == project_id), None)
    
    summary = fetch_boq_summary(project_id)
    if not summary:
        st.error("Could not fetch BOQ summary. Ensure rooms are saved first.")
        return
    
    st.subheader(f"Project: {summary.get('project_name')}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Project Type", summary.get("project_type"))
    with col2:
        st.metric("Total Items", summary.get("total_items", 0))
    with col3:
        st.metric("Est. Total Amount", f"₹ {summary.get('total_amount', 0):.2f}")
    
    st.subheader("Items by category")
    categories = summary.get("items_count_by_category", {})
    for cat, count in categories.items():
        st.write(f"- {cat}: {count} items")


def render_final_export():
    st.header("Final Estimate & Export")
    projects = fetch_projects()
    if not projects:
        st.info("Create a project first.")
        return
    
    project_id = st.selectbox("Select project", [p["id"] for p in projects], format_func=lambda pid: next(p["name"] for p in projects if p["id"] == pid))
    project = next((p for p in projects if p["id"] == project_id), None)
    
    st.subheader(f"Finalize Estimate: {project['name']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Project Details**")
        st.write(f"Type: {project.get('project_type')}")
        st.write(f"Estimation: {project.get('estimate_type')}")
        st.write(f"Client: {project.get('client', 'N/A')}")
        st.write(f"Location: {project.get('location', 'N/A')}")
    
    with col2:
        st.write("**Additional Info**")
        st.write(f"District: {project.get('district', 'N/A')}")
        st.write(f"State: {project.get('state', 'N/A')}")
        st.write(f"DSR Year: {project.get('dsr_year', 'N/A')}")
        st.write(f"Department: {project.get('department', 'N/A')}")
    
    st.subheader("Export Options")
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        if st.button("Generate BOQ Excel (with materials & labour)"):
            resp = export_boq(project_id)
            if resp.ok:
                st.download_button(
                    label="📥 Download BOQ.xlsx",
                    data=resp.content,
                    file_name=f"BOQ_{project['name']}_{project_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.error("Failed to generate BOQ.")
    
    with export_col2:
        if REFERENCE_XLSX.exists():
            with open(REFERENCE_XLSX, "rb") as f:
                st.download_button(
                    label="📥 Download Reference Format",
                    data=f.read(),
                    file_name=f"Reference_{REFERENCE_XLSX.name}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    
    st.divider()
    st.subheader("Reference Files")
    ref_col1, ref_col2 = st.columns(2)
    
    with ref_col1:
        if REFERENCE_PDF.exists():
            st.caption("Reference Plan (PDF)")
            st.write(f"File: {REFERENCE_PDF.name}")
            with open(REFERENCE_PDF, "rb") as f:
                st.download_button(
                    "📄 View Reference Plan",
                    f.read(),
                    file_name=REFERENCE_PDF.name,
                    mime="application/pdf",
                )
    
    with ref_col2:
        if REFERENCE_XLSX.exists():
            st.caption("Reference Excel Output")
            st.write(f"File: {REFERENCE_XLSX.name}")
            with open(REFERENCE_XLSX, "rb") as f:
                st.download_button(
                    "📊 View Reference Excel",
                    f.read(),
                    file_name=REFERENCE_XLSX.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )


def _pipeline_reset():
    for key in ["pipeline_stage", "pipeline_project_id", "pipeline_project", "pipeline_measurements"]:
        st.session_state.pop(key, None)
    st.rerun()


def _pipeline_header(stage: int):
    labels = ["Project and plan", "Measurements", "DSR and BOQ", "Excel output"]
    st.title("BuildEstimate Pro")
    st.caption("One guided PWD/DSR estimate from plan to submission workbook")
    cols = st.columns(len(labels))
    for index, label in enumerate(labels):
        with cols[index]:
            if index < stage:
                st.success(f"✓ {index + 1}. {label}")
            elif index == stage:
                st.info(f"{index + 1}. {label}")
            else:
                st.caption(f"{index + 1}. {label}")
    st.progress((stage + 1) / len(labels))


def _pipeline_measurement_rows(estimate_type: str, areas: list[str], building_data=None, stages=None):
    if estimate_type == "New Building":
        data = building_data or {"length": 20.0, "width": 15.0, "floor_height": 3.0, "wall_thickness": 0.23}
        length = float(data.get("length", 20.0) or 20.0)
        width = float(data.get("width", 15.0) or 15.0)
        height = float(data.get("floor_height", 3.0) or 3.0)
        thickness = float(data.get("wall_thickness", 0.23) or 0.23)
        rows = [
            {"Room": "Foundation", "Count": 1, "Length": length, "Width": width, "Height": 1.2, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Footings", "Count": 4, "Length": 1.5, "Width": 1.5, "Height": 0.3, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Columns", "Count": 12, "Length": 0.3, "Width": 0.3, "Height": height, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Beams", "Count": 1, "Length": 2 * (length + width), "Width": 0.3, "Height": 0.45, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "DPC", "Count": 1, "Length": 2 * (length + width), "Width": thickness, "Height": 0.05, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Wall masonry", "Count": 1, "Length": 2 * (length + width), "Width": thickness, "Height": height, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Slab", "Count": 1, "Length": length, "Width": width, "Height": 0.15, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Staircase", "Count": 1, "Length": 4.0, "Width": 1.5, "Height": 0.15, "Steps": 18, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Electrical points", "Count": 24, "Length": 1.0, "Width": 1.0, "Height": 1.0, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
            {"Room": "Plumbing points", "Count": 16, "Length": 1.0, "Width": 1.0, "Height": 1.0, "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 0, "Door W": 0.0, "Door H": 0.0, "Windows": 0, "Window W": 0.0, "Window H": 0.0},
        ]
        if stages:
            selected = " ".join(stages).lower()
            stage_aliases = {"Footings": "foundation", "Columns": "columns", "Beams": "beams", "DPC": "plinth", "Wall masonry": "walls", "Slab": "slab", "Staircase": "staircase", "Foundation": "foundation", "Electrical points": "electrical", "Plumbing points": "plumbing"}
            rows = [row for row in rows if stage_aliases.get(row["Room"], row["Room"].lower()) in selected]
        return rows
    rows = build_default_measurements("Repair", estimate_type)
    if areas:
        rows = [row for row in rows if row["Room"] in areas] or rows[:len(areas)]
    return [{"Room": row["Room"], "Count": 1, "Length": row["Length_m"], "Width": row["Width_m"], "Height": row["Height_m"], "Steps": 0, "Riser": 0.16, "Tread": 0.28, "Waist": 0.15, "Doors": 1, "Door W": 0.9, "Door H": 2.1, "Windows": 1, "Window W": 1.2, "Window H": 1.2} for row in rows]


def _analyze_plan_upload(file_obj):
    if file_obj is None:
        return {"status": "No plan uploaded", "pages": 0, "text_length": 0, "rooms": [], "dimensions": [], "excerpt": ""}
    if file_obj.name.lower().endswith(".pdf"):
        try:
            import fitz
            document = fitz.open(stream=file_obj.getvalue(), filetype="pdf")
            text = "\n".join(page.get_text("text") for page in document)
            known_rooms = ["hall", "kitchen", "bedroom", "bathroom", "toilet", "veranda", "staircase", "store", "office", "terrace"]
            rooms = sorted({room.title() for room in known_rooms if room in text.lower()})
            dimensions = re.findall(r"\b\d+(?:\.\d+)?\s*[xX×]\s*\d+(?:\.\d+)?(?:\s*[xX×]\s*\d+(?:\.\d+)?)?\s*(?:m|meter|mm|ft)?\b", text)
            return {"status": "Plan text extracted", "pages": len(document), "text_length": len(text), "rooms": rooms, "dimensions": dimensions[:30], "excerpt": " ".join(text.split())[:700]}
        except Exception as exc:
            return {"status": f"PDF extraction failed: {exc}", "pages": 0, "text_length": 0, "rooms": [], "dimensions": [], "excerpt": ""}
    return {"status": "Image plan uploaded; manual measurement confirmation required", "pages": 0, "text_length": 0, "rooms": [], "dimensions": [], "excerpt": ""}


def _pipeline_rooms_payload(dataframe):
    payload = []
    for row in ensure_dataframe(dataframe).to_dict("records"):
        name = str(row.get("Room") or "Room").strip()
        length = float(row.get("Length", 0) or 0)
        width = float(row.get("Width", 0) or 0)
        height = float(row.get("Height", 3) or 3)
        count = float(row.get("Count", 1) or 1)
        if length <= 0 or width <= 0 or height <= 0:
            raise ValueError(f"Dimensions for {name} must be greater than zero.")
        if count <= 0:
            raise ValueError(f"Count for {name} must be greater than zero.")
        openings = []
        if float(row.get("Doors", 0) or 0) > 0:
            openings.append({"type": "door", "width": float(row.get("Door W", 0) or 0), "height": float(row.get("Door H", 0) or 0), "count": int(row.get("Doors", 0) or 0)})
        if float(row.get("Windows", 0) or 0) > 0:
            openings.append({"type": "window", "width": float(row.get("Window W", 0) or 0), "height": float(row.get("Window H", 0) or 0), "count": int(row.get("Windows", 0) or 0)})
        details = {"steps": float(row.get("Steps", 0) or 0), "riser": float(row.get("Riser", 0.16) or 0.16), "tread": float(row.get("Tread", 0.28) or 0.28), "waist_thickness": float(row.get("Waist", 0.15) or 0.15)}
        payload.append({"name": name, "length": length, "width": width, "height": height, "count": count, "details": details, "openings": openings})
    return payload


def render_pipeline():
    stage = int(st.session_state.get("pipeline_stage", 0))
    _pipeline_header(stage)

    if st.session_state.get("pipeline_project_id"):
        project = st.session_state["pipeline_project"]
        st.caption(f"Working project: {project['name']} | {project.get('estimate_type')}")
        if st.button("Start another estimate"):
            _pipeline_reset()

    if stage == 0:
        st.header("1. Project and plan")
        st.write("Provide the project facts and upload the existing plan. The next stages use these inputs for measurements, PWD/DSR matching, and calculations.")
        estimate_type = st.radio("Estimate type", ["Repair & Maintenance", "New Building"], horizontal=True, key="pipeline_estimate_type")
        with st.expander("Project history", expanded=False):
            history = fetch_project_history()
            if history:
                history_rows = []
                for record in history:
                    last_run = record.get("last_run") or {}
                    history_rows.append({
                        "Project": record.get("project_name"),
                        "Type": record.get("estimate_type"),
                        "Last run": last_run.get("created_at", "Not run"),
                        "Items": last_run.get("item_count", 0),
                        "Total": last_run.get("total_amount", 0),
                        "Status": last_run.get("status", "Draft"),
                    })
                st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No completed estimate runs yet.")
        with st.form("pipeline_intake"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Project name", placeholder="Repair to Class IV quarters")
                client = st.text_input("Client / department")
                location = st.text_input("Location")
                district = st.text_input("District")
                state = st.text_input("State", value="Maharashtra")
            with col2:
                building_type = st.text_input("Existing building type" if estimate_type == "Repair & Maintenance" else "Building type")
                floors = st.text_input("Number of floors")
                dsr_year = st.text_input("PWD/DSR year", value="PWD SSR 2022-23")
                department = st.text_input("PWD department / circle")
                plan = st.file_uploader("Existing building plan", type=["pdf", "png", "jpg", "jpeg"])
            if estimate_type == "Repair & Maintenance":
                areas = st.multiselect("Rooms / areas to repair", ["Hall", "Kitchen", "Bedroom 1", "Bedroom 2", "Bathroom", "Balcony", "Terrace", "External Walls", "Store room", "Office", "Veranda", "Staircase"], default=["Hall", "Kitchen"])
                works = st.multiselect("Repair work types", ["Internal wall painting", "External wall painting", "Ceiling painting", "Plaster repair", "Flooring", "Door repair", "Window repair", "Plumbing", "Electrical"], default=["Internal wall painting"])
                new_building_data = {}
            else:
                areas = []
                works = st.multiselect("Construction stages", ["Site preparation", "Foundation", "Plinth", "Columns", "Beams", "Walls", "Slab", "Staircase", "Plaster", "Doors and windows", "Flooring", "Painting", "Electrical", "Plumbing"], default=["Foundation", "Walls", "Slab"])
                new_building_data = {"length": st.number_input("Overall length (m)", min_value=0.0, value=20.0), "width": st.number_input("Overall width (m)", min_value=0.0, value=15.0), "floor_height": st.number_input("Floor height (m)", min_value=0.0, value=3.0), "wall_thickness": st.number_input("Wall thickness (m)", min_value=0.0, value=0.23)}
            submitted = st.form_submit_button("Save project and continue")
        if submitted:
            if not name.strip():
                st.warning("Project name is required.")
            else:
                plan_analysis = _analyze_plan_upload(plan)
                result = create_project({"name": name, "client": client, "location": location, "district": district, "state": state, "project_type": estimate_type, "estimate_type": estimate_type, "existing_building_type": building_type, "number_of_floors": floors, "dsr_year": dsr_year, "department": department, "estimate_date": str(pd.Timestamp.today().date()), "building_type": building_type, "plan_file_name": plan.name if plan else "", "context": {"areas": areas, "works": works, "plan_analysis": plan_analysis, "new_building_data": new_building_data}})
                if result is not None and result.ok:
                    project = result.json()
                    project["areas"] = areas
                    project["works"] = works
                    project["plan_analysis"] = plan_analysis
                    project["new_building_data"] = new_building_data
                    st.session_state["pipeline_project_id"] = project["id"]
                    st.session_state["pipeline_project"] = project
                    st.session_state["pipeline_stage"] = 1
                    st.rerun()
                elif result is not None:
                    st.error(result.text)
        return

    if stage == 1:
        st.header("2. Measurements and openings")
        st.write("Confirm dimensions from the plan. Doors and windows are captured separately so paint and plaster quantities use net wall area.")
        st.warning("Plan text and starter measurements are not verified dimensions. Confirm all lengths, counts, footing sizes, reinforcement assumptions, and service points against the approved drawings before relying on the estimate.")
        project = st.session_state["pipeline_project"]
        back_col, info_col = st.columns([1, 4])
        with back_col:
            if st.button("Back"):
                st.session_state["pipeline_stage"] = 0
                st.rerun()
        with info_col:
            analysis = project.get("plan_analysis", {})
            st.info(f"Plan review: {analysis.get('status', 'Not available')} | {analysis.get('pages', 0)} page(s) | {len(analysis.get('rooms', []))} room name(s) detected")
        if project.get("plan_analysis", {}).get("rooms"):
            st.write("Detected from plan:", ", ".join(project["plan_analysis"]["rooms"]))
        if project.get("plan_analysis", {}).get("dimensions"):
            st.write("Dimension strings found:", ", ".join(project["plan_analysis"]["dimensions"][:10]))
        if "pipeline_measurements" not in st.session_state:
            st.session_state["pipeline_measurements"] = pd.DataFrame(_pipeline_measurement_rows(project["estimate_type"], project.get("areas", []), project.get("new_building_data"), project.get("works")))
        edited = st.data_editor(st.session_state["pipeline_measurements"], key="pipeline_measurement_editor", use_container_width=True, num_rows="dynamic")
        if st.button("Confirm measurements and calculate BOQ", type="primary"):
            try:
                rooms = _pipeline_rooms_payload(edited)
            except ValueError as exc:
                st.error(str(exc))
                return
            result = save_project_rooms(project["id"], rooms)
            if result is not None and result.ok:
                st.session_state["pipeline_measurements"] = edited
                st.session_state["pipeline_stage"] = 2
                st.rerun()
            else:
                st.error("Measurements could not be saved. Check that the backend is running.")
        return

    if stage == 2:
        st.header("3. DSR matching and calculations")
        st.write("The BOQ engine applies the PWD/DSR rate records and keeps each quantity formula auditable. Openings are deducted from paint and plaster areas.")
        if st.button("Back"):
            st.session_state["pipeline_stage"] = 1
            st.rerun()
        items = fetch_boq_items(st.session_state["pipeline_project_id"])
        summary = fetch_boq_summary(st.session_state["pipeline_project_id"])
        if not items or not summary:
            st.warning("No calculated items are available yet. Confirm measurements first.")
            if st.button("Back to measurements"):
                st.session_state["pipeline_stage"] = 1
                st.rerun()
            return
        st.metric("Calculated estimate", f"₹ {summary.get('total_amount', 0):,.2f}")
        if summary.get("unpriced_items", 0):
            st.error(f"{summary['unpriced_items']} BOQ item(s) do not have a compatible DSR price. The displayed value is a priced subtotal, not a final estimate.")
        boq_frame = pd.DataFrame(items)
        visible_columns = ["sr_no", "work_category", "description", "quantity", "unit", "dsr_item_no", "dsr_unit", "dsr_unit_matches", "dsr_rate", "amount", "dsr_confidence", "dsr_approval_required"]
        visible_columns = [column for column in visible_columns if column in boq_frame.columns]
        st.dataframe(boq_frame[visible_columns], use_container_width=True, hide_index=True)
        uncertain = boq_frame[boq_frame.get("dsr_approval_required", False) == True] if "dsr_approval_required" in boq_frame else pd.DataFrame()
        if not uncertain.empty and "dsr_item_no" in uncertain:
            unmatched = uncertain[uncertain["dsr_item_no"].isna()]
            if not unmatched.empty:
                st.warning(f"{len(unmatched)} item(s) have no matching DSR record. They will remain unpriced in the subtotal.")
            uncertain = uncertain[uncertain["dsr_item_no"].notna()]
        if not uncertain.empty:
            st.warning(f"{len(uncertain)} DSR match(es) need manual approval before final export.")
            approval_data = uncertain[["sr_no", "dsr_item_no", "description", "dsr_confidence"]].copy()
            approval_data["Approved"] = False
            approved_rows = st.data_editor(approval_data, use_container_width=True, hide_index=True, disabled=["sr_no", "dsr_item_no", "description", "dsr_confidence"], key="dsr_approval_editor")
            if st.button("Save DSR approvals"):
                approvals = {str(row["dsr_item_no"]): bool(row["Approved"]) for row in approved_rows.to_dict("records")}
                response = save_dsr_approvals(st.session_state["pipeline_project_id"], approvals)
                if response is not None and response.ok:
                    st.session_state["dsr_approvals"] = approvals
                    st.success("DSR approval decisions saved to project history.")
                elif response is not None:
                    st.error(response.text)
        if st.button("Accept BOQ and prepare Excel", type="primary"):
            if not uncertain.empty:
                saved_approvals = st.session_state.get("dsr_approvals", {})
                missing = [str(item_no) for item_no in uncertain["dsr_item_no"].tolist() if not saved_approvals.get(str(item_no), False)]
                if missing:
                    st.error("Approve all uncertain DSR matches before continuing to Excel.")
                    return
            run_response = create_estimate_run(st.session_state["pipeline_project_id"])
            if run_response is not None and run_response.ok:
                st.session_state["pipeline_run"] = run_response.json()
                st.session_state["pipeline_stage"] = 3
                st.rerun()
            elif run_response is not None:
                st.error(run_response.text)
        return

    st.header("4. Excel output")
    if st.button("Back"):
        st.session_state["pipeline_stage"] = 2
        st.rerun()
    project = st.session_state["pipeline_project"]
    summary = fetch_boq_summary(project["id"])
    if summary and summary.get("unpriced_items", 0):
        st.warning("Priced subtotal ready. Review the unpriced BOQ rows before using this estimate as a final submission.")
    else:
        st.success("Estimate complete. The workbook contains Face Sheet, Estimate, and Measurements tabs.")
    st.metric("Net estimate", f"₹ {summary.get('total_amount', 0):,.2f}" if summary else "Unavailable")
    if summary and summary.get("unpriced_items", 0):
        st.warning(f"This is a priced subtotal. {summary['unpriced_items']} BOQ item(s) have no compatible DSR rate and are excluded from the total.")
    response = export_boq(project["id"])
    if response.ok:
        st.download_button("Download final estimate Excel", response.content, file_name=f"Estimate_{project['name']}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    else:
        st.error("Excel generation failed. Return to the BOQ stage and try again.")


if __name__ == "__main__":
    render_pipeline()
