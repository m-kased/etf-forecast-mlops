locals {
  mlflow_bucket_name   = "${var.project_name}-mlflow-artifacts-${var.environment}"
  raw_data_bucket_name = "${var.project_name}-raw-data-${var.environment}"

  common_tags = merge(var.tags, {
    Module = "s3"
  })
}
