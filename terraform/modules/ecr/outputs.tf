output "repository_urls" {
  description = "Map of repository key to repository URL (without tag)"
  value       = { for k, r in aws_ecr_repository.this : k => r.repository_url }
}

output "repository_arns" {
  description = "Map of repository key to ARN"
  value       = { for k, r in aws_ecr_repository.this : k => r.arn }
}

output "repository_names" {
  description = "Map of repository key to name"
  value       = { for k, r in aws_ecr_repository.this : k => r.name }
}

output "api_repository_url" {
  description = "ECR repository URL for the API image"
  value       = try(aws_ecr_repository.this["api"].repository_url, null)
}

output "ui_repository_url" {
  description = "ECR repository URL for the UI image"
  value       = try(aws_ecr_repository.this["ui"].repository_url, null)
}

output "airflow_repository_url" {
  description = "ECR repository URL for the Airflow image"
  value       = try(aws_ecr_repository.this["airflow"].repository_url, null)
}
