variable "project_name" {
  description = "Project identifier used in resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "app_namespaces" {
  description = "Additional namespaces for application workloads (API, UI, etc.)"
  type = list(object({
    name            = string
    istio_injection = optional(bool, false)
    labels          = optional(map(string), {})
  }))
  default = []
}

variable "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  type        = string
  default     = ""
}

variable "rds_port" {
  description = "RDS PostgreSQL port"
  type        = number
  default     = 5432
}

variable "rds_username" {
  description = "RDS master username"
  type        = string
  default     = ""
}

variable "rds_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "rds_db_name" {
  description = "Default RDS database name (used for app workloads)"
  type        = string
  default     = "ml_data"
}

variable "region" {
  description = "AWS region (injected into Airflow platform ConfigMap)"
  type        = string
  default     = "us-east-1"
}

variable "redis_endpoint" {
  description = "ElastiCache Redis endpoint for Airflow workloads"
  type        = string
  default     = ""
}

variable "redis_port" {
  description = "ElastiCache Redis port"
  type        = number
  default     = 6379
}

variable "mlflow_artifacts_bucket" {
  description = "S3 bucket for MLflow artifacts"
  type        = string
  default     = ""
}

variable "raw_data_bucket" {
  description = "S3 bucket for market feature data"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags applied via labels where supported"
  type        = map(string)
  default     = {}
}

# --- Public ingress ---

variable "acme_email" {
  description = "Email address for Let's Encrypt ACME registration"
  type        = string
}

variable "acme_use_staging" {
  description = "Use Let's Encrypt staging CA (for testing; browsers will not trust certs)"
  type        = bool
  default     = false
}

variable "ingress_ui_host" {
  description = "Public hostname for the Streamlit UI"
  type        = string
  default     = "etf-forecast-mlops.mohamed-elkased.com"
}

variable "ingress_api_host" {
  description = "Public hostname for the FastAPI service"
  type        = string
  default     = "etf-forecast-mlops-api.mohamed-elkased.com"
}
