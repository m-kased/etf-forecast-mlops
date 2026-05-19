# ---------------------------------------------------------------------------
# Airflow
# ---------------------------------------------------------------------------

resource "helm_release" "airflow" {
  name             = "airflow"
  repository       = "https://airflow.apache.org"
  chart            = "airflow"
  version          = "1.16.0"
  namespace        = "airflow"
  create_namespace = false
  timeout          = 600

  values = [templatefile("${path.module}/values/airflow.yaml", {
    rds_endpoint            = var.rds_endpoint
    rds_port                = var.rds_port
    rds_db_name             = "airflow"
    rds_username            = var.rds_username
    rds_secret_arn          = var.rds_secret_arn
    airflow_role_arn        = var.airflow_role_arn
    mlflow_artifacts_bucket = var.mlflow_artifacts_bucket
    raw_data_bucket         = var.raw_data_bucket
    redis_endpoint          = var.redis_endpoint
    redis_port              = var.redis_port
    git_repo                = var.airflow_git_repo
    git_branch              = var.airflow_git_branch
    region                  = var.region
    environment             = var.environment
    mlflow_tracking_uri     = "http://mlflow.mlflow:5000"
  })]

  set_sensitive {
    name  = "data.metadataConnection.pass"
    value = var.rds_password
  }

  depends_on = [helm_release.istiod, terraform_data.namespace_airflow]
}
