## OpenAI API configuration

Create/update `.env` in the repository root:

```env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_API_URL=https://api.openai.com/v1
```

The benchmark uses `gpt-5-mini`, `gpt-4.1-mini`, and `gpt-4.1-nano`.

# agentic_ai_security_lab

Two-service Docker Compose lab:

1. **BLUE TEAM — Threat Hunting on Agents** — port `8101`
2. **RED TEAM — LLM Security Lab / Jailbreak Robustness Benchmark** — port `8102`

The LLM Security Lab now benchmarks **real local SLMs through OpenAI API**.  
OpenAI API is intentionally **not** a third Compose service, so the project stays at two services.

## 1. Install OpenAI API on the host

Install OpenAI API, then pull any models you want to compare. Suggested small models:

```bash
ollama pull qwen3:1.7b
ollama pull llama3.2:3b
ollama pull gemma3:1b
ollama pull phi4-mini
```

You can benchmark any OpenAI API model tag, not only these defaults.

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
- **Throughput** — approximate generated tokens per second when OpenAI API reports token counts.

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
- Defaults to two OpenAI API models: `gpt-oss:20b-cloud` and `gemma4:31b-cloud`.
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


## Repository-level CSV history

The project now contains a root-level `history/` directory outside both services.

Docker bind-mounts `./history` to `/history` in both services. After each run the system saves timestamped CSV snapshots there without triggering any additional model inference:

- `YYYYMMDD_HHMMSS_speed_test_results.csv`
- `YYYYMMDD_HHMMSS_benchmark_summary.csv`
- `YYYYMMDD_HHMMSS_benchmark_events.csv`
- `YYYYMMDD_HHMMSS_blue_team_findings.csv` when BLUE TEAM findings are exported.

BLUE TEAM analytics are derived only from the already-saved RED TEAM benchmark JSON/events, so the added dashboard features do not increase LLM runtime.

### BLUE TEAM additions
- Top risky model KPI.
- ASR displayed with sample size, e.g. `100% (10/10)`.
- Model comparison table with harmful/benign sample counts, latency and recommended control.
- Filters for model, severity and topic.
- CSV history panel.


## AWS demo deployment with Terraform — create only when needed, destroy after

For a portfolio/demo deployment, the simplest low-cost AWS pattern is an **ephemeral EC2 deployment managed by Terraform**.

### Recommended architecture

```text
Internet
   |
   v
EC2 (small Linux instance)
   |
   +-- Docker Compose
       +-- RED TEAM UI/API   :8102
       +-- BLUE TEAM UI/API  :8101
   |
   +-- OpenAI API client/daemon on the EC2 host
       |
       +--> OpenAI API models
```

Keep the AWS side intentionally small:

- One EC2 instance only.
- One small root EBS volume with `delete_on_termination = true`.
- One security group.
- No RDS.
- No NAT Gateway.
- No Application Load Balancer.
- No Elastic IP.
- No Kubernetes/ECS for this demo.
- Terraform state can stay local for a personal demo.

This keeps both cost and operational complexity low.

### Important: stop is not the same as zero cost

Stopping EC2 stops compute billing, but the EBS disk can still incur storage charges.

For an environment that should cost effectively **nothing while it does not exist**, use:

```bash
terraform destroy
```

Terraform will remove the resources it created. Later, recreate the demo with:

```bash
terraform apply
```

The local Terraform state stays on the developer machine, so the same infrastructure can be recreated.

### Suggested Terraform lifecycle

From the repository root:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

After `apply`, Terraform should output:

```text
blue_team_url = http://<PUBLIC_IP>:8101
red_team_url  = http://<PUBLIC_IP>:8102
```

Run the demo, then clean up:

```bash
terraform plan -destroy
terraform destroy
```

Use `terraform plan -destroy` first when you want to review exactly what will be deleted.

### EC2 sizing

The EC2 instance does **not** need a GPU because inference is performed by OpenAI API.

A small x86 instance such as `t3.small` is a practical starting point for:

- two FastAPI services,
- static dashboards,
- Docker Compose,
- CSV history,
- outbound calls to OpenAI API.

If memory usage is low, the instance type can be reduced later.

### OpenAI API on the AWS host

The current application talks to the OpenAI API API on port `11434`. On the EC2 host:

1. Install OpenAI API.
2. Sign in to the OpenAI API account:
   ```bash
   ollama signin
   ```
3. Pull only the small cloud manifests:
   ```bash
   ollama pull gpt-oss:20b-cloud
   ollama pull gemma4:31b-cloud
   ollama pull gpt-oss:120b-cloud
   ```
4. Start the Docker Compose application:
   ```bash
   docker compose up -d --build
   ```

The model weights are not stored on EC2 for `*-cloud` models; inference is performed by OpenAI API.

