"""
tests/visualize_benchmark.py
Run the accuracy benchmark and generate visual charts.

Usage: python tests/visualize_benchmark.py
Output: outputs/benchmark_report.html (open in browser)
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from agents.agent_evaluation.agent import (
    EvaluationAgent,
    _score_price,
    _score_delivery,
    _parse_warranty_months,
    _score_payment,
    _score_budget_fit,
    _parse_payment_days,
    _score_rse,
    QCDP_WEIGHTS,
)
from agents.agent_storage.agent import StorageAgent

# ═══════════════════════════════════════════════════════════════════════════════
# RUN ALL BENCHMARKS
# ═══════════════════════════════════════════════════════════════════════════════

def run_sub_scoring_benchmark():
    """Test each scoring function against ground-truth values."""
    tests = [
        ("Prix (min=100)", "_score_price", {"prices": [2500, 2960, 3780, 3240, 2700], "idx": 0}, 100.0),
        ("Prix (mid)", "_score_price", {"prices": [2500, 2960, 3780, 3240, 2700], "idx": 2}, 66.1),
        ("Prix (None)", "_score_price", {"prices": [None, 2960], "idx": 0}, 0.0),
        ("Délai (min=100)", "_score_delivery", {"days_list": [3, 5, 7, 10, 14], "idx": 0}, 100.0),
        ("Délai (slowest)", "_score_delivery", {"days_list": [3, 5, 7, 10, 14], "idx": 4}, 21.4),
        ("Garantie '2 years'", "_parse_warranty_months", {"warranty": "2 years"}, 24),
        ("Garantie '18 mois'", "_parse_warranty_months", {"warranty": "18 mois"}, 18),
        ("Garantie '6 months'", "_parse_warranty_months", {"warranty": "6 months"}, 6),
        ("Garantie '1 an'", "_parse_warranty_months", {"warranty": "1 an"}, 12),
        ("Garantie None", "_parse_warranty_months", {"warranty": None}, 0),
        ("Garantie text only", "_parse_warranty_months", {"warranty": "Produit authentique"}, 0),
        ("Paiement 'Net 30 jours'", "_parse_payment_days", {"terms": "Net 30 jours"}, 30),
        ("Paiement 'Net 60 jours'", "_parse_payment_days", {"terms": "Net 60 jours"}, 60),
        ("Paiement '30 days net'", "_parse_payment_days", {"terms": "30 days net"}, 30),
        ("Paiement '50% commande'", "_parse_payment_days", {"terms": "50% à la commande, solde à la livraison"}, 0),
        ("Paiement None", "_parse_payment_days", {"terms": None}, 0),
        ("Budget under", "_score_budget_fit", {"total_price": 2500, "budget_max": 3000}, 75.0),
        ("Budget exact", "_score_budget_fit", {"total_price": 3000, "budget_max": 3000}, 70.0),
        ("Budget over", "_score_budget_fit", {"total_price": 3780, "budget_max": 3000}, 44.0),
        ("Budget unknown", "_score_budget_fit", {"total_price": None, "budget_max": 3000}, 50.0),
    ]

    func_map = {
        "_score_price": _score_price,
        "_score_delivery": _score_delivery,
        "_parse_warranty_months": _parse_warranty_months,
        "_score_payment": _score_payment,
        "_score_budget_fit": _score_budget_fit,
        "_parse_payment_days": _parse_payment_days,
    }

    results = []
    for name, func_name, kwargs, expected in tests:
        func = func_map[func_name]
        actual = func(**kwargs)
        passed = abs(actual - expected) <= 0.15
        results.append({
            "name": name,
            "category": func_name.replace("_", " ").strip(),
            "expected": expected,
            "actual": actual,
            "passed": passed,
        })
    return results


def run_ranking_benchmark():
    """Test full QCDP ranking against expected order."""
    test_cases = [
        {
            "id": "E01 — 5 L'Oréal Shampoo Suppliers",
            "spec": {
                "product": "shampooing L'Oréal Elseve 250ml",
                "quantity": 200,
                "budget_max": 3000,
                "currency": "TND",
                "deadline": "2026-04-30",
            },
            "offers": [
                {"supplier_name": "Cosmétiques Tunisia", "supplier_email": "ventes@cosmetiques-tunisia.tn",
                 "unit_price": 12.5, "total_price": 2500.0, "currency": "TND", "delivery_days": 3,
                 "warranty": "18 mois", "payment_terms": "Net 30 jours",
                 "notes": "Distributeur agréé L'Oréal, certification ISO 9001"},
                {"supplier_name": "Beauté Pro Distribution", "supplier_email": "commercial@beaute-pro.tn",
                 "unit_price": 14.8, "total_price": 2960.0, "currency": "TND", "delivery_days": 5,
                 "warranty": "Produit authentique", "payment_terms": "50% à la commande, solde à la livraison",
                 "notes": "Certification RSE et emballage éco-responsable"},
                {"supplier_name": "Hygiène Express", "supplier_email": "info@hygiene-express.tn",
                 "unit_price": 18.9, "total_price": 3780.0, "currency": "TND", "delivery_days": 7,
                 "warranty": "2 ans", "payment_terms": "Net 45 jours",
                 "notes": "Fournisseur certifié ISO 14001, engagement RSE"},
                {"supplier_name": "ParaPharma Direct", "supplier_email": "devis@parapharma-direct.tn",
                 "unit_price": 16.2, "total_price": 3240.0, "currency": "TND", "delivery_days": 10,
                 "warranty": "Produit original sous scellé", "payment_terms": "Net 30 jours",
                 "notes": "Gamme premium, forte demande client. Pas de certification RSE"},
                {"supplier_name": "Soins Sahara Distribution", "supplier_email": "contact@soins-sahara.tn",
                 "unit_price": 13.5, "total_price": 2700.0, "currency": "TND", "delivery_days": 14,
                 "warranty": "Produit certifié", "payment_terms": "Net 60 jours",
                 "notes": "Grossiste agréé, Fournisseur certifié ISO 14001 (RSE)"},
            ],
            "expected_ranking": [
                "Cosmétiques Tunisia", "Soins Sahara Distribution",
                "Beauté Pro Distribution", "Hygiène Express", "ParaPharma Direct",
            ],
        },
        {
            "id": "E02 — 2 Office Chairs",
            "spec": {"product": "ergonomic office chairs", "quantity": 10, "budget_max": 5000, "currency": "TND"},
            "offers": [
                {"supplier_name": "SupplierA", "supplier_email": "a@supplier.com",
                 "unit_price": 400.0, "total_price": 4000.0, "currency": "TND",
                 "delivery_days": 10, "warranty": "2 years", "payment_terms": "30 days net"},
                {"supplier_name": "SupplierB", "supplier_email": "b@supplier.com",
                 "unit_price": 500.0, "total_price": 5000.0, "currency": "TND",
                 "delivery_days": 7, "warranty": "1 year", "payment_terms": "60 days net"},
            ],
            "expected_ranking": ["SupplierA", "SupplierB"],
        },
    ]

    results = []
    agent = EvaluationAgent()

    for tc in test_cases:
        eval_result = agent.evaluate(tc["offers"], tc["spec"], generate_pdf=False)
        actual_ranking = [s.supplier_name for s in eval_result.scores]
        expected = tc["expected_ranking"]

        correct = sum(1 for a, e in zip(actual_ranking, expected) if a == e)
        accuracy = correct / len(expected) * 100

        scores_detail = []
        for s in eval_result.scores:
            scores_detail.append({
                "rank": s.rank,
                "name": s.supplier_name,
                "qualite": s.qualite_score,
                "cout": s.cout_score,
                "delais": s.delais_score,
                "performance": s.performance_score,
                "overall": s.overall_score,
            })

        results.append({
            "id": tc["id"],
            "expected": expected,
            "actual": actual_ranking,
            "accuracy": accuracy,
            "rank1_correct": actual_ranking[0] == expected[0],
            "scores": scores_detail,
        })

    return results


def run_rse_benchmark():
    """Test RSE scoring heuristics."""
    tests = [
        {
            "name": "Full RSE (.tn + ISO + RSE + warranty)",
            "offer": {"supplier_email": "contact@supplier.tn",
                      "notes": "Fournisseur certifié ISO 14001, engagement RSE", "warranty": "2 ans"},
            "expected_min": 85, "expected_max": 100,
        },
        {
            "name": "No RSE (no .tn, no keywords)",
            "offer": {"supplier_email": "contact@supplier.com",
                      "notes": "Standard supplier, no special features", "warranty": ""},
            "expected_min": 0, "expected_max": 0,
        },
        {
            "name": "Partial (.tn + warranty only)",
            "offer": {"supplier_email": "contact@supplier.tn",
                      "notes": "Standard supplier", "warranty": "1 an"},
            "expected_min": 40, "expected_max": 70,
        },
        {
            "name": "RSE keywords only (no .tn)",
            "offer": {"supplier_email": "contact@supplier.com",
                      "notes": "Certification ISO 9001, engagement durable", "warranty": ""},
            "expected_min": 30, "expected_max": 60,
        },
    ]

    results = []
    for t in tests:
        score = _score_rse(t["offer"])
        passed = t["expected_min"] <= score <= t["expected_max"]
        results.append({
            "name": t["name"],
            "score": score,
            "expected_range": f"{t['expected_min']}-{t['expected_max']}",
            "passed": passed,
        })
    return results


def run_storage_benchmark():
    """Test storage data integrity."""
    results = []

    try:
        agent = StorageAgent(database_url="sqlite:///:memory:")
        spec = {
            "product": "shampooing L'Oréal", "category": "Cosmetics",
            "quantity": 200, "budget_max": 3000, "currency": "TND",
            "requester_email": "test@example.tn", "is_valid": True,
        }
        suppliers = {"suppliers": [
            {"name": "SupA", "email": "a@supplier.tn", "category": "Cosmetics"},
            {"name": "SupB", "email": "b@supplier.tn", "category": "Cosmetics"},
        ]}

        result = agent.store_full_pipeline(
            procurement_spec=spec, supplier_list=suppliers,
            rfq_records=[], offers=[],
        )

        results.append({"name": "Request ID generated", "passed": result.request_id is not None, "detail": result.request_id[:8] + "..."})
        results.append({"name": "Suppliers stored", "passed": result.suppliers_stored == 2, "detail": f"{result.suppliers_stored}/2"})
        results.append({"name": "Status tracked", "passed": result.status is not None, "detail": result.status})

        # Duplicate test
        agent2 = StorageAgent(database_url="sqlite:///:memory:")
        dup_suppliers = {"suppliers": [
            {"name": "Same Co", "email": "same@supplier.tn"},
            {"name": "Same Co Ltd", "email": "same@supplier.tn"},
        ]}
        r2 = agent2.store_full_pipeline(
            procurement_spec=spec, supplier_list=dup_suppliers,
            rfq_records=[], offers=[],
        )
        results.append({"name": "Deduplication", "passed": r2.suppliers_stored <= 2, "detail": f"{r2.suppliers_stored} stored from 2 (same email)"})

    except Exception as e:
        results.append({"name": "Storage tests", "passed": False, "detail": str(e)})

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE HTML REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_html(sub_scores, rankings, rse, storage):
    """Generate a self-contained HTML report with charts."""

    # Calculate summary stats
    sub_total = len(sub_scores)
    sub_passed = sum(1 for s in sub_scores if s["passed"])
    rse_total = len(rse)
    rse_passed = sum(1 for r in rse if r["passed"])
    storage_total = len(storage)
    storage_passed = sum(1 for s in storage if s["passed"])
    ranking_accuracy = sum(r["accuracy"] for r in rankings) / len(rankings) if rankings else 0

    total_tests = sub_total + len(rankings) + rse_total + storage_total
    total_passed = sub_passed + sum(1 for r in rankings if r["rank1_correct"]) + rse_passed + storage_passed

    # Build ranking detail rows
    ranking_html = ""
    for r in rankings:
        scores_table = ""
        for s in r["scores"]:
            bar_color = "#4CAF50" if s["overall"] >= 70 else "#FF9800" if s["overall"] >= 50 else "#F44336"
            scores_table += f"""
            <tr>
                <td style="text-align:center;font-weight:bold;">#{s['rank']}</td>
                <td>{s['name']}</td>
                <td style="text-align:center;">{s['qualite']:.0f}</td>
                <td style="text-align:center;">{s['cout']:.0f}</td>
                <td style="text-align:center;">{s['delais']:.0f}</td>
                <td style="text-align:center;">{s['performance']:.0f}</td>
                <td style="text-align:center;font-weight:bold;">
                    <div style="display:flex;align-items:center;gap:6px;justify-content:center;">
                        <div style="width:60px;height:12px;background:#e0e0e0;border-radius:6px;overflow:hidden;">
                            <div style="width:{s['overall']}%;height:100%;background:{bar_color};border-radius:6px;"></div>
                        </div>
                        {s['overall']:.1f}
                    </div>
                </td>
            </tr>"""

        rank1_icon = "&#9989;" if r["rank1_correct"] else "&#10060;"
        ranking_html += f"""
        <div class="card">
            <h3>{rank1_icon} {r['id']} — Accuracy: {r['accuracy']:.0f}%</h3>
            <div style="display:flex;gap:20px;margin-bottom:10px;">
                <div><strong>Expected #1:</strong> {r['expected'][0]}</div>
                <div><strong>Actual #1:</strong> {r['actual'][0]}</div>
            </div>
            <table class="score-table">
                <thead>
                    <tr>
                        <th>Rank</th><th>Supplier</th>
                        <th>Q /100</th><th>C /100</th><th>D /100</th><th>P /100</th>
                        <th>Overall</th>
                    </tr>
                </thead>
                <tbody>{scores_table}</tbody>
            </table>
        </div>"""

    # Build sub-scoring rows
    sub_rows = ""
    for s in sub_scores:
        icon = "&#9989;" if s["passed"] else "&#10060;"
        diff = abs(s["actual"] - s["expected"])
        sub_rows += f"""
        <tr class="{'pass-row' if s['passed'] else 'fail-row'}">
            <td>{icon}</td>
            <td>{s['name']}</td>
            <td style="text-align:center;">{s['expected']}</td>
            <td style="text-align:center;">{s['actual']}</td>
            <td style="text-align:center;">{diff:.2f}</td>
        </tr>"""

    # Build RSE rows
    rse_rows = ""
    for r in rse:
        icon = "&#9989;" if r["passed"] else "&#10060;"
        rse_rows += f"""
        <tr class="{'pass-row' if r['passed'] else 'fail-row'}">
            <td>{icon}</td>
            <td>{r['name']}</td>
            <td style="text-align:center;">{r['expected_range']}</td>
            <td style="text-align:center;">{r['score']:.0f}</td>
        </tr>"""

    # Build storage rows
    storage_rows = ""
    for s in storage:
        icon = "&#9989;" if s["passed"] else "&#10060;"
        storage_rows += f"""
        <tr class="{'pass-row' if s['passed'] else 'fail-row'}">
            <td>{icon}</td>
            <td>{s['name']}</td>
            <td>{s['detail']}</td>
        </tr>"""

    # Summary donut data
    pass_pct = total_passed / total_tests * 100 if total_tests else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Benchmark Accuracy Report — Procurement AI</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    h1 {{ color: #1A237E; margin-bottom: 5px; }}
    h2 {{ color: #1A237E; margin: 30px 0 15px; border-bottom: 2px solid #1A237E; padding-bottom: 5px; }}
    h3 {{ color: #333; margin-bottom: 10px; }}
    .subtitle {{ color: #666; margin-bottom: 20px; }}
    .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 15px;
             box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}

    /* Summary cards */
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
    .summary-card {{ background: white; border-radius: 8px; padding: 20px; text-align: center;
                     box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .summary-card .big-number {{ font-size: 36px; font-weight: bold; }}
    .summary-card .label {{ color: #666; font-size: 13px; margin-top: 5px; }}
    .green {{ color: #4CAF50; }}
    .orange {{ color: #FF9800; }}
    .red {{ color: #F44336; }}
    .blue {{ color: #1A237E; }}

    /* Donut chart */
    .donut-container {{ display: flex; justify-content: center; margin: 20px 0; }}
    .donut {{ width: 180px; height: 180px; border-radius: 50%;
              background: conic-gradient(#4CAF50 0% {pass_pct}%, #e0e0e0 {pass_pct}% 100%);
              display: flex; align-items: center; justify-content: center; }}
    .donut-inner {{ width: 120px; height: 120px; border-radius: 50%; background: white;
                    display: flex; align-items: center; justify-content: center;
                    flex-direction: column; }}
    .donut-pct {{ font-size: 28px; font-weight: bold; color: #4CAF50; }}
    .donut-label {{ font-size: 11px; color: #666; }}

    /* Agent accuracy bars */
    .agent-bars {{ margin: 20px 0; }}
    .agent-bar {{ display: flex; align-items: center; margin-bottom: 12px; }}
    .agent-bar .name {{ width: 180px; font-weight: 600; font-size: 14px; }}
    .agent-bar .bar-bg {{ flex: 1; height: 28px; background: #e0e0e0; border-radius: 14px; overflow: hidden; position: relative; }}
    .agent-bar .bar-fill {{ height: 100%; border-radius: 14px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; color: white; font-weight: bold; font-size: 13px; }}
    .agent-bar .pct {{ width: 55px; text-align: right; font-weight: bold; font-size: 14px; margin-left: 10px; }}

    /* Tables */
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: #1A237E; color: white; padding: 8px 10px; text-align: left; }}
    td {{ padding: 7px 10px; border-bottom: 1px solid #eee; }}
    .pass-row {{ background: #f1f8e9; }}
    .fail-row {{ background: #fce4ec; }}
    .score-table th {{ font-size: 12px; }}
    .score-table td {{ font-size: 12px; }}

    .timestamp {{ color: #999; font-size: 12px; margin-top: 30px; text-align: center; }}
</style>
</head>
<body>
<div class="container">

<h1>Benchmark Accuracy Report</h1>
<p class="subtitle">Procurement AI Pipeline — Agent-by-Agent Accuracy Testing</p>

<!-- ── Summary Cards ──────────────────────────────────────────────── -->
<div class="summary-grid">
    <div class="summary-card">
        <div class="big-number blue">{total_tests}</div>
        <div class="label">Total Tests</div>
    </div>
    <div class="summary-card">
        <div class="big-number green">{total_passed}</div>
        <div class="label">Passed</div>
    </div>
    <div class="summary-card">
        <div class="big-number {'red' if total_tests - total_passed > 0 else 'green'}">{total_tests - total_passed}</div>
        <div class="label">Failed</div>
    </div>
    <div class="summary-card">
        <div class="big-number green">{pass_pct:.0f}%</div>
        <div class="label">Overall Accuracy</div>
    </div>
</div>

<!-- ── Donut Chart ────────────────────────────────────────────────── -->
<div class="card">
    <h3>Overall Pass Rate</h3>
    <div class="donut-container">
        <div class="donut">
            <div class="donut-inner">
                <div class="donut-pct">{pass_pct:.0f}%</div>
                <div class="donut-label">{total_passed}/{total_tests} tests</div>
            </div>
        </div>
    </div>
</div>

<!-- ── Agent Accuracy Bars ────────────────────────────────────────── -->
<div class="card">
    <h3>Accuracy by Agent</h3>
    <div class="agent-bars">
        <div class="agent-bar">
            <div class="name">Evaluation (QCDP)</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{sub_passed/sub_total*100:.0f}%;background:#4CAF50;">{sub_passed}/{sub_total}</div></div>
            <div class="pct green">{sub_passed/sub_total*100:.0f}%</div>
        </div>
        <div class="agent-bar">
            <div class="name">Ranking Order</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{ranking_accuracy:.0f}%;background:{'#4CAF50' if ranking_accuracy >= 80 else '#FF9800'};">{ranking_accuracy:.0f}%</div></div>
            <div class="pct {'green' if ranking_accuracy >= 80 else 'orange'}">{ranking_accuracy:.0f}%</div>
        </div>
        <div class="agent-bar">
            <div class="name">RSE Scoring</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{rse_passed/rse_total*100:.0f}%;background:{'#4CAF50' if rse_passed == rse_total else '#FF9800'};">{rse_passed}/{rse_total}</div></div>
            <div class="pct {'green' if rse_passed == rse_total else 'orange'}">{rse_passed/rse_total*100:.0f}%</div>
        </div>
        <div class="agent-bar">
            <div class="name">Storage Integrity</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{storage_passed/storage_total*100:.0f}%;background:#4CAF50;">{storage_passed}/{storage_total}</div></div>
            <div class="pct green">{storage_passed/storage_total*100:.0f}%</div>
        </div>
    </div>
</div>

<!-- ── QCDP Ranking Details ───────────────────────────────────────── -->
<h2>QCDP Ranking Accuracy</h2>
{ranking_html}

<!-- ── Sub-Scoring Functions ──────────────────────────────────────── -->
<h2>Sub-Scoring Functions ({sub_passed}/{sub_total} passed)</h2>
<div class="card">
    <table>
        <thead><tr><th></th><th>Test</th><th>Expected</th><th>Actual</th><th>Diff</th></tr></thead>
        <tbody>{sub_rows}</tbody>
    </table>
</div>

<!-- ── RSE Scoring ────────────────────────────────────────────────── -->
<h2>RSE / Local Performance ({rse_passed}/{rse_total} passed)</h2>
<div class="card">
    <table>
        <thead><tr><th></th><th>Scenario</th><th>Expected Range</th><th>Actual Score</th></tr></thead>
        <tbody>{rse_rows}</tbody>
    </table>
</div>

<!-- ── Storage Integrity ──────────────────────────────────────────── -->
<h2>Storage Data Integrity ({storage_passed}/{storage_total} passed)</h2>
<div class="card">
    <table>
        <thead><tr><th></th><th>Test</th><th>Detail</th></tr></thead>
        <tbody>{storage_rows}</tbody>
    </table>
</div>

<!-- ── QCDP Weights Reference ─────────────────────────────────────── -->
<h2>QCDP Weights Configuration</h2>
<div class="card">
    <div style="display:flex;gap:15px;flex-wrap:wrap;">
        <div style="flex:1;min-width:150px;text-align:center;padding:15px;background:#E8EAF6;border-radius:8px;">
            <div style="font-size:24px;font-weight:bold;color:#1A237E;">25%</div>
            <div>Qualité (Q)</div>
            <div style="font-size:11px;color:#666;">Warranty + quality</div>
        </div>
        <div style="flex:1;min-width:150px;text-align:center;padding:15px;background:#FFF3E0;border-radius:8px;">
            <div style="font-size:24px;font-weight:bold;color:#E65100;">35%</div>
            <div>Coût (C)</div>
            <div style="font-size:11px;color:#666;">Price + budget fit</div>
        </div>
        <div style="flex:1;min-width:150px;text-align:center;padding:15px;background:#E0F2F1;border-radius:8px;">
            <div style="font-size:24px;font-weight:bold;color:#00695C;">20%</div>
            <div>Délais (D)</div>
            <div style="font-size:11px;color:#666;">Delivery speed</div>
        </div>
        <div style="flex:1;min-width:150px;text-align:center;padding:15px;background:#F3E5F5;border-radius:8px;">
            <div style="font-size:24px;font-weight:bold;color:#6A1B9A;">20%</div>
            <div>Performance (P)</div>
            <div style="font-size:11px;color:#666;">Payment + RSE</div>
        </div>
    </div>
</div>

<!-- ── AI Accuracy Metrics (if available) ─────────────────────────── -->
{_ai_metrics_section()}

<p class="timestamp">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — Procurement AI Benchmark</p>

</div>
</body>
</html>"""

    return html


