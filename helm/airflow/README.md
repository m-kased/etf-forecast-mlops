# Airflow (Helm)

1. Builds `docker/airflow/Dockerfile` (Python deps + `src/` only)
2. Pushes to ECR (`{project}-{env}-airflow`)
3. Installs the [Apache Airflow Helm chart](https://airflow.apache.org) with git-sync for `dags/`

## Prerequisites (from Terraform)

- `airflow` namespace and secrets (`airflow-rds-credentials`, `airflow-app-credentials`, `airflow-runtime-secrets`)
- IRSA role for `airflow-worker` service account
- RDS, Redis, MLflow, S3 buckets

## GitHub Environment variables

| Variable | Source |
|----------|--------|
| `AWS_ROLE_ARN` | OIDC deploy role |
| `AWS_REGION` | e.g. `us-east-1` |
| `TF_VAR_PROJECT_NAME` | Project name |
| `EKS_CLUSTER_NAME` | Optional; defaults to `{project}-{env}-eks` |
| `AIRFLOW_IRSA_ROLE_ARN` | `terraform output airflow_irsa_role_arn` |
| `RDS_SECRET_ARN` | `terraform output rds_secret_arn` |
| `AIRFLOW_GIT_REPO` | Optional; defaults to `https://github.com/<this-repo>.git` |
| `AIRFLOW_GIT_BRANCH` | Optional; defaults to `main` |

DAGs are pulled from `dags/` in the git repo (public HTTPS). For a private repo, add a git-sync credentials secret and wire it in the Helm values.

Redis, S3 bucket names, and Airflow crypto keys are supplied via Kubernetes resources created by Terraform (`airflow-platform-config`, `airflow-runtime-secrets`).

## Manual deploy

```bash
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow \
  --version 1.16.0 \
  --namespace airflow \
  -f helm/airflow/values.yaml \
  --set images.airflow.repository=<ecr-url> \
  --set images.airflow.tag=<tag>
```
