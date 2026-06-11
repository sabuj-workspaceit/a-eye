import time
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_real_api")

API_BASE_URL = "http://localhost:8000"

def run_test():
    # 1. Health check
    try:
        health_resp = requests.get(f"{API_BASE_URL}/health")
        logger.info(f"Health check status: {health_resp.status_code}")
        logger.info(f"Health check response: {health_resp.json()}")
    except Exception as exc:
        logger.error(f"Failed to connect to FastAPI server at {API_BASE_URL}: {exc}")
        return

    # 2. Upload and start analysis
    image_path = "tests/assets/eye_sample.jpg"
    logger.info(f"Uploading image {image_path} for 'eye' scan type...")
    
    with open(image_path, "rb") as img_file:
        files = {"image": ("eye_sample.jpg", img_file, "image/jpeg")}
        resp = requests.post(f"{API_BASE_URL}/api/v1/analyze/eye", files=files)
        
    if resp.status_code != 200:
        logger.error(f"Analysis request failed with status {resp.status_code}: {resp.text}")
        return
        
    job_data = resp.json()
    job_id = job_data["job_id"]
    status = job_data["status"]
    logger.info(f"Job created successfully. Job ID: {job_id}, Status: {status}")

    # 3. Poll for status
    max_retries = 30
    for i in range(max_retries):
        status_resp = requests.get(f"{API_BASE_URL}/api/v1/analyze/status/{job_id}")
        if status_resp.status_code != 200:
            logger.error(f"Failed to get status: {status_resp.text}")
            return
            
        status_data = status_resp.json()
        current_status = status_data["status"]
        logger.info(f"Polled status (attempt {i+1}/{max_retries}): {current_status}")
        
        if current_status in ["completed", "failed"]:
            break
            
        time.sleep(1)
    else:
        logger.error("Job did not complete within the timeout period.")
        return

    # 4. Get and display the generated reports
    report_resp = requests.get(f"{API_BASE_URL}/api/v1/analyze/report/{job_id}")
    if report_resp.status_code != 200:
        logger.error(f"Failed to fetch report: {report_resp.text}")
        return
        
    report_data = report_resp.json()
    logger.info("=" * 60)
    logger.info("ANALYSIS REPORT RESULTS:")
    logger.info("=" * 60)
    logger.info(f"Job ID: {report_data['job_id']}")
    logger.info(f"Final Job Status: {report_data['status']}")
    logger.info(f"Number of generated reports: {len(report_data['reports'])}")
    
    for idx, report in enumerate(report_data['reports']):
        logger.info("-" * 40)
        logger.info(f"Report {idx+1}: {report['report_type'].upper()}")
        logger.info("-" * 40)
        # Clean print of content
        content = report['content']
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                pass
        logger.info(json.dumps(content, indent=2))
        
    logger.info("=" * 60)

if __name__ == "__main__":
    run_test()
