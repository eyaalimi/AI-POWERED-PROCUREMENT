# Prompt for Claude Desktop — Procurement AI Report Writing

You are helping me write a detailed academic/professional report for my end-of-studies project (PFE - Projet de Fin d'Études). The project is an AI-powered procurement automation system. I'll describe the full context below — read everything carefully before we start writing.

## Project Overview

The system is called "Procurement AI" — an intelligent, multi-agent procurement platform that automates the entire purchasing workflow for companies: from receiving a purchase request via email, to finding suppliers, sending RFQs (Request for Quotation), collecting offers, evaluating them, generating comparison reports, and creating purchase orders.

## Architecture

### Backend (Python)

- **Multi-agent orchestration** using Google ADK (Agent Development Kit) with Gemini LLM
- **5 specialized AI agents**, each with dedicated tools:
  1. **Analysis Agent**: Parses incoming procurement emails (product, quantity, budget, specs), validates requests, rejects invalid ones with justification
  2. **Sourcing Agent**: Searches for relevant suppliers using web scraping (Google Maps, web search), scores them by relevance
  3. **Communication Agent**: Drafts and sends professional RFQ emails to suppliers via AWS SES, handles follow-up reminders
  4. **Storage Agent**: Persists all data (requests, suppliers, RFQs, offers, evaluations) to PostgreSQL (AWS RDS), logs pipeline events
  5. **Orchestrator Agent**: Coordinates the entire pipeline flow, delegates to sub-agents in sequence, handles errors and retries
- **Offer Collector**: Monitors an email inbox (AWS SES + S3), parses supplier responses (text + PDF attachments via Gemini vision), extracts pricing data
- **Evaluation Engine**: Scores suppliers on quality, cost, delivery, and performance using weighted multi-criteria analysis, generates PDF comparison reports in French

### Frontend (React + Vite)

- **Dashboard** at https://procurement-ai.click/ with real-time pipeline monitoring
- **Multi-tenant architecture**: company isolation via `company_id`, role-based access (admin vs employee)
- **Auth system**: JWT-based registration/login, first user per company becomes admin
- Pages: Dashboard KPIs, Pipelines with colored stage indicators, Inbox, Orders, Suppliers, Activity Log, Budget (admin-only), Blacklist, Team Members
- **New Request page**: employees submit procurement requests via the dashboard, triggering an email to the system

### Infrastructure (AWS + Terraform)

- **AWS Lambda** for the pipeline (analysis → sourcing → communication → evaluation)
- **AWS SES** for sending/receiving emails
- **AWS S3** for storing incoming emails and generated PDF reports
- **AWS RDS PostgreSQL** for all structured data
- **AWS API Gateway** (HTTP API) for the dashboard backend
- **CloudFront + S3** for frontend hosting
- **Terraform** for infrastructure-as-code (dev + prod environments)
- **GitHub Actions** CI/CD: lint, test, deploy to Lambda, build & deploy frontend

### Database Models

- Companies, Users (with roles)
- ProcurementRequest (with company_id scoping)
- Supplier, RFQ, Offer, Evaluation
- PipelineEvent (activity logging)
- PurchaseOrder, SupplierBlacklist

## Key Technical Challenges Solved

1. **Multi-tenant data isolation**: all queries scoped by company_id, employees see only their own requests
2. **Email parsing**: handling diverse supplier response formats (plain text, HTML, PDF attachments)
3. **Pipeline orchestration**: sequential agent coordination with error handling and status tracking
4. **Production deployment**: Lambda cold starts, environment variable management, SES domain verification
5. **Real-time pipeline visibility**: mapping internal statuses to visual stage indicators on the dashboard

## Tech Stack Summary

- Python 3.12, FastAPI, SQLAlchemy, Google ADK, Gemini (Flash/Pro)
- React 18, Vite, React Router, Lucide icons, Recharts
- AWS: Lambda, SES, S3, RDS, API Gateway, CloudFront, IAM
- Terraform, GitHub Actions
- JWT auth (python-jose, passlib)

## What I Need From You

Help me write a structured, detailed report covering:

1. **Introduction** — context, problem statement, objectives
2. **State of the Art** — existing procurement solutions, AI in procurement, multi-agent systems
3. **Requirements Analysis** — functional/non-functional requirements, use cases, actors
4. **System Design** — architecture diagrams description, data models, agent design, sequence diagrams description
5. **Implementation** — technical details of each component, code highlights, key algorithms
6. **Deployment & DevOps** — AWS infrastructure, Terraform, CI/CD pipeline
7. **Testing & Results** — test scenarios, screenshots description, performance analysis
8. **Conclusion** — summary, limitations, future work

Write in a formal academic tone. Each chapter should be thorough (multiple pages worth of content). Include technical depth — this is a computer science/engineering report. I'll provide screenshots and diagrams separately.

Let's start chapter by chapter. Ask me any clarifying questions before we begin.
