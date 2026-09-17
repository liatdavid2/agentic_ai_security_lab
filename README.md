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


## RED TEAM → BLUE TEAM integration

The RED TEAM stores both aggregate model metrics and one event per JailbreakBench prompt in the shared Docker volume.

The BLUE TEAM now reads the same run and provides:
- Security overview KPIs.
- ASR by model.
- Successful jailbreak findings.
- Benign false-refusal findings.
- Detection rules for repeated jailbreak success, high ASR, and over-refusal.
- Top failed JailbreakBench topics/categories.

This keeps the two services on the same experiment:
`JailbreakBench → SLM responses → RED TEAM results → BLUE TEAM detections and investigation`.


## RED TEAM benchmark modes and exports

The RED TEAM UI supports:

- **Fast benchmark** — stratified maximum number of rows **per class**. Default: 10,000 per class, editable in the UI.
- **Full benchmark** — uses all rows in every class.
- Live progress: `N/M models completed — currently running <model>` plus an overall progress bar and current sample counter.
- Automatic CSV persistence after each completed benchmark:
  - `/shared/benchmark_summary.csv`
  - `/shared/benchmark_events.csv`
- Both CSVs can be downloaded directly from the RED TEAM UI.

Fast-mode sampling is deterministic (seed 42) so runs are comparable.


## Latest portfolio features

### RED TEAM
- Defaults to two Ollama Cloud models: `gpt-oss:20b-cloud` and `gemma4:31b-cloud`.
- Requires a model speed test before the benchmark button is enabled.
- Speed test shows latency and Fast / Moderate / Slow status.
- Fast and Full benchmark modes remain available.
- Benchmark progress bar shows completed models and current sample progress.
- Results are persisted to CSV:
  - `/shared/benchmark_summary.csv`
  - `/shared/benchmark_events.csv`
  - `/shared/speed_test_results.csv`

### BLUE TEAM
- SOC-style findings with High / Medium / Low severity.
- Clickable drill-down for each finding.
- Drill-down shows model, prompt ID, topic, benchmark prompt, model response excerpt, outcome, latency, and recommended control.
- Detection rules include a concrete recommended control.
- BLUE TEAM findings can be exported to `/shared/blue_team_findings.csv`.
