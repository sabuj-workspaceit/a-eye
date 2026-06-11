# A-EYE FastAPI Service - Implementation Plan

This document outlines a comprehensive, step-by-step plan to build the A-EYE AI Analysis Service as specified in the `srs.md` document. It follows modern software architecture best practices to ensure a scalable, maintainable, and robust application.

---

### Recommended Project Architecture

A modular, service-oriented structure is recommended. The following directory structure separates concerns logically, making the codebase easier to navigate, test, and maintain.

```plaintext
a-eye-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app instance, middleware, routers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic settings for environment variables
│   │   └── logging.py          # Structured logging configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Common FastAPI dependencies (e.g., get_db_session)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/      # API route handlers
│   │       │   ├── __init__.py
│   │       │   ├── health.py
│   │       │   └── analysis.py
│   │       └── schemas/        # Pydantic models for API I/O
│   │           ├── __init__.py
│   │           ├── analysis.py
│   │           └── report.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy DeclarativeBase and session setup
│   │   └── models/             # Directory for all SQLAlchemy models
│   ├── services/               # Core business logic
│   │   ├── __init__.py
│   │   ├── analysis_pipeline/  # Modules for each step of the AI pipeline
│   │   │   ├── __init__.py
│   │   │   ├── 1_validation.py
│   │   │   ├── 2_detection.py
│   │   │   ├── 3_normalization.py
│   │   │   ├── 4_zoning.py
│   │   │   ├── 5_feature_extraction.py
│   │   │   └── ...
│   │   ├── rule_engine.py      # Logic for evaluating rules
│   │   ├── report_generator.py # Logic for creating reports
│   │   └── storage.py          # S3 client wrapper
│   └── workers/
│       ├── __init__.py
│       ├── celery_app.py       # Celery application instance
│       └── tasks.py            # Celery task definitions (e.g., run_full_analysis)
├── migrations/                 # Alembic database migration scripts
├── ml_models/                  # To store .tflite and other model files
├── tests/                      # Unit and integration tests
│   ├── conftest.py
│   └── ...
├── .env.example                # Example environment variables
├── .gitignore
├── Dockerfile                  # For building the production container
├── docker-compose.yml          # For local development (app, db, redis)
├── poetry.lock
├── pyproject.toml              # Project dependencies (using Poetry)
└── README.md
```

---

### Step-by-Step Implementation Plan

You can use this as a checklist to track your progress. Each phase builds upon the last, ensuring a stable and incremental development process.

#### Phase 1: Project Foundation & Setup (Completed: 6/6)
This phase establishes the project's skeleton and core infrastructure.

- [x] **1.1. Environment Setup:**
    - Install Python 3.10+ and Poetry for dependency management.
    - Initialize the project: `poetry new a-eye-fastapi && cd a-eye-fastapi`
    - Set up a Git repository: `git init`

- [x] **1.2. Core Dependencies:**
    - Add essential libraries:
      ```bash
      poetry add "fastapi[all]" uvicorn sqlalchemy psycopg2-binary alembic
      ```

- [x] **1.3. Basic Application & Health Check:**
    - Create the initial FastAPI app in `app/main.py`.
    - Implement the `GET /health` endpoint as specified in the SRS. This confirms the basic server is working.

- [x] **1.4. Configuration Management:**
    - In `app/core/config.py`, use Pydantic's `BaseSettings` to manage environment variables (e.g., `DATABASE_URL`, `S3_BUCKET`). This is crucial for separating config from code.

- [x] **1.5. Dockerization for Development:**
    - Create a `Dockerfile` to containerize the FastAPI application.
    - Create a `docker-compose.yml` file to orchestrate the `app`, a `postgres` database, and a `redis` instance for local development.

- [x] **1.6. Initial Project Structure:**
    - Create the directories and empty `__init__.py` files as outlined in the architecture diagram above.

#### Phase 2: Database & Async Task Setup (Completed: 4/4)
This phase connects the application to its stateful components.

- [x] **2.1. Database Integration:**
    - Configure SQLAlchemy in `app/db/base.py`.
    - Set up Alembic for database migrations: `alembic init migrations`.
    - Configure Alembic to use your app's models and database connection settings.

- [x] **2.2. Define Database Models:**
    - Create the SQLAlchemy models in `app/db/models/` for all items listed in section 16 of the SRS (`zone_maps`, `rules`, `analysis_jobs`, etc.).
    - Generate and apply the initial database migration: `alembic revision --autogenerate -m "Initial models" && alembic upgrade head`.

