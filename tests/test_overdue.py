import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand
from app.models.deal import Deal
from datetime import datetime, timedelta
import bcrypt

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_overdue_detection(app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashed
        )
        db.session.add(user)
        db.session.flush()
        
        brand = Brand(name="Test Brand", user_id=user.id)
        db.session.add(brand)
        db.session.flush()
        
        # Create deals with different due dates and statuses
        
        # Deal 1: Overdue (past due date, not paid)
        deal1 = Deal(
            user_id=user.id, brand_id=brand.id, amount=1000, content_type='post',
            due_date=(datetime.now() - timedelta(days=2)).date(),
            status='active'
        )
        
        # Deal 2: Not overdue (future due date)
        deal2 = Deal(
            user_id=user.id, brand_id=brand.id, amount=1000, content_type='post',
            due_date=(datetime.now() + timedelta(days=2)).date(),
            status='active'
        )
        
        # Deal 3: Already paid (past due date but shouldn't be touched)
        deal3 = Deal(
            user_id=user.id, brand_id=brand.id, amount=1000, content_type='post',
            due_date=(datetime.now() - timedelta(days=2)).date(),
            status='paid'
        )
        
        db.session.add_all([deal1, deal2, deal3])
        db.session.commit()
        
        # Run task
        from app.tasks.overdue import check_and_mark_overdue
        count = check_and_mark_overdue.apply().get()
        
        # Only deal 1 should have been marked
        assert count == 1
        
        # Verify DB state
        d1 = Deal.query.get(deal1.id)
        assert d1.status == 'overdue'
        
        d2 = Deal.query.get(deal2.id)
        assert d2.status == 'active'
        
        d3 = Deal.query.get(deal3.id)
        assert d3.status == 'paid'
