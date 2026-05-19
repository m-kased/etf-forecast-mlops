# ---------------------------------------------------------------------------
# Kubernetes Secrets — RDS credentials for app workloads
# ---------------------------------------------------------------------------

resource "kubernetes_secret" "airflow_rds" {
  metadata {
    name      = "airflow-rds-credentials"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }

  data = {
    DATABASE_URL = "postgresql://${var.rds_username}:${var.rds_password}@${var.rds_endpoint}:${var.rds_port}/airflow"
  }

  type = "Opaque"
}

resource "kubernetes_secret" "mlflow_rds" {
  metadata {
    name      = "mlflow-rds-credentials"
    namespace = kubernetes_namespace.mlflow.metadata[0].name
  }

  data = {
    DATABASE_URL = "postgresql://${var.rds_username}:${var.rds_password}@${var.rds_endpoint}:${var.rds_port}/mlflow"
  }

  type = "Opaque"
}
