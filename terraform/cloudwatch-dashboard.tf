# CloudWatch Dashboard for Procurement AI Agent Observability
# Metrics are pushed from Lambda via observability.py

resource "aws_cloudwatch_dashboard" "procurement_ai" {
  dashboard_name = "${var.project_name}-agent-observability"

  dashboard_body = jsonencode({
    widgets = [
      # ── Row 1: Pipeline Overview ──────────────────────────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "Pipelines Started (5min)"
          region = var.aws_region
          metrics = [
            ["ProcurementAI", "PipelineStarted", { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "Pipelines Completed by Status"
          region = var.aws_region
          metrics = [
            ["ProcurementAI", "PipelineCompleted", "Status", "completed", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "PipelineCompleted", "Status", "failed", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "PipelineCompleted", "Status", "rejected", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "PipelineCompleted", "Status", "awaiting_responses", { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "Pipeline Success Rate (%)"
          region = var.aws_region
          metrics = [
            [{
              expression = "100 * completed / (completed + failed)"
              label      = "Success Rate"
              id         = "rate"
            }],
            ["ProcurementAI", "PipelineCompleted", "Status", "completed", { stat = "Sum", period = 3600, id = "completed", visible = false }],
            ["ProcurementAI", "PipelineCompleted", "Status", "failed", { stat = "Sum", period = 3600, id = "failed", visible = false }]
          ]
          view = "singleValue"
        }
      },

      # ── Row 2: Agent Call Rates ───────────────────────────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Agent Calls (rate/5min)"
          region = var.aws_region
          metrics = [
            ["ProcurementAI", "AgentCalls", "Agent", "orchestrator", "Status", "success", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentCalls", "Agent", "analysis", "Status", "success", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentCalls", "Agent", "sourcing", "Status", "success", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentCalls", "Agent", "communication_rfq", "Status", "success", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentCalls", "Agent", "communication_parse", "Status", "success", { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Agent Errors"
          region = var.aws_region
          metrics = [
            ["ProcurementAI", "AgentErrors", "Agent", "orchestrator", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentErrors", "Agent", "analysis", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentErrors", "Agent", "sourcing", { stat = "Sum", period = 300 }],
            ["ProcurementAI", "AgentErrors", "Agent", "communication_rfq", { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },

      # ── Row 3: Latency ───────────────────────────────────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Agent Latency — Average (seconds)"
          region = var.aws_region
          metrics = [
            ["ProcurementAI", "AgentLatency", "Agent", "orchestrator", { stat = "Average", period = 300 }],
            ["ProcurementAI", "AgentLatency", "Agent", "analysis", { stat = "Average", period = 300 }],
            ["ProcurementAI", "AgentLatency", "Agent", "sourcing", { stat = "Average", period = 300 }],
            ["ProcurementAI", "AgentLatency", "Agent", "communication_rfq", { stat = "Average", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Agent Latency — p95 (seconds)"
          region = var.aws_region
          metrics = [
            ["ProcurementAI", "AgentLatency", "Agent", "orchestrator", { stat = "p95", period = 300 }],
            ["ProcurementAI", "AgentLatency", "Agent", "analysis", { stat = "p95", period = 300 }],
            ["ProcurementAI", "AgentLatency", "Agent", "sourcing", { stat = "p95", period = 300 }],
            ["ProcurementAI", "AgentLatency", "Agent", "communication_rfq", { stat = "p95", period = 300 }]
          ]
          view = "timeSeries"
        }
      },

      # ── Row 4: Bedrock Token Usage (native metrics) ─────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 8
        height = 6
        properties = {
          title  = "Bedrock - Input Tokens"
          region = var.aws_region
          metrics = [
            ["AWS/Bedrock", "InputTokenCount", "ModelId", "anthropic.claude-3-haiku-20240307-v1:0", { stat = "Sum", period = 3600 }],
            ["AWS/Bedrock", "InputTokenCount", "ModelId", "anthropic.claude-3-5-sonnet-20241022-v2:0", { stat = "Sum", period = 3600 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 18
        width  = 8
        height = 6
        properties = {
          title  = "Bedrock - Output Tokens"
          region = var.aws_region
          metrics = [
            ["AWS/Bedrock", "OutputTokenCount", "ModelId", "anthropic.claude-3-haiku-20240307-v1:0", { stat = "Sum", period = 3600 }],
            ["AWS/Bedrock", "OutputTokenCount", "ModelId", "anthropic.claude-3-5-sonnet-20241022-v2:0", { stat = "Sum", period = 3600 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 18
        width  = 8
        height = 6
        properties = {
          title  = "Bedrock - Invocations"
          region = var.aws_region
          metrics = [
            ["AWS/Bedrock", "Invocations", "ModelId", "anthropic.claude-3-haiku-20240307-v1:0", { stat = "Sum", period = 3600 }],
            ["AWS/Bedrock", "Invocations", "ModelId", "anthropic.claude-3-5-sonnet-20241022-v2:0", { stat = "Sum", period = 3600 }]
          ]
          view = "timeSeries"
        }
      }
    ]
  })
}
