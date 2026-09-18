data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "demo" {
  name_prefix = "agentic-ai-security-lab-"
  description = "Temporary HTTPS demo access for BLUE TEAM and RED TEAM"

  ingress {
    description = "HTTP ACME challenge"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "BLUE TEAM HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  ingress {
    description = "RED TEAM HTTPS"
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  dynamic "ingress" {
    for_each = var.key_name != "" ? [1] : []
    content {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    }
  }

  egress {
    description = "Outbound internet for package install, Git, Docker, OpenAI API, SSM and ACME"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "agentic-ai-security-lab-demo"
    Project = "agentic_ai_security_lab"
  }
}


resource "aws_iam_role" "demo" {
  name_prefix = "agentic-ai-security-lab-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name    = "agentic-ai-security-lab-demo"
    Project = "agentic_ai_security_lab"
  }
}

resource "aws_iam_role_policy" "openai_parameter" {
  name = "read-openai-api-key"
  role = aws_iam_role.demo.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter"
      ]
      Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.openai_api_key_parameter_name}"
    }]
  })
}

resource "aws_iam_instance_profile" "demo" {
  name_prefix = "agentic-ai-security-lab-"
  role        = aws_iam_role.demo.name
}


locals {
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    repo_url                      = var.repo_url
    repo_branch                   = var.repo_branch
    aws_region                    = var.aws_region
    openai_api_key_parameter_name = var.openai_api_key_parameter_name
  })
}

resource "aws_instance" "demo" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.demo.id]
  key_name                    = var.key_name != "" ? var.key_name : null
  iam_instance_profile         = aws_iam_instance_profile.demo.name

  user_data                   = local.user_data
  user_data_replace_on_change = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    delete_on_termination = true
    encrypted             = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name    = "agentic-ai-security-lab-demo"
    Project = "agentic_ai_security_lab"
  }
}
