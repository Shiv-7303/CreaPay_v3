import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand
from app.models.deal import Deal
from app.models.invoice import Invoice
import bcrypt
import os

@pytest.fixture
def app():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def pro_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test Pro',
            email='testpro@example.com',
            password_hash=hashed,
            plan='pro'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': 'testpro@example.com',
        'password': 'password123'
    })
    
    return client, user_id

@pytest.fixture
def free_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test Free',
            email='testfree@example.com',
            password_hash=hashed,
            plan='free'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': 'testfree@example.com',
        'password': 'password123'
    })
    
    return client, user_id

def test_send_reminder_pro(pro_client, app):
    client, user_id = pro_client
    
    # Create deal
    res = client.post('/deals/create', json={
        'brand_name': 'Remind Brand',
        'amount': '5000',
        'content_type': 'post'
    })
    deal_id = res.json['id']
    
    # Send reminder (this enqueues task and returns 200)
    res = client.post(f'/deals/{deal_id}/remind')
    assert res.status_code == 200
    assert res.json['status'] == 'reminder queued'

def test_send_reminder_free(free_client, app):
    client, user_id = free_client
    
    # Create deal
    res = client.post('/deals/create', json={
        'brand_name': 'Remind Brand',
        'amount': '5000',
        'content_type': 'post'
    })
    deal_id = res.json['id']
    
    # Send reminder (should fail due to @pro_required)
    res = client.post(f'/deals/{deal_id}/remind')
    assert res.status_code == 403
    assert res.json['upgrade_required'] == True
    
def test_send_reminder_task():
    # Don't use the app fixture to avoid session tearing down mid-celery call
    test_app = create_app('testing')
    
    with test_app.app_context():
        # Ensure DB is created properly in this context for SQLite memory DBs
        db.create_all()
        
        from app.models.deal import Deal
        from app.models.invoice import Invoice
        from app.models.brand import Brand
        from app.models.user import User
        from app.tasks.reminders import send_reminder
        
        user = User(
            full_name='Test',
            email='test2@example.com',
            password_hash='dummy',
            plan='pro'
        )
        db.session.add(user)
        db.session.flush()
        
        brand = Brand(name="Remind Task Brand", user_id=user.id, email="brand@test.com")
        db.session.add(brand)
        db.session.flush()
        
        from datetime import datetime
        deal = Deal(user_id=user.id, brand_id=brand.id, amount=1000, content_type='post', due_date=datetime.now().date())
        db.session.add(deal)
        db.session.flush()
        
        invoice = Invoice(deal_id=deal.id, user_id=user.id, invoice_number="CP-0001", gross_amount=1000, net_amount=1000)
        db.session.add(invoice)
        db.session.commit()
        
        # Test task directly (runs synchronously when called directly)
        # Because send_reminder does a db lookup internally which fails if we are using an in-memory db
        # that was generated in the test but not globally accessible to the task wrapper, we bypass the celery wrapper
        result = send_reminder.run(deal.id)
        assert result.startswith("Reminder sent")
        
        db.session.refresh(deal)
        assert deal.reminder_sent_at is not None
