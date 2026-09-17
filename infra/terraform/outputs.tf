output "public_ip" {
  description = "Ephemeral public IPv4 address of the demo EC2 instance."
  value       = aws_instance.demo.public_ip
}

output "blue_team_url" {
  value = "http://${aws_instance.demo.public_ip}:8101"
}

output "red_team_url" {
  value = "http://${aws_instance.demo.public_ip}:8102"
}

output "blue_team_swagger" {
  value = "http://${aws_instance.demo.public_ip}:8101/docs"
}

output "red_team_swagger" {
  value = "http://${aws_instance.demo.public_ip}:8102/docs"
}

output "ssh_command" {
  description = "Shown only when key_name is set. Replace the key path with your local PEM file."
  value       = var.key_name != "" ? "ssh -i <YOUR_KEY.pem> ubuntu@${aws_instance.demo.public_ip}" : "No EC2 key pair configured."
}