def _ai_metrics_section() -> str:
    """Load AI metrics from JSON (if exists) and render an HTML section."""
    metrics_path = PROJECT_ROOT / "outputs" / "ai_metrics_results.json"
    if not metrics_path.exists():
        return """
<h2>AI Accuracy Metrics (LLM Agents)</h2>
<div class="card">
    <p style="color:#999;text-align:center;padding:20px;">
        No AI metrics data found. Run <code>python tests/test_ai_accuracy_metrics.py</code> first to generate LLM accuracy metrics.
    </p>
</div>"""

    import json as _json
    data = _json.loads(metrics_path.read_text(encoding="utf-8"))

    analysis = data.get("analysis_agent", {})
    offer = data.get("offer_parsing", {})
    a_sum = analysis.get("summary", {})
    o_sum = offer.get("summary", {})

    def _bc(val):
        if val >= 0.9: return "#4CAF50"
        elif val >= 0.7: return "#8BC34A"
        elif val >= 0.5: return "#FF9800"
        return "#F44336"

    def _pc(val):
        return f"{val * 100:.1f}%"

    a_rows = ""
    for fname, fdata in analysis.get("per_field", {}).items():
        if fdata["tp"] + fdata["fp"] + fdata["fn"] + fdata["tn"] == 0:
            continue
        color = _bc(fdata["f1"])
        a_rows += f"""
        <tr>
            <td style="font-weight:600;">{fdata['field']}</td>
            <td style="text-align:center;">{fdata['tp']}</td>
            <td style="text-align:center;">{fdata['fp']}</td>
            <td style="text-align:center;">{fdata['fn']}</td>
            <td style="text-align:center;"><span style="color:{_bc(fdata['precision'])};font-weight:bold;">{_pc(fdata['precision'])}</span></td>
            <td style="text-align:center;"><span style="color:{_bc(fdata['recall'])};font-weight:bold;">{_pc(fdata['recall'])}</span></td>
            <td style="text-align:center;"><span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">{_pc(fdata['f1'])}</span></td>
        </tr>"""

    o_rows = ""
    for fname, fdata in offer.get("per_field", {}).items():
        if fdata["tp"] + fdata["fp"] + fdata["fn"] + fdata["tn"] == 0:
            continue
        color = _bc(fdata["f1"])
        o_rows += f"""
        <tr>
            <td style="font-weight:600;">{fdata['field']}</td>
            <td style="text-align:center;">{fdata['tp']}</td>
            <td style="text-align:center;">{fdata['fp']}</td>
            <td style="text-align:center;">{fdata['fn']}</td>
            <td style="text-align:center;"><span style="color:{_bc(fdata['precision'])};font-weight:bold;">{_pc(fdata['precision'])}</span></td>
            <td style="text-align:center;"><span style="color:{_bc(fdata['recall'])};font-weight:bold;">{_pc(fdata['recall'])}</span></td>
            <td style="text-align:center;"><span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">{_pc(fdata['f1'])}</span></td>
        </tr>"""

    combined_f1 = (a_sum.get("f1", 0) + o_sum.get("f1", 0)) / 2

    return f"""
<h2>AI Accuracy Metrics (LLM Agents)</h2>
<div class="card">
    <div style="display:flex;justify-content:space-around;flex-wrap:wrap;margin-bottom:15px;">
        <div style="text-align:center;min-width:120px;">
            <div style="font-size:28px;font-weight:bold;color:{_bc(a_sum.get('f1',0))};">{_pc(a_sum.get('f1',0))}</div>
            <div style="font-size:12px;color:#666;">Analysis F1</div>
        </div>
        <div style="text-align:center;min-width:120px;">
            <div style="font-size:28px;font-weight:bold;color:{_bc(o_sum.get('f1',0))};">{_pc(o_sum.get('f1',0))}</div>
            <div style="font-size:12px;color:#666;">Offer Parsing F1</div>
        </div>
        <div style="text-align:center;min-width:120px;">
            <div style="font-size:28px;font-weight:bold;color:{_bc(combined_f1)};">{_pc(combined_f1)}</div>
            <div style="font-size:12px;color:#666;">Combined F1</div>
        </div>
    </div>
    <p style="font-size:11px;color:#999;text-align:center;">
        Data from: {data.get('timestamp', 'unknown')} | Run <code>python tests/test_ai_accuracy_metrics.py</code> to refresh
    </p>
</div>

<div class="card">
    <h3>Analysis Agent — Per-Field Metrics</h3>
    <table>
        <thead><tr><th>Field</th><th>TP</th><th>FP</th><th>FN</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
        <tbody>{a_rows}</tbody>
    </table>
</div>

<div class="card">
    <h3>Communication Agent (Offer Parsing) — Per-Field Metrics</h3>
    <table>
        <thead><tr><th>Field</th><th>TP</th><th>FP</th><th>FN</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
        <tbody>{o_rows}</tbody>
    </table>
</div>"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Running benchmarks...")

    print("  [1/4] Sub-scoring functions...")
    sub_scores = run_sub_scoring_benchmark()
    passed = sum(1 for s in sub_scores if s["passed"])
    print(f"         {passed}/{len(sub_scores)} passed")

    print("  [2/4] QCDP ranking...")
    rankings = run_ranking_benchmark()
    for r in rankings:
        print(f"         {r['id']}: {r['accuracy']:.0f}% accuracy, rank #1 {'OK' if r['rank1_correct'] else 'WRONG'}")

    print("  [3/4] RSE scoring...")
    rse = run_rse_benchmark()
    passed = sum(1 for r in rse if r["passed"])
    print(f"         {passed}/{len(rse)} passed")

    print("  [4/4] Storage integrity...")
    storage = run_storage_benchmark()
    passed = sum(1 for s in storage if s["passed"])
    print(f"         {passed}/{len(storage)} passed")

    print("\nGenerating HTML report...")
    html = generate_html(sub_scores, rankings, rse, storage)

    out_dir = PROJECT_ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "benchmark_report.html"
    report_path.write_text(html, encoding="utf-8")

    print(f"\nReport saved to: {report_path}")
    print(f"Open in browser: file:///{report_path.as_posix()}")
