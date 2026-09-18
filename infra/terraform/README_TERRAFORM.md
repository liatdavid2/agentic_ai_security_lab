# Terraform deployment notes

This Terraform bootstrap configures Ollama automatically so Docker containers
can reach the host API at:

`http://host.docker.internal:11434`

The EC2 host configures:

`OLLAMA_HOST=0.0.0.0:11434`

Port `11434` is intentionally NOT opened in the AWS Security Group, so it is not publicly exposed.

## Deploy / Rebuild cleanly

From `infra/terraform`:

```cmd
terraform plan -destroy
terraform destroy
terraform plan
terraform apply
````

After `apply`, wait a few minutes for cloud-init to install Docker, Ollama, clone the repository, build the containers, and start Docker Compose.

## Get Public IP and SSH command

```cmd
terraform output public_ip
terraform output ssh_command
```

## Connect to EC2

```cmd
ssh -i agentic-ai-demo.pem ubuntu@<PUBLIC_IP>
```

## Check Docker services

```bash
docker ps
cd /opt/agentic_ai_security_lab
docker compose ps -a
```

## Sign in to Ollama Cloud

A new EC2 instance does not retain the previous Ollama Cloud login.

```bash
ollama signin
```

## Initialize / test cloud models

```bash
ollama run gpt-oss:20b-cloud "Say hello"
ollama run gemma4:31b-cloud "Say hello"
ollama run gpt-oss:120b-cloud "Say hello"
```

## Check Ollama models

```bash
curl http://localhost:11434/api/tags
```

## Check Ollama port

```bash
ss -ltnp | grep 11434
```

Expected:

```text
*:11434
```

## Test RED TEAM container → Ollama

```bash
docker exec -it llm-security-benchmark sh
```

Inside the container:

```sh
python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read().decode())"
```

Exit the container:

```sh
exit
```

## Check application logs

```bash
cd /opt/agentic_ai_security_lab

docker compose logs --tail=150
docker compose logs --tail=150 llm-security-service
docker compose logs --tail=150 threat-hunting-service
```

## Check Ollama service

```bash
systemctl status ollama --no-pager
```

## Check EC2 bootstrap logs

```bash
sudo tail -n 120 /var/log/cloud-init-output.log
```

## Destroy AWS environment

Exit EC2:

```bash
exit
```

From `infra/terraform`:

```cmd
terraform plan -destroy
terraform destroy
```

Confirm:

```text
yes
```

## Verify Terraform resources are gone

```cmd
terraform state list
```

```cmd
aws ec2 describe-instances --filters "Name=tag:Project,Values=agentic_ai_security_lab" --query "Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]" --output table
```

```cmd
aws ec2 describe-volumes --filters "Name=tag:Project,Values=agentic_ai_security_lab" --query "Volumes[].[VolumeId,State,Size]" --output table
```

```cmd
aws ec2 describe-security-groups --filters "Name=tag:Project,Values=agentic_ai_security_lab" --query "SecurityGroups[].[GroupId,GroupName]" --output table
```

```

