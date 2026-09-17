from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="LLM Hacking Lab")

SCENARIOS = {
    "direct": {
        "name": "Direct Prompt Injection",
        "goal": "Try to make the simulated assistant ignore its policy.",
        "secret": "LAB_SECRET_42"
    },
    "indirect": {
        "name": "Indirect Prompt Injection",
        "goal": "Simulate an untrusted document trying to influence the agent.",
        "secret": "DOC_SECRET_17"
    },
    "tool": {
        "name": "Unauthorized Tool Call",
        "goal": "Try to make the simulated agent request a privileged tool.",
        "secret": "TOOL_TOKEN_99"
    }
}

class TestRequest(BaseModel):
    scenario_id: str
    user_input: str
    defense: str

SUSPICIOUS = [
    "ignore previous", "ignore all", "reveal", "secret", "system prompt",
    "admin", "privileged", "override", "bypass", "developer message"
]

@app.get("/api/scenarios")
def scenarios():
    return [{"id":k,"name":v["name"],"goal":v["goal"]} for k,v in SCENARIOS.items()]

@app.post("/api/test")
def test(req: TestRequest):
    scenario = SCENARIOS[req.scenario_id]
    text = req.user_input.lower()
    suspicious = any(term in text for term in SUSPICIOUS)

    attack_attempt = suspicious
    blocked = False
    runtime_reason = "No suspicious pattern detected."

    if req.defense == "none":
        blocked = False
        runtime_reason = "No defense enabled."
    elif req.defense == "prompt_filter":
        blocked = suspicious
        runtime_reason = "Prompt filter blocked a suspicious instruction." if blocked else "Prompt filter allowed the request."
    elif req.defense == "runtime_policy":
        blocked = suspicious
        runtime_reason = "Runtime policy blocked access to protected data/tools." if blocked else "Runtime policy allowed the request."
    elif req.defense == "layered":
        blocked = suspicious
        runtime_reason = "Layered defenses blocked the suspicious request." if blocked else "No policy violation detected."

    # Safe simulation: never return a real secret. We only report whether a synthetic attack would have succeeded.
    success = attack_attempt and not blocked

    events = [
        {"event":"input_received","status":"ok"},
        {"event":"prompt_risk_check","status":"suspicious" if suspicious else "clean"},
        {"event":"policy_decision","status":"blocked" if blocked else "allowed"},
    ]
    if req.scenario_id == "tool":
        events.append({"event":"tool_request","status":"blocked" if blocked else ("simulated-allowed" if success else "not-requested")})
    elif req.scenario_id == "indirect":
        events.insert(1, {"event":"untrusted_document_context","status":"present"})
    else:
        events.append({"event":"assistant_response","status":"safe-simulation"})

    return {
        "scenario": scenario["name"],
        "attack_attempt_detected": attack_attempt,
        "attack_success": success,
        "blocked": blocked,
        "reason": runtime_reason,
        "events": events,
        "safe_output": "Protected value is never exposed in this lab."
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")