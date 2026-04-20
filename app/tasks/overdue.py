import os
import resend
from app import celery, db
from app.models.deal import Deal
from datetime import datetime

@celery.task(name='check_and_mark_overdue')
def check_and_mark_overdue():
    """
    Finds all non-paid deals whose due date is in the past,
    and updates their status to overdue.
    """
    today = datetime.now().date()
    
    # Query for deals that are not paid, not already overdue, and due date has passed
    overdue_deals = Deal.query.filter(
        Deal.status.notin_(['paid', 'overdue']),
        Deal.due_date < today,
        Deal.deleted_at == None
    ).all()
    
    count = len(overdue_deals)
    
    resend_api_key = os.environ.get('RESEND_API_KEY')
    
    for deal in overdue_deals:
        deal.status = 'overdue'
        
        # Pro Feature: Send email notification to creator
        if deal.user.plan == 'pro' and resend_api_key and os.environ.get('FLASK_ENV') != 'testing':
            try:
                resend.api_key = resend_api_key
                resend.Emails.send({
                    "from": "notifications@creapay.in",
                    "to": deal.user.email,
                    "subject": f"Deal Overdue: {deal.brand.name}",
                    "html": f"<p>Hi {deal.user.full_name},</p><p>Your deal with <b>{deal.brand.name}</b> for Rs. {deal.amount} is now officially overdue.</p><p>Consider logging in to send them a payment reminder.</p>"
                })
            except Exception as e:
                print(f"Failed to send overdue email to {deal.user.email}: {e}")
        
    db.session.commit()
    
    # Normally we'd log this or send to Sentry
    print(f"check_and_mark_overdue: Marked {count} deals as overdue.")
    return count
