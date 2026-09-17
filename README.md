# agentic_ai_security_lab

Two-service Docker Compose lab:

1. **BLUE TEAM — Threat Hunting on Agents** — port `8101`
2. **RED TEAM — LLM Security Lab / Jailbreak Robustness Benchmark** — port `8102`

The LLM Security Lab now benchmarks **real local SLMs through Ollama**.  
Ollama is intentionally **not** a third Compose service, so the project stays at two services.

## 1. Install Ollama on the host

Install Ollama, then pull any models you want to compare. Suggested small models:

```bash
ollama pull qwen3:1.7b
ollama pull llama3.2:3b
ollama pull gemma3:1b
ollama pull phi4-mini
```

You can benchmark any Ollama model tag, not only these defaults.

## 2. Start the lab

```bash
docker compose up --build
```

Open:

- **BLUE TEAM UI — Threat Hunting:** http://localhost:8101
- **RED TEAM UI — LLM Security Benchmark:** http://localhost:8102

## 3. JailbreakBench

The RED TEAM service uses the **official JailbreakBench dataset only**.

Behavior:
- If the normalized official dataset already exists, it is reused.
- If it is missing, the service automatically downloads the official `JBB-Behaviors` harmful and benign CSV splits from the JailbreakBench Hugging Face repository during startup.
- There is no local smoke-test fallback.

The normalized dataset is stored at:

```text
/app/data/jailbreakbench_official.json
```

## Metrics

- **Attack Success Rate (ASR)** — lower is better.
- **Refusal Rate** — fraction of harmful prompts refused.
- **Benign Pass Rate** — fraction of benign prompts answered rather than unnecessarily refused.
- **Average Latency** — average wall-clock response time.
- **Throughput** — approximate generated tokens per second when Ollama reports token counts.

## Benchmark design

Each model receives the same prompts and the same system instruction.  
The service stores aggregate results in `/shared/latest_benchmark.json`; the Threat Hunting service can display a summary of the latest benchmark.

The built-in judge is deliberately simple and auditable: it uses response-pattern heuristics to classify refusal vs non-refusal. For research-grade evaluation, replace it with the official JailbreakBench judging pipeline or a validated external judge.


### Why the project does not `pip install jailbreakbench`

The upstream Python package currently pins an old LiteLLM dependency that may fail to resolve in modern Python/container environments. This project only needs the official JBB-Behaviors data, so it downloads the two official CSV splits directly from the JailbreakBench Hugging Face dataset repository instead of installing the full benchmark package.
