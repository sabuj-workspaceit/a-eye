import json

from fastapi import APIRouter, Depends, File, Response, UploadFile, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.schemas.analysis import AnalysisJobResponse, AnalysisReportResponse
from app.api.v1.schemas.common import APIResponse
from app.db.models.analysis_job import AnalysisJob
from app.db.models.report import Report
from app.services.storage import save_upload_file
from app.workers.tasks import run_analysis_job

router = APIRouter()


@router.post("/analyze/{scan_type}", response_model=APIResponse[AnalysisJobResponse], tags=["Analysis"])
async def create_analysis_job(
    scan_type: str,
    response: Response,
    image: UploadFile = File(...),
    landmarks: str | None = Form(None),
    db: Session = Depends(get_db),
) -> APIResponse[AnalysisJobResponse]:
    try:
        try:
            image_path = save_upload_file(image, subdir=scan_type)
        except Exception as exc:
            response.status_code = 500
            return APIResponse(status=False, message="Failed to save uploaded image", errors={"detail": str(exc)})

        job = AnalysisJob(
            scan_type=scan_type,
            status="pending",
            input_data=json.dumps({"image_path": image_path, "landmarks": landmarks}),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        run_analysis_job.delay(job.id)

        return APIResponse(
            status=True, 
            message="Analysis job created successfully", 
            data=AnalysisJobResponse(job_id=job.id, status=job.status)
        )
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get("/analyze/status/{job_id}", response_model=APIResponse[dict], tags=["Analysis"])
async def get_analysis_status(job_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[dict]:
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            response.status_code = 404
            return APIResponse(status=False, message="Analysis job not found", errors={"detail": "Job not found"})
        data = {"job_id": str(job.id), "status": job.status}
        if job.status == "failed" and job.result_data:
            try:
                res = json.loads(job.result_data)
                if "error" in res:
                    data["reason"] = res["error"]
            except Exception:
                pass
        return APIResponse(status=True, message="Success", data=data)
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})


@router.get("/analyze/report/{job_id}", response_model=APIResponse[AnalysisReportResponse], tags=["Analysis"])
async def get_analysis_report(job_id: int, response: Response, db: Session = Depends(get_db)) -> APIResponse[AnalysisReportResponse]:
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            response.status_code = 404
            return APIResponse(status=False, message="Analysis job not found", errors={"detail": "Job not found"})
        
        reports = db.query(Report).filter(Report.analysis_job_id == job_id).all()
        
        formatted_reports = []
        for r in reports:
            try:
                content_json = json.loads(r.content) if r.content else None
            except Exception:
                content_json = r.content
            
            formatted_reports.append({
                "id": r.id,
                "report_type": r.report_type,
                "content": content_json,
                "created_at": r.created_at
            })
            
        response_data = {
            "job_id": job.id,
            "status": job.status,
            "reports": formatted_reports
        }
        if job.status == "failed" and job.result_data:
            try:
                res = json.loads(job.result_data)
                if "error" in res:
                    response_data["reason"] = res["error"]
            except Exception:
                pass
            
        return APIResponse(
            status=True, 
            message="Success", 
            data=AnalysisReportResponse(**response_data)
        )
    except Exception as exc:
        response.status_code = 500
        return APIResponse(status=False, message="An error occurred", errors={"detail": str(exc)})
