from datetime import datetime
from typing import Any, List
from pydantic import BaseModel


class AnalysisJobResponse(BaseModel):
    job_id: int
    status: str = "pending"


class ReportResponse(BaseModel):
    id: int
    report_type: str
    content: Any
    created_at: datetime


class AnalysisReportResponse(BaseModel):
    job_id: int
    status: str
    reports: List[ReportResponse]
