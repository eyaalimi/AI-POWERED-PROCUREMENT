# terraform/environments/dev/main.tf
# DEV environment — calls the root Terraform module with development-specific values.
#
# Usage:
#   cd terraform/environments/dev
#   terraform init
#   terraform plan -var-file="terraform.tfvars"
#   terraform apply -var-file="terraform.tfvars"

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after creating the S3 bucket and DynamoDB table (see terraform/backend.tf)
  # backend "s3" {
  #   bucket         = "procurement-ai-tfstate"
  #   key            = "dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "procurement-ai-tfstate-lock"
  # }
}

# ── Call root module with DEV-specific values ─────────────────────────────────
module "procurement_agent" {
  source = "../../"

  project_name         = "procurement-agent-dev"
  aws_region           = var.aws_region
  image_tag            = var.image_tag
  bedrock_model_id     = var.bedrock_model_id
  ses_recipient_emails = var.ses_recipient_emails
  gmail_address        = var.gmail_address
  gmail_app_password   = var.gmail_app_password
  tavily_api_key       = var.tavily_api_key
  log_level            = "DEBUG"
  domain_name          = var.domain_name

  # RDS — dev settings (cheaper, no protection)
  rds_instance_class      = "db.t3.micro"
  rds_deletion_protection = false
  rds_skip_final_snapshot = true
  rds_allowed_cidrs       = ["0.0.0.0/0"]

  tags = {
    Project     = "procurement-ai"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# ── Variables (override values in terraform.tfvars) ───────────────────────────
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID"
  type        = string
  default     = "arn:aws:bedrock:us-east-1:415529767461:inference-profile/global.amazon.nova-2-lite-v1:0"
}

variable "ses_recipient_emails" {
  description = "Email addresses SES should accept (must be on a verified domain)"
  type        = list(string)
  default     = []
}

variable "gmail_address" {
  description = "Gmail address for sending ACK emails"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gmail_app_password" {
  description = "Gmail App Password for SMTP auth"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tavily_api_key" {
  description = "Tavily search API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "domain_name" {
  description = "Root domain for the dashboard"
  type        = string
  default     = "procurement-ai.click"
}

# ── Pass-through outputs ───────────────────────────────────────────────────────
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.procurement_agent.ecr_repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.procurement_agent.s3_bucket_name
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.procurement_agent.lambda_function_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group"
  value       = module.procurement_agent.cloudwatch_log_group
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.procurement_agent.rds_endpoint
}

output "frontend_url" {
  description = "Dashboard URL"
  value       = module.procurement_agent.frontend_url
}

output "api_url" {
  description = "Dashboard API URL"
  value       = module.procurement_agent.api_url
}
