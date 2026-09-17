from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json

app = FastAPI(title="Threat Hunting on Agents")
SHARED = Path("/shared/latest_benchmark.json")

SCENARIOS = {
    "secret-egress": {
        "name": "Secret Access → Suspicious Egress",
        "description": "An agent reads a sensitive file and shortly afterwards sends outbound traffic.",
        "recommended_control": "Secret isolation + egress restriction + least privilege",
        "events": [
            {"ts":"13:00:01","agent":"research-agent","event":"user_request","resource":"quarterly-summary","risk":"normal"},
            {"ts":"13:00:04","agent":"research-agent","event":"file_read","resource":"report.pdf","risk":"normal"},
            {"ts":"13:00:07","agent":"research-agent","event":"file_read","resource":".env","risk":"secret_access"},
            {"ts":"13:00:10","agent":"research-agent","event":"tool_request","resource":"http.post","risk":"suspicious"},
            {"ts":"13:00:12","agent":"research-agent","event":"network_egress","resource":"untrusted.example","risk":"high"},
        ]
    },
    "indirect-injection": {
        "name": "Indirect Prompt Injection → Tool Request",
        "description": "The agent reads untrusted content and then requests a privileged tool.",
        "recommended_control": "Context isolation + tool authorization + human approval",
        "events": [
            {"ts":"13:10:00","agent":"assistant-agent","event":"document_read","resource":"vendor-note.md","risk":"normal"},
            {"ts":"13:10:02","agent":"assistant-agent","event":"untrusted_instruction_detected","resource":"vendor-note.md","risk":"suspicious"},
            {"ts":"13:10:05","agent":"assistant-agent","event":"tool_request","resource":"admin.export","risk":"high"},
            {"ts":"13:10:06","agent":"assistant-agent","event":"policy_decision","resource":"BLOCKED","risk":"contained"},
        ]
    }
}

@app.get("/api/scenarios")
def scenarios():
    return [{"id": k, **v} for k,v in SCENARIOS.items()]

@app.get("/api/latest-llm-benchmark")
def latest_benchmark():
    if not SHARED.exists():
        return {"available": False, "models": []}
    try:
        data = json.loads(SHARED.read_text(encoding="utf-8"))
        return {"available": True, **data}
    except Exception as e:
        return {"available": False, "error": str(e), "models": []}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")
