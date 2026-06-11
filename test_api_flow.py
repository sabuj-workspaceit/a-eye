import time
import requests
import json

def run_test():
    url = "http://127.0.0.1:8000/api/v1/analyze/iris"
    image_path = "tests/assets/camera-eye_eye1.jpg"
    
    print(f"Uploading {image_path} to {url}...")
    try:
        with open(image_path, "rb") as f:
            files = {"image": f}
            response = requests.post(url, files=files)
    except Exception as e:
        print(f"Failed to connect to API: {e}")
        return
        
    print(f"Upload response: {response.status_code}")
    if response.status_code != 200:
        print(response.text)
        return
        
    job_id = response.json()["data"]["job_id"]
    print(f"Job created successfully! Job ID: {job_id}")
    print("Polling for results...")
    
    status_url = f"http://127.0.0.1:8000/api/v1/analyze/status/{job_id}"
    for _ in range(30):
        time.sleep(2)
        resp = requests.get(status_url)
        if resp.status_code != 200:
            print("Status fetch failed:", resp.status_code)
            continue
            
        data = resp.json()["data"]
        status = data["status"]
        print(f"Current status: {status}")
        
        if status in ("completed", "failed"):
            print("\n" + "="*40)
            print("ANALYSIS FINISHED")
            print("="*40)
            if data.get("result_data"):
                try:
                    res = json.loads(data["result_data"])
                    print("\n--- REPORT ---")
                    print(res.get("report", "No report field found in result_data."))
                except Exception as e:
                    print("Failed to parse result_data:", e)
                    print("Raw result:", data["result_data"])
            else:
                print("No result_data found in response.")
            break

if __name__ == "__main__":
    run_test()
