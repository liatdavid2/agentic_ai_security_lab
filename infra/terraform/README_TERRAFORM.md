# Terraform deployment notes

This Terraform bootstrap now configures Ollama automatically so Docker containers
can reach the host API at:

`http://host.docker.internal:11434`

The EC2 host configures:

`OLLAMA_HOST=0.0.0.0:11434`

Port 11434 is intentionally NOT opened in the AWS Security Group, so it is not
publicly exposed.

## Rebuild cleanly

From `infra/terraform` (or this Terraform directory):

```cmd
terraform plan -destroy
terraform destroy
terraform plan
terraform apply
```

After `apply`, wait a few minutes for cloud-init to install Docker/Ollama and
start Docker Compose.

Useful checks over SSH:

```bash
docker ps
systemctl status ollama --no-pager
ss -ltnp | grep 11434
curl http://localhost:11434/api/tags
```

A brand-new EC2 instance does not retain the previous Ollama Cloud login.
For cloud-model inference, sign in again on the new host:

```bash
ollama signin
ollama run gpt-oss:20b-cloud "Say hello"
```

Then the RED TEAM container should be able to reach the host Ollama service.

To test from the RED TEAM container without curl:

```bash
docker exec -it llm-security-benchmark sh
python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read().decode())"
```
