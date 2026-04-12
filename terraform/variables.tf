variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all resources (e.g. 'procurement-agent')"
  type        = string
  default     = "procurement-agent"
}

variable "image_tag" {
  description = "Docker image tag to deploy (e.g. 'latest' or a git SHA)"
  type        = string
  default     = "latest"
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID for Claude"
  type        = string
  default     = "arn:aws:bedrock:us-east-1:415529767461:inference-profile/global.amazon.nova-2-lite-v1:0"
}

variable "ses_recipient_emails" {
  description = "List of email addresses that SES should process (must be on a verified SES domain)"
  type        = list(string)
  # Example: ["procurement@yourdomain.com"]
}

variable "gmail_address" {
  description = "Gmail address used to send ACK emails via SMTP"
  type        = string
  sensitive   = true
}

variable "gmail_app_password" {
  description = "Gmail App Password (16-char, no spaces) for SMTP auth"
  type        = string
  sensitive   = true
}

variable "log_level" {
  description = "Python log level (DEBUG, INFO, WARNING, ERROR)"
  type        = string
  default     = "INFO"
}

variable "tavily_api_key" {
  description = "Tavily search API key for supplier sourcing"
  type        = string
  default     = ""
  sensitive   = true
}

# ── RDS ──────────────────────────────────────────────────────────────────────

variable "rds_instance_class" {
  description = "RDS instance class (db.t3.micro = Free Tier eligible)"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_deletion_protection" {
  description = "Enable deletion protection on RDS (true for prod, false for dev)"
  type        = bool
  default     = false
}

variable "rds_skip_final_snapshot" {
  description = "Skip final snapshot on RDS deletion (false for prod, true for dev)"
  type        = bool
  default     = true
}

variable "rds_allowed_cidrs" {
  description = "CIDR blocks allowed to connect to RDS (Lambda IPs + dev machine)"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict in prod to known IPs
}

# ── Dashboard / Domain ───────────────────────────────────────────────────────

variable "domain_name" {
  description = "Root domain for the dashboard (e.g. procurement-ai.click)"
  type        = string
  default     = "procurement-ai.click"
}

# ── Tags ─────────────────────────────────────────────────────────────────────

variable "tags" {
  description = "Tags applied to all AWS resources"
  type        = map(string)
  default = {
    Project     = "procurement-agent"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
