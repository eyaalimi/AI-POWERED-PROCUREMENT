# DevSecOps & MLOps — Procurement AI

## Overview

This document summarizes all DevSecOps and MLOps practices implemented in the Procurement AI platform. The system runs on AWS (Lambda, ECR, S3, CloudFront, RDS, SES, Bedrock) with a fully automated CI/CD pipeline and production observability.

---

## 1. CI/CD Pipeline (GitHub Actions)

**File:** `.github/workflows/pipeline.yml`

```
┌──────────┐   ┌──────────┐   ┌───────────────┐   ┌──────────────────┐
│   Lint   │──▶│  Tests   │──▶│  Build Agent  │──▶│  Deploy Lambdas  │
└──────────┘   └──────────┘   │  Build Dash   │   │  Deploy Dashboard│
                              │  Build Front  │   │  Deploy Frontend │
                              └───────────────┘   └──────────────────┘
```

### CI Jobs (all pushes & PRs)
| Job | Tool | Purpose |
|-----|------|---------|
| Lint | Ruff | Python code quality |
| Unit Tests | Pytest | Deterministic agent tests + prompt regression |
| Frontend Build | Vite/React | Verify frontend compiles |
| SAST | Bandit | Static Application Security Testing |
| SCA | pip-audit + npm audit | Dependency vulnerability scanning |
| Secrets Scan | TruffleHog | Detect leaked credentials in git history |

### CD Jobs (main branch only, after CI passes)
| Job | Action |
|-----|--------|
| Build Agent Image | Docker build → ECR push → **Trivy container scan** |
| Build Dashboard Image | Docker build → ECR push → **Trivy container scan** |
| Deploy Agent Lambdas | `aws lambda update-function-code` (analysis + offer-collector) |
| Deploy Dashboard API | `aws lambda update-function-code` |
| Deploy Frontend | `npm build` → S3 sync → CloudFront invalidation |
| Smoke Test | HTTP health checks on frontend + API post-deploy |
| Summary | GitHub Step Summary with all job results |

---

## 2. DevSecOps Security Gates

### SAST (Static Analysis)
- **Tool:** Bandit
- **Scope:** `agents/`, `dashboard/api/`
- **Severity:** Low-Low excluded, Medium+ reported
- **Output:** JSON artifact uploaded to GitHub Actions

### SCA (Software Composition Analysis)
- **Tool:** pip-audit (Python) + npm audit (Frontend)
- **Action:** Fails on known vulnerabilities in dependencies

### Container Scanning
- **Tool:** Trivy (Aqua Security)
- **Scope:** Both Docker images (agent + dashboard)
- **Severity:** HIGH + CRITICAL → pipeline fails
- **Config:** `.trivyignore` for accepted risks

### Secrets Detection
- **Tool:** TruffleHog
- **Mode:** Full git history scan, only verified secrets reported
- **Scope:** All branches, all commits

### Infrastructure as Code
- **Tool:** Terraform
- **Environments:** `terraform/environments/dev/` and `terraform/environments/prod/`
- **Resources managed:** VPC, RDS, Lambda, ECR, S3, CloudFront, API Gateway, SES, IAM, CloudWatch Dashboard
- **Secrets:** Managed via `terraform/secrets.tf` (AWS Secrets Manager)

---

## 3. Observability & Monitoring

### Production: AWS CloudWatch (Push Model)

**File:** `observability.py`

The system pushes custom metrics directly to CloudWatch from Lambda — no scraping needed (serverless-compatible).

**Namespace:** `ProcurementAI`

| Metric | Dimensions | Description |
|--------|-----------|-------------|
| `PipelineStarted` | — | Pipeline invocations |
| `PipelineCompleted` | Status (completed/failed/rejected/awaiting_responses) | Pipeline outcomes |
| `AgentCalls` | Agent, Status | Per-agent invocation count |
| `AgentLatency` | Agent | Execution time (seconds) |
| `AgentErrors` | Agent, ErrorType | Error count by exception type |

### CloudWatch Dashboard

**Files:** `monitoring/cloudwatch-dashboard.json`, `terraform/cloudwatch-dashboard.tf`

