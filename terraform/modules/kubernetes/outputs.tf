output "app_namespace_names" {
  description = "Names of app deployment namespaces"
  value       = [for ns in kubernetes_namespace.app : ns.metadata[0].name]
}

output "app_namespace_uids" {
  description = "Map of app namespace name to UID"
  value       = { for name, ns in kubernetes_namespace.app : name => ns.metadata[0].uid }
}

output "ingress_ui_host" {
  description = "Public UI hostname"
  value       = var.ingress_ui_host
}

output "ingress_api_host" {
  description = "Public API hostname"
  value       = var.ingress_api_host
}

output "ingress_gateway_name" {
  description = "Istio Gateway resource used by app VirtualServices"
  value       = "istio-ingressgateway"
}
