output "nginx_public_ip" {
  description = "Public IP of the Nginx Frontend Server"
  value       = aws_instance.frontend.public_ip
}

output "backend_private_ip" {
  description = "Private IP of the Backend Server"
  value       = aws_instance.backend.private_ip
}

output "worker_private_ip" {
  description = "Private IP of the Worker Server"
  value       = aws_instance.worker.private_ip
}

output "rds_endpoint" {
  description = "Endpoint URL of the PostgreSQL database"
  value       = aws_db_instance.postgres.endpoint
}

