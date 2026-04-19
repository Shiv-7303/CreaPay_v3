import uuid
from datetime import datetime, timezone
from app import db

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    razorpay_payment_id = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='pro', nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    
    starts_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('active', 'cancelled', 'expired', name='subscription_status'), default='active', nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))

    def __repr__(self):
        return f"<Subscription {self.id} User {self.user_id}>"
