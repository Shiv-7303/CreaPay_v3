import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_invoice_pdf_bytes(invoice, deal, user):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6C47FF'),
        alignment=2 # Right align
    )
    
    normal_style = styles['Normal']
    bold_style = ParagraphStyle('BoldStyle', parent=normal_style, fontName='Helvetica-Bold')

    # Header
    # User / Creator info on left, Invoice title on right
    header_data = [
        [Paragraph(f"<b>{user.full_name}</b>", bold_style), Paragraph("INVOICE", title_style)],
        [Paragraph(f"{user.email}", normal_style), Paragraph(f"#{invoice.invoice_number}", ParagraphStyle('RightNorm', alignment=2))],
        ["", Paragraph(f"Date: {invoice.generated_at.strftime('%Y-%m-%d')}", ParagraphStyle('RightNorm', alignment=2))]
    ]
    
    header_table = Table(header_data, colWidths=['50%', '50%'])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 2), (-1, 2), 2, colors.HexColor('#6C47FF')),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 10),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Bill To
    brand_email_str = f"<br/>{deal.brand.email}" if deal.brand.email else ""
    bill_to_data = [
        [Paragraph("<b>Bill To:</b>", bold_style), Paragraph(f"<b>Due Date:</b> {deal.due_date.strftime('%Y-%m-%d')}", ParagraphStyle('RightNorm', alignment=2))],
        [Paragraph(f"{deal.brand.name}{brand_email_str}", normal_style), ""]
    ]
    bill_to_table = Table(bill_to_data, colWidths=['50%', '50%'])
    bill_to_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    
    elements.append(bill_to_table)
    elements.append(Spacer(1, 30))
    
    # Invoice Items Table
    content_type_cap = deal.content_type.capitalize()
    items_data = [
        ["Description", "Amount"],
        [f"Content Creation - {content_type_cap}", f"Rs. {invoice.gross_amount}"]
    ]
    
    items_table = Table(items_data, colWidths=['70%', '30%'])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6C47FF')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('LINEBELOW', (0, 1), (-1, -1), 1, colors.lightgrey),
        ('PADDING', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Totals
    # Need to do this separately because ReportLab expects identical nested lists if we use `.append` directly on the first list
    t_data = [
        ["Gross Amount:", f"Rs. {invoice.gross_amount}"]
    ]
    
    if invoice.tds_amount > 0:
        t_data.append(["TDS (10%):", f"- Rs. {invoice.tds_amount}"])
        
    t_data.append(["Net Amount:", f"Rs. {invoice.net_amount}"])
    
    totals_table = Table(t_data, colWidths=['70%', '30%'])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#6C47FF')),
        ('TOPPADDING', (0, -1), (-1, -1), 10),
    ]))
    
    elements.append(totals_table)
    
    # Notes
    if deal.notes:
        elements.append(Spacer(1, 40))
        elements.append(Paragraph("<b>Notes:</b>", bold_style))
        elements.append(Paragraph(deal.notes, normal_style))
        
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