9 panels organized in 4 rows:
1. **Pipeline metrics** — Started, Completed by Status, Success Rate (%)
2. **Agent metrics** — Call rate per agent, Error rate per agent
3. **Latency** — Average (s) and p95 (s) per agent
4. **Bedrock native metrics** — Input Tokens, Output Tokens, Invocations (per model)

Token usage is tracked via AWS/Bedrock native metrics (automatic, no custom code needed).

### Local Development: Grafana + Prometheus

**File:** `monitoring/docker-compose.yml`

- Prometheus scrapes local `/metrics` endpoint
- Grafana dashboard pre-provisioned (`monitoring/provisioning/`)
- Access: `http://localhost:3001` (admin/admin)

---

## 4. MLOps — Prompt Versioning & Regression Testing

### Prompt Versioning

**Directory:** `prompts/`

| File | Agent | Version |
|------|-------|---------|
| `analysis_v1.0.md` | Analysis | v1.0 |
| `sourcing_v1.0.md` | Sourcing | v1.0 |
| `communication_rfq_v1.0.md` | Communication | v1.0 |
| `orchestrator_v1.0.md` | Orchestrator | v1.0 |

- **Loader:** `prompts/__init__.py` — loads markdown files, strips header comments
- **Changelog:** `prompts/CHANGELOG.md` — documents every prompt change
- **Naming:** `{agent}_v{major}.{minor}.md` for semantic versioning

### Prompt Regression Tests

**File:** `tests/test_prompt_regression.py`

Runs in CI on every push. Validates that prompts maintain critical structural invariants:

- **Analysis:** Required JSON fields (product, category, quantity, etc.), TND currency, tool references
- **Sourcing:** Required fields, Tunisia requirement, max 12 suppliers, audit trail requirement
- **Communication:** No budget reveal, English requirement, RFQ subject format, required response fields
- **Orchestrator:** 5-step pipeline in correct order, final JSON structure, error handling

### AI Accuracy Benchmarking

**File:** `tests/test_benchmark_accuracy.py`

Ground-truth datasets for all 5 agents. Measures extraction accuracy against known inputs:
- 10 test emails for Analysis Agent
- Supplier discovery scenarios for Sourcing Agent
- Offer parsing scenarios for Communication Agent
- Deterministic CRUD for Storage Agent
- QCDP scoring for Evaluation Agent

### AI Accuracy Metrics (Precision/Recall/F1)

**File:** `tests/test_ai_accuracy_metrics.py`

Runs actual LLM agents against ground-truth data and computes per-field:
- True Positives, False Positives, False Negatives
- Precision, Recall, F1-Score
- Generates HTML report for visual inspection

---

## 5. Infrastructure

### Docker Images
| Image | File | Purpose |
|-------|------|---------|
| Agent | `Dockerfile` | Lambda: analysis pipeline + offer collector |
| Dashboard | `Dockerfile.dashboard` | Lambda: FastAPI dashboard API |

### AWS Architecture
```
User Email → SES → S3 → Lambda (Agent)
                              ↓
                         RDS (PostgreSQL)
                              ↓
                    Lambda (Dashboard API)
                              ↓
                    S3 + CloudFront (React Frontend)
                              ↓
                    https://procurement-ai.click/
```

### IAM Permissions
- Lambda roles have `cloudwatch:PutMetricData` for observability
- Lambda roles have `bedrock:InvokeModel` for AI agents
- Minimal privilege principle applied via Terraform

---

## 6. Summary of DevSecOps Maturity

| Practice | Status | Tool |
|----------|--------|------|
| Code linting | Active | Ruff |
| Unit testing | Active | Pytest |
| SAST | Active | Bandit |
| SCA | Active | pip-audit, npm audit |
| Container scanning | Active | Trivy |
| Secrets detection | Active | TruffleHog |
| IaC | Active | Terraform |
| CI/CD automation | Active | GitHub Actions |
| Smoke testing | Active | curl health checks |
| Observability | Active | CloudWatch (custom + Bedrock native) |
| Prompt versioning | Active | Markdown files + changelog |
| Prompt regression | Active | Pytest in CI |
| AI accuracy benchmarks | Active | Ground-truth datasets + F1 metrics |
| Multi-environment | Active | dev/prod Terraform workspaces |
