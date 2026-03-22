"""
run_demo.py — Demo mode: runs the full pipeline with simulated data.

No LLM, no emails, no database needed. Shows the complete flow
from request analysis to PDF report generation.

Usage:
    python run_demo.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    print("=" * 60)
    print("  PROCUREMENT PIPELINE — DEMO MODE")
    print("=" * 60)

    # ── Step 1: Simulated Analysis (Agent 1) ─────────────────────
    print("\n[Agent 1 — Analysis] Analyzing procurement request...")
    procurement_spec = {
        "product": "chaises de bureau ergonomiques",
        "category": "Mobilier de bureau",
        "quantity": 50,
        "unit": "unités",
        "budget_min": 10000,
        "budget_max": 15000,
        "deadline": "2026-04-30",
        "requester_email": "eya@company.com",
        "is_valid": True,
        "rejection_reason": None,
    }
    print(f"  Product:  {procurement_spec['product']}")
    print(f"  Quantity: {procurement_spec['quantity']} {procurement_spec['unit']}")
    print(f"  Budget:   {procurement_spec['budget_min']} - {procurement_spec['budget_max']} TND")
    print(f"  Deadline: {procurement_spec['deadline']}")
    print(f"  Valid:    {procurement_spec['is_valid']}")

    # ── Step 2: Simulated Sourcing (Agent 2) ─────────────────────
    print("\n[Agent 2 — Sourcing] Searching for Tunisian suppliers...")
    supplier_list = {
        "suppliers": [
            {
                "name": "Meublatex",
                "email": "contact@meublatex.com.tn",
                "website": "https://www.meublatex.com.tn",
                "phone": "+216 71 940 600",
                "location": "Ben Arous, Tunisie",
            },
            {
                "name": "Sotufab",
                "email": "info@sotufab.tn",
                "website": "https://www.sotufab.tn",
                "phone": "+216 71 600 300",
                "location": "Tunis, Tunisie",
            },
            {
                "name": "Office Plus Tunisie",
                "email": "commercial@officeplus.tn",
                "website": "https://www.officeplus.tn",
                "phone": "+216 70 100 200",
                "location": "Sfax, Tunisie",
            },
        ],
        "query_used": "fournisseur chaises bureau ergonomiques Tunisie",
        "search_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for s in supplier_list["suppliers"]:
        print(f"  Found: {s['name']} ({s['email']})")

    # ── Step 3: Simulated Communication (Agent 3) ────────────────
    print("\n[Agent 3 — Communication] Sending RFQs to suppliers...")
    communication_result = {
        "rfqs_sent": [
            {"supplier_name": "Meublatex", "email": "contact@meublatex.com.tn", "status": "sent",
             "subject": "Demande de devis — 50 chaises de bureau ergonomiques"},
            {"supplier_name": "Sotufab", "email": "info@sotufab.tn", "status": "sent",
             "subject": "Demande de devis — 50 chaises de bureau ergonomiques"},
            {"supplier_name": "Office Plus Tunisie", "email": "commercial@officeplus.tn", "status": "sent",
             "subject": "Demande de devis — 50 chaises de bureau ergonomiques"},
        ],
        "offers_received": [
            {
                "supplier_name": "Meublatex",
                "unit_price": 220,
                "total_price": 11000,
                "currency": "TND",
                "delivery_days": 14,
                "warranty": "2 ans",
                "payment_terms": "30 jours net",
                "notes": "Livraison gratuite pour commande > 30 unités",
            },
            {
                "supplier_name": "Sotufab",
                "unit_price": 195,
                "total_price": 9750,
                "currency": "TND",
                "delivery_days": 21,
                "warranty": "1 an",
                "payment_terms": "50% avance, solde à livraison",
                "notes": "Stock disponible immédiatement",
            },
            {
                "supplier_name": "Office Plus Tunisie",
                "unit_price": 250,
                "total_price": 12500,
                "currency": "TND",
                "delivery_days": 10,
                "warranty": "3 ans",
                "payment_terms": "net 45 jours",
                "notes": "Garantie étendue incluse, installation sur site",
            },
        ],
        "pending_suppliers": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for rfq in communication_result["rfqs_sent"]:
        print(f"  RFQ sent to: {rfq['supplier_name']} ({rfq['status']})")
    print(f"\n  Offers received: {len(communication_result['offers_received'])}")
    for offer in communication_result["offers_received"]:
        print(f"    - {offer['supplier_name']}: {offer['total_price']} {offer['currency']} "
              f"({offer['delivery_days']}j, {offer['warranty']})")

    # ── Step 4: Storage skipped in demo ──────────────────────────
    print("\n[Agent 4 — Storage] Skipped in demo mode (no database)")

    # ── Step 5: Real Evaluation (Agent 5) ────────────────────────
    print("\n[Agent 5 — Evaluation] Scoring and ranking offers...")
    from agents.agent_evaluation.agent import EvaluationAgent

    eval_agent = EvaluationAgent()
    eval_result = eval_agent.evaluate(
        offers=communication_result["offers_received"],
        procurement_spec=procurement_spec,
    )

    print(f"\n  {'Rank':<6} {'Supplier':<25} {'Score':<8} {'Price':<12} {'Recommendation'}")
    print("  " + "-" * 75)
    for score in eval_result["scores"]:
        print(f"  {score['rank']:<6} {score['supplier_name']:<25} {score['total_score']:<8.1f} "
              f"{score.get('total_price', 'N/A'):<12} {score['recommendation']}")

    print(f"\n  Best offer: {eval_result['best_offer']}")
    print(f"  Report:     {eval_result.get('report_path', 'N/A')}")

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Product:         {procurement_spec['product']}")
    print(f"  Suppliers found: {len(supplier_list['suppliers'])}")
    print(f"  RFQs sent:       {len(communication_result['rfqs_sent'])}")
    print(f"  Offers received: {len(communication_result['offers_received'])}")
    print(f"  Best offer:      {eval_result['best_offer']}")
    if eval_result.get("report_path"):
        print(f"  PDF report:      {eval_result['report_path']}")
    print()


if __name__ == "__main__":
    main()
