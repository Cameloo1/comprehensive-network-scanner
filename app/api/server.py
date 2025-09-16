from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
import ipaddress, uuid, os
import time
from collections import deque
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.core.db import init_db
from app.scans.baseline import run_tcp_scan
from app.report.generator import make_report
from fastapi.responses import FileResponse

app = FastAPI(title="Evolve NetScan", version="0.1.0")
templates = Jinja2Templates(directory="app/ui/templates")
RECENT = deque(maxlen=10)

class ScanRequest(BaseModel):
    target: str = Field(..., examples=["127.0.0.1","192.0.2.0/28"])
    safe_mode: bool = True

def expand_targets(target: str) -> list[str]:
    try:
        # Handle comma-separated targets first
        if "," in target:
            targets = [t.strip() for t in target.split(",")]
            expanded_targets = []
            for t in targets:
                expanded_targets.extend(expand_targets(t))  # Recursively expand each target
            return expanded_targets
        
        # Handle CIDR notation
        if "/" in target:
            net = ipaddress.ip_network(target, strict=False)
            return [str(ip) for ip in net.hosts()]
        
        # Try to parse as IP address first
        try:
            ipaddress.ip_address(target)
            return [target]
        except ValueError:
            # If not an IP, assume it's a hostname and return as-is
            # The scanning code will handle DNS resolution
            return [target]
    except ValueError as e:
        raise HTTPException(400, f"Invalid target: {e}")

def assert_authorized(target: str):
    lab_ok = any(target.startswith(p) for p in ("127.","10.","192.168.","172.16.","172.17.","172.18.","172.19.","172.20.","172.21.","172.22.","172.23.","172.24.","172.25.","172.26.","172.27.","172.28.","172.29.","172.30.","172.31."))
    if not (lab_ok or os.path.exists("AUTHORIZATION.txt")):
        raise HTTPException(403, "Authorization file missing for non-lab targets.")

@app.get("/health")
def health(): return {"ok": True}

def run_scan_background(scan_id: str, ips: list[str], safe_mode: bool):
    """Background task to run scan without blocking the API"""
    try:
        run_tcp_scan(scan_id, ips, safe_mode)
    except Exception as e:
        print(f"Background scan error: {e}")

@app.post("/scan/start")
def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    assert_authorized(req.target)
    now=time.time(); RECENT.append(now)
    recent = [t for t in list(RECENT) if now - t < 60]
    if len(recent)>3:
        raise HTTPException(429, "Rate limit: too many scans this minute.")
    with open("audit.log","a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} START {req.target} safe={req.safe_mode}\n")
    init_db()
    ips = expand_targets(req.target)
    scan_id = str(uuid.uuid4())
    
    # Start scan in background to prevent timeout
    background_tasks.add_task(run_scan_background, scan_id, ips, req.safe_mode)
    
    return {
        "scan_id": scan_id, 
        "status": "started",
        "message": "Scan started in background. Check /ui/result/{scan_id} for results."
    }

@app.get("/ui", response_class=HTMLResponse)
def ui_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ui/start")
def ui_start(target: str = Form(...), safe_mode: bool = Form(False), background_tasks: BackgroundTasks = None):
    data = start_scan(ScanRequest(target=target, safe_mode=safe_mode), background_tasks)
    return RedirectResponse(f"/ui/result/{data['scan_id']}", status_code=303)

@app.get("/scan/status/{scan_id}")
def scan_status(scan_id: str):
    """Check scan status"""
    p = f"runs/{scan_id}.json"
    if not os.path.exists(p):
        return {"status": "not_found", "message": "Scan not found"}
    
    try:
        with open(p, 'r') as f:
            data = json.load(f)
        return {"status": data.get("status", "unknown"), "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/ui/result/{scan_id}", response_class=HTMLResponse)
def ui_result(scan_id: str):
    p = f"runs/{scan_id}.json"
    if not os.path.exists(p): 
        return HTMLResponse("Scan not found or still running. Please wait and try again.", status_code=404)
    
    try:
        with open(p, 'r') as f:
            data = json.load(f)
        
        # Add Build Report button
        btn = f'<p><form method="post" action="/report/build/{scan_id}"><button>Build Report</button></form></p>'
        
        # Format the JSON nicely for display
        formatted_json = json.dumps(data, indent=2)
        return HTMLResponse(btn + "<pre>" + formatted_json + "</pre>")
    except Exception as e:
        return HTMLResponse(f"Error reading scan results: {e}", status_code=500)

@app.post("/report/build/{scan_id}")
def report_build(scan_id: str):
    paths = make_report(scan_id)
    return paths

@app.get("/report/{scan_id}.html")
def report_html(scan_id: str):
    p = f"reports/{scan_id}.html"
    if not os.path.exists(p): 
        raise HTTPException(404, "Not found")
    return FileResponse(p, media_type="text/html")

@app.get("/report/{scan_id}.pdf")
def report_pdf(scan_id: str):
    p = f"reports/{scan_id}.pdf"
    if not os.path.exists(p): 
        raise HTTPException(404, "Not found")
    return FileResponse(p, media_type="application/pdf")
