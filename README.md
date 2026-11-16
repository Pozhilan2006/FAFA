# Football Analytics Platform

Initial scaffold for a football video-analysis platform. Computer vision, ingestion, and analytics are deliberately independent so a future identity/AI layer can consume their observations and event candidates.

## Quick start

1. Copy `.env.example` to `.env` and set `POSTGRES_PASSWORD` plus a local `DATABASE_URL` if running without Docker.
2. Create a Python 3.11+ virtual environment and run `pip install -e .`.
3. Start the API with `uvicorn backend.app.main:app --reload`; visit `/docs` and `/health`.
4. For containers, run `docker compose up --build` after defining `POSTGRES_PASSWORD` in `.env`.
5. In `frontend`, run `npm install` then `npm run dev`.

Run checks: `pytest`, `python -m json.tool shared/data_contracts/observation.schema.json`, and `npm run typecheck`.

## Scope

The endpoints and CV interfaces are placeholders. No model, event detection, confirmed identity, or football statistic is implemented. Optional GPU/model packages must be added in a separately pinned environment when needed.

## Baseline versions

The Python baseline targets Python 3.11+ with FastAPI 0.115+, SQLAlchemy 2.x, Pydantic Settings 2.x, OpenCV 4.x, and JSON Schema validation 4.x. The frontend uses Next.js 15, React 19, and TypeScript 5.6+. Version ranges are deliberately bounded in `pyproject.toml` and the frontend lockfile records the resolved Node dependency set.