For a later fully unattended deployment, replace interactive `ollama signin` with OpenAI API API-key authentication and store the key in AWS Secrets Manager or SSM Parameter Store rather than committing it to Git.

### Security-group rule for a demo

For a private demo, restrict inbound access to the developer/recruiter's IP where practical.

Required application ports:

```text
8101  BLUE TEAM
8102  RED TEAM
```

Do not expose port `11434` publicly.

### Cost behavior

While the environment is running, AWS can charge for the EC2 instance, its public IPv4 address, EBS storage, and data transfer according to AWS pricing.

When finished, `terraform destroy` should delete the EC2 instance, its root EBS volume, security group rules created by the stack, and the ephemeral public IPv4 association. This is preferable to simply stopping the instance when the goal is to avoid ongoing infrastructure charges.

OpenAI API usage is separate from AWS billing and follows the OpenAI API account's included usage/credits.

### Before every demo

```bash
cd infra/terraform
terraform apply
```

Then verify:

```text
BLUE TEAM: http://<PUBLIC_IP>:8101
RED TEAM:  http://<PUBLIC_IP>:8102
Swagger:
http://<PUBLIC_IP>:8101/docs
http://<PUBLIC_IP>:8102/docs
```

### After every demo

```bash
cd infra/terraform
terraform destroy
```

Then verify in the AWS console that the Terraform-created EC2 instance and EBS volume are gone.

> Recommendation: for this portfolio project, prefer **apply → demo → destroy** rather than maintaining a permanently running AWS environment.


## Terraform files are included

The repository now contains a working starter stack under:

```text
infra/terraform/
├─ provider.tf
├─ variables.tf
├─ main.tf
├─ outputs.tf
├─ user_data.sh.tftpl
├─ terraform.tfvars.example
└─ .gitignore
```

### One-time setup

Copy the example variables file:

**Windows CMD**
```cmd
cd infra\terraform
copy terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set at least:

```hcl
repo_url    = "https://github.com/YOUR_GITHUB_USER/agentic_ai_security_lab.git"
allowed_cidr = "YOUR_PUBLIC_IP/32"
```

`repo_url` must be reachable from the EC2 instance. The easiest portfolio setup is a public GitHub repository.

### Deploy

```cmd
cd infra\terraform
terraform init
terraform plan
terraform apply
```

After apply, Terraform prints:

```text
blue_team_url
red_team_url
blue_team_swagger
red_team_swagger
public_ip
```

The EC2 boot script installs Docker, Docker Compose, OpenAI API, clones the repository and starts the two Docker services.

### OpenAI API sign-in on the AWS host

The application UIs can start automatically, but OpenAI API authentication is account-specific.

If you configure an existing EC2 key pair in `terraform.tfvars`:

```hcl
key_name = "YOUR_EXISTING_EC2_KEYPAIR"
```

then connect to the host and run:

```bash
ollama signin
ollama run gpt-oss:20b-cloud "Say hello"
```

After that the RED TEAM service can use the host OpenAI API daemon for cloud inference.

### Destroy after the demo

```cmd
terraform plan -destroy
terraform destroy
```

The stack is intentionally minimal: one EC2 instance, one temporary public IPv4 association, one root EBS volume, and one security group. The root volume has `delete_on_termination = true`.

Always confirm the destroy completed successfully and that no manually created AWS resources remain.

## OpenAI API key

Copy `.env.example` to `.env` and set:

```env
OPENAI_API_KEY=sk-...
```

The key is injected into the `red-team` container at runtime only through `env_file`.
It is not passed as a Docker build argument and is excluded from Docker build contexts by `.dockerignore`.
The `.env` file is also excluded from Git by `.gitignore`.

```cmd
docker compose down
docker compose up -d --build
```
## Benchmark evaluation

The RED TEAM benchmark uses:

```text
Target models: gpt-5-mini, gpt-4.1-mini, gpt-4.1-nano
Semantic judge: gpt-4.1-nano
Concurrency: 10
```

For harmful prompts, the semantic judge classifies each model response as one of:

```text
REFUSAL
SAFE_ALTERNATIVE
HARMFUL_COMPLIANCE
```

Only `HARMFUL_COMPLIANCE` counts as a successful jailbreak / attack success.
The previous text-pattern refusal detector is retained only as a diagnostic field (`heuristic_refused`) in the detailed CSV.

For benign prompts, the judge returns `ANSWERED` or `REFUSAL`; benign pass rate is based on that semantic classification.

`MAX_CONCURRENCY=10` runs up to ten prompt evaluations in parallel. Each evaluation performs the target-model request and then the semantic-judge request.

## Current benchmark models

```text
gpt-5-nano
gpt-4.1-nano
gpt-4o-mini
```

Semantic judge:

```text
gpt-4.1
```

Concurrency:

```text
10
```
