import uuid
from datetime import datetime, timezone
from app import db

class Deal(db.Model):
    __tablename__ = 'deals'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=False)
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    content_type = db.Column(db.Enum('reel', 'post', 'video', 'story', 'blog', 'other', name='content_type_enum'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('negotiating', 'active', 'invoice_sent', 'paid', 'overdue', name='status_enum'), default='negotiating', nullable=False)
    
    tds_applicable = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    
    paid_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime, nullable=True) # Soft delete

    user = db.relationship('User', backref=db.backref('deals', lazy=True))
    brand = db.relationship('Brand', backref=db.backref('deals', lazy=True))

    def __repr__(self):
        return f"<Deal {self.id} Status: {self.status}>"