- [x] **2.3. Background Task Queue:**
    - Add Celery and a Redis client: `poetry add celery redis`.
    - Configure the Celery instance in `app/workers/celery_app.py` to use Redis as the broker.

- [x] **2.4. Object Storage (S3/Local):**
    - Add the AWS S3 client library: `poetry add boto3`.
    - Create a service wrapper in `app/services/storage.py`.
    - **Note:** Configured to use local filesystem storage for now. Can be switched to S3 via environment variables.

#### Phase 3: Core AI Pipeline - Validation & Detection (Completed: 5/5)
Now, we start building the heart of the service: the computer vision pipeline.

- [x] **3.1. Add CV Dependencies:**
    - `poetry add opencv-python-headless mediapipe tensorflow-lite`

- [x] **3.2. Image Validation Service:**
    - In `app/services/analysis_pipeline/validation.py`, implement the functions for:
        - Blur Detection (`cv2.Laplacian`).
        - Lighting Validation (histogram analysis).
        - Glare Detection.
        - Framing Validation.

- [x] **3.3. Region Detection Service:**
    - In `app/services/analysis_pipeline/detection.py`, implement the functions for:
        - **Iris:** `Hough Circle Transform` using OpenCV.
        - **Face:** Face Mesh detection using MediaPipe (with OpenCV fallback).
        - **Tongue:** Segmentation using a TFLite model placeholder.

- [x] **3.4. Image Normalization Service:**
    - In `app/services/analysis_pipeline/normalization.py`, implement the functions to standardize images (resize, align, correct brightness/contrast) as per the SRS.

- [x] **3.5. Create Analysis API & Worker Task:**
    - Implement the `POST /analyze/{scan_type}` endpoint in `app/api/v1/endpoints/analysis.py`.
    - These endpoints do not perform analysis directly. Instead, they:
        1. Upload the incoming image to local storage.
        2. Create an `analysis_jobs` record in the database with a `pending` status.
        3. Trigger a background Celery task in `app/workers/tasks.py`, passing the job ID.
        4. Immediately return the `job_id` to the client.
    - This async pattern is essential for meeting the performance requirements and preventing blocked API requests.

#### Phase 4: Analysis, Rules, and Reporting (Completed: 4/4)
This phase focuses on extracting meaning from the processed images.

- [x] **4.1. Zone Mapping & Feature Extraction:**
    - Implement the zone mapping system in `app/services/analysis_pipeline/zoning.py`.
    - Implement the feature extraction logic (color, texture, etc.) in `app/services/analysis_pipeline/feature_extraction.py`.

- [x] **4.2. Rule Engine Implementation:**
    - In `app/services/rule_engine.py`, build a class or module that can:
        1. Load rules from the database for a given scan type.
        2. Parse the condition string (`redness > 0.7`).
        3. Evaluate the condition against the extracted features for each zone.
        4. Generate findings based on matching rules.

- [x] **4.3. Protocol & LLM Integration:**
    - Implement the protocol engine to attach recommendations to findings.
    - Integrate an LLM client placeholder to generate human-readable summaries.
    - **Crucially**, implement the `Safety Filter` from section 14 of the SRS to scan all generated text for blocked words.

- [x] **4.4. Report Generation:**
    - Create the `ReportGenerator` service in `app/services/report_generator.py`.
    - This service assembles Practitioner and Client reports from completed analysis jobs.

#### Phase 5: Testing, Deployment & Polish (Completed: 0/4)
The final phase ensures the application is robust, reliable, and ready for production.

- [ ] **5.1. Comprehensive Testing:**
    - Add `pytest` and related plugins: `poetry add --group dev pytest pytest-cov pytest-asyncio`.
    - Write **unit tests** for individual functions (e.g., blur detection, rule parser).
    - Write **integration tests** that call the API endpoints and verify the end-to-end flow (job creation, status update, final report).

- [ ] **5.2. Observability:**
    - Add and configure OpenTelemetry for structured logging and tracing as per the non-functional requirements.

- [ ] **5.3. API Documentation:**
    - Review and refine the auto-generated OpenAPI (`/docs`) documentation. Add detailed descriptions, examples, and response models to make the API easy to use.

- [ ] **5.4. Production CI/CD & Deployment:**
    - Set up a CI/CD pipeline (e.g., using GitHub Actions) that automatically runs tests on every push.
    - Build and push the final, optimized Docker image to a container registry (e.g., AWS ECR, Docker Hub).
    - Deploy the application to your hosting environment.