"""
Integration tests for the practitioner management API endpoints.
Covers ZoneMap, ZoneRegion, and Rule CRUD operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.db.base import Base


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_engine(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test_practitioner.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def test_session_factory(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="module")
def client(test_session_factory):
    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────
# ZoneMap tests
# ─────────────────────────────────────────────

class TestZoneMapEndpoints:
    def test_create_zone_map(self, client):
        """Create a zone map and verify 201 + returned data."""
        resp = client.post("/api/v1/practitioner/zone-maps", json={
            "name": "iris_test_map",
            "scan_type": "eye",
            "description": "Test iris zone map",
        })
        assert resp.status_code == 201
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["name"] == "iris_test_map"
        assert data["scan_type"] == "eye"
        assert "id" in data

    def test_list_zone_maps(self, client):
        """List zone maps and verify at least one is returned."""
        resp = client.get("/api/v1/practitioner/zone-maps")
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["total"] >= 1
        assert isinstance(data["items"], list)

    def test_list_zone_maps_filter_by_scan_type(self, client):
        """Filter zone maps by scan type."""
        resp = client.get("/api/v1/practitioner/zone-maps?scan_type=eye")
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        for item in data["items"]:
            assert item["scan_type"] == "eye"

    def test_get_zone_map_by_id(self, client):
        """Get a specific zone map by ID."""
        # First create one
        create_resp = client.post("/api/v1/practitioner/zone-maps", json={
            "name": "face_test_map", "scan_type": "face",
        })
        zone_map_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/practitioner/zone-maps/{zone_map_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == zone_map_id

    def test_get_zone_map_not_found(self, client):
        resp = client.get("/api/v1/practitioner/zone-maps/99999")
        assert resp.status_code == 404

    def test_update_zone_map(self, client):
        """Update a zone map description."""
        create_resp = client.post("/api/v1/practitioner/zone-maps", json={
            "name": "tongue_update_test", "scan_type": "tongue",
        })
        zone_map_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/practitioner/zone-maps/{zone_map_id}", json={
            "description": "Updated description",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["description"] == "Updated description"

    def test_update_zone_map_not_found(self, client):
        resp = client.put("/api/v1/practitioner/zone-maps/99999", json={"description": "X"})
        assert resp.status_code == 404

    def test_delete_zone_map(self, client):
        """Delete a zone map and verify it is gone."""
        create_resp = client.post("/api/v1/practitioner/zone-maps", json={
            "name": "to_delete_map", "scan_type": "eye",
        })
        zone_map_id = create_resp.json()["data"]["id"]

        del_resp = client.delete(f"/api/v1/practitioner/zone-maps/{zone_map_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/v1/practitioner/zone-maps/{zone_map_id}")
        assert get_resp.status_code == 404


# ─────────────────────────────────────────────
# ZoneRegion tests
# ─────────────────────────────────────────────

class TestZoneRegionEndpoints:
    @pytest.fixture(autouse=True)
    def zone_map_id(self, client):
        """Create a parent zone map for region tests."""
        resp = client.post("/api/v1/practitioner/zone-maps", json={
            "name": "region_parent_map", "scan_type": "eye",
        })
        self._zone_map_id = resp.json()["data"]["id"]

    def test_create_zone_region(self, client):
        resp = client.post("/api/v1/practitioner/zone-regions", json={
            "zone_map_id": self._zone_map_id,
            "name": "center",
            "coordinates": "[0.25, 0.25, 0.75, 0.75]",
            "description": "Central iris zone",
        })
        assert resp.status_code == 201
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["name"] == "center"
        assert data["zone_map_id"] == self._zone_map_id
        assert "id" in data

    def test_create_zone_region_invalid_parent(self, client):
        """Creating a zone region with a non-existent zone map should 404."""
        resp = client.post("/api/v1/practitioner/zone-regions", json={
            "zone_map_id": 99999,
            "name": "orphan",
        })
        assert resp.status_code == 404

    def test_list_zone_regions(self, client):
        resp = client.get("/api/v1/practitioner/zone-regions")
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_zone_regions_by_zone_map(self, client):
        resp = client.get(f"/api/v1/practitioner/zone-regions?zone_map_id={self._zone_map_id}")
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["zone_map_id"] == self._zone_map_id

    def test_get_zone_region_not_found(self, client):
        resp = client.get("/api/v1/practitioner/zone-regions/99999")
        assert resp.status_code == 404

    def test_update_zone_region(self, client):
        create_resp = client.post("/api/v1/practitioner/zone-regions", json={
            "zone_map_id": self._zone_map_id,
            "name": "top_left",
        })
        region_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/practitioner/zone-regions/{region_id}", json={
            "description": "Top-left quadrant",
            "coordinates": "[0, 0, 0.5, 0.5]",
        })
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["description"] == "Top-left quadrant"
        assert data["coordinates"] == "[0, 0, 0.5, 0.5]"

    def test_delete_zone_region(self, client):
        create_resp = client.post("/api/v1/practitioner/zone-regions", json={
            "zone_map_id": self._zone_map_id,
            "name": "to_delete_region",
        })
        region_id = create_resp.json()["data"]["id"]

        del_resp = client.delete(f"/api/v1/practitioner/zone-regions/{region_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/v1/practitioner/zone-regions/{region_id}")
        assert get_resp.status_code == 404


# ─────────────────────────────────────────────
# Rule tests
# ─────────────────────────────────────────────

class TestRuleEndpoints:
    @pytest.fixture(autouse=True)
    def setup_region(self, client):
        """Create a zone map + region to attach rules to."""
        zone_map_resp = client.post("/api/v1/practitioner/zone-maps", json={
            "name": "rule_test_map", "scan_type": "eye",
        })
        zone_map_id = zone_map_resp.json()["data"]["id"]

        region_resp = client.post("/api/v1/practitioner/zone-regions", json={
            "zone_map_id": zone_map_id, "name": "center",
        })
        self._zone_region_id = region_resp.json()["data"]["id"]

    def test_create_rule(self, client):
        resp = client.post("/api/v1/practitioner/rules", json={
            "zone_region_id": self._zone_region_id,
            "scan_type": "eye",
            "condition": "redness > 0.1",
            "description": "Elevated redness in iris center",
            "severity": "medium",
        })
        assert resp.status_code == 201
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["condition"] == "redness > 0.1"
        assert data["scan_type"] == "eye"
        assert data["severity"] == "medium"
        assert "id" in data

    def test_create_rule_invalid_zone_region(self, client):
        resp = client.post("/api/v1/practitioner/rules", json={
            "zone_region_id": 99999,
            "scan_type": "eye",
            "condition": "brightness < 50",
        })
        assert resp.status_code == 404

    def test_list_rules(self, client):
        resp = client.get("/api/v1/practitioner/rules")
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_rules_filter_by_scan_type(self, client):
        resp = client.get("/api/v1/practitioner/rules?scan_type=eye")
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["scan_type"] == "eye"

    def test_list_rules_filter_by_zone_region(self, client):
        resp = client.get(f"/api/v1/practitioner/rules?zone_region_id={self._zone_region_id}")
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["zone_region_id"] == self._zone_region_id

    def test_get_rule_not_found(self, client):
        resp = client.get("/api/v1/practitioner/rules/99999")
        assert resp.status_code == 404

    def test_update_rule_condition(self, client):
        create_resp = client.post("/api/v1/practitioner/rules", json={
            "zone_region_id": self._zone_region_id,
            "scan_type": "eye",
            "condition": "texture > 10",
            "severity": "low",
        })
        rule_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/practitioner/rules/{rule_id}", json={
            "condition": "texture > 20",
            "severity": "high",
            "description": "Updated — high texture complexity",
        })
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["status"] is True
        data = resp_json["data"]
        assert data["condition"] == "texture > 20"
        assert data["severity"] == "high"
        assert data["description"] == "Updated — high texture complexity"

    def test_update_rule_not_found(self, client):
        resp = client.put("/api/v1/practitioner/rules/99999", json={"condition": "redness > 0.5"})
        assert resp.status_code == 404

    def test_delete_rule(self, client):
        create_resp = client.post("/api/v1/practitioner/rules", json={
            "zone_region_id": self._zone_region_id,
            "scan_type": "eye",
            "condition": "brightness < 30",
        })
        rule_id = create_resp.json()["data"]["id"]

        del_resp = client.delete(f"/api/v1/practitioner/rules/{rule_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/v1/practitioner/rules/{rule_id}")
        assert get_resp.status_code == 404
