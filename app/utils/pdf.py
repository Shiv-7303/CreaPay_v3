from weasyprint import HTML
from flask import render_template

def generate_invoice_pdf_bytes(invoice, deal, user):
    html_content = render_template(
        'invoice_pdf.html',
        invoice=invoice,
        deal=deal,
        user=user
    )
    return HTML(string=html_content).write_pdf()
