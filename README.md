# ETF Volatility MLOps Platform

Forecasts how much **SPY, QQQ, IWM and other ETFs** will move over the next six hours. Every hour the system pulls market data, retrains, and replaces the live model only when the new one has a lower error than the one already serving traffic. It is deployed on AWS.


A production-style reference for MLOps roles and contract platform work. The lifecycle, the cloud deploy, and the dashboards are running.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5)](https://kubernetes.io/)
[![Airflow](https://img.shields.io/badge/Airflow-3.0-017CEE)](https://airflow.apache.org/)
[![MLflow](https://img.shields.io/badge/MLflow-3.x-0194E2)](https://mlflow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What this demonstrates

- **A worse model never goes live** — each ticker is promoted to the MLflow `@champion` alias only when its RMSE beats the current champion. The API reloads only after that promotion.
- **The forecast keeps itself current** — an hourly Airflow pipeline fetches prices, builds features, trains, and serves the winner.
- **Cloud-native AWS** — Terraform modules for EKS, RDS, S3, ElastiCache, ECR, and **IRSA**
- **Failure is visible** — Prometheus scrapes the API, batch jobs push metrics after each run, and four Grafana dashboards cover inference, ETL, training, and the platform.

## Architecture

A user opens the forecast UI or the API. Istio terminates TLS and routes into the cluster. FastAPI serves the current champion. Airflow retrains from data in S3 and PostgreSQL. MLflow keeps the previous champion unless the new model is better. Prometheus scrapes the API, batch jobs push metrics after each run, and Grafana shows whether data, training, or the API misbehaved.

Redis is deployed for Airflow. Production Airflow uses the Kubernetes executor, so tasks run as pods.

<p align="center">
  <img src="./assets/architecture.png" alt="Request path from the user through EKS to the forecast API, training, and dashboards" width="900"/>
</p>

| Phase | What happens |
|-------|----------------|
| Data | Market data is fetched, log return / RSI / MACD are computed, and features are written to object storage |
| Orchestration | Hourly pipeline: build features, train, reload the API only if a new champion was promoted |
| Registry | Experiments are logged; the best model per ticker is aliased `@champion` when its RMSE is lower |
| Serving | The API loads champions and exposes `/predict` and `/reload` |
| UI | A small web app runs an interactive forecast against that API |
| Monitoring | The API is scraped at `/metrics`; ETL and training push metrics after each run |

## Dashboards

These four boards show whether the data, the training run, or the API is what failed.

<details open>
<summary>Grafana screenshots</summary>

<table>
  <tr>
    <td align="center" width="50%">
      <strong>API inference</strong><br/>
      <img src="./assets/API-Inference.png" alt="API inference dashboard" width="100%"/>
    </td>
    <td align="center" width="50%">
      <strong>ETL pipeline</strong><br/>
      <img src="./assets/ETL-Pipeline.png" alt="ETL pipeline dashboard" width="100%"/>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <strong>ML training</strong><br/>
      <img src="./assets/ML-Training.png" alt="ML training dashboard" width="100%"/>
    </td>
    <td align="center" width="50%">
      <strong>Platform overview</strong><br/>
      <img src="./assets/Platform-Overview.png" alt="Platform overview dashboard" width="100%"/>
    </td>
  </tr>
</table>

</details>

## Run it yourself

**Prerequisites:** Docker and Docker Compose ([uv](https://docs.astral.sh/uv/) optional for host-side ETL).

1. Copy the environment template and set secrets:

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
   | Forecast UI | http://localhost:8501 |
   | Prediction API | http://localhost:8000 |
   | API docs | http://localhost:8000/docs |
   | Airflow | http://localhost:8080 |
   | MLflow | http://localhost:5000 |
   | MinIO console | http://localhost:9001 |
   | Grafana | http://localhost:3000 (admin / admin) |
   | Prometheus | http://localhost:9090 |

4. In Airflow, unpause and trigger **`etf_hourly_feature_pipeline`**. Metrics show up in Grafana after ETL and training finish and the API serves traffic. Details: [monitoring/README.md](monitoring/README.md).

**Run ETL only, on the host** (with Docker Compose running):

```bash
set -a && source .env && set +a
export PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
export DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/ml_data
uv run python -m src.data.etl
```

## MLOps pipeline (DAG)

DAG ID: `etf_hourly_feature_pipeline` (`dags/etl_dag.py`)

| Task | What it does |
|------|----------------|
| `extract_transform_load_to_minio` | Writes features to S3/MinIO and pushes ETL metrics |
| `train_models` | Trains one model per ticker and promotes `@champion` only on a lower RMSE |
| `reload_api_models` | `POST /reload` only when training promoted a new champion |

### Repository

```text
.
├── dags/                      # Airflow DAGs (etf_hourly_feature_pipeline)
├── src/
│   ├── api/                   # FastAPI inference + /metrics
│   ├── ui/                    # Forecast UI
│   ├── data/                  # ETL pipeline
│   ├── ml/                    # Training + champion promotion
│   └── common/                # DB helpers, Prometheus metrics
├── docker/                    # API, UI, and Airflow images
├── helm/                      # API/UI chart and Airflow values
├── monitoring/                # Grafana dashboards and local Prometheus config
├── terraform/                 # AWS infra (see terraform/README.md)
└── .github/workflows/         # Terraform, app-deploy, airflow-deploy
```

| Layer | Tools |
|-------|--------|
| ML & data | Python 3.12, XGBoost, pandas, scikit-learn, yfinance |
| Apps | FastAPI, Streamlit, PostgreSQL |
| MLOps | Airflow 3, MLflow |
| Observability | Prometheus, Grafana, Pushgateway; on EKS also Loki and Kiali |
| Cloud | Terraform, AWS (EKS, RDS, ElastiCache, S3, ECR), IRSA |
| Delivery | Docker, Helm, GitHub Actions, Istio, cert-manager |

### Deploy to EKS

Terraform provisions the cluster (`terraform/README.md`). It does not deploy application images. GitHub Actions builds them, pushes to ECR, and Helm installs the releases.

| Workflow | Deploys |
|----------|---------|
| `app-deploy.yml` | API and forecast UI |
| `airflow-deploy.yml` | Airflow, with DAGs synced from git |
| `terraform-*.yml` | AWS and platform installs (Istio, MLflow, monitoring) |

Public HTTPS after apply:

| Host | Service |
|------|---------|
| `etf-forecast-mlops.mohamed-elkased.com` | Forecast UI |
| `etf-forecast-mlops-api.mohamed-elkased.com` | Prediction API |

```bash
kubectl get svc -n istio-system istio-ingressgateway \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
```

Point DNS for both hostnames at that load balancer. Set `TF_VAR_acme_email` for Let's Encrypt (`terraform/README.md`).

**Production:** Airflow on EKS with `KubernetesExecutor` and DAGs synced via git-sync.  
**Local:** Airflow 3 `standalone` with `LocalExecutor` in Docker Compose.

In-cluster UIs stay off the public hostnames. Port-forward them:

```bash
# Grafana (EKS)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# MLflow
kubectl port-forward -n mlflow svc/mlflow 5000:5000
```


## Further reading

- [terraform/README.md](terraform/README.md) — modules, state, variables, apply order
- [monitoring/README.md](monitoring/README.md) — metrics and dashboards
- [helm/README.md](helm/README.md) — chart usage for API and UI deploys

## License

See [LICENSE](LICENSE).
