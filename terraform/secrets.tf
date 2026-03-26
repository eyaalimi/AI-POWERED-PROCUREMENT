# ══════════════════════════════════════════════════════════════════════════════
# Secrets Manager — Centralized credential storage (~$2/month for 5 secrets)
# ══════════════════════════════════════════════════════════════════════════════

# ── Database credentials ─────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.project_name}/db-credentials"
  description             = "PostgreSQL credentials for ${var.project_name}"
  recovery_window_in_days = 7

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_db_instance.postgres.username
    password = random_password.db_password.result
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    dbname   = aws_db_instance.postgres.db_name
    url      = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  })
}

# ── Gmail SMTP credentials ───────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "gmail_credentials" {
  name                    = "${var.project_name}/gmail-credentials"
  description             = "Gmail SMTP credentials for ${var.project_name}"
  recovery_window_in_days = 7

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "gmail_credentials" {
  secret_id = aws_secretsmanager_secret.gmail_credentials.id
  secret_string = jsonencode({
    address      = var.gmail_address
    app_password = var.gmail_app_password
  })
}

# ── Tavily API key ───────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "tavily_api_key" {
  name                    = "${var.project_name}/tavily-api-key"
  description             = "Tavily search API key for ${var.project_name}"
  recovery_window_in_days = 7

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "tavily_api_key" {
  secret_id     = aws_secretsmanager_secret.tavily_api_key.id
  secret_string = var.tavily_api_key
}

# ── IAM: Allow Lambda to read secrets ────────────────────────────────────────

resource "aws_iam_role_policy" "lambda_secrets" {
  name = "lambda-secrets-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.db_credentials.arn,
        aws_secretsmanager_secret.gmail_credentials.arn,
        aws_secretsmanager_secret.tavily_api_key.arn,
      ]
    }]
  })
}
