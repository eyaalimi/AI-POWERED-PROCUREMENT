"""
tests/test_prompt_regression.py — Prompt regression tests.
Ensures prompts maintain critical structural requirements across versions.
Run with: pytest tests/test_prompt_regression.py -v
"""
import pytest
from prompts import (
    ANALYSIS_PROMPT,
    SOURCING_PROMPT,
    COMMUNICATION_RFQ_PROMPT,
    ORCHESTRATOR_PROMPT,
)


class TestAnalysisPrompt:
    """Ensure analysis prompt contains required extraction fields."""

    def test_contains_required_json_fields(self):
        required_fields = [
            "product", "category", "quantity", "unit",
            "budget_min", "budget_max", "deadline",
            "requester_email", "is_valid", "rejection_reason",
        ]
        for field in required_fields:
            assert f'"{field}"' in ANALYSIS_PROMPT, f"Missing field: {field}"

    def test_mentions_tnd_currency(self):
        assert "TND" in ANALYSIS_PROMPT

    def test_requires_json_only_output(self):
        assert "ONLY the JSON" in ANALYSIS_PROMPT

    def test_mentions_tool_usage(self):
        assert "suggest_procurement_category" in ANALYSIS_PROMPT
        assert "validate_budget_range" in ANALYSIS_PROMPT
        assert "validate_deadline" in ANALYSIS_PROMPT

    def test_handles_french_input(self):
        assert "French" in ANALYSIS_PROMPT


class TestSourcingPrompt:
    """Ensure sourcing prompt maintains supplier discovery requirements."""

    def test_contains_required_json_fields(self):
        required_fields = [
            "name", "website", "country", "email",
            "category", "relevance_score", "source",
        ]
        for field in required_fields:
            assert f'"{field}"' in SOURCING_PROMPT, f"Missing field: {field}"

    def test_tunisia_requirement(self):
        assert "Tunisia" in SOURCING_PROMPT

    def test_max_suppliers_limit(self):
        assert "12" in SOURCING_PROMPT

    def test_audit_trail_required(self):
        assert "AUDIT TRAIL" in SOURCING_PROMPT
        assert "log_sourcing_decision" in SOURCING_PROMPT

    def test_internal_db_priority(self):
        assert "internal_db" in SOURCING_PROMPT
        assert "internal DB suppliers first" in SOURCING_PROMPT


class TestCommunicationRfqPrompt:
    """Ensure RFQ prompt maintains email quality requirements."""

    def test_no_budget_reveal(self):
        assert "do NOT reveal the exact max" in COMMUNICATION_RFQ_PROMPT.lower() or \
               "do not reveal the exact maximum budget" in COMMUNICATION_RFQ_PROMPT.lower()

    def test_english_requirement(self):
        assert "English" in COMMUNICATION_RFQ_PROMPT

    def test_subject_format(self):
        assert "RFQ" in COMMUNICATION_RFQ_PROMPT

    def test_required_response_fields(self):
        required = ["unit price", "total price", "delivery time", "warranty", "payment terms"]
        for field in required:
            assert field in COMMUNICATION_RFQ_PROMPT, f"Missing: {field}"


class TestOrchestratorPrompt:
    """Ensure orchestrator maintains correct pipeline order."""

    def test_5_step_pipeline(self):
        assert "analyze_request" in ORCHESTRATOR_PROMPT
        assert "source_suppliers" in ORCHESTRATOR_PROMPT
        assert "send_rfqs_and_collect_offers" in ORCHESTRATOR_PROMPT
        assert "store_pipeline_data" in ORCHESTRATOR_PROMPT
        assert "evaluate_offers" in ORCHESTRATOR_PROMPT

    def test_step_order(self):
        # Steps must appear in correct order
        steps = [
            "analyze_request",
            "source_suppliers",
            "send_rfqs_and_collect_offers",
            "store_pipeline_data",
            "evaluate_offers",
        ]
        positions = [ORCHESTRATOR_PROMPT.index(s) for s in steps]
        assert positions == sorted(positions), "Steps are out of order"

    def test_final_json_structure(self):
        required = ["request_id", "product", "status", "suppliers_found",
                    "rfqs_sent", "offers_received"]
        for field in required:
            assert f'"{field}"' in ORCHESTRATOR_PROMPT, f"Missing: {field}"

    def test_error_handling(self):
        assert "failed" in ORCHESTRATOR_PROMPT
        assert "rejected" in ORCHESTRATOR_PROMPT
