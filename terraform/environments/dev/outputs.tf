output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_update_kubeconfig" {
  description = "Command to update kubeconfig"
  value       = "aws eks --region ${var.region} update-kubeconfig --name ${module.eks.cluster_name}"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.db_endpoint
}

output "rds_secret_arn" {
  description = "Secrets Manager ARN for RDS credentials"
  value       = module.rds.secrets_manager_secret_arn
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.redis_endpoint
}

output "mlflow_artifacts_bucket" {
  description = "S3 bucket for MLflow artifacts"
  value       = module.s3.mlflow_artifacts_bucket_name
}

output "raw_data_bucket" {
  description = "S3 bucket for raw market data"
  value       = module.s3.raw_data_bucket_name
}

output "app_namespace_names" {
  description = "App deployment namespace names"
  value       = module.kubernetes.app_namespace_names
}

output "ecr_api_repository_url" {
  description = "ECR repository URL for API images"
  value       = module.ecr.api_repository_url
}

output "ecr_ui_repository_url" {
  description = "ECR repository URL for UI images"
  value       = module.ecr.ui_repository_url
}

output "ecr_repository_urls" {
  description = "All ECR repository URLs"
  value       = module.ecr.repository_urls
}

output "api_irsa_role_arn" {
  description = "IAM role ARN for API pods (IRSA)"
  value       = module.iam.api_role_arn
}
