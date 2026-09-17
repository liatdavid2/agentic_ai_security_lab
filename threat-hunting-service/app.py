from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Threat Hunting on Agents")

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
    "poisoned-skill": {
        "name": "Poisoned Agent Skill",
        "description": "A previously benign skill introduces a new, unapproved dependency.",
        "recommended_control": "Signed skills + dependency allowlist + version pinning",
        "events": [
            {"ts":"13:05:00","agent":"repo-agent","event":"skill_load","resource":"github-summary@1.4.2","risk":"normal"},
            {"ts":"13:05:02","agent":"repo-agent","event":"dependency_load","resource":"helper-lib","risk":"normal"},
            {"ts":"13:05:03","agent":"repo-agent","event":"dependency_load","resource":"unknown-package","risk":"new_dependency"},
            {"ts":"13:05:06","agent":"repo-agent","event":"file_read","resource":"~/.ssh/config","risk":"high"},
        ]
    },
    "indirect-injection": {
        "name": "Indirect Prompt Injection → Tool Request",
        "description": "The agent reads untrusted content containing a hidden instruction and then requests a privileged tool.",
        "recommended_control": "Context isolation + tool authorization + human approval",
        "events": [
            {"ts":"13:10:00","agent":"assistant-agent","event":"document_read","resource":"vendor-note.md","risk":"normal"},
            {"ts":"13:10:02","agent":"assistant-agent","event":"untrusted_instruction_detected","resource":"vendor-note.md","risk":"suspicious"},
            {"ts":"13:10:05","agent":"assistant-agent","event":"tool_request","resource":"admin.export","risk":"high"},
            {"ts":"13:10:06","agent":"assistant-agent","event":"policy_decision","resource":"BLOCKED","risk":"contained"},
        ]
    }
}

class HuntRequest(BaseModel):
    scenario_id: str
    rule: str

def run_rule(events: List[Dict[str, Any]], rule: str):
    findings = []
    if rule == "secret_then_egress":
        secret_idx = next((i for i,e in enumerate(events) if e["risk"]=="secret_access"), None)
        egress_idx = next((i for i,e in enumerate(events) if e["event"]=="network_egress"), None)
        if secret_idx is not None and egress_idx is not None and egress_idx > secret_idx:
            findings.append("Secret access was followed by outbound network activity.")
    elif rule == "new_dependency":
        for e in events:
            if e["risk"]=="new_dependency":
                findings.append(f"Unapproved dependency detected: {e['resource']}")
    elif rule == "prompt_to_tool":
        inj = next((i for i,e in enumerate(events) if e["event"]=="untrusted_instruction_detected"), None)
        tool = next((i for i,e in enumerate(events) if e["event"]=="tool_request"), None)
        if inj is not None and tool is not None and tool > inj:
            findings.append("Untrusted instruction was followed by a privileged tool request.")
    elif rule == "high_risk":
        findings = [f"{e['ts']} {e['event']} → {e['resource']}" for e in events if e["risk"] in ("high","suspicious","secret_access","new_dependency")]
    return findings

@app.get("/api/scenarios")
def scenarios():
    return [{"id": k, "name": v["name"], "description": v["description"]} for k,v in SCENARIOS.items()]

@app.get("/api/scenarios/{scenario_id}")
def scenario(scenario_id: str):
    return SCENARIOS[scenario_id]

@app.post("/api/hunt")
def hunt(req: HuntRequest):
    scenario = SCENARIOS[req.scenario_id]
    findings = run_rule(scenario["events"], req.rule)
    return {
        "findings": findings,
        "finding_count": len(findings),
        "recommended_control": scenario["recommended_control"],
        "events": scenario["events"]
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")