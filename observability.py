"""
observability.py — Agent metrics pushed to AWS CloudWatch.
Tracks: invocations, latency, errors, token usage per agent.

Usage in agents:
    from observability import track_agent_call

    with track_agent_call("analysis"):
        result = self._agent(prompt)

Metrics are pushed to CloudWatch namespace "ProcurementAI".
In dev mode (no AWS credentials), metrics are logged locally.
"""
import logging
import os
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ── CloudWatch namespace ─────────────────────────────────────────────────────

NAMESPACE = "ProcurementAI"
_cw_client = None


def _get_cloudwatch():
    """Lazy-init CloudWatch client."""
    global _cw_client
    if _cw_client is None:
        try:
            import boto3
            region = os.environ.get(
                "AWS_REGION_NAME",
                os.environ.get("AWS_REGION", "us-east-1"),
            )
            _cw_client = boto3.client("cloudwatch", region_name=region)
        except Exception as e:
            logger.warning("CloudWatch unavailable, metrics will be logged only: %s", e)
    return _cw_client


def _put_metric(metric_name: str, value: float, unit: str, dimensions: list[dict]):
    """Push a single metric to CloudWatch (or log it in dev)."""
    client = _get_cloudwatch()
    if client:
        try:
            client.put_metric_data(
                Namespace=NAMESPACE,
                MetricData=[{
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": dimensions,
                }],
            )
        except Exception as e:
            logger.warning("Failed to push metric %s: %s", metric_name, e)
    else:
        dims = {d["Name"]: d["Value"] for d in dimensions}
        logger.info("METRIC | %s = %.2f %s | %s", metric_name, value, unit, dims)


# ── Context manager for tracking ─────────────────────────────────────────────

@contextmanager
def track_agent_call(agent_name: str):
    """Track an agent call's latency and success/failure."""
    dims = [{"Name": "Agent", "Value": agent_name}]
    start = time.time()
    try:
        yield
        duration = time.time() - start
        _put_metric("AgentCalls", 1, "Count", dims + [{"Name": "Status", "Value": "success"}])
        _put_metric("AgentLatency", duration, "Seconds", dims)
    except Exception as e:
        duration = time.time() - start
        _put_metric("AgentCalls", 1, "Count", dims + [{"Name": "Status", "Value": "error"}])
        _put_metric("AgentLatency", duration, "Seconds", dims)
        _put_metric("AgentErrors", 1, "Count", dims + [{"Name": "ErrorType", "Value": type(e).__name__}])
        raise



def pipeline_started():
    """Mark a pipeline as started."""
    _put_metric("PipelineStarted", 1, "Count", [])


def pipeline_finished(status: str):
    """Mark a pipeline as finished."""
    _put_metric("PipelineCompleted", 1, "Count", [{"Name": "Status", "Value": status}])
