from flask import Blueprint, jsonify, make_response, current_app
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from app.models.deal import Deal
from app.models.invoice import Invoice
from sqlalchemy.exc import IntegrityError
import io

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')

def generate_invoice_number():
    import uuid
    # Simple global counter for invoice numbers. 
    # In a real production app, we'd want to use a sequence or lock to prevent race conditions.
    last_invoice = Invoice.query.order_by(Invoice.generated_at.desc()).first()
    if not last_invoice:
        return "CP-0001"
    
    try:
        num = int(last_invoice.invoice_number.split('-')[1])
        # Need to ensure this is completely unique for tests too, where multiple things run fast
        new_num = num + 1
        while Invoice.query.filter_by(invoice_number=f"CP-{new_num:04d}").first():
            new_num += 1
        return f"CP-{new_num:04d}"
    except (IndexError, ValueError):
        return f"CP-{uuid.uuid4().hex[:4].upper()}"

from decimal import Decimal

def auto_generate_invoice(deal):
    """Called when a deal is created to auto-generate an invoice."""
    gross_amount = Decimal(str(deal.amount))
    tds_amount = (gross_amount * Decimal('0.10')) if deal.tds_applicable else Decimal('0')
    net_amount = gross_amount - tds_amount
    
    invoice_number = generate_invoice_number()
    
    invoice = Invoice(
        deal_id=deal.id,
        user_id=deal.user_id,
        invoice_number=invoice_number,
        gross_amount=gross_amount,
        tds_amount=tds_amount,
        net_amount=net_amount
    )
    
    db.session.add(invoice)
    db.session.flush() # get invoice ID without committing yet
    
    # Generate PDF
    from app.utils.pdf import generate_invoice_pdf_bytes
    from app.utils.storage import upload_pdf_to_r2
    
    try:
        pdf_bytes = generate_invoice_pdf_bytes(invoice, deal, deal.user)
        # Upload to R2
        filename = f"invoice_{invoice_number}_{deal.id}.pdf"
        pdf_url = upload_pdf_to_r2(pdf_bytes, filename)
        invoice.pdf_url = pdf_url
    except Exception as e:
        print(f"Error generating/uploading PDF: {e}")
        invoice.pdf_url = None
        
    return invoice

import urllib.parse

@invoices_bp.route('/<deal_id>/share/whatsapp', methods=['GET'])
@login_required
def share_whatsapp(deal_id):
    invoice = Invoice.query.filter_by(deal_id=deal_id, user_id=current_user.id).first_or_404()
    if not invoice.pdf_url:
        return jsonify({"error": "Invoice PDF not available yet"}), 400
        
    deal = invoice.deal
    phone = getattr(deal.brand, 'phone', '') or '' # Future-proof for brand phone field
    
    message = f"Hello {deal.brand.name},\n\nHere is the invoice #{invoice.invoice_number} for our recent collaboration: {invoice.pdf_url}\n\nAmount Due: Rs. {invoice.net_amount}\nDue Date: {deal.due_date.strftime('%d %b %Y')}\n\nThanks,\n{current_user.full_name}"
    encoded_message = urllib.parse.quote(message)
    
    url = f"https://wa.me/{phone}?text={encoded_message}"
    
    return jsonify({"whatsapp_url": url})

@invoices_bp.route('/<deal_id>/pdf', methods=['GET'])
@login_required
def download_invoice_pdf(deal_id):
    invoice = Invoice.query.filter_by(deal_id=deal_id, user_id=current_user.id).first_or_404()
    deal = invoice.deal
    user = current_user
    
    try:
        from app.utils.pdf import generate_invoice_pdf_bytes
        pdf_bytes = generate_invoice_pdf_bytes(invoice, deal, user)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=invoice_{invoice.invoice_number}.pdf'
        return response
    except Exception as e:
        return jsonify({"error": f"PDF generation failed. Error: {e}"}), 500

@invoices_bp.route('/<deal_id>/regenerate', methods=['POST'])
@login_required
def regenerate_invoice(deal_id):
    if current_user.plan != 'pro':
        return jsonify({'error': 'Pro plan required', 'upgrade_required': True}), 403
        
    invoice = Invoice.query.filter_by(deal_id=deal_id, user_id=current_user.id).first_or_404()
    deal = invoice.deal
    user = current_user
    
    from app.utils.storage import delete_from_r2, upload_pdf_to_r2
    from app.utils.pdf import generate_invoice_pdf_bytes
    
    # 1. Delete old PDF
    if invoice.pdf_url:
        delete_from_r2(invoice.pdf_url)
        
    try:
        # 2. Regenerate PDF bytes
        pdf_bytes = generate_invoice_pdf_bytes(invoice, deal, user)
        
        # 3. Upload new PDF
        filename = f"invoice_{invoice.invoice_number}_{deal.id}.pdf"
        new_pdf_url = upload_pdf_to_r2(pdf_bytes, filename)
        
        # 4. Save
        invoice.pdf_url = new_pdf_url
        invoice.generated_at = datetime.now() # update timestamp to show it's new
        db.session.commit()
        
        return jsonify({'status': 'regenerated', 'pdf_url': new_pdf_url}), 200
    except Exception as e:
        return jsonify({"error": f"PDF regeneration failed. Error: {e}"}), 500
