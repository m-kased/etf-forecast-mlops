output "namespace_istio_system" {
  description = "UID of the istio-system namespace (for helm depends_on)"
  value       = kubernetes_namespace.istio_system.metadata[0].uid
}

output "namespace_cert_manager" {
  description = "UID of the cert-manager namespace (for helm depends_on)"
  value       = kubernetes_namespace.cert_manager.metadata[0].uid
}

output "namespace_monitoring" {
  description = "UID of the monitoring namespace (for helm depends_on)"
  value       = kubernetes_namespace.monitoring.metadata[0].uid
}

output "namespace_airflow" {
  description = "UID of the airflow namespace (for helm depends_on)"
  value       = kubernetes_namespace.airflow.metadata[0].uid
}

output "namespace_mlflow" {
  description = "UID of the mlflow namespace (for helm depends_on)"
  value       = kubernetes_namespace.mlflow.metadata[0].uid
}

output "app_namespace_names" {
  description = "Names of app deployment namespaces"
  value       = [for ns in kubernetes_namespace.app : ns.metadata[0].name]
}

output "app_namespace_uids" {
  description = "Map of app namespace name to UID"
  value       = { for name, ns in kubernetes_namespace.app : name => ns.metadata[0].uid }
}
