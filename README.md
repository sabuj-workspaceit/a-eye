# A-EYE AI Analysis Service

A FastAPI service for wellness image analysis, as detailed in the SRS.

## Project Setup

This project uses [Poetry](https://python-poetry.org/docs/) for dependency management.

**1. Install Dependencies**

First, navigate to your project directory and install the required Python packages using Poetry.

```bash
cd /home/sabuj/Office/a-eye-fastapi
poetry install
```

If there is no `requirements.txt`, install the core dependencies directly:

```bash
.venv/bin/python -m pip install fastapi uvicorn pydantic-settings psycopg2-binary alembic celery redis python-multipart opencv-python-headless pytest pytest-asyncio pytest-cov
```

Create a local `.env` file from `.env.example` before starting the services:

```bash
cp .env.example .env
```

## Local development

Start the supporting services first:

```bash
docker compose up -d db redis worker
```

If you have not initialized the database schema yet, run:

```bash
alembic upgrade head
```

Run the FastAPI application:

```bash
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the service in your browser:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Local development (without Docker)

If you are running supporting services like PostgreSQL and Redis on your local machine instead of using Docker, you will also need to run the Celery worker manually in a separate terminal. The worker process is responsible for executing background analysis jobs.

After activating your virtual environment, start the worker from the project root:

```bash
.venv/bin/python -m celery -A app.workers.celery_app worker --loglevel=info
```

**Note:** The `-A app.workers.celery_app` argument points to the Celery application instance. If your Celery app is defined elsewhere, you will need to adjust this path accordingly.

Then, run the FastAPI application as usual in another terminal:

```bash
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Run the full unit and integration test suite:

```bash
.venv/bin/python -m pytest tests/ -v
```

Run the end-to-end workflow test only:

```bash
.venv/bin/python -m pytest tests/test_e2e.py -q
```

## End-to-end test coverage

The E2E test exercises the following path:

1. Uploads an image to `POST /api/v1/analyze/{scan_type}`
2. Creates a pending analysis job
3. Executes background analysis logic directly in-process
4. Verifies completion status via `GET /api/v1/analyze/status/{job_id}`

## Analysis Capabilities

A-EYE supports advanced computer vision processing across three scan types:

### Iris Analysis
- Implements `cv2.HoughCircles` boundary estimation.
- Mathematically partitions the iris into 3 rings and 12 sectors (36 dynamic zones).

### Face Analysis
- Integrates MediaPipe Face Mesh processing.
- Supports frontend landmarks injection to reduce server inference loads.
- Mathematically groups 468 facial landmarks into distinct convex hulls (`forehead`, `chin`, `nose`, `left_cheek`, `right_cheek`).

### Tongue Analysis
- Integrates TFLite (DeepLabv3) segmentation.
- Organizes the tongue bounding box into orientation-based partitions (`tip`, `rear`, `center`, `left`, `right`).

### Feature Extraction
Each generated zone evaluates the following features for the Rule Engine:
- **Color**: Exact HSV & LAB derivations.
- **Texture**: GLCM and LBP metrics (`roughness`, `uniformity`).
- **Pathologies**: Spot mapping (DoG/LoG algorithms) and Crack/Fissure tracking (Frangi-style filters).

### Safety Filter
A strict `protocol_engine` evaluates all text generation to block and redact medical diagnostics, guaranteeing wellness compliance.

## Project structure

- `app/main.py` - FastAPI application and route registration
- `app/api/v1/endpoints/analysis.py` - analysis job endpoints
- `app/api/v1/endpoints/health.py` - health check endpoint
- `app/core/config.py` - configuration and environment loading
- `app/db/base.py` - SQLAlchemy engine and session setup
- `app/services` - analysis pipeline, rule engine, and report generation
- `app/workers/tasks.py` - Celery task implementation for async analysis
- `tests/` - pytest test suites including E2E coverage
- `IMPLEMENTATION_PLAN.md` - implementation checklist and architecture plan
- `srs.md` - service requirements specification
