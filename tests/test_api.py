"""
Integration tests for the FastAPI endpoints.
"""

import io
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_db


@pytest.fixture
def mock_db():
    """Provide a mocked database session that simulates job creation."""
    db = MagicMock(spec=Session)
    
    # Track jobs added to the database
    job_id_counter = [1]
    added_jobs = []
    
    def mock_add(job):
        """Mock the add operation - just track the job."""
        added_jobs.append(job)
    
    def mock_commit():
        """Mock commit - do nothing."""
        pass
    
    def mock_refresh(job):
        """Mock refresh - simulate populating the id after insertion."""
        if job.id is None:
            job.id = job_id_counter[0]
            job_id_counter[0] += 1
    
    db.add.side_effect = mock_add
    db.commit.side_effect = mock_commit
    db.refresh.side_effect = mock_refresh
    db.get.return_value = None  # Default to job not found
    
    return db


@pytest.fixture
def client(mock_db):
    """Provide a FastAPI test client with mocked database."""
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client):
        """Test that health check response has expected structure."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] is True
        assert "data" in data


class TestAnalysisEndpoints:
    """Tests for the /analyze endpoints."""

    @patch('app.api.v1.endpoints.analysis.save_upload_file')
    @patch('app.api.v1.endpoints.analysis.run_analysis_job')
    def test_analysis_endpoint_accepts_files(self, mock_task, mock_save, client, sample_image_path):
        """Test that analysis endpoint accepts file uploads."""
        # Mock the file save and task execution
        mock_save.return_value = "/uploads/test.jpg"
        mock_task.delay.return_value = None
        
        with open(sample_image_path, "rb") as f:
            response = client.post(
                "/api/v1/analyze/eye",
                files={"image": ("test.jpg", f, "image/jpeg")},
            )
        # Should succeed (200/201) with proper mocking
        assert response.status_code in [200, 201, 202]
        if response.status_code in [200, 201, 202]:
            resp_json = response.json()
            assert resp_json["status"] is True
            data = resp_json["data"]
            assert "job_id" in data
            assert "status" in data

    def test_analysis_requires_file(self, client):
        """Test that analysis endpoint requires a file."""
        response = client.post("/api/v1/analyze/eye")
        # Should fail because no file provided (400 Bad Request or 422 Unprocessable Entity)
        assert response.status_code in [400, 422]

    @patch('app.api.v1.endpoints.analysis.save_upload_file')
    @patch('app.api.v1.endpoints.analysis.run_analysis_job')
    def test_analysis_with_different_scan_types(self, mock_task, mock_save, client, sample_image_path):
        """Test analysis endpoint with different scan types."""
        mock_save.return_value = "/uploads/test.jpg"
        mock_task.delay.return_value = None
        
        for scan_type in ["eye", "tongue", "face"]:
            with open(sample_image_path, "rb") as f:
                response = client.post(
                    f"/api/v1/analyze/{scan_type}",
                    files={"image": ("test.jpg", f, "image/jpeg")},
                )
            # All scan types should be accepted
            assert response.status_code in [200, 201, 202]


class TestJobStatusEndpoint:
    """Tests for job status retrieval."""

    def test_job_status_endpoint_with_nonexistent_job(self, client):
        """Test that job status endpoint handles nonexistent jobs."""
        # Attempt to get status of non-existent job
        response = client.get("/api/v1/analyze/status/999")
        # Should return 404 (not found)
        assert response.status_code == 404
        assert response.json()["status"] is False

    def test_job_status_endpoint_with_valid_job(self, client, mock_db):
        """Test job status endpoint returns job data."""
        # Create a mock job
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.status = "pending"
        mock_db.get.return_value = mock_job
        
        response = client.get("/api/v1/analyze/status/1")
        # Should return 200 with job data
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert "job_id" in data
        assert "status" in data


class TestJobReportEndpoint:
    """Tests for job report retrieval."""

    def test_job_report_endpoint_with_nonexistent_job(self, client):
        """Test that job report endpoint handles nonexistent jobs."""
        response = client.get("/api/v1/analyze/report/999")
        assert response.status_code == 404

    def test_job_report_endpoint_with_valid_job(self, client, mock_db):
        """Test job report endpoint returns job reports."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.status = "completed"
        mock_db.get.return_value = mock_job

        mock_report = MagicMock()
        mock_report.id = 10
        mock_report.report_type = "practitioner"
        mock_report.content = '{"key": "value"}'
        from datetime import datetime
        mock_report.created_at = datetime(2026, 6, 10, 3, 18, 2)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_report]

        response = client.get("/api/v1/analyze/report/1")
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["job_id"] == 1
        assert data["status"] == "completed"
        assert len(data["reports"]) == 1
        assert data["reports"][0]["id"] == 10
        assert data["reports"][0]["report_type"] == "practitioner"
        assert data["reports"][0]["content"] == {"key": "value"}
