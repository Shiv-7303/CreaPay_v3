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
    for deal in overdue_deals:
        deal.status = 'overdue'
        
    db.session.commit()
    
    # Normally we'd log this or send to Sentry
    print(f"check_and_mark_overdue: Marked {count} deals as overdue.")
    return count
