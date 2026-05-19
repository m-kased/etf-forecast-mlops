# TLS ingress for UI + API.
# DNS: point both hostnames at the istio-ingressgateway LoadBalancer.

locals {
  ingress_hosts = [
    var.ingress_ui_host,
    var.ingress_api_host,
  ]
  cluster_issuer_name    = var.acme_use_staging ? "letsencrypt-staging" : "letsencrypt-prod"
  acme_server            = var.acme_use_staging ? "https://acme-staging-v02.api.letsencrypt.org/directory" : "https://acme-v02.api.letsencrypt.org/directory"
  istio_system_namespace = "istio-system"
  gateway_name           = "istio-ingressgateway"

  manifest_template_vars = {
    cluster_issuer_name    = local.cluster_issuer_name
    acme_server            = local.acme_server
    acme_email             = var.acme_email
    ingress_hosts          = local.ingress_hosts
    istio_system_namespace = local.istio_system_namespace
    gateway_name           = local.gateway_name
  }
}

resource "kubernetes_manifest" "cluster_issuer" {
  manifest = yamldecode(templatefile(
    "${path.module}/manifests/cluster-issuer.yaml.tpl",
    local.manifest_template_vars,
  ))
}

resource "kubernetes_manifest" "etf_forecast_certificate" {
  manifest = yamldecode(templatefile(
    "${path.module}/manifests/certificate.yaml.tpl",
    local.manifest_template_vars,
  ))

  depends_on = [kubernetes_manifest.cluster_issuer]
}

resource "kubernetes_manifest" "etf_forecast_gateway" {
  manifest = yamldecode(templatefile(
    "${path.module}/manifests/gateway.yaml.tpl",
    local.manifest_template_vars,
  ))
}
