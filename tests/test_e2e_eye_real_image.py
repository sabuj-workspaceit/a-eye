"""
End-to-end tests for the eye analysis pipeline using a real camera eye image.

This module exercises the full lifecycle of an eye scan job:
  1. POST /api/v1/analyze/eye  – upload image, receive pending job
  2. run_analysis_job (sync)   – process the job through the full pipeline
  3. GET /api/v1/analyze/status/{job_id} – assert job completed
  4. GET /api/v1/analyze/report/{job_id} – assert report was generated

The test uses ``tests/assets/camera-eye_eye1.jpg`` – a real photograph of a
human eye – so that the detection, zoning and feature-extraction stages are
exercised against genuine image content rather than a synthetic blank frame.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
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

# ---------------------------------------------------------------------------
# Path to the real eye image shipped with the test assets
# ---------------------------------------------------------------------------
ASSETS_DIR = Path(__file__).parent / "assets"
REAL_EYE_IMAGE = ASSETS_DIR / "camera-eye_eye1.jpg"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_eye_image_path():
    """Return the absolute path to the real eye photograph, failing fast if missing."""
    if not REAL_EYE_IMAGE.exists():
        pytest.fail(
            f"Required test asset not found: {REAL_EYE_IMAGE}\n"
            "Please ensure tests/assets/camera-eye_eye1.jpg is present."
        )
    return str(REAL_EYE_IMAGE)


@pytest.fixture
def isolated_db_engine(tmp_path):
    """Spin up a fresh file-backed SQLite database for each test."""
    db_path = tmp_path / "e2e_eye_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def isolated_session_local(isolated_db_engine):
    return sessionmaker(bind=isolated_db_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def patch_infra(monkeypatch, isolated_session_local, isolated_db_engine, tmp_path):
    """Redirect DB, storage and Celery so the test is fully self-contained."""
    # Patch database references
    monkeypatch.setattr(db_base, "engine", isolated_db_engine)
    monkeypatch.setattr(db_base, "SessionLocal", isolated_session_local)
    monkeypatch.setattr(tasks_module, "SessionLocal", isolated_session_local)
    monkeypatch.setattr("app.api.deps.SessionLocal", isolated_session_local)

    # Disable async Celery dispatch (we call the task synchronously below)
    import app.api.v1.endpoints.analysis as analysis_module

    monkeypatch.setattr(analysis_module.run_analysis_job, "delay", lambda *a, **kw: None)

    # Redirect uploaded files to a temp directory
    storage_path = tmp_path / "uploads"
    storage_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", str(storage_path))

    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _post_eye_image(client: TestClient, image_path: str) -> dict:
    """Upload an eye image and return the parsed JSON response."""
    with open(image_path, "rb") as f:
        response = client.post(
            "/api/v1/analyze/eye",
            files={"image": ("camera-eye_eye1.jpg", f, "image/jpeg")},
        )
    assert response.status_code == 200, (
        f"Expected 200 from /analyze/eye, got {response.status_code}: {response.text}"
    )
    resp_json = response.json()
    assert resp_json["status"] is True
    return resp_json["data"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEyeJobSubmission:
    """Verify that the API accepts the real eye image and creates a pending job."""

    def test_submit_returns_200(self, real_eye_image_path):
        client = TestClient(app)
        with open(real_eye_image_path, "rb") as f:
            response = client.post(
                "/api/v1/analyze/eye",
                files={"image": ("camera-eye_eye1.jpg", f, "image/jpeg")},
            )
        assert response.status_code == 200

    def test_submit_returns_job_id(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        assert "job_id" in payload, "Response must contain 'job_id'"
        assert payload["job_id"] is not None

    def test_submit_returns_pending_status(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        assert payload["status"] == "pending", (
            f"Initial job status should be 'pending', got '{payload['status']}'"
        )


class TestEyeJobProcessing:
    """Run the analysis task synchronously and verify it completes successfully."""

    def test_analysis_job_completes(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])

        result = run_analysis_job.__wrapped__(job_id)

        assert result["status"] == "completed", (
            f"Expected task result status 'completed', got '{result['status']}'"
        )
        assert int(result["job_id"]) == job_id

    def test_status_endpoint_reflects_completed(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])

        run_analysis_job.__wrapped__(job_id)

        status_resp = client.get(f"/api/v1/analyze/status/{job_id}")
        assert status_resp.status_code == 200
        status_resp_json = status_resp.json()
        assert status_resp_json["status"] is True
        status_data = status_resp_json["data"]
        assert status_data["status"] == "completed"
        assert int(status_data["job_id"]) == job_id

    def test_normalized_image_written_to_storage(self, real_eye_image_path, tmp_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])

        run_analysis_job.__wrapped__(job_id)

        storage_dir = Path(settings.LOCAL_STORAGE_PATH)
        all_files = list(storage_dir.rglob("*"))
        assert any(f.is_file() for f in all_files), (
            "Expected at least one file written to storage after processing"
        )

    def test_normalized_file_is_a_valid_image(self, real_eye_image_path, tmp_path):
        """The normalized output file must be readable by OpenCV."""
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])

        run_analysis_job.__wrapped__(job_id)

        storage_dir = Path(settings.LOCAL_STORAGE_PATH)
        image_files = [
            f for f in storage_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]
        assert image_files, "No image files found in storage after processing"

        for img_path in image_files:
            loaded = cv2.imread(str(img_path))
            assert loaded is not None, (
                f"OpenCV could not load stored image: {img_path}"
            )


class TestEyeReportGeneration:
    """Verify the report endpoint returns a well-formed response after job completion."""

    def test_report_endpoint_returns_200(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])
        run_analysis_job.__wrapped__(job_id)

        report_resp = client.get(f"/api/v1/analyze/report/{job_id}")
        assert report_resp.status_code == 200

    def test_report_response_has_required_fields(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])
        run_analysis_job.__wrapped__(job_id)

        resp = client.get(f"/api/v1/analyze/report/{job_id}")
        assert resp.json()["status"] is True
        data = resp.json()["data"]
        assert "job_id" in data
        assert "status" in data
        assert "reports" in data
        assert isinstance(data["reports"], list)

    def test_report_job_id_matches(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])
        run_analysis_job.__wrapped__(job_id)

        data = client.get(f"/api/v1/analyze/report/{job_id}").json()["data"]
        assert int(data["job_id"]) == job_id

    def test_report_status_is_completed(self, real_eye_image_path):
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])
        run_analysis_job.__wrapped__(job_id)

        data = client.get(f"/api/v1/analyze/report/{job_id}").json()["data"]
        assert data["status"] == "completed"

    def test_report_content_is_valid_json(self, real_eye_image_path):
        """Each report's content field must be a dict (parsed JSON), not a raw string."""
        client = TestClient(app)
        payload = _post_eye_image(client, real_eye_image_path)
        job_id = int(payload["job_id"])
        run_analysis_job.__wrapped__(job_id)

        data = client.get(f"/api/v1/analyze/report/{job_id}").json()["data"]
        for report in data["reports"]:
            assert isinstance(report.get("content"), dict), (
                f"Report content should be a dict, got: {type(report.get('content'))}"
            )


