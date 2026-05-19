# ETF Forecast MLOps — Terraform Infrastructure

AWS infrastructure for the ETF Forecast MLOps platform, provisioned with Terraform.

## Architecture

| Component | AWS Service | Purpose |
|-----------|------------|---------|
| Compute | EKS (Kubernetes 1.31) | Runs MLflow, Airflow, API, UI, Istio, monitoring |
| Database | RDS PostgreSQL 15 (Multi-AZ) | MLflow metadata, Airflow metadata, application data |
| Cache | ElastiCache Redis 7 | Feature caching for inference |
| Storage | S3 | MLflow artifacts, raw market data |
| Networking | VPC + NAT Gateway | Private subnets for EKS/RDS/Redis, public for load balancers |
| Auth | IRSA | IAM roles for Kubernetes service accounts (no static keys) |

### Helm Charts Deployed by Terraform

| Chart | Namespace | Purpose |
|-------|-----------|---------|
| cert-manager | cert-manager | TLS certificate management |
| istio (base + istiod + gateway) | istio-system | Service mesh + ingress |
| kube-prometheus-stack | monitoring | Prometheus + Grafana |
| loki-stack | monitoring | Log aggregation (Promtail → Loki → Grafana) |
| kiali | istio-system | Istio observability dashboard |
| airflow | airflow | Pipeline orchestration (KubernetesExecutor) |
| mlflow | mlflow | Model registry + experiment tracking |

> **Note:** The application chart (API + UI) is **not** deployed by Terraform — it's deployed via GitHub Actions CI/CD.

## Directory Structure

```
terraform/
├── bootstrap/          # S3 bucket + DynamoDB table for remote state (run first)
├── environments/
│   ├── dev/            # Dev environment config
│   └── prod/           # Prod environment config
└── modules/
    ├── vpc/            # VPC, subnets, NAT, IGW
    ├── eks/            # EKS cluster, node groups, OIDC, addons
    ├── rds/            # RDS PostgreSQL
    ├── elasticache/    # ElastiCache Redis
    ├── s3/             # S3 buckets
    ├── iam/            # IAM roles (EKS + IRSA)
    ├── kubernetes/     # Namespaces and Kubernetes secrets
    └── helm/           # Helm chart releases (platform components)
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.5
- kubectl
- Helm 3

## Getting Started

### 1. Bootstrap Remote State

Run this once to create the S3 bucket and DynamoDB table for Terraform state:

```bash
cd terraform/bootstrap
terraform init
terraform apply
```

### 2. Deploy Dev Environment

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### 3. Connect to EKS

After provisioning, connect to the cluster:

```bash
# The exact command is in Terraform outputs
aws eks --region us-east-1 update-kubeconfig --name etf-forecast-dev
```

### 4. Deploy Prod Environment

```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

## Kubernetes namespaces

**Core platform namespaces** (fixed resources in `modules/kubernetes/core-namespaces.tf`):

| Resource | Namespace |
|----------|-----------|
| `kubernetes_namespace.istio_system` | `istio-system` |
| `kubernetes_namespace.cert_manager` | `cert-manager` |
| `kubernetes_namespace.monitoring` | `monitoring` |
| `kubernetes_namespace.airflow` | `airflow` |
| `kubernetes_namespace.mlflow` | `mlflow` |

Each core namespace UID is passed to the helm module and used in `depends_on` so charts install only after their namespace exists.

**App namespaces** — extend via `app_namespaces` per environment (`TF_VAR_app_namespaces`):

```hcl
app_namespaces = [
  { name = "app", istio_injection = true },
  # { name = "staging-app", istio_injection = true },
]
```

Creates `kubernetes_namespace.app` (for_each) plus `app-rds-credentials` secret per namespace.

## Environment Differences

| Setting | Dev | Prod |
|---------|-----|------|
| VPC CIDR | 10.0.0.0/16 | 10.1.0.0/16 |
| NAT Gateway | Single (cheaper) | Per-AZ (HA) |
| EKS Nodes | t3.medium, 2 nodes | m5.large, 3 nodes |
| RDS | db.t3.medium | db.r6g.large |
| RDS Deletion Protection | Off | On |
| Redis | cache.t3.micro | cache.t3.small |

## Destroying

```bash
# Dev
cd terraform/environments/dev
terraform destroy

# Prod (requires disabling deletion protection on RDS first)
cd terraform/environments/prod
terraform destroy
```
