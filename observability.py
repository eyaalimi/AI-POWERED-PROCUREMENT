"""
observability.py — Agent metrics for Prometheus/Grafana.
Tracks: invocations, latency, errors, token usage per agent.

Usage in agents:
    from observability import track_agent_call

    with track_agent_call("analysis"):
        result = self._agent(prompt)

Exposes metrics at /metrics endpoint (added to dashboard API).
"""
import time
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, Info

# ── Metrics ──────────────────────────────────────────────────────────────────

AGENT_CALLS_TOTAL = Counter(
    "agent_calls_total",
    "Total number of agent invocations",
    ["agent", "status"],
)

AGENT_LATENCY = Histogram(
    "agent_latency_seconds",
    "Agent call latency in seconds",
    ["agent"],
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60, 120],
)

AGENT_ERRORS_TOTAL = Counter(
    "agent_errors_total",
    "Total agent errors",
    ["agent", "error_type"],
)

AGENT_TOKENS_USED = Counter(
    "agent_tokens_total",
    "Total tokens consumed by agent calls",
    ["agent", "direction"],  # direction: input or output
)

PIPELINE_ACTIVE = Gauge(
    "pipeline_active_count",
    "Number of currently running pipelines",
)

PIPELINE_COMPLETED = Counter(
    "pipeline_completed_total",
    "Total completed pipelines",
    ["status"],  # completed, rejected, failed, awaiting_responses
)

SYSTEM_INFO = Info(
    "procurement_ai",
    "System information",
)
SYSTEM_INFO.info({
    "version": "1.0.0",
    "model": "amazon-nova-2-lite",
    "provider": "aws-bedrock",
})


# ── Context manager for tracking ─────────────────────────────────────────────

@contextmanager
def track_agent_call(agent_name: str):
    """Track an agent call's latency and success/failure."""
    start = time.time()
    try:
        yield
        duration = time.time() - start
        AGENT_CALLS_TOTAL.labels(agent=agent_name, status="success").inc()
        AGENT_LATENCY.labels(agent=agent_name).observe(duration)
    except Exception as e:
        duration = time.time() - start
        AGENT_CALLS_TOTAL.labels(agent=agent_name, status="error").inc()
        AGENT_LATENCY.labels(agent=agent_name).observe(duration)
        AGENT_ERRORS_TOTAL.labels(
            agent=agent_name,
            error_type=type(e).__name__,
        ).inc()
        raise


def record_tokens(agent_name: str, input_tokens: int, output_tokens: int):
    """Record token usage for an agent call."""
    AGENT_TOKENS_USED.labels(agent=agent_name, direction="input").inc(input_tokens)
    AGENT_TOKENS_USED.labels(agent=agent_name, direction="output").inc(output_tokens)


def pipeline_started():
    """Mark a pipeline as started."""
    PIPELINE_ACTIVE.inc()


def pipeline_finished(status: str):
    """Mark a pipeline as finished."""
    PIPELINE_ACTIVE.dec()
    PIPELINE_COMPLETED.labels(status=status).inc()
