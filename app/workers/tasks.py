from __future__ import annotations

import json
import logging
from pathlib import Path

import cv2
from celery import Task

from app.db.base import SessionLocal
from app.db.models.analysis_job import AnalysisJob
from app.services.analysis_pipeline import detect_all, extract_zone_features, generate_zones, normalize_image, validate_image
from app.workers.celery_app import celery_app
from app.db.models.finding import Finding
from app.db.models.zone_map import ZoneMap
from app.db.models.zone_region import ZoneRegion
from app.services.report_generator import generate_report_for_job
from app.services.rule_engine import evaluate_rules

logger = logging.getLogger(__name__)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@celery_app.task(bind=True, name="a_eye_worker.run_analysis_job")
def run_analysis_job(self: Task, job_id: int) -> dict[str, str]:
    """Run a single analysis job in the background."""
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            logger.error("AnalysisJob %s not found", job_id)
            raise ValueError(f"AnalysisJob {job_id} not found")

        logger.info("Starting analysis job %s", job_id)
        job.status = "running"
        db.add(job)
        db.commit()
        db.refresh(job)

        input_data = json.loads(job.input_data or "{}")
        image_path = input_data.get("image_path")
        landmarks_str = input_data.get("landmarks")
        
        landmarks = None
        if landmarks_str:
            try:
                landmarks_raw = json.loads(landmarks_str)
                landmarks = []
                for lm in landmarks_raw:
                    x = lm.get("x", 0)
                    y = lm.get("y", 0)
                    z = lm.get("z", 0)
                    landmarks.append({"x": x, "y": y, "z": z})
            except Exception:
                logger.warning("Failed to parse landmarks JSON")

        if not image_path:
            raise ValueError("No image path provided for analysis job")

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from path: {image_path}")

        validation_results = validate_image(image)
        
        height, width = image.shape[:2]
        if landmarks:
            # Scale if normalized
            if all(lm["x"] <= 1.5 and lm["y"] <= 1.5 for lm in landmarks):
                for lm in landmarks:
                    lm["x"] *= width
                    lm["y"] *= height
                    
        detection_results = detect_all(image, landmarks)
        if job.scan_type.lower() == "face" and not landmarks and "landmarks" in detection_results.get("face", {}):
            landmarks = detection_results["face"]["landmarks"]
            
        zones = generate_zones(image, job.scan_type, landmarks, detection_results)
        zone_features = extract_zone_features(image, zones)
        normalized_image = normalize_image(image)

        normalized_path = Path(image_path).with_name(f"normalized_{Path(image_path).name}")
        cv2.imwrite(str(normalized_path), normalized_image)

        rule_findings = evaluate_rules(job.scan_type, zone_features, db)
        findings = []
        report_findings = []
        for finding_data in rule_findings:
            zone_name = finding_data["zone_name"]
            zone_region = db.query(ZoneRegion).filter(ZoneRegion.name == zone_name).first()
            if zone_region is None:
                zone_map = db.query(ZoneMap).filter(ZoneMap.name == f"{job.scan_type}_default").first()
                if zone_map is None:
                    zone_map = ZoneMap(name=f"{job.scan_type}_default", scan_type=job.scan_type)
                    db.add(zone_map)
                    db.commit()
                    db.refresh(zone_map)
                zone_region = ZoneRegion(
                    zone_map_id=zone_map.id,
                    name=zone_name,
                    coordinates=json.dumps(next((z.get("polygon", z.get("coordinates", [])) for z in zones if z["name"] == zone_name), [])),
                )
                db.add(zone_region)
                db.commit()
                db.refresh(zone_region)

            finding = Finding(
                analysis_job_id=job.id,
                rule_id=finding_data["rule_id"],
                zone_region_id=zone_region.id,
                status="triggered",
                notes=finding_data.get("notes", ""),
            )
            db.add(finding)
            db.commit()
            db.refresh(finding)
            findings.append(finding)
            
            report_findings.append({
                "zone_name": zone_name,
                "notes": finding.notes,
                "status": finding.status,
            })

        report_result = generate_report_for_job(job.id, job.scan_type, report_findings, db)

        result_data = {
            "image_path": image_path,
            "normalized_image_path": str(normalized_path),
            "validation": validation_results,
            "detection": detection_results,
            "zones": zones,
            "zone_features": zone_features,
            "findings": [f.notes for f in findings],
            "report": report_result,
        }

        job.result_data = json.dumps(result_data)
        job.status = "completed"
        db.add(job)
        db.commit()

        return {"status": "completed", "job_id": str(job_id)}
    except Exception as exc:
        logger.exception("Analysis job %s failed", job_id)
        if job is not None:
            job.status = "failed"
            job.result_data = json.dumps({"error": str(exc)})
            db.add(job)
            db.commit()
        raise
    finally:
        db.close()
