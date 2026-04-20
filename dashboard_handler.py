"""
dashboard_handler.py — AWS Lambda entry point for the Dashboard API.

This wraps the FastAPI app with Mangum so it can run behind API Gateway.
Lambda handler: dashboard_handler.handler
"""
from dashboard.api.main import handler  # noqa: F401
