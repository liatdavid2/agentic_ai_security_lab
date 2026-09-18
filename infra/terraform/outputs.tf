output "public_ip" {
  description = "Ephemeral public IPv4 address of the demo EC2 instance."
  value       = aws_instance.demo.public_ip
}

output "blue_team_url" {
  description = "BLUE TEAM HTTPS URL. Certificate bootstrap can take a few minutes after apply."
  value       = "https://${aws_instance.demo.public_ip}"
}

output "red_team_url" {
  description = "RED TEAM HTTPS URL. Certificate bootstrap can take a few minutes after apply."
  value       = "https://${aws_instance.demo.public_ip}:8443"
}

output "blue_team_swagger" {
  value = "https://${aws_instance.demo.public_ip}/docs"
}

output "red_team_swagger" {
  value = "https://${aws_instance.demo.public_ip}:8443/docs"
}

output "ssh_command" {
  description = "Shown only when key_name is set. Replace the key path with your local PEM file."
  value       = var.key_name != "" ? "ssh -i <YOUR_KEY.pem> ubuntu@${aws_instance.demo.public_ip}" : "No EC2 key pair configured."
}
