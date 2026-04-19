import uuid
from datetime import datetime, timezone
from app import db

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = db.Column(db.String(36), db.ForeignKey('deals.id'), unique=True, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    pdf_url = db.Column(db.Text, nullable=True)
    
    gross_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tds_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    net_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    deal = db.relationship('Deal', backref=db.backref('invoice', uselist=False, lazy=True))
    user = db.relationship('User', backref=db.backref('invoices', lazy=True))

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"
