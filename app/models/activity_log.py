import uuid
from datetime import datetime, timezone
from app import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True) # Can be null if system action
    action = db.Column(db.String(255), nullable=False)
    metadata_info = db.Column(db.Text, nullable=True) # Using Text for JSON string representation
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __repr__(self):
        return f"<ActivityLog {self.action}>"
