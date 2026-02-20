module "irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.2.0"

  role_name = "autoapply-role-${var.environment}"

  oidc_providers = {
    main = {
      provider_arn               = var.oidc_provider_arn
      namespace_service_accounts = ["autoapply:api", "autoapply:worker"]
    }
  }

  role_policy_arns = {
    s3_read_write = aws_iam_policy.s3_access.arn
  }

  tags = var.tags
}

resource "aws_iam_policy" "s3_access" {
  name        = "autoapply-s3-${var.environment}"
  description = "Allow autoapply pods to access S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
    ]
  })
}
