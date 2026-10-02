# BuildEstimate Pro - Supabase Setup Guide

This guide will help you connect BuildEstimate Pro to Supabase PostgreSQL database.

## Prerequisites

- Supabase account (free tier at https://supabase.com)
- Python 3.8+
- pip

## Step 1: Get Your Supabase Credentials

1. Go to [Supabase Console](https://app.supabase.com)
2. Create a new project or use existing one
3. Go to **Settings > Database > Connection string**
4. Copy the PostgreSQL connection string
5. Your credentials are:
   - **Project URL**: https://bmujrwrzyxllrmpjtzeq.supabase.co
   - **Publishable Key (anon)**: your-supabase-anon-key-here
   - **Secret Key**: your-supabase-secret-key-here

## Step 2: Create `.env` File

Create a `.env` file in the project root with:

```env
# Supabase Configuration
SUPABASE_URL=https://bmujrwrzyxllrmpjtzeq.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
SUPABASE_SECRET=your-supabase-secret-key-here

# PostgreSQL Connection (replace YOUR_PASSWORD with your Supabase password)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@bmujrwrzyxllrmpjtzeq.db.supabase.co:5432/postgres

# API Configuration
API_URL=http://127.0.0.1:8000

# Gemini API Key (optional, for PDF Q&A)
GEMINI_API_KEY=your-gemini-api-key-here
```

## Step 3: Find Your Supabase Password

1. In Supabase Console, go to **Settings > Database**
2. Look for **Database Password** section
3. If not visible, you can reset it:
   - Click **Reset password**
   - Copy the new password
4. Use this password in `DATABASE_URL`

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

The project will automatically install:
- `psycopg2-binary` for PostgreSQL
- SQLAlchemy with PostgreSQL support
- All other dependencies

## Step 5: Initialize Supabase Database

Run the seeding script to create tables and add demo data:

```bash
python buildestimate_pro/scripts/seed_database.py
```

This will create:
- `projects` table
- `rooms` table
- `openings` table
- `dsr_items` table
- `dsr_materials` table
- `dsr_labour` table

## Step 6: Start the Backend

```bash
cd buildestimate_pro
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Step 7: Start the Frontend

In a new terminal:

```bash
cd buildestimate_pro
streamlit run frontend/app.py --server.port 8501
```

## Step 8: Complete Workflow

1. **Dashboard**: View projects and metrics
2. **Projects**: Create new Repair & Maintenance or New Building project
3. **Measurements**: Edit and save room dimensions
4. **BOQ Summary**: View cost estimates and item breakdown
5. **Export**: Download Excel BOQ with materials & labour
6. **SSR Import**: Load PWD rate items from PDF

## Verification

To verify Supabase connection:

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(result.fetchone())
```

## Troubleshooting

### Connection Refused
- Verify `DATABASE_URL` is correct
- Check Supabase project is running
- Ensure firewall allows PostgreSQL (port 5432)

### Authentication Failed
- Verify password in connection string
- Check credentials in `.env`
- Reset password in Supabase console

### psycopg2 Installation Issues
On Windows:
```bash
pip install psycopg2-binary
```

On Mac/Linux with M1/M2:
```bash
pip install psycopg2-binary --only-binary :all:
```

### Tables Don't Exist
Run the seed script again:
```bash
python buildestimate_pro/scripts/seed_database.py
```

## Architecture

```
Frontend (Streamlit)
    ↓
Backend (FastAPI)
    ↓
SQLAlchemy ORM
    ↓
Supabase PostgreSQL
```

The app uses SQLAlchemy as ORM, which abstracts the database layer. The same code works with:
- SQLite (local dev)
- PostgreSQL (Supabase)
- Other SQL databases

## Key Features

✅ Project metadata management
✅ Room/measurement storage
✅ BOQ generation from DSR rates
✅ Material & labour decomposition
✅ Excel export with cost sheets
✅ PWD SSR PDF integration
✅ Repair & Maintenance workflow
✅ New Building workflow
✅ Reference file downloads
✅ Fully scalable on Supabase free tier

## Support

For Supabase help: https://supabase.com/docs
For SQLAlchemy help: https://docs.sqlalchemy.org
