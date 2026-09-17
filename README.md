# Agentic AI Security Lab

A local, safe training lab with exactly two Docker Compose services:

1. **Threat Hunting on Agents** — investigate synthetic agent telemetry and identify attack chains.
2. **LLM Hacking / Jailbreak / Prompt Injection** — test a simulated agent against controlled prompt-injection scenarios and compare defenses.

## Run

```bash
docker compose up --build
```

Then open:

- Threat Hunting UI: http://localhost:8101
- LLM Hacking UI: http://localhost:8102

Stop:

```bash
docker compose down
```

## Safety / scope

This lab is intentionally synthetic and local. It does not connect to real targets, exfiltrate secrets, or execute privileged tools.
The "LLM hacking" service simulates policy outcomes so you can learn the concepts safely and reproducibly.

## Structure

```text
agentic-ai-security-lab/
├─ docker-compose.yml
├─ threat-hunting-service/
│  ├─ app.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ static/index.html
└─ llm-hacking-service/
   ├─ app.py
   ├─ requirements.txt
   ├─ Dockerfile
   └─ static/index.html
```