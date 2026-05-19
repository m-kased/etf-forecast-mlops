# Helm Charts

## `charts/app` — generic single-application chart

One **Helm release per application**. Install the same chart multiple times with different release names and values files.

| Release | Purpose |
|---------|---------|
| `api` | FastAPI inference service |
| `ui` | Streamlit dashboard |

### Deploy API and UI

```bash
# Namespace must exist before install (e.g. created by Terraform or kubectl)

helm upgrade --install api ./helm/charts/app \
  --namespace app \
  -f ./helm/charts/app/examples/api.values.yaml \
  --set image.repository=<ecr>/etf-forecast-api \
  --set image.tag=<tag>

helm upgrade --install ui ./helm/charts/app \
  --namespace app \
  -f ./helm/charts/app/examples/ui.values.yaml \
  --set image.repository=<ecr>/etf-forecast-ui \
  --set image.tag=<tag>
```

### Values you typically set per app

| Value | Description |
|-------|-------------|
| `namespace` | Kubernetes namespace (must already exist) |
| `image.repository` / `image.tag` | Container image |
| `containerPort` | Container listen port |
| `service.port` | Service port (defaults to `containerPort`) |
| `env` / `envFrom` | Environment variables and secret refs |
| `serviceAccount.annotations` | IRSA role ARN, etc. |
| `resources` | CPU/memory limits |
| `livenessProbe` / `readinessProbe` | Health checks |
| `istio.enabled` / `istio.hosts` | Optional Istio VirtualService |

Release name becomes the Deployment/Service name (e.g. release `api` → Service `api` in namespace `app`).

Platform charts (Istio, Airflow, MLflow) are deployed by Terraform under `terraform/modules/helm/`.
