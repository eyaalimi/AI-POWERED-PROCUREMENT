# terraform/environments/dev/terraform.tfvars
# Development environment variable values.
# Do NOT commit real secrets — use TF_VAR_* env vars or terraform.tfvars.local.

aws_region           = "us-east-1"
image_tag            = "latest"
bedrock_model_id     = "arn:aws:bedrock:us-east-1:415529767461:inference-profile/global.amazon.nova-2-lite-v1:0"
ses_recipient_emails = []    # e.g. ["dev-procurement@yourdomain.com"]

# ── Credentials (set via TF_VAR_* env vars) ───────────────────────────────
gmail_address        = ""
gmail_app_password   = ""
tavily_api_key       = ""

# ── Dashboard ─────────────────────────────────────────────────────────────
domain_name = "procurement-ai.click"
