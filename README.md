# Football Analytics Platform

Phase 1 implements a local video-ingestion pipeline: validated MP4/MOV/AVI uploads, metadata extraction, background frame sampling/preprocessing, persistent job/frame metadata, and a connected Next.js dashboard. Computer vision analysis is deliberately out of scope.

## Quick start

### Windows PowerShell

Terminal 1 (backend):

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --reload --port 8010
```

Terminal 2 (frontend):

```powershell
cd frontend
Copy-Item .env.local.example .env.local
npm install
npm run dev -- --port 3001
```

Open `http://localhost:3001`; API docs are at `http://127.0.0.1:8010/docs`. Upload MP4, MOV, or AVI footage, choose a sampling rate, and start processing. Files are stored under `storage/uploads` and `storage/frames/<video-id>`; access them through the API, not direct browser paths.

For PostgreSQL via Docker, set a real `POSTGRES_PASSWORD` in `.env`, then run `docker compose up -d --build`. Docker supplies its own PostgreSQL connection URL. The default non-Docker setup uses SQLite so the application remains locally runnable without a database service.

FFprobe is optional but recommended for richer codec/duration metadata. Install an FFmpeg build for Windows, add its `bin` directory to `PATH`, then verify with `ffprobe -version`. OpenCV metadata extraction and frame processing still work when it is unavailable.

Run checks: `python -m pytest`, `python -m json.tool shared/data_contracts/observation.schema.json`, and `npm run typecheck` inside `frontend`.

## Scope

No model, player/event detection, tracking, identity, or football statistic is implemented. Optional GPU/model packages must be added in a separately pinned environment when needed.

## Baseline versions

The Python baseline targets Python 3.11+ with FastAPI 0.115+, SQLAlchemy 2.x, Pydantic Settings 2.x, OpenCV 4.x, and JSON Schema validation 4.x. The frontend uses Next.js 15, React 19, and TypeScript 5.6+. Version ranges are deliberately bounded in `pyproject.toml` and the frontend lockfile records the resolved Node dependency set.
