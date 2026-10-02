# BuildEstimate Pro (Prototype)

This repository contains an initial prototype scaffold for BuildEstimate Pro.

Components included:

- FastAPI backend with SQLAlchemy models
- Minimal DSR demo dataset and seeder
- Basic calculation engines for painting and wall quantities
- Streamlit frontend scaffold
- Formula-driven single-sheet Class IV style estimate export

See `requirements.txt` for dependencies and `.env.example` for environment variables.

Quick start (development):

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Seed demo data:

```bash
python scripts/seed_database.py
```

3. Run FastAPI backend:

```bash
uvicorn backend.main:app --reload
```

4. Run Streamlit frontend:

```bash
streamlit run frontend/app.py
```