class TestEyeDetectionPipeline:
    """
    Unit-style checks on individual pipeline stages run against the real image.
    These verify that the actual eye photograph yields meaningful detector output.
    """

    @pytest.fixture(scope="class")
    def real_image_array(self):
        img = cv2.imread(str(REAL_EYE_IMAGE))
        assert img is not None, f"Could not load {REAL_EYE_IMAGE}"
        return img

    def test_image_loads_correctly(self, real_image_array):
        assert real_image_array is not None
        assert real_image_array.ndim == 3
        assert real_image_array.shape[2] == 3  # BGR channels

    def test_image_has_reasonable_dimensions(self, real_image_array):
        h, w = real_image_array.shape[:2]
        assert h > 50 and w > 50, f"Image too small: {w}x{h}"

    def test_validate_image_returns_expected_keys(self, real_image_array):
        from app.services.analysis_pipeline import validate_image

        result = validate_image(real_image_array)
        assert "blur" in result
        assert "lighting" in result
        assert "glare" in result
        assert "framing" in result

    def test_lighting_score_is_numeric(self, real_image_array):
        from app.services.analysis_pipeline import validate_image

        result = validate_image(real_image_array)
        lighting = result["lighting"]
        assert isinstance(lighting["average_brightness"], float)
        assert isinstance(lighting["contrast"], float)
        # A real eye photo should have non-trivial brightness
        assert lighting["average_brightness"] > 0

    def test_detect_all_returns_expected_structure(self, real_image_array):
        from app.services.analysis_pipeline import detect_all

        result = detect_all(real_image_array)
        assert "iris" in result
        assert "face" in result
        assert "tongue" in result

    def test_iris_detection_on_real_eye(self, real_image_array):
        from app.services.analysis_pipeline.detection import detect_iris

        result = detect_iris(real_image_array)
        assert "iris_found" in result
        assert "circles" in result
        assert isinstance(result["iris_found"], bool)
        assert isinstance(result["circles"], list)
        # A clear close-up eye photo should produce at least one detected circle
        assert result["iris_found"] is True, (
            "Expected iris to be detected in a real eye photograph. "
            f"Got circles: {result['circles']}"
        )

    def test_generate_zones_for_eye_scan(self, real_image_array):
        from app.services.analysis_pipeline import generate_zones

        zones = generate_zones(real_image_array, "eye")
        assert isinstance(zones, list)
        assert len(zones) > 0
        for zone in zones:
            assert "name" in zone
            assert "coordinates" in zone
            assert len(zone["coordinates"]) == 4

    def test_extract_zone_features_produces_output(self, real_image_array):
        from app.services.analysis_pipeline import generate_zones, extract_zone_features

        zones = generate_zones(real_image_array, "eye")
        features = extract_zone_features(real_image_array, zones)
        # Returns a dict keyed by zone name, one entry per zone
        assert isinstance(features, dict)
        assert len(features) == len(zones)
        for zone in zones:
            assert zone["name"] in features, (
                f"Expected zone '{zone['name']}' in features dict, got keys: {list(features.keys())}"
            )

    def test_extract_zone_features_has_expected_sub_keys(self, real_image_array):
        from app.services.analysis_pipeline import generate_zones, extract_zone_features

        zones = generate_zones(real_image_array, "eye")
        features = extract_zone_features(real_image_array, zones)
        for zone_name, zone_data in features.items():
            assert "coordinates" in zone_data, (
                f"Zone '{zone_name}' missing 'coordinates' key"
            )
            # Either proper feature keys OR an 'error' key for empty regions
            has_features = "average_color" in zone_data and "redness" in zone_data
            has_error = "error" in zone_data
            assert has_features or has_error, (
                f"Zone '{zone_name}' has neither feature keys nor 'error': {zone_data}"
            )

    def test_normalize_image_returns_fixed_size(self, real_image_array):
        """normalize_image always resizes to (512, 512) regardless of input dimensions."""
        from app.services.analysis_pipeline import normalize_image

        normalized = normalize_image(real_image_array)
        assert normalized is not None
        assert normalized.ndim == 3
        assert normalized.shape[2] == 3  # BGR channels preserved
        # Default target size is (512, 512)
        assert normalized.shape == (512, 512, 3), (
            f"Expected normalized shape (512, 512, 3), got {normalized.shape}"
        )


class TestEyeEdgeCases:
    """Boundary and error-path tests for the eye endpoint."""

    def test_status_404_for_nonexistent_job(self):
        client = TestClient(app)
        response = client.get("/api/v1/analyze/status/99999")
        assert response.status_code == 404

    def test_report_404_for_nonexistent_job(self):
        client = TestClient(app)
        response = client.get("/api/v1/analyze/report/99999")
        assert response.status_code == 404

    def test_submit_without_file_returns_422(self):
        client = TestClient(app)
        response = client.post("/api/v1/analyze/eye")
        assert response.status_code == 422
