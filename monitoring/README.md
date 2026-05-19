# Monitoring

## Metrics

| Source | Export | Scrape |
|--------|--------|--------|
| **FastAPI API** | `/metrics` (Prometheus client + HTTP middleware) | `ServiceMonitor` on `app/api` |
| **ETL** (`src/data/etl.py`) | Pushgateway job `etf-etl` | Prometheus scrapes Pushgateway |
| **Training** (`src/ml/train.py`) | Pushgateway job `etf-training` | Prometheus scrapes Pushgateway |

Custom metrics use the `etf_forecast_*` prefix (see `src/common/metrics.py`).

## Grafana dashboards

Provisioned as ConfigMaps in the `monitoring` namespace (label `grafana_dashboard: "1"`).

| Dashboard | UID | Focus |
|-----------|-----|--------|
| ETF Forecast — API Inference | `etf-api-inference` | HTTP traffic, predictions, model cache |
| ETF Forecast — ETL Pipeline | `etf-etl-pipeline` | Runs, duration, rows, tickers |
| ETF Forecast — ML Training | `etf-ml-training` | RMSE, promotions, training time |
| ETF Forecast — Platform Overview | `etf-platform-overview` | Cross-service summary |

Access Grafana (in-cluster):

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# http://localhost:3000 — default admin / admin (change in terraform helm values)
```

## Local (docker-compose)

Optional stack: Prometheus `9090`, Pushgateway `9091`, Grafana `3000`.

Set `PROMETHEUS_PUSHGATEWAY_URL=http://pushgateway:9091` for Airflow services.
