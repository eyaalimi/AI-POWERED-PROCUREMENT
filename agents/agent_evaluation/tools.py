"""
agents/agent_evaluation/tools.py
PDF report generation for the Evaluation Agent.

Generates a comparison table as a PDF using only the Python standard library
+ reportlab (lightweight PDF library).

Fallback: if reportlab is not installed, generates a plain-text .txt report.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logger import get_logger

logger = get_logger(__name__)


def _fmt(value, fallback="N/A"):
    """Format a value for display, returning fallback if None."""
    if value is None:
        return fallback
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def generate_pdf_report(
    product: str,
    procurement_spec: dict,
    scores: list,
    output_dir: str = None,
) -> Optional[str]:
    """
    Generate a PDF comparison report for evaluated offers.

    Args:
        product: product name
        procurement_spec: the original procurement spec dict
        scores: list of OfferScore dataclasses (ranked)
        output_dir: output directory (default: outputs/)

    Returns:
        Path to the generated PDF file, or None on failure.
    """
    if not scores:
        return None

    default_dir = os.environ.get("OUTPUTS_DIR", str(PROJECT_ROOT / "outputs"))
    out = Path(output_dir) if output_dir else Path(default_dir)
    try:
        out.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        out = Path("/tmp/outputs")
        out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_report_{ts}.pdf"
    filepath = out / filename

    try:
        return _generate_with_reportlab(filepath, product, procurement_spec, scores)
    except ImportError:
        logger.warning("reportlab not installed — falling back to text report")
        return _generate_text_report(filepath.with_suffix(".txt"), product, procurement_spec, scores)
    except Exception as exc:
        logger.error("PDF generation failed", extra={"error": str(exc)})
        return _generate_text_report(filepath.with_suffix(".txt"), product, procurement_spec, scores)


def _draw_score_bar(canvas_obj, x, y, width, height, score, color):
    """Draw a horizontal score bar with percentage fill."""
    from reportlab.lib import colors as c
    # Background (grey)
    canvas_obj.setFillColor(c.HexColor("#E8E8E8"))
    canvas_obj.roundRect(x, y, width, height, 2, fill=1, stroke=0)
    # Filled portion
    fill_width = max(0, min(width, width * score / 100))
    if fill_width > 0:
        canvas_obj.setFillColor(color)
        canvas_obj.roundRect(x, y, fill_width, height, 2, fill=1, stroke=0)


def _generate_with_reportlab(
    filepath: Path,
    product: str,
    spec: dict,
    scores: list,
) -> str:
    """Generate a polished PDF evaluation report."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        HRFlowable,
    )

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1A237E"),
        spaceAfter=2 * mm,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#455A64"),
        spaceAfter=1 * mm,
    )
    section_style = ParagraphStyle(
        "SectionHeader", parent=styles["Heading2"],
        fontSize=14, textColor=colors.HexColor("#1A237E"),
        spaceBefore=4 * mm, spaceAfter=2 * mm,
        borderPadding=(0, 0, 2, 0),
    )
    rec_style = ParagraphStyle(
        "Recommendation", parent=styles["Normal"],
        fontSize=9, leading=13, spaceBefore=1 * mm, spaceAfter=1 * mm,
        leftIndent=6 * mm,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#9E9E9E"),
        alignment=TA_CENTER,
    )

    elements = []

    # ── Header banner ────────────────────────────────────────────────────────
    elements.append(Paragraph("Rapport d'Évaluation des Fournisseurs", title_style))
    elements.append(Paragraph("Matrice QCDP — Qualité, Coût, Délais, Performance", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A237E")))
    elements.append(Spacer(1, 4 * mm))

    # ── Project info box ─────────────────────────────────────────────────────
    budget_max = spec.get("budget_max")
    quantity = spec.get("quantity")
    unit = spec.get("unit", "")
    deadline = spec.get("deadline")
    currency = spec.get("currency", "TND")

    info_data = [
        ["Produit", product, "Quantité", f"{quantity} {unit}" if quantity else "N/A"],
        ["Budget max", f"{_fmt(budget_max)} {currency}" if budget_max else "N/A",
         "Délai souhaité", deadline or "Non spécifié"],
        ["Offres reçues", str(len(scores)), "Date", datetime.now(timezone.utc).strftime("%d/%m/%Y")],
    ]
    info_table = Table(info_data, colWidths=[65, 150, 70, 150])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EAF6")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E8EAF6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1A237E")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#1A237E")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C5CAE9")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Classement Général (main ranking table) ──────────────────────────────
    elements.append(Paragraph("Classement Général", section_style))

    # Cell styles for wrapping text inside table cells
    cell_style = ParagraphStyle(
        "CellText", parent=styles["Normal"],
        fontSize=7.5, leading=9,
    )
    cell_center = ParagraphStyle(
        "CellCenter", parent=cell_style,
        alignment=TA_CENTER,
    )
    header_style = ParagraphStyle(
        "HeaderCell", parent=styles["Normal"],
        fontSize=7.5, leading=9, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_CENTER,
    )

    header = [
        Paragraph("#", header_style),
        Paragraph("Fournisseur", header_style),
        Paragraph("Prix<br/>unitaire", header_style),
        Paragraph("Prix<br/>total", header_style),
        Paragraph("Délai<br/>(jours)", header_style),
        Paragraph("Garantie", header_style),
        Paragraph("Paiement", header_style),
        Paragraph("Qualité<br/>/100", header_style),
        Paragraph("Coût<br/>/100", header_style),
        Paragraph("Délais<br/>/100", header_style),
        Paragraph("Perf/RSE<br/>/100", header_style),
        Paragraph("SCORE<br/>GLOBAL", header_style),
    ]

    data = [header]
    for s in scores:
        row = [
            Paragraph(str(s.rank), cell_center),
            Paragraph(s.supplier_name, cell_style),
            Paragraph(_fmt(s.unit_price), cell_center),
            Paragraph(_fmt(s.total_price), cell_center),
            Paragraph(_fmt(s.delivery_days), cell_center),
            Paragraph(s.warranty or "N/A", cell_style),
            Paragraph(s.payment_terms or "N/A", cell_style),
            Paragraph(f"{getattr(s, 'qualite_score', 0):.0f}", cell_center),
            Paragraph(f"{getattr(s, 'cout_score', 0):.0f}", cell_center),
            Paragraph(f"{getattr(s, 'delais_score', 0):.0f}", cell_center),
            Paragraph(f"{getattr(s, 'performance_score', 0):.0f}", cell_center),
            Paragraph(f"<b>{s.overall_score:.1f}</b>", cell_center),
        ]
        data.append(row)

    col_widths = [18, 90, 42, 45, 32, 75, 75, 34, 34, 34, 38, 42]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Color code for score columns
    def _score_color(val):
        if val >= 80:
            return colors.HexColor("#C8E6C9")  # green
        elif val >= 60:
            return colors.HexColor("#FFF9C4")  # yellow
        else:
            return colors.HexColor("#FFCDD2")  # red

    style_cmds = [
        # Header row background
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A237E")),
        # Vertical alignment
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        # Grid
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A237E")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]

    # Highlight #1 row in green
    if len(data) > 1:
        style_cmds.append(("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#C8E6C9")))

    # Color-code individual QCDP score cells
    for row_idx, s in enumerate(scores, start=1):
        for col_idx, score_val in [
            (7, getattr(s, 'qualite_score', 0)),
            (8, getattr(s, 'cout_score', 0)),
            (9, getattr(s, 'delais_score', 0)),
            (10, getattr(s, 'performance_score', 0)),
        ]:
            style_cmds.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), _score_color(score_val)))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    elements.append(Spacer(1, 4 * mm))

    # ── QCDP Weights legend ──────────────────────────────────────────────────
    weights_data = [
        ["Qualité (Q)", "25%", "Coût (C)", "35%", "Délais (D)", "20%", "Performance/RSE (P)", "20%"],
    ]
    weights_table = Table(weights_data, colWidths=[65, 30, 55, 30, 55, 30, 85, 30])
    weights_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3E0")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
        ("FONTNAME", (4, 0), (4, 0), "Helvetica-Bold"),
        ("FONTNAME", (6, 0), (6, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, 0), "Helvetica-Bold"),
        ("FONTNAME", (5, 0), (5, 0), "Helvetica-Bold"),
        ("FONTNAME", (7, 0), (7, 0), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#E65100")),
        ("TEXTCOLOR", (3, 0), (3, 0), colors.HexColor("#E65100")),
        ("TEXTCOLOR", (5, 0), (5, 0), colors.HexColor("#E65100")),
        ("TEXTCOLOR", (7, 0), (7, 0), colors.HexColor("#E65100")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FFB74D")),
    ]))
    elements.append(weights_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Recommandations ──────────────────────────────────────────────────────
    elements.append(Paragraph("Recommandations", section_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#C5CAE9")))
    elements.append(Spacer(1, 2 * mm))

    for s in scores:
        # Medal emoji for top 3
        medal = {1: "1er", 2: "2ème", 3: "3ème"}.get(s.rank, f"{s.rank}ème")
        score_color = "#2E7D32" if s.overall_score >= 75 else "#F57F17" if s.overall_score >= 50 else "#C62828"
        elements.append(
            Paragraph(
                f'<b><font color="{score_color}">{medal}</font> — {s.supplier_name}</b>'
                f' <font color="#757575">(Score: {s.overall_score:.1f}/100)</font><br/>'
                f'<font color="#424242">{s.recommendation}</font>',
                rec_style,
            )
        )

    # ── Footer ───────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E0E0E0")))
    elements.append(Spacer(1, 2 * mm))
    elements.append(
        Paragraph(
            f"Rapport généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}"
            f" — Procurement AI System — Confidentiel",
            footer_style,
        )
    )

    doc.build(elements)
    logger.info("PDF report generated", extra={"path": str(filepath)})
    return str(filepath)


def _generate_text_report(
    filepath: Path,
    product: str,
    spec: dict,
    scores: list,
) -> str:
    """Fallback: generate a plain-text report."""
    lines = [
        "=" * 70,
        "RAPPORT D'ÉVALUATION DES FOURNISSEURS",
        "Matrice QCDP — Qualité, Coût, Délais, Performance",
        "=" * 70,
        f"Produit  : {product}",
        f"Quantité : {spec.get('quantity', 'N/A')} {spec.get('unit', '')}",
        f"Budget   : {_fmt(spec.get('budget_max'))} {spec.get('currency', 'TND')}",
        f"Délai    : {spec.get('deadline', 'Non spécifié')}",
        f"Offres   : {len(scores)}",
        "",
        "-" * 70,
    ]

    for s in scores:
        lines.extend([
            f"#{s.rank} — {s.supplier_name}",
            f"  Email          : {getattr(s, 'supplier_email', '') or 'N/A'}",
            f"  Prix unitaire  : {_fmt(s.unit_price)} TND",
            f"  Prix total     : {_fmt(s.total_price)} {s.currency}",
            f"  Délai livraison: {_fmt(s.delivery_days)} jours",
            f"  Garantie       : {s.warranty or 'N/A'}",
            f"  Paiement       : {s.payment_terms or 'N/A'}",
            f"  Qualité  : {getattr(s, 'qualite_score', 0):5.1f}/100  (25%)",
            f"  Coût     : {getattr(s, 'cout_score', 0):5.1f}/100  (35%)",
            f"  Délais   : {getattr(s, 'delais_score', 0):5.1f}/100  (20%)",
            f"  Perf/RSE : {getattr(s, 'performance_score', 0):5.1f}/100  (20%)",
            f"  SCORE GLOBAL : {s.overall_score:.1f} / 100",
            f"  Recommandation : {s.recommendation}",
            "-" * 70,
        ])

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"\nRapport généré le {ts} — Procurement AI System — Confidentiel")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Text report generated (fallback)", extra={"path": str(filepath)})
    return str(filepath)
