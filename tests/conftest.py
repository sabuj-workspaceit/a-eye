"""
Shared pytest fixtures and configuration for all tests.
"""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base


# Use an in-memory SQLite database for testing
@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Provide a database session for tests."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_upload_dir():
    """Provide a temporary directory for upload tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image_path():
    """Create a minimal test image file."""
    import numpy as np
    import cv2

    # Create a simple test image
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:] = (200, 150, 100)  # BGR color

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cv2.imwrite(f.name, image)
        yield f.name
        os.unlink(f.name)


@pytest.fixture
def mock_analysis_job_data():
    """Provide sample analysis job data for tests."""
    return {
        "scan_type": "eye",
        "status": "pending",
        "image_path": "/uploads/test.jpg",
        "findings": [],
    }
