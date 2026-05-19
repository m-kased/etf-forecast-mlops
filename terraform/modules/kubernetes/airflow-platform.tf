resource "random_password" "airflow_fernet" {
  length  = 32
  special = false
}

resource "random_password" "airflow_jwt" {
  length  = 32
  special = false
}

resource "random_password" "airflow_internal_api" {
  length  = 32
  special = false
}

resource "random_password" "airflow_webserver_secret" {
  length  = 32
  special = false
}

resource "kubernetes_secret" "airflow_runtime" {
  metadata {
    name      = "airflow-runtime-secrets"
    namespace = "airflow"
  }

  type = "Opaque"

  string_data = {
    AIRFLOW__CORE__FERNET_KEY              = random_password.airflow_fernet.result
    AIRFLOW__API_AUTH__JWT_SECRET          = random_password.airflow_jwt.result
    AIRFLOW__CORE__INTERNAL_API_SECRET_KEY = random_password.airflow_internal_api.result
    AIRFLOW__WEBSERVER__SECRET_KEY         = random_password.airflow_webserver_secret.result
  }
}

resource "kubernetes_secret" "airflow_app" {
  metadata {
    name      = "airflow-app-credentials"
    namespace = "airflow"
  }

  type = "Opaque"

  string_data = {
    DATABASE_URL = "postgresql://${var.rds_username}:${var.rds_password}@${var.rds_endpoint}:${var.rds_port}/${var.rds_db_name}"
  }
}

resource "kubernetes_config_map" "airflow_platform" {
  metadata {
    name      = "airflow-platform-config"
    namespace = "airflow"
  }

  data = {
    AWS_DEFAULT_REGION         = var.region
    REDIS_HOST                 = var.redis_endpoint
    REDIS_PORT                 = tostring(var.redis_port)
    MLFLOW_S3_ARTIFACT_BUCKET  = var.mlflow_artifacts_bucket
    S3_DATA_BUCKET             = var.raw_data_bucket
    PROMETHEUS_PUSHGATEWAY_URL = "http://prometheus-pushgateway.monitoring.svc.cluster.local:9091"
  }
}
