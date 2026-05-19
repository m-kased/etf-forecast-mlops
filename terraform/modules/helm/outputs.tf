output "grafana_namespace" {
  description = "Namespace where Grafana is deployed"
  value       = "monitoring"
}

output "prometheus_namespace" {
  description = "Namespace where Prometheus is deployed"
  value       = "monitoring"
}

output "airflow_namespace" {
  description = "Namespace where Airflow is deployed"
  value       = "airflow"
}

output "mlflow_namespace" {
  description = "Namespace where MLflow is deployed"
  value       = "mlflow"
}

output "istio_namespace" {
  description = "Namespace where Istio is deployed"
  value       = "istio-system"
}
