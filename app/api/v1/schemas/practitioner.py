from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# ZoneMap Schemas
# ─────────────────────────────────────────────

class ZoneMapCreate(BaseModel):
    name: str = Field(..., examples=["iris_default"], description="Unique name for this zone map")
    scan_type: str = Field(..., examples=["eye"], description="Scan type: eye, tongue, or face")
    description: Optional[str] = Field(None, description="Optional description of this zone map")


class ZoneMapUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New name for the zone map")
    scan_type: Optional[str] = Field(None, description="Scan type: eye, tongue, or face")
    description: Optional[str] = Field(None, description="Updated description")


class ZoneMapResponse(BaseModel):
    id: int
    name: str
    scan_type: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# ZoneRegion Schemas
# ─────────────────────────────────────────────

class ZoneRegionCreate(BaseModel):
    zone_map_id: int = Field(..., description="ID of the parent ZoneMap")
    name: str = Field(..., examples=["center"], description="Zone region name (must match pipeline zone names)")
    coordinates: Optional[str] = Field(
        None,
        examples=["[0.25, 0.25, 0.75, 0.75]"],
        description="JSON-encoded bounding box [x1, y1, x2, y2] as fractions 0-1"
    )
    description: Optional[str] = Field(None, description="Optional description")


class ZoneRegionUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New zone region name")
    coordinates: Optional[str] = Field(None, description="Updated coordinates JSON")
    description: Optional[str] = Field(None, description="Updated description")


class ZoneRegionResponse(BaseModel):
    id: int
    zone_map_id: int
    name: str
    coordinates: Optional[str]
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Rule Schemas
# ─────────────────────────────────────────────

class RuleCreate(BaseModel):
    zone_region_id: int = Field(..., description="ID of the zone region this rule applies to")
    scan_type: str = Field(..., examples=["eye"], description="Scan type: eye, tongue, or face")
    condition: str = Field(
        ...,
        examples=["redness > 0.1"],
        description="Rule condition evaluated against extracted zone features (redness, brightness, texture)"
    )
    finding: Optional[str] = Field(
        None,
        examples=["cardiac heat pattern"],
        description="Short name or category of the finding"
    )
    description: Optional[str] = Field(
        None,
        examples=["Elevated redness in iris center — possible heat pattern"],
        description="Human-readable finding text when rule is triggered"
    )
    severity: Optional[str] = Field(
        "medium",
        examples=["low", "medium", "high"],
        description="Severity level: low, medium, or high"
    )


class RuleUpdate(BaseModel):
    condition: Optional[str] = Field(None, description="Updated condition expression")
    finding: Optional[str] = Field(None, description="Updated finding name")
    description: Optional[str] = Field(None, description="Updated finding description")
    severity: Optional[str] = Field(None, description="Updated severity level")


class RuleResponse(BaseModel):
    id: int
    zone_region_id: int
    scan_type: str
    condition: str
    finding: Optional[str]
    description: Optional[str]
    severity: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# List response wrappers
# ─────────────────────────────────────────────

class ZoneMapListResponse(BaseModel):
    total: int
    items: List[ZoneMapResponse]


class ZoneRegionListResponse(BaseModel):
    total: int
    items: List[ZoneRegionResponse]


class RuleListResponse(BaseModel):
    total: int
    items: List[RuleResponse]
