# Grafana dashboards — auto-loaded by kube-prometheus-stack Grafana sidecar.

locals {
  grafana_dashboard_files = {
    "etf-api-inference"     = "${path.module}/../../../monitoring/grafana-dashboards/api-inference.json"
    "etf-etl-pipeline"      = "${path.module}/../../../monitoring/grafana-dashboards/etl-pipeline.json"
    "etf-ml-training"       = "${path.module}/../../../monitoring/grafana-dashboards/ml-training.json"
    "etf-platform-overview" = "${path.module}/../../../monitoring/grafana-dashboards/platform-overview.json"
  }
}

resource "kubernetes_config_map_v1" "grafana_dashboards" {
  for_each = local.grafana_dashboard_files

  metadata {
    name      = "grafana-dashboard-${each.key}"
    namespace = "monitoring"
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "${each.key}.json" = file(each.value)
  }
}
