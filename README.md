<div align="center">
  <h1>🏗️ BuildEstimate Pro</h1>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python 3.11" />
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT" />
    <img src="https://img.shields.io/badge/Status-Production-success.svg" alt="Status Production" />
  </p>
</div>

## 📖 Overview
**BuildEstimate Pro** is a professional PWD (Public Works Department) estimation tool that generates Class IV style estimate workbooks with DSR (Departmental Schedule of Rates) matching. It takes building plans and measurements through a guided 4-step pipeline to produce submission-ready Excel estimates.

## ✨ Features
- 🔄 **Complete 4-step estimation pipeline**
- 🛠️ **Repair & Maintenance and New Building estimation**
- 📊 **PWD SSR 2022-23 DSR rate matching**
- 📑 **Class IV Excel output with formulas**
- 📐 **Room measurements with doors/windows openings**
- 📄 **PDF plan upload and text extraction**
- 🕒 **Project history tracking**
- 🌙 **Professional dark theme UI**

## 🌐 Live Demo
Deployed on Streamlit Cloud: [BuildEstimate Pro App](https://buildestimate-pro.streamlit.app)

## 🛠️ Tech Stack
| Technology | Purpose |
|---|---|
| **Streamlit** | Frontend UI |
| **SQLAlchemy** | ORM / Database |
| **SQLite** | Local database |
| **openpyxl** | Excel generation |
| **PyMuPDF** | PDF processing |
| **pandas** | Data manipulation |

## 📂 Project Structure
```text
BuildEstimate pro/
├── streamlit_app.py              # Main entry point
├── requirements.txt              # Python dependencies
├── packages.txt                  # System dependencies
├── .streamlit/config.toml        # Theme configuration
├── .gitignore
├── buildestimate_pro/
│   ├── backend/
│   │   ├── api/                  # API routes (for local dev)
│   │   ├── models/               # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── boq_engine.py     # BOQ calculation engine
│   │   │   ├── excel_export.py   # Class IV Excel generation
│   │   │   ├── calculation_engine/
│   │   │   │   ├── new_building.py
│   │   │   │   └── painting.py
│   │   │   └── ssr_ingestion_service.py
│   │   └── database/
│   ├── frontend/
│   │   └── app.py                # Original Streamlit UI
│   ├── knowledge_base/
│   │   └── PWD Civil SSR_2022-23_Final.pdf
│   └── refernace Excell output/
│       └── EST Class IV Urjent repairs.xlsx
└── README.md
```

## 🚀 Getting Started

### Local Development
```bash
git clone https://github.com/YOUR_USERNAME/BuildEstimate-Pro.git
cd BuildEstimate-Pro
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Deploy to Streamlit Cloud
Step by step:
1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repo
5. Set main file: `streamlit_app.py`
6. Click "Deploy"

## 🔄 Workflow
1. **Project & Plan** — Enter project details, upload building plan
2. **Measurements** — Edit room dimensions, doors, windows
3. **DSR & BOQ** — Auto-matched PWD rates, approve uncertain matches
4. **Excel Output** — Download Class IV estimate workbook

## 📊 Excel Output Format
The generated Class IV sheet features:
- MIDC header with merged cells
- 18-column layout (Item No through Waist Thick)
- Formula-driven quantities with yellow input cells
- Green computed cells for quantities and amounts
- Bookman Old Style typography
- Landscape A4, fit to width

## 🧮 Key Calculations
Formulas and calculations handled internally:
- **Paint area:** Surface area of walls and ceilings minus openings.
- **Floor area:** Internal room dimensions (length × width).
- **Plaster area:** Similar to paint area but for plastering requirements.
- **Wall masonry:** Volume based on wall length, height, and thickness minus openings.
- **Slab concrete:** Volume of concrete based on floor area and slab thickness.

## 🔌 API Documentation (for Local Dev)
The FastAPI backend provides API documentation at `http://localhost:8000/docs` when running locally.

## 📄 License
This project is licensed under the MIT License.

---
**Last Updated:** October 2026 | **Version:** 2.0.0 | **Author:** BuildEstimate Pro Team
