# Critical Procurement Bottleneck Analytics

Operational data system for identifying bottlenecks in critical procurement workflows.

This project is not a purchase approval system. It analyzes procurement process data to show which requests are blocking important operations, where the delay is happening, and what should be handled first.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- Pipeline: Python scripts
- Frontend: React, TypeScript, Vite
- Local infra: Docker Compose

## Project Structure

```text
backend/
frontend/
docs/
docker-compose.yml
```

## Local Setup

Copy environment values if needed:

```bash
cp .env.example .env
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Verification

Backend tests:

```bash
cd backend
source .venv/bin/activate
pytest
```

Generate deterministic sample source data:

```bash
cd backend
source .venv/bin/activate
python -m app.sample_data.generator --output-dir generated/sample_data
```

Run ingestion, core transformation, analytics build, and data quality checks:

```bash
cd backend
source .venv/bin/activate
python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
```

Frontend build:

```bash
cd frontend
npm run build
```
