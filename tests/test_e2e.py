import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.base as db_base
import app.workers.tasks as tasks_module
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.workers.tasks import run_analysis_job


@pytest.fixture
def test_db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session_local(test_db_engine):
    return sessionmaker(bind=test_db_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def patch_database_and_storage(monkeypatch, test_session_local, test_db_engine, tmp_path):
    monkeypatch.setattr(db_base, "engine", test_db_engine)
    monkeypatch.setattr(db_base, "SessionLocal", test_session_local)
    monkeypatch.setattr(tasks_module, "SessionLocal", test_session_local)
    monkeypatch.setattr("app.api.deps.SessionLocal", test_session_local)

    import app.api.v1.endpoints.analysis as analysis_module
    monkeypatch.setattr(analysis_module.run_analysis_job, "delay", lambda *args, **kwargs: None)

    storage_path = tmp_path / "uploads"
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", str(storage_path))

    yield


def _run_analysis_job_lifecycle(client: TestClient, sample_image_path: str, scan_type: str):
    with open(sample_image_path, "rb") as f:
        response = client.post(
            f"/api/v1/analyze/{scan_type}",
            files={"image": ("test.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["status"] is True
    payload = resp_json["data"]
    assert "job_id" in payload
    assert payload["status"] == "pending"

    job_id = int(payload["job_id"])
    task_result = run_analysis_job.__wrapped__(job_id)
    assert task_result["status"] == "completed"
    assert int(task_result["job_id"]) == job_id

    status_response = client.get(f"/api/v1/analyze/status/{job_id}")
    assert status_response.status_code == 200
    status_resp_json = status_response.json()
    assert status_resp_json["status"] is True
    status_payload = status_resp_json["data"]
    assert status_payload["status"] == "completed"
    assert int(status_payload["job_id"]) == job_id

    storage_dir = Path(settings.LOCAL_STORAGE_PATH)
    assert storage_dir.exists()
    assert any(storage_dir.iterdir())


def test_e2e_analysis_job_lifecycle_eye(sample_image_path):
    client = TestClient(app)
    _run_analysis_job_lifecycle(client, sample_image_path, "eye")


def test_e2e_analysis_job_lifecycle_tongue(sample_image_path):
    client = TestClient(app)
    _run_analysis_job_lifecycle(client, sample_image_path, "tongue")
