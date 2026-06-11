from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.schemas.common import APIResponse
from app.api.v1.schemas.practitioner import (
    RuleCreate,
    RuleListResponse,
    RuleResponse,
    RuleUpdate,
    ZoneMapCreate,
    ZoneMapListResponse,
    ZoneMapResponse,
    ZoneMapUpdate,
    ZoneRegionCreate,
    ZoneRegionListResponse,
    ZoneRegionResponse,
    ZoneRegionUpdate,
)
from app.db.models.rule import Rule
from app.db.models.zone_map import ZoneMap
from app.db.models.zone_region import ZoneRegion

router = APIRouter(prefix="/practitioner", tags=["Practitioner"])


# ─────────────────────────────────────────────
# Zone Maps
# ─────────────────────────────────────────────

@router.post(
    "/zone-maps",
    response_model=APIResponse[ZoneMapResponse],
    status_code=201,
    summary="Create a zone map",
    description="Create a new practitioner zone map for a given scan type (eye, tongue, face).",
)
def create_zone_map(payload: ZoneMapCreate, response: Response, db: Session = Depends(get_db)) -> APIResponse[ZoneMapResponse]:
    try:
        zone_map = ZoneMap(**payload.model_dump())
        db.add(zone_map)
        db.commit()
        db.refresh(zone_map)
        return APIResponse(status=True, message="Zone map created successfully", data=ZoneMapResponse.model_validate(zone_map))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get(
    "/zone-maps",
    response_model=APIResponse[ZoneMapListResponse],
    summary="List zone maps",
    description="List all practitioner zone maps, optionally filtered by scan type.",
)
def list_zone_maps(
    response: Response,
    scan_type: str | None = None,
    db: Session = Depends(get_db),
) -> APIResponse[ZoneMapListResponse]:
    try:
        query = db.query(ZoneMap)
        if scan_type:
            query = query.filter(ZoneMap.scan_type == scan_type)
        items = query.order_by(ZoneMap.id).all()
        data = ZoneMapListResponse(total=len(items), items=[ZoneMapResponse.model_validate(z) for z in items])
        return APIResponse(status=True, message="Success", data=data)
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get(
    "/zone-maps/{zone_map_id}",
    response_model=APIResponse[ZoneMapResponse],
    summary="Get a zone map",
)
def get_zone_map(zone_map_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[ZoneMapResponse]:
    try:
        zone_map = db.get(ZoneMap, zone_map_id)
        if zone_map is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneMap not found", errors={"detail": "ZoneMap not found"})
        return APIResponse(status=True, message="Success", data=ZoneMapResponse.model_validate(zone_map))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.put(
    "/zone-maps/{zone_map_id}",
    response_model=APIResponse[ZoneMapResponse],
    summary="Update a zone map",
    description="Update the name, scan type, or description of an existing zone map.",
)
def update_zone_map(
    zone_map_id: int,
    payload: ZoneMapUpdate,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[ZoneMapResponse]:
    try:
        zone_map = db.get(ZoneMap, zone_map_id)
        if zone_map is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneMap not found", errors={"detail": "ZoneMap not found"})
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(zone_map, field, value)
        db.commit()
        db.refresh(zone_map)
        return APIResponse(status=True, message="Zone map updated successfully", data=ZoneMapResponse.model_validate(zone_map))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.delete(
    "/zone-maps/{zone_map_id}",
    response_model=APIResponse[None],
    summary="Delete a zone map",
)
def delete_zone_map(zone_map_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[None]:
    try:
        zone_map = db.get(ZoneMap, zone_map_id)
        if zone_map is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneMap not found", errors={"detail": "ZoneMap not found"})
        db.delete(zone_map)
        db.commit()
        return APIResponse(status=True, message="Zone map deleted successfully")
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


# ─────────────────────────────────────────────
# Zone Regions
# ─────────────────────────────────────────────

@router.post(
    "/zone-regions",
    response_model=APIResponse[ZoneRegionResponse],
    status_code=201,
    summary="Create a zone region",
    description="Add a zone region to an existing zone map. The `name` must match the zone names returned by the analysis pipeline (e.g. `center`, `top_left`, `bottom_right`).",
)
def create_zone_region(payload: ZoneRegionCreate, response: Response, db: Session = Depends(get_db)) -> APIResponse[ZoneRegionResponse]:
    try:
        if db.get(ZoneMap, payload.zone_map_id) is None:
            response.status_code = 404
            return APIResponse(status=False, message="Parent ZoneMap not found", errors={"detail": "Parent ZoneMap not found"})
        zone_region = ZoneRegion(**payload.model_dump())
        db.add(zone_region)
        db.commit()
        db.refresh(zone_region)
        return APIResponse(status=True, message="Zone region created successfully", data=ZoneRegionResponse.model_validate(zone_region))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get(
    "/zone-regions",
    response_model=APIResponse[ZoneRegionListResponse],
    summary="List zone regions",
    description="List all zone regions, optionally filtered by parent zone map ID.",
)
def list_zone_regions(
    response: Response,
    zone_map_id: int | None = None,
    db: Session = Depends(get_db),
) -> APIResponse[ZoneRegionListResponse]:
    try:
        query = db.query(ZoneRegion)
        if zone_map_id:
            query = query.filter(ZoneRegion.zone_map_id == zone_map_id)
        items = query.order_by(ZoneRegion.id).all()
        data = ZoneRegionListResponse(total=len(items), items=[ZoneRegionResponse.model_validate(z) for z in items])
        return APIResponse(status=True, message="Success", data=data)
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get(
    "/zone-regions/{zone_region_id}",
    response_model=APIResponse[ZoneRegionResponse],
    summary="Get a zone region",
)
def get_zone_region(zone_region_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[ZoneRegionResponse]:
    try:
        zone_region = db.get(ZoneRegion, zone_region_id)
        if zone_region is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneRegion not found", errors={"detail": "ZoneRegion not found"})
        return APIResponse(status=True, message="Success", data=ZoneRegionResponse.model_validate(zone_region))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.put(
    "/zone-regions/{zone_region_id}",
    response_model=APIResponse[ZoneRegionResponse],
    summary="Update a zone region",
    description="Update the name, coordinates, or description of an existing zone region.",
)
def update_zone_region(
    zone_region_id: int,
    payload: ZoneRegionUpdate,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[ZoneRegionResponse]:
    try:
        zone_region = db.get(ZoneRegion, zone_region_id)
        if zone_region is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneRegion not found", errors={"detail": "ZoneRegion not found"})
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(zone_region, field, value)
        db.commit()
        db.refresh(zone_region)
        return APIResponse(status=True, message="Zone region updated successfully", data=ZoneRegionResponse.model_validate(zone_region))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.delete(
    "/zone-regions/{zone_region_id}",
    response_model=APIResponse[None],
    summary="Delete a zone region",
)
def delete_zone_region(zone_region_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[None]:
    try:
        zone_region = db.get(ZoneRegion, zone_region_id)
        if zone_region is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneRegion not found", errors={"detail": "ZoneRegion not found"})
        db.delete(zone_region)
        db.commit()
        return APIResponse(status=True, message="Zone region deleted successfully")
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


# ─────────────────────────────────────────────
# Rules
# ─────────────────────────────────────────────

@router.post(
    "/rules",
    response_model=APIResponse[RuleResponse],
    status_code=201,
    summary="Create a practitioner rule",
    description=(
        "Create a rule that the analysis engine will evaluate against extracted zone features. "
        "Supported features in conditions: `redness` (0-1), `brightness` (0-255), `texture` (float). "
        "Supported operators: `>`, `<`, `>=`, `<=`, `==`, `!=`."
    ),
)
def create_rule(payload: RuleCreate, response: Response, db: Session = Depends(get_db)) -> APIResponse[RuleResponse]:
    try:
        if db.get(ZoneRegion, payload.zone_region_id) is None:
            response.status_code = 404
            return APIResponse(status=False, message="ZoneRegion not found", errors={"detail": "ZoneRegion not found"})
        rule = Rule(**payload.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return APIResponse(status=True, message="Rule created successfully", data=RuleResponse.model_validate(rule))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get(
    "/rules",
    response_model=APIResponse[RuleListResponse],
    summary="List practitioner rules",
    description="List all rules, optionally filtered by scan type.",
)
def list_rules(
    response: Response,
    scan_type: str | None = None,
    zone_region_id: int | None = None,
    db: Session = Depends(get_db),
) -> APIResponse[RuleListResponse]:
    try:
        query = db.query(Rule)
        if scan_type:
            query = query.filter(Rule.scan_type == scan_type)
        if zone_region_id:
            query = query.filter(Rule.zone_region_id == zone_region_id)
        items = query.order_by(Rule.id).all()
        data = RuleListResponse(total=len(items), items=[RuleResponse.model_validate(r) for r in items])
        return APIResponse(status=True, message="Success", data=data)
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get(
    "/rules/{rule_id}",
    response_model=APIResponse[RuleResponse],
    summary="Get a rule",
)
def get_rule(rule_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[RuleResponse]:
    try:
        rule = db.get(Rule, rule_id)
        if rule is None:
            response.status_code = 404
            return APIResponse(status=False, message="Rule not found", errors={"detail": "Rule not found"})
        return APIResponse(status=True, message="Success", data=RuleResponse.model_validate(rule))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.put(
    "/rules/{rule_id}",
    response_model=APIResponse[RuleResponse],
    summary="Update a practitioner rule",
    description="Update the condition expression, description, or severity of an existing rule.",
)
def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[RuleResponse]:
    try:
        rule = db.get(Rule, rule_id)
        if rule is None:
            response.status_code = 404
            return APIResponse(status=False, message="Rule not found", errors={"detail": "Rule not found"})
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        db.commit()
        db.refresh(rule)
        return APIResponse(status=True, message="Rule updated successfully", data=RuleResponse.model_validate(rule))
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.delete(
    "/rules/{rule_id}",
    response_model=APIResponse[None],
    summary="Delete a rule",
)
def delete_rule(rule_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[None]:
    try:
        rule = db.get(Rule, rule_id)
        if rule is None:
            response.status_code = 404
            return APIResponse(status=False, message="Rule not found", errors={"detail": "Rule not found"})
        db.delete(rule)
        db.commit()
        return APIResponse(status=True, message="Rule deleted successfully")
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})
