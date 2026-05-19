variable "project_name" {
  description = "Project identifier used in resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# --- IRSA (IAM Roles for Service Accounts) ---

variable "oidc_provider_arn" {
  description = "ARN of the EKS OIDC provider"
  type        = string
  default     = ""
}

variable "oidc_provider_url" {
  description = "URL of the EKS OIDC provider (without https:// prefix)"
  type        = string
  default     = ""
}

variable "mlflow_artifacts_bucket_arn" {
  description = "ARN of the S3 bucket used for MLflow artifact storage"
  type        = string
  default     = ""
}

variable "raw_data_bucket_arn" {
  description = "ARN of the S3 bucket used for raw ETL data"
  type        = string
  default     = ""
}

variable "mlflow_namespace" {
  description = "Kubernetes namespace where MLflow is deployed"
  type        = string
  default     = "mlflow"
}

variable "mlflow_service_account" {
  description = "Kubernetes service account name for MLflow"
  type        = string
  default     = "mlflow"
}

variable "airflow_namespace" {
  description = "Kubernetes namespace where Airflow is deployed"
  type        = string
  default     = "airflow"
}

variable "airflow_service_account" {
  description = "Kubernetes service account name for Airflow workers"
  type        = string
  default     = "airflow-worker"
}

variable "api_namespace" {
  description = "Kubernetes namespace where the API service is deployed"
  type        = string
  default     = "app"
}

variable "api_service_account" {
  description = "Kubernetes service account name for the API service"
  type        = string
  default     = "api"
}
