locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Module      = "elasticache"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  })
}
