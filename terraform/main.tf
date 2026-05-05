terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Data sources ───────────────────────────────────────────────────────────────
data "aws_caller_identity" "current" {}

locals {
  account_id   = data.aws_caller_identity.current.account_id
  function_name = "${var.project_name}-analysis-agent"
  ecr_image_uri = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}:${var.image_tag}"
}

# ══════════════════════════════════════════════════════════════════════════════
# ECR — Docker image repository
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_ecr_repository" "agent" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

resource "aws_ecr_lifecycle_policy" "agent" {
  repository = aws_ecr_repository.agent.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# ══════════════════════════════════════════════════════════════════════════════
# S3 — Bucket for storing emails (SES) and results
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_s3_bucket" "emails" {
  bucket        = "${var.project_name}-emails-${local.account_id}"
  force_destroy = true
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "emails" {
  bucket = aws_s3_bucket.emails.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "emails" {
  bucket = aws_s3_bucket.emails.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "emails" {
  bucket                  = aws_s3_bucket.emails.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Allow SES to write emails into the bucket
resource "aws_s3_bucket_policy" "ses_write" {
  bucket = aws_s3_bucket.emails.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowSESPuts"
      Effect    = "Allow"
      Principal = { Service = "ses.amazonaws.com" }
      Action    = "s3:PutObject"
      Resource  = "${aws_s3_bucket.emails.arn}/emails/*"
      Condition = {
        StringEquals = { "AWS:SourceAccount" = local.account_id }
      }
    }]
  })
}

# ══════════════════════════════════════════════════════════════════════════════
# IAM — Lambda execution role
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_iam_role" "lambda_exec" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

# CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access (read emails, write results)
resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.emails.arn,
        "${aws_s3_bucket.emails.arn}/*"
      ]
    }]
  })
}

# Bedrock access (Claude Sonnet)
resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "lambda-bedrock-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      Resource = [
        "arn:aws:bedrock:*::foundation-model/*",
        "arn:aws:bedrock:*:${local.account_id}:inference-profile/*"
      ]
    }]
  })
}

# ══════════════════════════════════════════════════════════════════════════════
# Lambda — Container image function
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_lambda_function" "agent" {
  function_name = local.function_name
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = local.ecr_image_uri

  memory_size = 1024   # tesseract + ML libs need RAM
  timeout     = 300    # 5 minutes max (Bedrock can be slow)

  environment {
    variables = {
      AWS_REGION_NAME      = var.aws_region
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      S3_BUCKET_NAME       = aws_s3_bucket.emails.bucket
      S3_OUTPUT_PREFIX      = "outputs/"
      SMTP_HOST            = "smtp.gmail.com"
      SMTP_PORT            = "587"
      GMAIL_ADDRESS        = var.gmail_address
      GMAIL_APP_PASSWORD   = var.gmail_app_password
      TAVILY_API_KEY       = var.tavily_api_key
      LOG_LEVEL            = var.log_level
      APP_ENV              = "production"
      # Credentials loaded from Secrets Manager at runtime
      SECRETS_DB_ARN       = aws_secretsmanager_secret.db_credentials.arn
      SECRETS_GMAIL_ARN    = aws_secretsmanager_secret.gmail_credentials.arn
      SECRETS_TAVILY_ARN   = aws_secretsmanager_secret.tavily_api_key.arn
      # Direct DATABASE_URL for convenience (also available via Secrets Manager)
      DATABASE_URL         = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
    }
  }

  tags = var.tags
}

# CloudWatch Log Group for the Lambda
resource "aws_cloudwatch_log_group" "agent" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

# ══════════════════════════════════════════════════════════════════════════════
# S3 → Lambda trigger
# When SES drops an email in s3://bucket/emails/<messageId>, Lambda fires.
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.emails.arn
}

resource "aws_s3_bucket_notification" "trigger_lambda" {
  bucket = aws_s3_bucket.emails.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.agent.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "emails/"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

# ══════════════════════════════════════════════════════════════════════════════
# SES — Receipt Rule: store incoming emails in S3
# Requires a verified SES domain and an active receipt rule set.
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_ses_receipt_rule_set" "main" {
  rule_set_name = "${var.project_name}-rules"
}

resource "aws_ses_active_receipt_rule_set" "main" {
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
}

resource "aws_ses_receipt_rule" "store_in_s3" {
  name          = "store-emails-in-s3"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  recipients    = var.ses_recipient_emails  # e.g. ["procurement@yourdomain.com"]
  enabled       = true
  scan_enabled  = true

  s3_action {
    bucket_name = aws_s3_bucket.emails.bucket
    object_key_prefix = "emails/"
    position    = 1
  }
}

# ══════════════════════════════════════════════════════════════════════════════
# Offer Collector Lambda — polls Gmail IMAP every 15 min for supplier replies
# Uses the same container image as the main agent Lambda
# ══════════════════════════════════════════════════════════════════════════════
resource "aws_lambda_function" "offer_collector" {
  function_name = "${local.function_name}-offer-collector"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.agent.repository_url}:${var.image_tag}"
  memory_size   = 512
  timeout       = 300   # 5 minutes

  image_config {
    command = ["offer_collector_handler.handler"]
  }

  environment {
    variables = {
      AWS_REGION_NAME    = var.aws_region
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      S3_BUCKET_NAME     = aws_s3_bucket.emails.bucket
      S3_OUTPUT_PREFIX   = "outputs/"
      SMTP_HOST          = "smtp.gmail.com"
      SMTP_PORT          = "587"
      GMAIL_ADDRESS      = var.gmail_address
      GMAIL_APP_PASSWORD = var.gmail_app_password
      TAVILY_API_KEY     = var.tavily_api_key
      LOG_LEVEL          = var.log_level
      APP_ENV            = "production"
      OUTPUTS_DIR               = "/tmp/outputs"
      DATABASE_URL              = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
      EVALUATION_DEADLINE_DAYS  = "5"
      REMINDER_AFTER_HOURS      = "72"
      SECRETS_GMAIL_ARN         = aws_secretsmanager_secret.gmail_credentials.arn
      SECRETS_TAVILY_ARN        = aws_secretsmanager_secret.tavily_api_key.arn
      SECRETS_DB_ARN            = aws_secretsmanager_secret.db_credentials.arn
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "offer_collector" {
  name              = "/aws/lambda/${local.function_name}-offer-collector"
  retention_in_days = 30
  tags              = var.tags
}

# ── EventBridge (CloudWatch Events) scheduled rule — every 15 minutes ────────
resource "aws_cloudwatch_event_rule" "offer_check" {
  name                = "${var.project_name}-offer-check"
  description         = "Poll Gmail every 15 minutes for supplier RFQ replies"
  schedule_expression = "rate(15 minutes)"
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "offer_check" {
  rule      = aws_cloudwatch_event_rule.offer_check.name
  target_id = "OfferCollectorLambda"
  arn       = aws_lambda_function.offer_collector.arn
}

resource "aws_lambda_permission" "eventbridge_invoke_collector" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.offer_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.offer_check.arn
}
