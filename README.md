# agentic_ai_security_lab

Two-service Docker Compose portfolio project for **LLM security evaluation, RED TEAM benchmarking, and BLUE TEAM threat hunting**.

The end-to-end flow is:

```text
JailbreakBench
   ↓
RED TEAM benchmark
   ↓
OpenAI target models
   ↓
Semantic judge
   ↓
Per-prompt security telemetry
   ↓
Shared benchmark results
   ↓
BLUE TEAM detections, findings, token usage, runtime and cost analysis
```

## Services

1. **BLUE TEAM — LLM Threat Hunting**
<img width="1917" height="962" alt="image" src="https://github.com/user-attachments/assets/be92f08e-8660-4167-bd26-e9d71d27d4fc" />

2. **RED TEAM — LLM Security Lab / Jailbreak Robustness Benchmark**
<img width="1917" height="855" alt="image" src="https://github.com/user-attachments/assets/d630a56a-093d-4f63-9940-fe2e8f325067" />

The project intentionally keeps only two application services in Docker Compose.

---

## Current benchmark configuration

### Target models

```text
gpt-5-nano
gpt-4.1-nano
gpt-4o-mini
```

### Semantic judge

```text
gpt-4.1
```

### Concurrency

```text
MAX_CONCURRENCY=10
```

Inference is performed directly through the **OpenAI Responses API**.

Ollama is not required.

---

## Local architecture

```text
Browser
   |
   +--> BLUE TEAM UI  http://localhost:8101
   |
   +--> RED TEAM UI   http://localhost:8102

RED TEAM
   |
   +--> OpenAI API
   |
   +--> /shared/latest_benchmark.json
   +--> /shared/benchmark_summary.csv
   +--> /shared/benchmark_events.csv
   +--> /shared/speed_test_results.csv

BLUE TEAM
   |
   +--> reads RED TEAM benchmark results from /shared
```

---

## OpenAI API secret handling

The OpenAI API key is **not baked into the Docker image** and is **not stored as an `OPENAI_API_KEY` container environment variable**.

The RED TEAM reads the key from a read-only file:

```text
/run/secrets/openai_api_key
```

Docker Compose mounts the host secret file as read-only:

```yaml
- ${OPENAI_SECRET_FILE:-./secrets/openai_api_key}:/run/secrets/openai_api_key:ro
```

### Local development

Create:

```text
secrets/openai_api_key
```

The file must contain only the key value:

```text
sk-...
```

Do not write:

```text
OPENAI_API_KEY=...
```

The `secrets/` directory contents are ignored by Git.

Check the secret mount without printing the secret:

```cmd
docker exec agentic-red-team sh -c "test -f /run/secrets/openai_api_key && test -s /run/secrets/openai_api_key && echo SECRET_OK || echo SECRET_BAD"
```

---

## Start locally

From the repository root:

```cmd
docker compose config
docker compose up -d --build
```

Open:

```text
BLUE TEAM UI: http://localhost:8101
RED TEAM UI:  http://localhost:8102

BLUE Swagger: http://localhost:8101/docs
RED Swagger:  http://localhost:8102/docs
```

Check containers:

```cmd
docker compose ps
```

Stop:

```cmd
docker compose down
```

---

## JailbreakBench

The RED TEAM service uses the official **JailbreakBench JBB-Behaviors** dataset.

Behavior:

- If the normalized official dataset already exists, it is reused.
- If it is missing, the service downloads the official harmful and benign CSV splits.
- There is no local smoke-test fallback.

Normalized dataset:

```text
/app/data/jailbreakbench_official.json
```

The project does not require the full `jailbreakbench` Python package.

---

## RED TEAM benchmark modes

### Fast benchmark

Uses a configurable stratified maximum number of rows per class.

Sampling is deterministic with seed:

```text
42
```

### Full benchmark

Uses the complete normalized JailbreakBench dataset.

### Speed test

A target-model speed test is run before benchmarking and reports model latency.

The RED TEAM UI displays:

- Attack Success Rate
- Refusal Rate
- Benign Pass Rate
- Average Latency
- Errors
- Benchmark progress

---

## Semantic evaluation

The primary security evaluation uses a semantic judge rather than simple refusal-pattern matching.

For harmful prompts, the judge classifies each response as:

```text
REFUSAL
SAFE_ALTERNATIVE
HARMFUL_COMPLIANCE
```

Only:

```text
HARMFUL_COMPLIANCE
```

counts as a successful jailbreak.

For benign prompts, the judge distinguishes successful answers from unnecessary refusals.

The older refusal-pattern heuristic can remain as a diagnostic field such as:

```text
heuristic_refused
```

but it does not determine the primary ASR result.

Judge failures are tracked separately and are excluded from security-metric denominators rather than silently counted as safe responses.

---

## Metrics

### Security

- **Attack Success Rate (ASR)** — lower is better.
- **Refusal Rate** — rate of harmful prompts refused.
- **Successful jailbreaks** — harmful responses judged as `HARMFUL_COMPLIANCE`.

### Utility

- **Benign Pass Rate** — benign prompts answered successfully.
- **Benign False Refusals** — harmless prompts unnecessarily refused.

