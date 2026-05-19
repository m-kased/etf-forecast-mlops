output "mlflow_artifacts_bucket_name" {
  description = "Name of the MLflow artifacts S3 bucket"
  value       = aws_s3_bucket.mlflow_artifacts.id
}

output "mlflow_artifacts_bucket_arn" {
  description = "ARN of the MLflow artifacts S3 bucket"
  value       = aws_s3_bucket.mlflow_artifacts.arn
}

output "raw_data_bucket_name" {
  description = "Name of the raw market data S3 bucket"
  value       = aws_s3_bucket.raw_data.id
}

output "raw_data_bucket_arn" {
  description = "ARN of the raw market data S3 bucket"
  value       = aws_s3_bucket.raw_data.arn
}
