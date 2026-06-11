import pytest
import numpy as np
from app.services.analysis_pipeline.zoning import generate_zones

class TestZoning:
    def test_generate_iris_zones(self):
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        zones = generate_zones(image, "iris")
        assert len(zones) == 36
        # Basic check of zone structure
        assert "name" in zones[0]
        assert "coordinates" in zones[0]
        assert "polygon" in zones[0]

    def test_generate_face_zones(self):
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Mock landmarks uniformly distributed to ensure all geometric zones are hit
        landmarks = []
        for x in range(0, 100, 5):
            for y in range(0, 100, 5):
                landmarks.append({"x": float(x), "y": float(y), "z": 0.0})
        zones = generate_zones(image, "face", landmarks=landmarks[:468])
        assert len(zones) > 0
        names = [z["name"] for z in zones]
        assert "forehead" in names
        assert "chin" in names
        assert "left_cheek" in names
        assert "right_cheek" in names

    def test_generate_tongue_zones(self):
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        detection_results = {"tongue": {"bbox": [20, 20, 80, 80]}}
        zones = generate_zones(image, "tongue", detection_results=detection_results)
        assert len(zones) == 5
        names = [z["name"] for z in zones]
        assert "tip" in names
        assert "rear" in names
        assert "center" in names