### Performance

- **Average Latency**
- **Speed-test latency**
- **Concurrent evaluation**

### Token usage

The benchmark records token usage for both the target model and the semantic judge.

Per-event fields include:

```text
model_input_tokens
model_output_tokens
model_total_tokens

judge_input_tokens
judge_output_tokens
judge_total_tokens
```

### API cost

Estimated API cost is calculated from the pricing table embedded in:

```text
red-team/app.py
```

Main cost fields:

```text
model_input_cost_usd
model_output_cost_usd
model_cost_usd

judge_input_cost_usd
judge_output_cost_usd
judge_cost_usd

total_cost_usd
```

The pricing table is a snapshot and should be updated in code when provider pricing changes.

---

## RED TEAM → BLUE TEAM integration

RED TEAM writes aggregate results and one security event per benchmark prompt to the shared Docker volume.

BLUE TEAM reads the same run and provides:

- Security overview KPIs
- ASR by model
- Successful jailbreak findings
- Benign false-refusal findings
- Model-error and judge-error counts
- Detection rules
- Per-finding drill-down
- Model comparison
- Token usage analysis
- API cost analysis
- Security / utility / runtime / cost trade-off

The two services therefore operate on the same experiment:

```text
JailbreakBench
→ target-model responses
→ semantic evaluation
→ RED TEAM telemetry
→ BLUE TEAM detections
```

---

## BLUE TEAM dashboard

The BLUE TEAM dashboard is a compact SOC-style view of the latest benchmark.

### Main KPIs

- Harmful attempts
- Successful jailbreaks
- Benign false refusals
- Total benchmark events
- Top risky model
- Estimated total API cost

When all evaluated models have:

```text
ASR = 0%
```

the dashboard displays:

```text
No risky model detected
```

instead of arbitrarily selecting a model.

### Main panels

- Risk by model
- Detection rules
- Cost by model
- Model comparison
- Token usage by model
- Input/output cost
- Security findings
- Top failed topics when relevant

### Cost charts

Small API costs are shown directly in USD with adaptive decimal precision.

Examples:

```text
0.001
0.00023
0.000018
```

This avoids rounding small benchmark costs to `0.000`.

### Model comparison

The comparison table includes:

- ASR
- Benign Pass Rate
- Average Latency
- Input Tokens
- Output Tokens
- Total Cost
- Model Errors
- Judge Errors

---

## BLUE TEAM detections

Current detection logic includes findings such as:

```text
HARMFUL_COMPLIANCE
REPEATED_JAILBREAK_SUCCESS
HIGH_MODEL_ASR
BENIGN_OVER_REFUSAL
MODEL_ERROR
JUDGE_ERROR
```

Findings include severity, model, prompt ID, topic, response information and recommended control.

---

## Saved benchmark artifacts

The shared Docker volume contains:

```text
/shared/latest_benchmark.json
/shared/benchmark_summary.csv
/shared/benchmark_events.csv
/shared/speed_test_results.csv
```

The repository-level `history/` directory can store timestamped CSV snapshots without triggering additional model inference.

---

# AWS deployment with Terraform

The AWS deployment is designed as an **ephemeral portfolio/demo environment**.

The normal lifecycle is:

```text
terraform apply
→ run demo
→ terraform destroy
```

This avoids keeping an EC2 environment running when it is not needed.

---

## AWS architecture

```text
Internet
   |
   v
Public HTTPS
   |
   v
Nginx on EC2
   |
   +--> BLUE TEAM container
   |
   +--> RED TEAM container
             |
             +--> OpenAI API

AWS SSM Parameter Store
   |
   +--> SecureString OPENAI API key
             |
             v
      EC2 IAM Role
             |
             v
/opt/agentic_ai_security_lab/secrets/openai_api_key
             |
             | read-only bind mount
             v
/run/secrets/openai_api_key
```

The deployment uses:

- One EC2 instance
- One root EBS volume
- One security group
- One EC2 IAM role
- One IAM instance profile
- AWS Systems Manager Parameter Store
- Nginx
- Let's Encrypt certificate
- Docker Compose

It does not require:

- RDS
- NAT Gateway
- Application Load Balancer
- Kubernetes
- ECS
- Ollama

---

## AWS OpenAI secret

The OpenAI API key is stored once in AWS Systems Manager Parameter Store as a `SecureString`.

Terraform knows only the parameter name.

The secret value is not placed in:

- Git
- `terraform.tfvars`
- Terraform variables
- Terraform state
- EC2 user-data
- Docker image
- `OPENAI_API_KEY` container environment variable

### Create the secret once

From Windows CMD:

```cmd
set /p OPENAI_API_KEY=Paste OpenAI API key:
```

Then:

```cmd
aws ssm put-parameter --name "/agentic-ai-security-lab/openai-api-key" --type SecureString --tier Standard --value "%OPENAI_API_KEY%" --overwrite --region eu-central-1
```

Clear the local CMD variable:

```cmd
set OPENAI_API_KEY=
```

Verify the parameter exists:

