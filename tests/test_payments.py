import pytest
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
import bcrypt
import json

@pytest.fixture
def app():
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
def auth_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashed,
            plan='free'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    return client, user_id

def test_create_order(auth_client, app):
    client, user_id = auth_client
    
    res = client.post('/payments/create-order')
    assert res.status_code == 200
    assert 'id' in res.json
    assert res.json['amount'] == 29900

def test_payment_webhook(client, app):
    # Setup user
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashed,
            plan='free'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Mock webhook payload
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_mock123",
                    "amount": 29900,
                    "notes": {
                        "user_id": user_id,
                        "plan": "pro"
                    }
                }
            }
        }
    }
    
    # Send webhook
    res = client.post('/payments/webhook', 
                      data=json.dumps(payload), 
                      content_type='application/json')
    assert res.status_code == 200
    
    with app.app_context():
        # User plan should be updated
        u = User.query.get(user_id)
        assert u.plan == 'pro'
        
        # Subscription record should exist
        sub = Subscription.query.filter_by(user_id=user_id).first()
        assert sub is not None
        assert sub.plan == 'pro'
        assert sub.status == 'active'
        assert sub.razorpay_payment_id == 'pay_mock123'
