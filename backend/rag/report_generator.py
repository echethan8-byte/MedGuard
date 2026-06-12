"""
rag/report_generator.py — Generate PDF compliance reports using ReportLab.
"""
import io
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger('medguard')

RISK_COLORS = {
    'critical': (0.937, 0.267, 0.267),   # #EF4444
    'high':     (0.961, 0.620, 0.043),   # #F59E0B
    'medium':   (0.231, 0.510, 0.965),   # #3B82F6
    'low':      (0.063, 0.725, 0.506),   # #10B981
}

DARK_BG   = (0.039, 0.059, 0.118)   # #0A0F1E
TEAL      = (0.000, 0.784, 0.722)   # #00C9B8
LIGHT     = (0.910, 0.941, 1.000)   # #E8EEFF
MID_GRAY  = (0.533, 0.573, 0.643)   # #8892A4
CARD_BG   = (0.059, 0.086, 0.157)   # #0F1628


def generate_pdf_report(report_data: Dict[str, Any], document_name: str) -> bytes:
    """
    Generate a professional PDF compliance report.
    Returns PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.graphics.shapes import Drawing, Circle, String, Rect
        from reportlab.graphics import renderPDF
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )

        W, H = A4
        styles = getSampleStyleSheet()

        # Custom styles
        def make_style(name, parent='Normal', **kwargs):
            return ParagraphStyle(name=name, parent=styles[parent], **kwargs)

        title_style = make_style('Title', fontSize=22, textColor=colors.HexColor('#E8EEFF'),
                                 fontName='Helvetica-Bold', spaceAfter=4, leading=28)
        subtitle_style = make_style('Subtitle', fontSize=11, textColor=colors.HexColor('#00C9B8'),
                                    fontName='Helvetica', spaceAfter=2)
        heading_style = make_style('Heading', fontSize=12, textColor=colors.HexColor('#E8EEFF'),
                                   fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
        body_style = make_style('Body', fontSize=9, textColor=colors.HexColor('#8892A4'),
                                fontName='Helvetica', leading=14, spaceAfter=4)
        evidence_style = make_style('Evidence', fontSize=8, textColor=colors.HexColor('#00C9B8'),
                                    fontName='Courier', leading=12, leftIndent=10,
                                    borderColor=colors.HexColor('#F59E0B'), borderWidth=1,
                                    borderPadding=6, backColor=colors.HexColor('#05080F'))
        label_style = make_style('Label', fontSize=7, textColor=colors.HexColor('#4A5568'),
                                 fontName='Helvetica', leading=10, spaceAfter=2)

        elements = []

        # ── Header ─────────────────────────────────────────────────────────────
        score = report_data.get('compliance_score', 0)
        generated = datetime.now().strftime('%B %d, %Y at %H:%M UTC')
        violations = report_data.get('violations', [])

        elements.append(Paragraph("⚕ MedGuard", subtitle_style))
        elements.append(Paragraph("Healthcare Compliance Audit Report", title_style))
        elements.append(Paragraph(f"Document: {document_name}", body_style))
        elements.append(Paragraph(f"Generated: {generated}", body_style))
        elements.append(Spacer(1, 6*mm))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#151D35')))
        elements.append(Spacer(1, 4*mm))

        # ── Score Summary Table ────────────────────────────────────────────────
        score_color = '#10B981' if score >= 80 else '#F59E0B' if score >= 60 else '#EF4444'
        risk_counts = {r: sum(1 for v in violations if v.get('risk') == r) for r in ['critical', 'high', 'medium', 'low']}

        summary_data = [
            [Paragraph('<b>COMPLIANCE SCORE</b>', label_style),
             Paragraph('<b>CRITICAL</b>', label_style),
             Paragraph('<b>HIGH RISK</b>', label_style),
             Paragraph('<b>MEDIUM</b>', label_style),
             Paragraph('<b>LOW</b>', label_style)],
            [Paragraph(f'<font size=24 color="{score_color}"><b>{score}/100</b></font>', styles['Normal']),
             Paragraph(f'<font size=18 color="#EF4444"><b>{risk_counts["critical"]}</b></font>', styles['Normal']),
             Paragraph(f'<font size=18 color="#F59E0B"><b>{risk_counts["high"]}</b></font>', styles['Normal']),
             Paragraph(f'<font size=18 color="#3B82F6"><b>{risk_counts["medium"]}</b></font>', styles['Normal']),
             Paragraph(f'<font size=18 color="#10B981"><b>{risk_counts["low"]}</b></font>', styles['Normal'])],
        ]

        summary_table = Table(summary_data, colWidths=[W*0.26, W*0.16, W*0.16, W*0.16, W*0.16])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0F1628')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#151D35')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#0F1628'), colors.HexColor('#0A0F1E')]),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 5*mm))

        # ── Executive Summary ──────────────────────────────────────────────────
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Paragraph(report_data.get('summary', ''), body_style))
        elements.append(Spacer(1, 4*mm))

        # ── Violations Table ───────────────────────────────────────────────────
        elements.append(Paragraph(f"Violations Detected ({len(violations)})", heading_style))

        if violations:
            v_header = [
                Paragraph('<b>REG ID</b>', label_style),
                Paragraph('<b>FINDING</b>', label_style),
                Paragraph('<b>RISK</b>', label_style),
                Paragraph('<b>CATEGORY</b>', label_style),
            ]
            v_rows = [v_header]
            for v in violations:
                risk = v.get('risk', 'low')
                rc = colors.HexColor('#' + ''.join(f'{int(c*255):02X}' for c in RISK_COLORS.get(risk, (0.5, 0.5, 0.5))))
                v_rows.append([
                    Paragraph(f'<font size=7 color="#00C9B8">{v.get("regulation_id", "")}</font>', styles['Normal']),
                    Paragraph(f'<font size=8><b>{v.get("title", "")}</b></font><br/><font size=7 color="#8892A4">{v.get("description", "")[:120]}…</font>', styles['Normal']),
                    Paragraph(f'<font size=8 color="#{int(RISK_COLORS.get(risk, (0.5,0.5,0.5))[0]*255):02X}{int(RISK_COLORS.get(risk, (0.5,0.5,0.5))[1]*255):02X}{int(RISK_COLORS.get(risk, (0.5,0.5,0.5))[2]*255):02X}"><b>{risk.upper()}</b></font>', styles['Normal']),
                    Paragraph(f'<font size=7 color="#8892A4">{v.get("category", "")}</font>', styles['Normal']),
                ])

            v_table = Table(v_rows, colWidths=[30*mm, 95*mm, 22*mm, 35*mm])
            v_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#151D35')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0F1628'), colors.HexColor('#0A0F1E')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#151D35')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(v_table)
            elements.append(Spacer(1, 5*mm))

        # ── Detailed Findings ──────────────────────────────────────────────────
        elements.append(Paragraph("Detailed Findings & Corrective Actions", heading_style))

        for i, v in enumerate(violations, 1):
            risk = v.get('risk', 'low')
            rc_hex = '#' + ''.join(f'{int(c*255):02X}' for c in RISK_COLORS.get(risk, (0.5,0.5,0.5)))

            finding_block = [
                Paragraph(f'<font size=10 color="{rc_hex}"><b>[{risk.upper()}]</b></font> <font size=10 color="#E8EEFF"><b>{i}. {v.get("title", "")}</b></font>', styles['Normal']),
                Spacer(1, 2*mm),
                Paragraph(f'<font size=7 color="#4A5568">REGULATION: </font><font size=7 color="#00C9B8">{v.get("regulation_id", "")} · {v.get("citation", "")}</font>', styles['Normal']),
                Spacer(1, 2*mm),
                Paragraph(v.get('description', ''), body_style),
                Spacer(1, 2*mm),
                Paragraph('<font size=7 color="#F59E0B">EVIDENCE FROM DOCUMENT:</font>', styles['Normal']),
                Paragraph(v.get('evidence', ''), evidence_style),
                Spacer(1, 2*mm),
                Paragraph('<font size=7 color="#10B981">CORRECTIVE ACTION:</font>', styles['Normal']),
                Paragraph(v.get('corrective_action', ''), body_style),
                HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#151D35')),
                Spacer(1, 3*mm),
            ]
            elements.extend(finding_block)

        # ── Citations ──────────────────────────────────────────────────────────
        citations = report_data.get('citations', [])
        if citations:
            elements.append(Paragraph("Policy Sources Referenced", heading_style))
            for i, c in enumerate(citations, 1):
                elements.append(Paragraph(f'{i}. {c}', body_style))
            elements.append(Spacer(1, 4*mm))

        # ── Footer note ────────────────────────────────────────────────────────
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#151D35')))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(
            f'Report generated by MedGuard RAG v1.0 · Model: {report_data.get("llm_model", "N/A")} · '
            f'Chunks analyzed: {report_data.get("chunks_reranked", "N/A")} · '
            f'Processing: {report_data.get("processing_time_ms", 0) / 1000:.1f}s',
            make_style('Footer', fontSize=7, textColor=colors.HexColor('#4A5568'))
        ))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info(f"PDF report generated: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise
