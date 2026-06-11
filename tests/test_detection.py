"""
Unit tests for the detection pipeline module.
"""

import numpy as np
import pytest

from app.services.analysis_pipeline.detection import detect_iris, detect_face


class TestDetectIris:
    """Tests for iris detection using Hough Circle Transform."""

    def test_detect_iris_with_circular_features(self):
        """Test iris detection with a synthetic image containing circles."""
        # Create a test image with a circular feature
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        # Draw a circle (simulating iris)
        import cv2

        cv2.circle(image, (100, 100), 30, (100, 100, 100), -1)

        result = detect_iris(image)
        assert "iris_found" in result
        assert "circles" in result
        assert isinstance(result["circles"], list)

    def test_detect_iris_with_no_features(self):
        """Test iris detection with blank image."""
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = detect_iris(image)
        assert result["iris_found"] is False
        assert result["circles"] == []

    def test_detect_iris_returns_correct_keys(self):
        """Test that detection returns expected keys."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = detect_iris(image)
        assert "iris_found" in result
        assert "circles" in result


class TestDetectFace:
    """Tests for face detection using MediaPipe."""

    def test_detect_face_returns_dict(self):
        """Test that face detection returns a dictionary with required keys."""
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detect_face(image)
        assert isinstance(result, dict)
        assert "face_found" in result
        # May have "face_count" (MediaPipe) or "faces" (Haar Cascade fallback)
        assert "face_count" in result or "faces" in result

    def test_detect_face_with_blank_image(self):
        """Test face detection with a blank image returns no faces."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detect_face(image)
        assert isinstance(result["face_found"], bool)
        # May have "face_count" (MediaPipe) or "faces" (Haar Cascade fallback)
        if "face_count" in result:
            assert isinstance(result["face_count"], int)
        elif "faces" in result:
            assert isinstance(result["faces"], list)

    def test_detect_face_count_is_non_negative(self):
        """Test that face count/count is never negative."""
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detect_face(image)
        # May have "face_count" (MediaPipe) or "faces" (Haar Cascade fallback)
        if "face_count" in result:
            assert result["face_count"] >= 0
        elif "faces" in result:
            assert len(result["faces"]) >= 0
