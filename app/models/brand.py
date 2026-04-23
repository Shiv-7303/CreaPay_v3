import uuid
from datetime import datetime, timezone
from app import db

class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    total_deals = db.Column(db.Integer, default=0, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('brands', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_user_brand_name'),
    )

    def __repr__(self):
        return f"<Brand {self.name} for User {self.user_id}>"
