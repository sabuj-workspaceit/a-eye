from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.report import Report
from app.services.protocol_engine import apply_safety_filter, attach_recommendations, generate_summary


def generate_report_for_job(job_id: int, scan_type: str, findings: list[dict[str, object]], db: Session) -> dict[str, object]:
    findings_with_recommendations = attach_recommendations(findings, scan_type, db)
    summary = generate_summary(findings_with_recommendations, scan_type)
    summary = apply_safety_filter(summary)

    practitioner_report = Report(
        analysis_job_id=job_id,
        report_type="practitioner",
        content=json.dumps({
            "generated_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "findings": findings_with_recommendations,
        }),
    )
    db.add(practitioner_report)
    db.commit()
    db.refresh(practitioner_report)

    client_report = Report(
        analysis_job_id=job_id,
        report_type="client",
        content=json.dumps({
            "generated_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "findings": findings_with_recommendations,
        }),
    )
    db.add(client_report)
    db.commit()
    db.refresh(client_report)

    return {
        "practitioner_report_id": practitioner_report.id,
        "client_report_id": client_report.id,
        "summary": summary,
    }
