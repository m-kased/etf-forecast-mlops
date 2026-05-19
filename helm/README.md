# Helm Charts

## `charts/app` — generic single-application chart

One **Helm release per application**. Install the same chart multiple times with different release names and values files.

| Release | Purpose |
|---------|---------|
| `api` | FastAPI inference service |
| `ui` | Streamlit dashboard |

### GitHub Actions (recommended)

Push to `main` (paths under `src/`, `docker/`, `helm/charts/app/`) deploys **both** apps to **dev**.

Manual run: **Actions → Build and Deploy Apps** — choose environment (`dev` / `prod`) and app (`all` / `api` / `ui`).

**GitHub Environment variables** (per `dev` / `prod`):

| Variable | Description |
|----------|-------------|
| `AWS_ROLE_ARN` | OIDC role with ECR push + EKS access |
| `AWS_REGION` | AWS region |
| `TF_VAR_PROJECT_NAME` | e.g. `etf-forecast` (used for ECR repo and cluster name) |
| `API_IRSA_ROLE_ARN` | IRSA role for API pods (from `terraform output api_irsa_role_arn`) |
| `EKS_CLUSTER_NAME` | Optional; defaults to `{project}-{env}-eks` |

### Manual Helm install

```bash
# Namespace must exist (created by Terraform kubernetes module)

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
| `istio.enabled` / `istio.hosts` | Istio VirtualService + TLS Gateway (`istio-ingressgateway`) |

Public URLs (after Terraform + DNS):

| App | URL |
|-----|-----|
| UI | `https://etf-forecast-mlops.mohamed-elkased.com` |
| API | `https://etf-forecast-mlops-api.mohamed-elkased.com` |

Release name becomes the Deployment/Service name (e.g. release `api` → Service `api` in namespace `app`).

Platform charts (Istio, Airflow, MLflow) are deployed by Terraform under `terraform/modules/helm/`.
