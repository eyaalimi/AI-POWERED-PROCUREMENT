# Prompt Changelog

## v1.0 — 2026-04-20 (Initial versioning)

All prompts extracted from inline code into versioned files.

### analysis_v1.0.md
- Extracts ProcurementSpec from French/English emails
- Uses tools: suggest_procurement_category, validate_budget_range, validate_deadline

### sourcing_v1.0.md
- Finds Tunisian suppliers via internal DB + web search
- Audit trail logging for every supplier decision

### communication_rfq_v1.0.md
- Sends professional RFQ emails
- Handles missing emails with retry

### orchestrator_v1.0.md
- Coordinates 5-agent pipeline in sequence
- Handles early stops (invalid request, no suppliers)
