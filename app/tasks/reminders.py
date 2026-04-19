import os
from flask import current_app
from app import celery, db
from app.models.deal import Deal
import resend
from datetime import datetime

@celery.task(name='send_reminder')
def send_reminder(deal_id, reminder_message=None):
    """
    Sends an email to the brand reminding them of the payment.
    Also logs the reminder generation for WhatsApp (which is manual for MVP).
    """
    deal = Deal.query.get(deal_id)
    if not deal or not deal.invoice:
        return "Deal or invoice not found"
        
    brand = deal.brand
    user = deal.user
    
    # WhatsApp message generation (manual for MVP)
    # The frontend generates the wa.me link directly using these details.
    
    # Resend Email Integration
    resend_api_key = os.environ.get('RESEND_API_KEY')
    if resend_api_key and brand.email:
        resend.api_key = resend_api_key
        
        pdf_url = deal.invoice.pdf_url or '#'
        amount = deal.invoice.gross_amount
        due_date = deal.due_date.strftime('%b %d, %Y')
        
        html_content = f"""
        <div style="font-family: sans-serif;">
            <h2>Payment Reminder from {user.full_name}</h2>
            <p>Hi {brand.name},</p>
            <p>This is a friendly reminder that invoice <strong>{deal.invoice.invoice_number}</strong> 
            for <strong>₹{amount}</strong> is due on <strong>{due_date}</strong>.</p>
            <p>You can view and download your invoice PDF here:</p>
            <p><a href="{pdf_url}" style="background: #6C47FF; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">View Invoice</a></p>
            <br>
            <p>Thanks,<br>{user.full_name}</p>
        </div>
        """
        
        try:
            # We use a mocked API key or check testing config during tests
            # Real resend sends the email
            if os.environ.get('FLASK_ENV') != 'testing':
                resend.Emails.send({
                    "from": "invoices@creapay.in",
                    "to": brand.email,
                    "subject": f"Payment Reminder: {deal.invoice.invoice_number}",
                    "html": html_content
                })
        except Exception as e:
            # Sentry log would go here
            print(f"Failed to send email to {brand.email}: {e}")
            
    # Mark reminder sent
    deal.reminder_sent_at = datetime.now()
    db.session.commit()
    
    return f"Reminder sent for deal {deal_id}"
