"""
config.py — Centralised configuration via Pydantic Settings.
All values are read from environment variables (or .env file).
In production (Lambda), secrets are fetched from AWS Secrets Manager.
"""
import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


def _load_secrets_from_aws():
    """Fetch secrets from AWS Secrets Manager and inject into env vars."""
    secret_mappings = {
        "SECRETS_TAVILY_ARN": {"TAVILY_API_KEY": "tavily_api_key"},
        "SECRETS_GMAIL_ARN": {
            "GMAIL_ADDRESS": "address",
            "GMAIL_APP_PASSWORD": "app_password",
        },
        "SECRETS_DB_ARN": {"DATABASE_URL": "database_url"},
    }

    try:
        import boto3
        region = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))
        client = boto3.client("secretsmanager", region_name=region)
    except Exception:
        return

    for arn_env, field_map in secret_mappings.items():
        arn = os.environ.get(arn_env, "")
        if not arn:
            continue

        # Skip if all target env vars are already populated
        if all(os.environ.get(env_key, "") for env_key in field_map):
            continue

        try:
            resp = client.get_secret_value(SecretId=arn)
            secret_str = resp["SecretString"]
            try:
                secret_data = json.loads(secret_str)
            except (json.JSONDecodeError, TypeError):
                # Plain string secret — use for the first field
                first_env = next(iter(field_map))
                if not os.environ.get(first_env):
                    os.environ[first_env] = secret_str.strip()
                continue

            for env_key, secret_key in field_map.items():
                if not os.environ.get(env_key) and secret_key in secret_data:
                    os.environ[env_key] = str(secret_data[secret_key])
        except Exception:
            pass


# In production, load secrets before building Settings
if os.environ.get("APP_ENV") == "production":
    _load_secrets_from_aws()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── AWS ────────────────────────────────────────────────────────
    aws_region: str = Field(default="us-west-2")
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")

    # ── Amazon Bedrock ─────────────────────────────────────────────
    bedrock_model_id: str = Field(
        default="arn:aws:bedrock:us-east-1:415529767461:inference-profile/global.amazon.nova-2-lite-v1:0"
    )

    # ── Tavily Search ──────────────────────────────────────────────
    tavily_api_key: str = Field(default="")

    # ── Database ───────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://procurement:devpassword@localhost:5433/procurement_db"
    )

    # ── Gmail SMTP / IMAP ──────────────────────────────────────────
    gmail_address: str = Field(default="")
    gmail_app_password: str = Field(default="")
    imap_host: str = Field(default="imap.gmail.com")
    imap_port: int = Field(default=993)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    email_poll_interval_seconds: int = Field(default=300)

    # ── JWT ─────────────────────────────────────────────────────────
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_expiry_hours: int = Field(default=24)

    # ── Application ────────────────────────────────────────────────
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")


# Singleton — import this everywhere
settings = Settings()
