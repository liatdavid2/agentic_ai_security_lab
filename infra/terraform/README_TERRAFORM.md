# Terraform deployment notes — HTTPS with $0 TLS certificate cost

This version exposes the demo through **HTTPS without a domain, Route 53, ALB, or a paid TLS certificate**.
It uses a free Let's Encrypt short-lived certificate issued directly for the EC2 public IPv4 address.

Public endpoints after bootstrap:

- BLUE TEAM: `https://<PUBLIC_IP>`
- BLUE Swagger: `https://<PUBLIC_IP>/docs`
- RED TEAM: `https://<PUBLIC_IP>:8443`
- RED Swagger: `https://<PUBLIC_IP>:8443/docs`

The application containers continue to use their existing host ports `8101` and `8102`, but those ports are **not publicly opened** by Terraform. Nginx terminates TLS and proxies locally to them.

Ollama remains internal at:

`http://host.docker.internal:11434`

Port `11434` is intentionally NOT opened in the AWS Security Group.

## Cost model

HTTPS/TLS itself adds **$0 certificate cost**:

- Let's Encrypt certificate: free
- Nginx: free/open source, runs on the same EC2
- Certbot: free/open source, runs on the same EC2
- No domain required
- No Route 53 required
- No ALB required

You still pay the normal AWS costs while the EC2/public IPv4 exist. `terraform destroy` removes the Terraform-managed demo resources.

## Deploy / rebuild cleanly

From `infra/terraform`:

```cmd
terraform plan
terraform apply
```

Confirm with:

```text
yes
```

After `apply`, cloud-init installs Docker, Ollama, Nginx and Certbot, starts the Docker services, obtains the public-IP certificate, and enables HTTPS. Certificate issuance happens after EC2 creation, so the HTTPS URLs can take a few minutes to become reachable.

## Get URLs and SSH command

```cmd
terraform output public_ip
terraform output blue_team_url
terraform output red_team_url
terraform output blue_team_swagger
terraform output red_team_swagger
terraform output ssh_command
```

## Connect to EC2

```cmd
ssh -i agentic-ai-demo.pem ubuntu@<PUBLIC_IP>
```

## Check HTTPS

From the EC2 host:

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
sudo ss -ltnp | grep -E ':443|:8443'
sudo certbot certificates
```

From your PC:

```cmd
curl https://<PUBLIC_IP>
curl https://<PUBLIC_IP>:8443
```

Do **not** add `-k` for the normal test. A successful public Let's Encrypt certificate should validate normally.

## Check HTTPS / certificate bootstrap logs

```bash
sudo journalctl -u nginx -n 100 --no-pager
sudo tail -n 200 /var/log/cloud-init-output.log
sudo ls -la /etc/letsencrypt/live/
```

If certificate issuance failed, search bootstrap logs:

```bash
sudo grep -iE "certbot|letsencrypt|acme|certificate|nginx" /var/log/cloud-init-output.log | tail -n 100
```

## Check Docker services

```bash
docker ps
cd /opt/agentic_ai_security_lab
docker compose ps -a
docker compose logs --tail=150
```

## Sign in to Ollama Cloud

A new EC2 instance does not retain the previous Ollama Cloud login:

```bash
ollama signin
```

Test cloud models:

```bash
ollama run gpt-oss:20b-cloud "Say hello"
ollama run gemma4:31b-cloud "Say hello"
ollama run gpt-oss:120b-cloud "Say hello"
```

## Check Ollama

```bash
systemctl status ollama --no-pager
sudo journalctl -u ollama -n 100 --no-pager
curl http://localhost:11434/api/tags
ss -ltnp | grep 11434
```

Expected Ollama listener:

```text
*:11434
```

## Test RED TEAM container -> Ollama

```bash
docker exec -it llm-security-benchmark sh
```

Inside the container:

```sh
python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read().decode())"
```

Exit:

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
aws ec2 describe-network-interfaces --filters "Name=tag:Project,Values=agentic_ai_security_lab" --query "NetworkInterfaces[].[NetworkInterfaceId,Status,Attachment.InstanceId]" --output table
```

```cmd
aws ec2 describe-security-groups --filters "Name=tag:Project,Values=agentic_ai_security_lab" --query "SecurityGroups[].[GroupId,GroupName]" --output table
```

## Important notes

Let's Encrypt IP-address certificates are short-lived (about six days). That is a good match for this disposable `terraform apply -> demo -> terraform destroy` workflow. A fresh EC2 public IP receives a fresh certificate during bootstrap.

Port `80` is public only so the ACME HTTP-01 validation can prove control of the public IP. BLUE/RED application traffic is exposed only through HTTPS (`443` and `8443`). Ports `8101`, `8102`, and `11434` are not opened publicly by this Terraform configuration.
