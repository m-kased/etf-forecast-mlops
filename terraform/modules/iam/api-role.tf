resource "aws_iam_role" "api" {
  name               = local.irsa_roles.api.name
  assume_role_policy = data.aws_iam_policy_document.trust["api"].json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "api" {
  statement {
    actions = ["s3:GetObject"]
    resources = [
      "${var.mlflow_artifacts_bucket_arn}/*",
      "${var.raw_data_bucket_arn}/*",
    ]
  }

  statement {
    actions = ["s3:ListBucket"]
    resources = [
      var.mlflow_artifacts_bucket_arn,
      var.raw_data_bucket_arn,
    ]
  }
}

resource "aws_iam_role_policy" "api" {
  name   = "${local.irsa_roles.api.name}-s3"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.api.json
}
