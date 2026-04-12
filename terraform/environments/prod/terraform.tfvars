# terraform/environments/prod/terraform.tfvars
# Production environment variable values.
# Do NOT commit real secrets — use terraform.tfvars.local or TF_VAR_ env vars.

aws_region           = "us-east-1"
image_tag            = "latest"    # Use a specific git SHA in production (e.g. "a1b2c3d")
bedrock_model_id     = "arn:aws:bedrock:us-east-1:415529767461:inference-profile/global.amazon.nova-2-lite-v1:0"
ses_recipient_emails = ["test@procurement-ai.click"]

# ── Credentials (set via TF_VAR_* env vars or terraform.tfvars.local) ─────
gmail_address        = ""
gmail_app_password   = ""
tavily_api_key       = ""

# ── RDS (production settings) ─────────────────────────────────────────────
rds_instance_class      = "db.t3.micro"     # Free Tier eligible (~$13/mo after)
rds_deletion_protection = true              # Prevent accidental deletion
rds_skip_final_snapshot = false             # Take snapshot before deletion
rds_allowed_cidrs       = ["0.0.0.0/0"]    # TODO: restrict to known IPs

# ── Dashboard ─────────────────────────────────────────────────────────────
domain_name = "procurement-ai.click"
