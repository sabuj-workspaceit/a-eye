from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.protocol import Protocol

BLOCKED_WORDS = [
    "urgent", "emergency", "panic", "fatal",
    "diagnose", "treatment", "cure", "disease",
    "illness", "medical", "prescription", "therapy",
    "diagnosis", "treat", "cures"
]


def load_protocol(scan_type: str, db: Session) -> Protocol | None:
    return db.query(Protocol).filter(Protocol.scan_type == scan_type).first()


def generate_summary(findings: list[dict[str, object]], scan_type: str) -> str:
    summary_lines = [f"Scan type: {scan_type}"]
    summary_lines.append("Findings:")
    for finding in findings:
        summary_lines.append(f"- {finding.get('notes', 'No note')} in zone {finding.get('zone_name', 'unknown')}")
    return "\n".join(summary_lines)


def apply_safety_filter(text: str) -> str:
    filtered = text
    for blocked in BLOCKED_WORDS:
        filtered = filtered.replace(blocked, "[REDACTED]")
    return filtered


def attach_recommendations(findings: list[dict[str, object]], scan_type: str, db: Session) -> list[dict[str, object]]:
    protocol = load_protocol(scan_type, db)
    recommendation = protocol.description if protocol else "No protocol available for this scan type."
    for finding in findings:
        findings_text = finding.get("notes", "")
        finding["recommendation"] = apply_safety_filter(recommendation)
    return findings
