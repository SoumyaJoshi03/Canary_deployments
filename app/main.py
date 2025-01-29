import os
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import subprocess
import requests

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def handle_upload(request: Request, model: UploadFile = File(...)):
    # Validate file extension
    allowed_extensions = [".pt", ".pth", ".h5", ".pb", ".onnx"]
    filename = model.filename
    _, ext = os.path.splitext(filename)
    if ext.lower() not in allowed_extensions:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": "Invalid file type. Allowed types: .pt, .pth, .h5, .pb, .onnx"
        })
    
    # Save the uploaded model
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(model.file, buffer)
    
    # Trigger CI/CD pipeline or deployment process
    # Option 1: Use a local script (deploy_new_model.sh)
    # Option 2: Trigger GitHub Actions via API
    # Below is Option 2
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise Exception("GITHUB_TOKEN not set in environment variables.")
        
        model_version = os.getenv("MODEL_VERSION", "v1")
        # Optionally, generate a unique version identifier
        # For simplicity, using model_version from environment
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "event_type": "model-upload",
            "client_payload": {
                "model_path": file_path,
                "model_version": model_version
            }
        }
        response = requests.post(
            "https://api.github.com/repos/your-username/ai-canary-deployment/actions/workflows/deploy.yml/dispatches",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
    except Exception as e:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": f"Failed to trigger deployment: {str(e)}"
        })
    
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/success", response_class=HTMLResponse)
async def upload_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

# API endpoint to fetch model statistics
@app.get("/api/model-stats", response_class=JSONResponse)
async def get_model_stats():
    # Fetch metrics from Prometheus
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus-operated.monitoring.svc.cluster.local:9090")
    
    try:
        # Example Prometheus queries
        accuracy_query = 'avg(rate(model_accuracy[1m])) * 100'
        latency_query = 'avg(rate(model_latency_seconds_sum[1m])) / avg(rate(model_latency_seconds_count[1m])) * 1000'
        traffic_split_query = 'sum(rate(http_requests_total{version="v2"}[1m])) / sum(rate(http_requests_total[1m])) * 100'
        
        accuracy_response = requests.get(f"{prometheus_url}/api/v1/query", params={'query': accuracy_query})
        latency_response = requests.get(f"{prometheus_url}/api/v1/query", params={'query': latency_query})
        traffic_split_response = requests.get(f"{prometheus_url}/api/v1/query", params={'query': traffic_split_query})
        
        accuracy_response.raise_for_status()
        latency_response.raise_for_status()
        traffic_split_response.raise_for_status()
        
        accuracy_data = accuracy_response.json()
        latency_data = latency_response.json()
        traffic_split_data = traffic_split_response.json()
        
        # Extract values
        accuracy = accuracy_data['data']['result'][0]['value'][1] if accuracy_data['data']['result'] else "N/A"
        latency = latency_data['data']['result'][0]['value'][1] if latency_data['data']['result'] else "N/A"
        traffic_split = traffic_split_data['data']['result'][0]['value'][1] if traffic_split_data['data']['result'] else "N/A"
        
        return {
            "accuracy": float(accuracy) if accuracy != "N/A" else "N/A",
            "latency": float(latency) if latency != "N/A" else "N/A",
            "traffic_split": float(traffic_split) if traffic_split != "N/A" else "N/A"
        }
        
    except Exception as e:
        # Log the error
        print(f"Error fetching model stats: {e}")
        return {
            "accuracy": "N/A",
            "latency": "N/A",
            "traffic_split": "N/A"
        }
