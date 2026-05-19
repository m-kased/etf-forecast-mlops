locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ──────────────────────────────────────────────
#  Networking
# ──────────────────────────────────────────────
module "vpc" {
  source = "../../modules/vpc"

  project_name          = var.project_name
  environment           = var.environment
  vpc_cidr              = var.vpc_cidr
  availability_zones    = var.availability_zones
  private_subnet_cidrs  = var.private_subnet_cidrs
  public_subnet_cidrs   = var.public_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  single_nat_gateway    = true
  tags                  = local.tags
}

# ──────────────────────────────────────────────
#  Object Storage
# ──────────────────────────────────────────────
module "s3" {
  source = "../../modules/s3"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.tags
}

# ──────────────────────────────────────────────
#  ECR (container images)
# ──────────────────────────────────────────────
module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
  repositories = var.ecr_repositories
  tags         = local.tags
}

# ──────────────────────────────────────────────
#  IAM Roles (EKS + IRSA)
# ──────────────────────────────────────────────
module "iam" {
  source = "../../modules/iam"

  project_name                = var.project_name
  environment                 = var.environment
  oidc_provider_arn           = module.eks.oidc_provider_arn
  oidc_provider_url           = module.eks.oidc_provider_url
  mlflow_artifacts_bucket_arn = module.s3.mlflow_artifacts_bucket_arn
  raw_data_bucket_arn         = module.s3.raw_data_bucket_arn
  tags                        = local.tags
}

# ──────────────────────────────────────────────
#  EKS Cluster
# ──────────────────────────────────────────────
module "eks" {
  source = "../../modules/eks"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  cluster_role_arn    = module.iam.eks_cluster_role_arn
  node_role_arn       = module.iam.eks_node_role_arn
  kubernetes_version  = var.kubernetes_version
  node_instance_types = var.node_instance_types
  node_desired_size   = var.node_desired_size
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
  tags                = local.tags
}

# ──────────────────────────────────────────────
#  RDS PostgreSQL
# ──────────────────────────────────────────────
module "rds" {
  source = "../../modules/rds"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.vpc.vpc_id
  database_subnet_ids        = module.vpc.database_subnet_ids
  allowed_security_group_ids = [module.eks.node_security_group_id]
  instance_class             = var.rds_instance_class
  multi_az                   = var.rds_multi_az
  deletion_protection        = false
  skip_final_snapshot        = true
  tags                       = local.tags
}

# ──────────────────────────────────────────────
#  ElastiCache Redis
# ──────────────────────────────────────────────
module "elasticache" {
  source = "../../modules/elasticache-redis"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.vpc.vpc_id
  database_subnet_ids        = module.vpc.database_subnet_ids
  allowed_security_group_ids = [module.eks.node_security_group_id]
  node_type                  = var.redis_node_type
  tags                       = local.tags
}

# ──────────────────────────────────────────────
#  Kubernetes (namespaces, secrets)
# ──────────────────────────────────────────────
module "kubernetes" {
  source = "../../modules/kubernetes"

  project_name   = var.project_name
  environment    = var.environment
  app_namespaces = var.app_namespaces
  rds_endpoint   = module.rds.db_endpoint
  rds_port       = module.rds.db_port
  rds_username   = module.rds.db_username
  rds_password   = module.rds.db_password
  rds_db_name    = module.rds.db_name
  tags           = local.tags
}

# ──────────────────────────────────────────────
#  Helm Charts (platform services)
# ──────────────────────────────────────────────
module "helm" {
  source = "../../modules/helm"

  namespace_istio_system = module.kubernetes.namespace_istio_system
  namespace_cert_manager = module.kubernetes.namespace_cert_manager
  namespace_monitoring   = module.kubernetes.namespace_monitoring
  namespace_airflow      = module.kubernetes.namespace_airflow
  namespace_mlflow       = module.kubernetes.namespace_mlflow

  project_name            = var.project_name
  environment             = var.environment
  cluster_name            = module.eks.cluster_name
  cluster_endpoint        = module.eks.cluster_endpoint
  cluster_ca_data         = module.eks.cluster_certificate_authority_data
  oidc_provider_arn       = module.eks.oidc_provider_arn
  oidc_provider_url       = module.eks.oidc_provider_url
  rds_endpoint            = module.rds.db_endpoint
  rds_port                = module.rds.db_port
  rds_db_name             = module.rds.db_name
  rds_username            = module.rds.db_username
  rds_password            = module.rds.db_password
  rds_secret_arn          = module.rds.secrets_manager_secret_arn
  redis_endpoint          = module.elasticache.redis_endpoint
  redis_port              = module.elasticache.redis_port
  mlflow_artifacts_bucket = module.s3.mlflow_artifacts_bucket_name
  raw_data_bucket         = module.s3.raw_data_bucket_name
  mlflow_role_arn         = module.iam.mlflow_role_arn
  airflow_role_arn        = module.iam.airflow_role_arn
  api_role_arn            = module.iam.api_role_arn
  region                  = var.region
  airflow_git_repo        = var.airflow_git_repo
  airflow_git_branch      = var.airflow_git_branch
  tags                    = local.tags
}
