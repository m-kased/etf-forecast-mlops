# ---------------------------------------------------------------------------
# cert-manager
# ---------------------------------------------------------------------------

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "v1.17.2"
  namespace        = "cert-manager"
  create_namespace = false

  values = [file("${path.module}/values/cert-manager.yaml")]

  set {
    name  = "crds.enabled"
    value = "true"
  }

  depends_on = [terraform_data.namespace_cert_manager]
}