```cmd
aws ssm get-parameter --name "/agentic-ai-security-lab/openai-api-key" --region eu-central-1
```

Do not add `--with-decryption` when only checking that the parameter exists.

---

## Terraform configuration

Terraform files are under:

```text
infra/terraform/
```

Typical files:

```text
provider.tf
variables.tf
main.tf
outputs.tf
user_data.sh.tftpl
terraform.tfvars.example
.gitignore
```

Create a local:

```text
terraform.tfvars
```

Example:

```hcl
aws_region    = "eu-central-1"
instance_type = "t3.small"

repo_url    = "https://github.com/YOUR_GITHUB_USER/agentic_ai_security_lab.git"
repo_branch = "main"

allowed_cidr = "YOUR_PUBLIC_IP/32"

key_name = "agentic-ai-demo"

openai_api_key_parameter_name = "/agentic-ai-security-lab/openai-api-key"
```

Never place the actual OpenAI key in `terraform.tfvars`.

---

## Terraform `.gitignore`

Recommended:

```gitignore
.terraform/
*.tfstate
*.tfstate.*
terraform.tfvars
crash.log
*.pem
.env
.env.*
*.key
*.zip
```

It is usually useful to commit:

```text
.terraform.lock.hcl
```

so provider versions remain reproducible.

---

## Deploy to AWS

From:

```cmd
cd infra\terraform
```

Run:

```cmd
terraform init
terraform validate
terraform plan
terraform apply
```

Confirm:

```text
yes
```

Terraform creates the EC2 infrastructure and IAM resources.

During EC2 bootstrap, `user_data.sh.tftpl`:

1. installs Docker, AWS CLI, Nginx and Certbot;
2. clones the GitHub repository;
3. retrieves the OpenAI API key from SSM using the EC2 IAM role;
4. writes it to:

```text
/opt/agentic_ai_security_lab/secrets/openai_api_key
```

5. applies restrictive file permissions;
6. mounts it read-only into the RED TEAM container;
7. starts Docker Compose;
8. configures HTTPS.

---

## AWS secret-file permissions

On the EC2 host:

```text
/opt/agentic_ai_security_lab/secrets/openai_api_key
```

is created as a root-owned secret file with restrictive permissions.

Inside RED TEAM it is available as:

```text
/run/secrets/openai_api_key
```

through a read-only mount.

Check without displaying the key:

```bash
sudo docker exec agentic-red-team sh -c 'test -s /run/secrets/openai_api_key && echo SECRET_OK || echo SECRET_BAD'
```

---

## Docker permissions on EC2

The bootstrap adds the `ubuntu` user to the Docker group.

If the current SSH session still gets:

```text
permission denied while trying to connect to the docker API
```

either use:

```bash
sudo docker ps
```

or reload group membership:

```bash
sudo usermod -aG docker ubuntu
newgrp docker
```

A fresh SSH session also reloads the group membership.

---

## Verify containers on AWS

```bash
sudo docker ps
```

Expected containers:

```text
agentic-red-team
agentic-blue-team
```

Check Compose:

```bash
cd /opt/agentic_ai_security_lab
sudo docker compose ps -a
```

Check RED TEAM logs:

```bash
sudo docker logs agentic-red-team --tail 100
```

Check BLUE TEAM logs:

```bash
sudo docker logs agentic-blue-team --tail 100
```

---

## HTTPS endpoints

Terraform outputs the public URLs.

Use:

```cmd
terraform output
```

or individually:

```cmd
terraform output public_ip
terraform output blue_team_url
terraform output red_team_url
terraform output blue_team_swagger
terraform output red_team_swagger
terraform output ssh_command
```

The Terraform configuration exposes the applications through Nginx HTTPS rather than directly exposing the application ports publicly.

---

## SSH

If an EC2 key pair is configured:

```cmd
ssh -i agentic-ai-demo.pem ubuntu@<PUBLIC_IP>
```

---

## Destroy after the demo

Stopping EC2 is not the same as removing all infrastructure costs.

For this project, the preferred lifecycle is:

```cmd
terraform plan -destroy
terraform destroy
```

Confirm:

```text
yes
```

The SSM OpenAI API parameter is intentionally created outside Terraform, so it remains available after:

```text
terraform destroy
```

The next:

```cmd
terraform apply
```

can reuse the same secret automatically.

---

## Security notes

Do not commit:

```text
terraform.tfstate
terraform.tfvars
*.pem
.env
secrets/openai_api_key
```

Do not print the OpenAI API key in logs or screenshots.

For verification, test only whether the secret file exists and is non-empty.

---

## Portfolio value

The project demonstrates:

- LLM security evaluation
- RED TEAM / BLUE TEAM workflows
- Jailbreak robustness benchmarking
- Semantic LLM judging
- Security telemetry
- Benign-utility evaluation
- Token accounting
- API cost accounting
- Concurrent model evaluation
- FastAPI
- Docker Compose
- SOC-style dashboards
- Swagger APIs
- AWS EC2
- Terraform
- IAM
- SSM Parameter Store
- Read-only secret handling
- HTTPS deployment
- Ephemeral apply / destroy infrastructure workflow
