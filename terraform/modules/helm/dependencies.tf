# Namespace readiness triggers — values come from the kubernetes module outputs.

resource "terraform_data" "namespace_istio_system" {
  input = var.namespace_istio_system
}

resource "terraform_data" "namespace_cert_manager" {
  input = var.namespace_cert_manager
}

resource "terraform_data" "namespace_monitoring" {
  input = var.namespace_monitoring
}

resource "terraform_data" "namespace_mlflow" {
  input = var.namespace_mlflow
}
