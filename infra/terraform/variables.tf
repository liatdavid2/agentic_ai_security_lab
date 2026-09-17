variable "aws_region" {
  description = "AWS region for the demo."
  type        = string
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "EC2 instance type. No GPU is required because model inference is done by Ollama Cloud."
  type        = string
  default     = "t3.small"
}

variable "allowed_cidr" {
  description = "CIDR allowed to reach the demo UIs and SSH. For a private demo, set this to YOUR_PUBLIC_IP/32."
  type        = string
  default     = "0.0.0.0/0"
}

variable "repo_url" {
  description = "Public Git repository URL for agentic_ai_security_lab, e.g. https://github.com/<user>/agentic_ai_security_lab.git"
  type        = string
}

variable "repo_branch" {
  description = "Git branch to deploy."
  type        = string
  default     = "main"
}

variable "root_volume_gb" {
  description = "Root EBS volume size."
  type        = number
  default     = 16
}

variable "key_name" {
  description = "Optional existing EC2 key pair name for SSH. Leave empty to create the instance without an SSH key."
  type        = string
  default     = ""
}
