# ETF Volatility MLOps Platform

*Production-style MLOps reference: automated retraining on EKS, champion models in MLflow, and observable inference APIs for multi-ETF volatility forecasting.*

End-to-end platform for next-day volatility for ETFs like **SPY, QQQ, and IWM** — ETL, XGBoost training, MLflow registry, FastAPI inference, and Grafana observability. Runnable locally with Docker Compose; production workloads on **AWS EKS** (Terraform).

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5)](https://kubernetes.io/)
[![Airflow](https://img.shields.io/badge/Airflow-3.0-017CEE)](https://airflow.apache.org/)
[![MLflow](https://img.shields.io/badge/MLflow-3.x-0194E2)](https://mlflow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What this demonstrates

- **End-to-end ML pipeline** — scheduled ETL, per-ticker training, registry promotion, and live inference
- **GitOps-style delivery** — GitHub Actions build images, push to ECR, deploy with Helm
- **Cloud-native AWS** — Terraform modules for EKS, RDS, S3, ElastiCache, ECR, and **IRSA** (no static keys in pods)
- **Model lifecycle** — MLflow `@champion` alias and conditional API reload after promotion
- **Observability** — Prometheus metrics on the API, batch jobs via Pushgateway, four Grafana dashboards
- **Service mesh ingress** — Istio + cert-manager with TLS on public UI and API hostnames

## Architecture

The platform is provisioned on AWS EKS via Terraform; the design center is the automated ML lifecycle—from extraction through inference and monitoring.

<p align="center">
  <img src="./assets/architecture.png" alt="ETF Forecast MLOps architecture" width="900"/>
</p>

### Phases of the pipeline

| Phase | Component | What it does |
|-------|-----------|--------------|
| Data | `src/data/etl.py` | Fetch market data, compute log return / RSI / MACD, write Parquet to object storage |
| Orchestration | `dags/etl_dag.py` | Hourly DAG: ETL → train → reload API if a new champion was promoted |
| Registry | MLflow | Log experiments; promote best model per ticker to `@champion` |
| Serving | `src/api/app.py` | Load champions from registry; `/predict`, `/reload` |
| UI | `src/ui/app.py` | Streamlit dashboard for interactive inference |
| Monitoring | Prometheus + Grafana | API scraped from `/metrics`; batch jobs push to Pushgateway |

**Production:** Airflow on EKS with `KubernetesExecutor` and DAGs synced via git-sync.  
**Local:** Airflow 3 `standalone` with `LocalExecutor` in Docker Compose.

## Technology stack

| Layer | Tools |
|-------|--------|
| ML & data | Python 3.12, XGBoost, pandas, scikit-learn, yfinance |
| Apps | FastAPI, Streamlit, PostgreSQL |
| MLOps | Airflow 3, MLflow |
| Observability | Prometheus, Grafana, Pushgateway; on EKS also Loki and Kiali |
| Cloud | Terraform, AWS (EKS, RDS, ElastiCache, S3, ECR), IRSA |
| Delivery | Docker, Helm, GitHub Actions, Istio, cert-manager |

## Repository structure

```text
.
├── dags/                      # Airflow DAGs (etf_hourly_feature_pipeline)
├── src/
│   ├── api/                   # FastAPI inference + /metrics
│   ├── ui/                    # Streamlit UI
│   ├── data/                  # ETL pipeline
│   ├── ml/                    # Training + champion promotion
│   └── common/                # DB helpers, Prometheus metrics
├── docker/
│   ├── api/                   # API image
│   ├── ui/                    # UI image
│   └── airflow/               # Airflow image (prod + local)
├── helm/
│   ├── charts/app/            # Generic chart for API & UI
│   └── airflow/               # Airflow values (git-sync, executor, …)
├── monitoring/
│   ├── grafana-dashboards/    # Four Grafana dashboards (JSON)
│   └── prometheus.yml         # Local Prometheus scrape config
├── terraform/                 # AWS infra (see terraform/README.md)
└── .github/workflows/         # Terraform, app-deploy, airflow-deploy
```

## Quick start (local)

**Prerequisites:** Docker and Docker Compose ([uv](https://docs.astral.sh/uv/) optional for host-side ETL).

1. Copy environment template and set secrets:

   ```bash
   cp .env.example .env
   # Edit POSTGRES_*, MINIO_*, AIRFLOW_* (see .env.example comments)
   ```

2. Start the stack:

   ```bash
   docker compose up -d
   # or: make compose-up
   ```

3. Open services:

   | Service | URL |
   |---------|-----|
   | Streamlit UI | http://localhost:8501 |
   | FastAPI | http://localhost:8000 |
   | API docs | http://localhost:8000/docs |
   | Airflow | http://localhost:8080 |
   | MLflow | http://localhost:5000 |
   | MinIO console | http://localhost:9001 |
   | Grafana | http://localhost:3000 (admin / admin) |
   | Prometheus | http://localhost:9090 |

4. Run the pipeline: in Airflow, unpause and trigger DAG **`etf_hourly_feature_pipeline`** (tasks: `extract_transform_load_to_minio` → `train_models` → `reload_api_models`). Metrics appear in Grafana after ETL/training tasks complete and the API serves traffic (see [monitoring/README.md](monitoring/README.md)).

**Run ETL only on the host** (with compose running):

```bash
set -a && source .env && set +a
export PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
export DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/ml_data
uv run python -m src.data.etl
```

## MLOps pipeline (DAG)

DAG ID: `etf_hourly_feature_pipeline` (`dags/etl_dag.py`)

| Task | Callable | Notes |
|------|----------|--------|
| `extract_transform_load_to_minio` | `run_pipeline` | Writes features to S3/MinIO; pushes ETL metrics |
| `train_models` | `run_training_pipeline` | Trains per ticker; may promote `@champion` |
| `reload_api_models` | `reload_api_models` | `POST /reload` only when training promoted a new champion |

## Deployment (EKS + CI/CD)

Infrastructure is provisioned with Terraform (`terraform/README.md`). Application images are **not** deployed by Terraform; GitHub Actions build and push to ECR, then Helm deploys the applications to the cluster.

| Workflow | Triggers | Deploys |
|----------|----------|---------|
| `app-deploy.yml` | Changes under `src/api`, `src/ui`, `helm/charts/app`, … | API & UI Helm releases |
| `airflow-deploy.yml` | Airflow image / `helm/airflow`, `src/`, `dags/` | Airflow Helm release (git-sync DAGs) |
| `terraform-*.yml` | `terraform/**` | AWS / platform Helm (Istio, MLflow, monitoring, …) |

After Terraform apply, public HTTPS ingress (separate hostnames):

| Host | Service |
|------|---------|
| `etf-forecast-mlops.mohamed-elkased.com` | Streamlit UI |
| `etf-forecast-mlops-api.mohamed-elkased.com` | FastAPI |

Get the Istio ingress address:

```bash
kubectl get svc -n istio-system istio-ingressgateway \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
```

Point DNS for both hostnames to that load balancer. Set `TF_VAR_acme_email` for Let's Encrypt (see `terraform/README.md`).

**In-cluster UIs** (not on the public UI/API hostnames above): use port-forward, for example:

```bash
# Grafana (EKS)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# MLflow
kubectl port-forward -n mlflow svc/mlflow 5000:5000
```

## Observability

- **API:** Prometheus scrapes `/metrics` (HTTP + `etf_forecast_*` counters).
- **ETL / training:** After each run, metrics are pushed to Pushgateway (`job=etf-etl`, `job=etf-training`).

| Dashboard | UID |
|-----------|-----|
| ETF Forecast — API Inference | `etf-api-inference` |
| ETF Forecast — ETL Pipeline | `etf-etl-pipeline` |
| ETF Forecast — ML Training | `etf-ml-training` |
| ETF Forecast — Platform Overview | `etf-platform-overview` |

Local dashboards use scrape labels `job="api"`, `job="etf-etl"`, `job="etf-training"`. Details: [monitoring/README.md](monitoring/README.md).

<details open>
<summary>Grafana screenshots</summary>

<p align="center">
  <img width="49%" src="./assets/API-Inference.png" alt="API Inference dashboard"/>
  <img width="49%" src="./assets/ETL-Pipeline.png" alt="ETL Pipeline dashboard"/>
</p>
<p align="center">
  <img width="49%" src="./assets/ML-Training.png" alt="ML Training dashboard"/>
  <img width="49%" src="./assets/Platform-Overview.png" alt="Platform Overview dashboard"/>
</p>

</details>

## Further reading

- [terraform/README.md](terraform/README.md) — modules, state, variables, apply order
- [monitoring/README.md](monitoring/README.md) — metrics and dashboards
- [helm/README.md](helm/README.md) — chart usage for API/UI deploys

## License

See [LICENSE](LICENSE).
